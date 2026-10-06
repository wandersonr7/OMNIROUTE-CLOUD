import time
from dataclasses import dataclass


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float | None = None


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._states: dict[str, CircuitState] = {}

    def _state(self, provider: str) -> CircuitState:
        if provider not in self._states:
            self._states[provider] = CircuitState()
        return self._states[provider]

    def is_open(self, provider: str) -> bool:
        state = self._state(provider)

        if state.opened_at is None:
            return False

        elapsed = time.monotonic() - state.opened_at

        if elapsed >= self.recovery_timeout_seconds:
            state.failures = 0
            state.opened_at = None
            return False

        return True

    def record_success(self, provider: str) -> None:
        state = self._state(provider)
        state.failures = 0
        state.opened_at = None

    def record_failure(self, provider: str) -> None:
        state = self._state(provider)
        state.failures += 1

        if state.failures >= self.failure_threshold:
            state.opened_at = time.monotonic()

    def reset(self, provider: str) -> None:
        self._states[provider] = CircuitState()