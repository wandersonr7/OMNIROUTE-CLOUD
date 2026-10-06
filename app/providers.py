import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any

import httpx
from fastapi import HTTPException

from .circuit_breaker import CircuitBreaker
from .config import settings
from .models import ChatRequest


logger = logging.getLogger(__name__)


circuit_breaker = CircuitBreaker(
    failure_threshold=settings.circuit_breaker_failure_threshold,
    recovery_timeout_seconds=(
        settings.circuit_breaker_recovery_timeout_seconds
    ),
)


class Provider(ABC):
    @abstractmethod
    async def complete(self, request: ChatRequest) -> dict[str, Any]:
        raise NotImplementedError


def openai_response(model: str, content: str) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


async def post_with_retry(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    provider_name: str = "unknown",
) -> httpx.Response:
    if circuit_breaker.is_open(provider_name):
        logger.warning(
            "Provider circuit breaker is open",
            extra={
                "provider": provider_name,
            },
        )

        raise HTTPException(
            status_code=503,
            detail=f"Provider temporarily unavailable: {provider_name}",
        )

    attempts = settings.provider_max_retries + 1

    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(
                timeout=settings.provider_timeout_seconds
            ) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

            if response.status_code == 429 or response.status_code >= 500:
                if attempt < attempts - 1:
                    delay = (
                        settings.provider_retry_backoff_seconds
                        * (2 ** attempt)
                    )

                    logger.warning(
                        "Retrying upstream provider request",
                        extra={
                            "provider": provider_name,
                            "attempt": attempt + 1,
                            "status_code": response.status_code,
                            "backoff_seconds": delay,
                        },
                    )

                    await asyncio.sleep(delay)
                    continue

                circuit_breaker.record_failure(provider_name)

                logger.error(
                    "Upstream provider failed after retries",
                    extra={
                        "provider": provider_name,
                        "attempt": attempt + 1,
                        "status_code": response.status_code,
                    },
                )

                return response

            circuit_breaker.record_success(provider_name)
            return response

        except httpx.TimeoutException as exc:
            if attempt >= attempts - 1:
                circuit_breaker.record_failure(provider_name)

                logger.error(
                    "Upstream provider timeout",
                    extra={
                        "provider": provider_name,
                        "attempt": attempt + 1,
                    },
                )

                raise HTTPException(
                    status_code=504,
                    detail="Upstream provider timeout",
                ) from exc

        except httpx.RequestError as exc:
            if attempt >= attempts - 1:
                circuit_breaker.record_failure(provider_name)

                logger.error(
                    "Upstream provider connection error",
                    extra={
                        "provider": provider_name,
                        "attempt": attempt + 1,
                    },
                )

                raise HTTPException(
                    status_code=502,
                    detail="Upstream provider connection error",
                ) from exc

        delay = settings.provider_retry_backoff_seconds * (2 ** attempt)

        logger.warning(
            "Retrying upstream provider request after exception",
            extra={
                "provider": provider_name,
                "attempt": attempt + 1,
                "backoff_seconds": delay,
            },
        )

        await asyncio.sleep(delay)

    circuit_breaker.record_failure(provider_name)

    raise HTTPException(
        status_code=502,
        detail="Upstream provider request failed",
    )


class MockProvider(Provider):
    async def complete(self, request: ChatRequest) -> dict[str, Any]:
        last_user = next(
            (
                message.content
                for message in reversed(request.messages)
                if message.role == "user"
            ),
            "",
        )

        return openai_response(
            request.model or "mock-1",
            f"OmniRoute mock response: {last_user}",
        )


class OpenAICompatibleProvider(Provider):
    async def complete(
        self,
        request: ChatRequest,
    ) -> dict[str, Any]:
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=503,
                detail="OPENAI_API_KEY is not configured",
            )

        payload = request.model_dump(exclude_none=True)
        payload["model"] = (
            request.model or settings.openai_default_model
        )

        if not payload["model"]:
            raise HTTPException(
                status_code=400,
                detail="A model is required for the OpenAI provider",
            )

        response = await post_with_retry(
            f"{settings.openai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
            },
            payload=payload,
            provider_name="openai",
        )

        if response.is_error:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Upstream provider error: "
                    f"{response.status_code}"
                ),
            )

        return response.json()


class AnthropicProvider(Provider):
    async def complete(
        self,
        request: ChatRequest,
    ) -> dict[str, Any]:
        if not settings.anthropic_api_key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY is not configured",
            )

        model = request.model or settings.anthropic_default_model

        if not model:
            raise HTTPException(
                status_code=400,
                detail=(
                    "A model is required for the Anthropic provider"
                ),
            )

        system_parts = [
            message.content
            for message in request.messages
            if message.role == "system"
        ]

        messages = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in request.messages
            if message.role != "system"
        ]

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or 1024,
        }

        if system_parts:
            payload["system"] = "\n".join(system_parts)

        if request.temperature is not None:
            payload["temperature"] = request.temperature

        response = await post_with_retry(
            f"{settings.anthropic_base_url}/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            payload=payload,
            provider_name="anthropic",
        )

        if response.is_error:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Upstream provider error: "
                    f"{response.status_code}"
                ),
            )

        data = response.json()

        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )

        result = openai_response(
            model,
            text,
        )

        result["id"] = data.get(
            "id",
            result["id"],
        )

        return result


PROVIDERS: dict[str, Provider] = {
    "mock": MockProvider(),
    "openai": OpenAICompatibleProvider(),
    "anthropic": AnthropicProvider(),
}


def get_provider(name: str) -> Provider:
    provider = PROVIDERS.get(name.lower())

    if provider is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {name}",
        )

    return provider