import httpx
import pytest
from fastapi import HTTPException

from app.config import settings
from app.providers import circuit_breaker, post_with_retry


@pytest.mark.asyncio
async def test_retry_on_500(monkeypatch):
    calls = 0

    async def fake_post(self, url, headers=None, json=None):
        nonlocal calls
        calls += 1

        request = httpx.Request("POST", url)

        if calls < 3:
            return httpx.Response(
                500,
                request=request,
            )

        return httpx.Response(
            200,
            request=request,
            json={"ok": True},
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post,
    )

    monkeypatch.setattr(
        "app.providers.asyncio.sleep",
        no_sleep,
    )

    circuit_breaker.reset("unknown")

    response = await post_with_retry(
        "https://example.com/test",
        headers={},
        payload={},
    )

    assert response.status_code == 200
    assert calls == 3


@pytest.mark.asyncio
async def test_retry_on_429(monkeypatch):
    calls = 0

    async def fake_post(self, url, headers=None, json=None):
        nonlocal calls
        calls += 1

        request = httpx.Request("POST", url)

        if calls == 1:
            return httpx.Response(
                429,
                request=request,
            )

        return httpx.Response(
            200,
            request=request,
            json={"ok": True},
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post,
    )

    monkeypatch.setattr(
        "app.providers.asyncio.sleep",
        no_sleep,
    )

    circuit_breaker.reset("unknown")

    response = await post_with_retry(
        "https://example.com/test",
        headers={},
        payload={},
    )

    assert response.status_code == 200
    assert calls == 2


@pytest.mark.asyncio
async def test_timeout_becomes_504(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        request = httpx.Request(
            "POST",
            url,
        )

        raise httpx.ReadTimeout(
            "timeout",
            request=request,
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post,
    )

    monkeypatch.setattr(
        "app.providers.asyncio.sleep",
        no_sleep,
    )

    circuit_breaker.reset("unknown")

    with pytest.raises(HTTPException) as exc:
        await post_with_retry(
            "https://example.com/test",
            headers={},
            payload={},
        )

    assert exc.value.status_code == 504


@pytest.mark.asyncio
async def test_connection_error_becomes_502(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        request = httpx.Request(
            "POST",
            url,
        )

        raise httpx.ConnectError(
            "connection failed",
            request=request,
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post,
    )

    monkeypatch.setattr(
        "app.providers.asyncio.sleep",
        no_sleep,
    )

    circuit_breaker.reset("unknown")

    with pytest.raises(HTTPException) as exc:
        await post_with_retry(
            "https://example.com/test",
            headers={},
            payload={},
        )

    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_repeated_failures(
    monkeypatch,
):
    provider_name = "openai-test"

    circuit_breaker.reset(provider_name)

    async def fake_post(self, url, headers=None, json=None):
        request = httpx.Request(
            "POST",
            url,
        )

        return httpx.Response(
            500,
            request=request,
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post,
    )

    monkeypatch.setattr(
        "app.providers.asyncio.sleep",
        no_sleep,
    )

    for _ in range(
        settings.circuit_breaker_failure_threshold
    ):
        response = await post_with_retry(
            "https://example.com/test",
            headers={},
            payload={},
            provider_name=provider_name,
        )

        assert response.status_code == 500

    assert circuit_breaker.is_open(provider_name) is True

    circuit_breaker.reset(provider_name)


@pytest.mark.asyncio
async def test_open_circuit_blocks_request(
    monkeypatch,
):
    provider_name = "anthropic-test"

    circuit_breaker.reset(provider_name)

    for _ in range(
        settings.circuit_breaker_failure_threshold
    ):
        circuit_breaker.record_failure(provider_name)

    calls = 0

    async def fake_post(self, url, headers=None, json=None):
        nonlocal calls
        calls += 1

        request = httpx.Request(
            "POST",
            url,
        )

        return httpx.Response(
            200,
            request=request,
        )

    monkeypatch.setattr(
        httpx.AsyncClient,
        "post",
        fake_post,
    )

    with pytest.raises(HTTPException) as exc:
        await post_with_retry(
            "https://example.com/test",
            headers={},
            payload={},
            provider_name=provider_name,
        )

    assert exc.value.status_code == 503
    assert calls == 0

    circuit_breaker.reset(provider_name)