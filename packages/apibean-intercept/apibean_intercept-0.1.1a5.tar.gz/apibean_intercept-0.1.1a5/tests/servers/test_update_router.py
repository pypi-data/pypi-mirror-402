import pytest
import httpx

from fastapi import APIRouter, FastAPI
from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

@pytest.mark.asyncio
async def test_update_router_with_apirouter(mount_handler):
    """update_router với APIRouter"""
    router = APIRouter()

    @router.get("/hello")
    async def hello():
        return {"msg": "router"}

    server = EmbeddedAPIServerBase(verbose=False)
    server.update_router(router)

    app = mount_handler(server._handler)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/hello")

    assert resp.status_code == 200
    assert resp.json() == {"msg": "router"}


@pytest.mark.asyncio
async def test_update_router_with_fastapi_app(mount_handler):
    """update_router với FastAPI app"""
    app = FastAPI()

    @app.get("/hello")
    async def hello():
        return {"msg": "fastapi-app"}

    server = EmbeddedAPIServerBase(verbose=False)
    server.update_router(app)

    app2 = mount_handler(server._handler)

    transport = httpx.ASGITransport(app=app2)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/hello")

    assert resp.status_code == 200
    assert resp.json() == {"msg": "fastapi-app"}


def test_update_router_none_clears_handler():
    """Test: update_router(None) → clear handler"""
    server = EmbeddedAPIServerBase(verbose=False)
    server.update_router(None)

    assert server._handler is None


def test_update_router_invalid_type():
    """Test: truyền router sai type → TypeError"""
    server = EmbeddedAPIServerBase(verbose=False)

    with pytest.raises(TypeError):
        server.update_router(object())
