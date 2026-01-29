import json
import pytest
import httpx

from fastapi import Request
from starlette.requests import Request as StarletteRequest
from starlette.datastructures import Headers
from starlette.types import Scope

from apibean.intercept.brokers.dispatchers.fastapi_app import FastAPIAppDispatcher
from apibean.intercept.brokers.models import RequestContext, ResponseContext


@pytest.mark.asyncio
async def test_match_without_prefix(simple_fastapi_app):
    dispatcher = FastAPIAppDispatcher(simple_fastapi_app)

    ctx = RequestContext(
        method="GET",
        path="/any/path",
        headers={},
        query={},
        body=None,
        base_url="http://test",
        raw_request=None,
    )

    assert dispatcher.match(ctx) is True


@pytest.mark.asyncio
async def test_match_with_prefix(simple_fastapi_app):
    dispatcher = FastAPIAppDispatcher(
        simple_fastapi_app,
        match_prefix="/internal",
    )

    ctx1 = RequestContext(
        method="GET",
        path="/internal/health",
        headers={},
        query={},
        body=None,
        base_url="http://test",
        raw_request=None,
    )

    ctx2 = RequestContext(
        method="GET",
        path="/public",
        headers={},
        query={},
        body=None,
        base_url="http://test",
        raw_request=None,
    )

    assert dispatcher.match(ctx1) is True
    assert dispatcher.match(ctx2) is False


@pytest.mark.asyncio
async def test_dispatch_returns_response_context(simple_fastapi_app):
    dispatcher = FastAPIAppDispatcher(simple_fastapi_app)

    scope: Scope = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "headers": [],
        "query_string": b"",
        "scheme": "http",
        "server": ("test", 80),
        "client": ("test", 1234),
    }

    request = StarletteRequest(scope, receive=lambda: None)

    ctx = RequestContext(
        method="GET",
        path="/health",
        headers={},
        query={},
        body=None,
        base_url="http://test",
        raw_request=request,
    )

    resp = await dispatcher.handle(ctx)

    assert isinstance(resp, ResponseContext)
    assert resp.status_code == 200
    assert b"ok" in resp.body


@pytest.mark.asyncio
async def test_dispatcher_used_in_broker(simple_fastapi_app, builder, mount_handler):
    dispatcher = FastAPIAppDispatcher(
        simple_fastapi_app,
        match_prefix="/health",
    )

    builder.broker.dispatchers.append(dispatcher)

    app = mount_handler(builder.router, is_asgi_app=False)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_fallback_used_when_not_matching(monkeypatch, builder, mount_handler):
    async def fake_forward(ctx, upstream):
        return ResponseContext(200, {}, b'{"source": "upstream"}')

    monkeypatch.setattr(builder.broker, "_forward", fake_forward)
    monkeypatch.setattr(
        builder.broker.resolver_chain,
        "resolve",
        lambda ctx: "http://upstream",
    )

    app = mount_handler(builder.router, is_asgi_app=False)

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        resp = await client.get("/fallback")

    assert resp.status_code == 200
    assert resp.json() == {"source": "upstream"}
