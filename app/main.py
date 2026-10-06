import logging
import uuid

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from .config import settings
from .logging_config import configure_logging
from .models import ChatRequest, HealthResponse
from .rate_limit import InMemoryRateLimiter
from .routing import complete_with_failover, provider_health


configure_logging(settings.log_level)

logger = logging.getLogger("omniroute")
limiter = InMemoryRateLimiter(settings.rate_limit_per_minute)


app = FastAPI(
    title="OmniRoute Cloud",
    version="0.1.0",
    description="Multi-provider AI routing gateway",
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex

    try:
        response = await call_next(request)

    except Exception:
        logger.exception(
            "Unhandled request error",
            extra={
                "request_id": request_id,
            },
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
            },
        )

    response.headers["x-request-id"] = request_id

    logger.info(
        f"{request.method} {request.url.path} {response.status_code}",
        extra={
            "request_id": request_id,
        },
    )

    return response


@app.get(
    "/health",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="omniroute-cloud",
        default_provider=settings.default_provider,
    )


@app.get("/health/providers")
async def health_providers():
    return {
        "providers": provider_health(),
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    payload: ChatRequest,
    request: Request,
    x_omniroute_provider: str | None = Header(
        default=None,
    ),
):
    client = (
        request.client.host
        if request.client
        else "unknown"
    )

    limiter.check(client)

    provider_name = (
        x_omniroute_provider
        or settings.default_provider
    )

    return await complete_with_failover(
        payload,
        provider_name,
    )