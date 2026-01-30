import asyncio
import os
import sys

import httpx
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from philvault_sdk import AsyncPhilVaultClient, PhilVaultClient


def test_from_env_requires_base_url_and_api_key(monkeypatch):
    monkeypatch.delenv("PHILVAULT_BASE_URL", raising=False)
    monkeypatch.delenv("PHILVAULT_API_KEY", raising=False)

    with pytest.raises(ValueError):
        PhilVaultClient.from_env()


def test_sync_request_headers_and_url():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://example.com/healthz")
        assert request.headers["X-API-Key"] == "test-key"
        assert request.headers["Authorization"] == "Bearer token-123"
        assert request.headers["User-Agent"] == "philvault-sdk/0.1.0"
        assert request.headers["X-Trace-Id"] == "trace-1"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    httpx_client = httpx.Client(transport=transport)

    client = PhilVaultClient(
        base_url="http://example.com",
        api_key="test-key",
        access_token="token-123",
        extra_headers={"X-Trace-Id": "trace-1"},
        client=httpx_client,
    )

    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_sync_helper_returns_json():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://example.com/api/v1/auth/me/")
        return httpx.Response(200, json={"username": "alice"})

    transport = httpx.MockTransport(handler)
    httpx_client = httpx.Client(transport=transport)

    client = PhilVaultClient(
        base_url="http://example.com",
        api_key="test-key",
        client=httpx_client,
    )

    result = client.me()
    assert result == {"username": "alice"}


def test_async_request_headers_and_url():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://example.com/healthz")
        assert request.headers["X-API-Key"] == "test-key"
        assert request.headers["Authorization"] == "Bearer token-123"
        return httpx.Response(200, json={"ok": True})

    async def run():
        transport = httpx.MockTransport(handler)
        httpx_client = httpx.AsyncClient(transport=transport)

        async with AsyncPhilVaultClient(
            base_url="http://example.com",
            api_key="test-key",
            access_token="token-123",
            client=httpx_client,
        ) as client:
            response = await client.get("/healthz")
            assert response.status_code == 200
            assert response.json() == {"ok": True}

    asyncio.run(run())
