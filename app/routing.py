import logging
from typing import Any

from fastapi import HTTPException

from .config import settings
from .models import ChatRequest
from .providers import PROVIDERS, circuit_breaker, get_provider


logger = logging.getLogger(__name__)


def provider_configured(provider_name: str) -> bool:
    if provider_name == "mock":
        return True

    if provider_name == "openai":
        return bool(settings.openai_api_key)

    if provider_name == "anthropic":
        return bool(settings.anthropic_api_key)

    return False


def provider_health() -> dict[str, dict[str, Any]]:
    health: dict[str, dict[str, Any]] = {}

    for provider_name in PROVIDERS:
        configured = provider_configured(provider_name)
        circuit_open = circuit_breaker.is_open(provider_name)

        if not configured:
            status = "not_configured"
        elif circuit_open:
            status = "unavailable"
        else:
            status = "available"

        health[provider_name] = {
            "status": status,
            "configured": configured,
            "circuit_open": circuit_open,
        }

    return health


def failover_candidates(primary_provider: str) -> list[str]:
    order = [
        primary_provider,
        "openai",
        "anthropic",
        "mock",
    ]

    candidates: list[str] = []

    for provider_name in order:
        if provider_name not in PROVIDERS:
            continue

        if provider_name in candidates:
            continue

        if not provider_configured(provider_name):
            continue

        candidates.append(provider_name)

    return candidates


async def complete_with_failover(
    request: ChatRequest,
    primary_provider: str,
) -> dict[str, Any]:
    if primary_provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown provider: {primary_provider}",
        )

    candidates = failover_candidates(primary_provider)

    if not candidates:
        raise HTTPException(
            status_code=503,
            detail="No providers are available",
        )

    last_error: HTTPException | None = None

    for provider_name in candidates:
        if circuit_breaker.is_open(provider_name):
            logger.warning(
                "Skipping provider because circuit breaker is open",
                extra={
                    "provider": provider_name,
                },
            )
            continue

        provider = get_provider(provider_name)

        try:
            response = await provider.complete(request)

            if provider_name != primary_provider:
                logger.warning(
                    "Request completed using failover provider",
                    extra={
                        "provider": provider_name,
                    },
                )

            return response

        except HTTPException as exc:
            last_error = exc

            if exc.status_code not in {
                502,
                503,
                504,
            }:
                raise

            logger.warning(
                "Provider unavailable, attempting failover",
                extra={
                    "provider": provider_name,
                    "status_code": exc.status_code,
                },
            )

    if last_error is not None:
        raise HTTPException(
            status_code=503,
            detail="All available providers failed",
        ) from last_error

    raise HTTPException(
        status_code=503,
        detail="No healthy providers are available",
    )