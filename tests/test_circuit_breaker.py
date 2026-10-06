from app.circuit_breaker import CircuitBreaker


def test_circuit_starts_closed():
    breaker = CircuitBreaker()

    assert breaker.is_open("openai") is False


def test_circuit_opens_after_threshold():
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout_seconds=30,
    )

    breaker.record_failure("openai")
    breaker.record_failure("openai")

    assert breaker.is_open("openai") is False

    breaker.record_failure("openai")

    assert breaker.is_open("openai") is True


def test_success_resets_failures():
    breaker = CircuitBreaker(failure_threshold=3)

    breaker.record_failure("openai")
    breaker.record_failure("openai")

    breaker.record_success("openai")

    assert breaker.is_open("openai") is False


def test_providers_are_tracked_separately():
    breaker = CircuitBreaker(failure_threshold=2)

    breaker.record_failure("openai")
    breaker.record_failure("openai")

    assert breaker.is_open("openai") is True
    assert breaker.is_open("anthropic") is False


def test_reset_closes_circuit():
    breaker = CircuitBreaker(failure_threshold=1)

    breaker.record_failure("openai")
    assert breaker.is_open("openai") is True

    breaker.reset("openai")

    assert breaker.is_open("openai") is False