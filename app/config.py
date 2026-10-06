import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    default_provider: str = os.getenv(
        "OMNIROUTE_DEFAULT_PROVIDER",
        "mock",
    ).lower()

    rate_limit_per_minute: int = int(
        os.getenv(
            "OMNIROUTE_RATE_LIMIT_PER_MINUTE",
            "30",
        )
    )

    log_level: str = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    provider_timeout_seconds: float = float(
        os.getenv(
            "OMNIROUTE_PROVIDER_TIMEOUT_SECONDS",
            "30",
        )
    )

    provider_max_retries: int = int(
        os.getenv(
            "OMNIROUTE_PROVIDER_MAX_RETRIES",
            "2",
        )
    )

    provider_retry_backoff_seconds: float = float(
        os.getenv(
            "OMNIROUTE_PROVIDER_RETRY_BACKOFF_SECONDS",
            "0.5",
        )
    )

    circuit_breaker_failure_threshold: int = int(
        os.getenv(
            "OMNIROUTE_CIRCUIT_BREAKER_FAILURE_THRESHOLD",
            "3",
        )
    )

    circuit_breaker_recovery_timeout_seconds: float = float(
        os.getenv(
            "OMNIROUTE_CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS",
            "30",
        )
    )

    openai_api_key: str = os.getenv(
        "OPENAI_API_KEY",
        "",
    )

    openai_base_url: str = os.getenv(
        "OPENAI_BASE_URL",
        "https://api.openai.com/v1",
    ).rstrip("/")

    openai_default_model: str = os.getenv(
        "OPENAI_DEFAULT_MODEL",
        "",
    )

    anthropic_api_key: str = os.getenv(
        "ANTHROPIC_API_KEY",
        "",
    )

    anthropic_base_url: str = os.getenv(
        "ANTHROPIC_BASE_URL",
        "https://api.anthropic.com",
    ).rstrip("/")

    anthropic_default_model: str = os.getenv(
        "ANTHROPIC_DEFAULT_MODEL",
        "",
    )


settings = Settings()