import httpx
import pytest
from fastapi import HTTPException

from app.providers import post_with_retry


@pytest.mark.asyncio
async def test_retry_on_500(monkeypatch):
    calls = 0

    async def fake_post(self, url, headers=None, json=None):
        nonlocal calls
        calls += 1

        request = httpx.Request("POST", url)

        if calls < 3:
            return httpx.Response(500, request=request)

        return httpx.Response(
            200,
            request=request,
            json={"ok": True},
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr("app.providers.asyncio.sleep", no_sleep)

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
            return httpx.Response(429, request=request)

        return httpx.Response(
            200,
            request=request,
            json={"ok": True},
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr("app.providers.asyncio.sleep", no_sleep)

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
        request = httpx.Request("POST", url)
        raise httpx.ReadTimeout(
            "timeout",
            request=request,
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr("app.providers.asyncio.sleep", no_sleep)

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
        request = httpx.Request("POST", url)
        raise httpx.ConnectError(
            "connection failed",
            request=request,
        )

    async def no_sleep(delay):
        return None

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr("app.providers.asyncio.sleep", no_sleep)

    with pytest.raises(HTTPException) as exc:
        await post_with_retry(
            "https://example.com/test",
            headers={},
            payload={},
        )

    assert exc.value.status_code == 502