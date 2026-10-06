from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "omniroute-cloud",
        "default_provider": "mock",
    }


def test_mock_chat_completion():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "mock-1",
            "messages": [
                {
                    "role": "user",
                    "content": "hello",
                }
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["content"] == (
        "OmniRoute mock response: hello"
    )


def test_unknown_provider():
    response = client.post(
        "/v1/chat/completions",
        headers={
            "X-OmniRoute-Provider": "missing",
        },
        json={
            "messages": [
                {
                    "role": "user",
                    "content": "hello",
                }
            ],
        },
    )

    assert response.status_code == 400


def test_openai_falls_back_to_mock_when_not_configured():
    response = client.post(
        "/v1/chat/completions",
        headers={
            "X-OmniRoute-Provider": "openai",
        },
        json={
            "model": "mock-1",
            "messages": [
                {
                    "role": "user",
                    "content": "hello failover",
                }
            ],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["choices"][0]["message"]["content"] == (
        "OmniRoute mock response: hello failover"
    )