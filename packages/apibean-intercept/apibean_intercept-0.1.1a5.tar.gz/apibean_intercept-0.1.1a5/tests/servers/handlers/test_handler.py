import pytest

import json
import asyncio

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from starlette.testclient import TestClient


@pytest.mark.asyncio
async def test_router_not_found(mount_handler, handler_factory):
    """
    Trường hợp router không có endpoint tương ứng.
    """
    router = APIRouter()

    client = TestClient(mount_handler(handler_factory(router)))
    resp = client.get("/missing")

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_basic_json_response_body(mount_handler, handler_factory):
    router = APIRouter()

    @router.get("/hello")
    async def hello():
        return {"msg": "world"}

    client = TestClient(mount_handler(handler_factory(router)))
    resp = client.get("/hello")

    assert resp.status_code == 200
    assert resp.json() == {"msg": "world"}


@pytest.mark.asyncio
async def test_normal_response_body_and_headers(mount_handler, handler_factory):
    """Trường hợp response thường, body trả về một lần."""
    router = APIRouter()

    @router.get("/hello")
    async def hello():
        return Response(
            content=b"hello world",
            media_type="text/plain",
            headers={"x-test": "1"},
        )

    client = TestClient(mount_handler(handler_factory(router)))
    resp = client.get("/hello")

    assert resp.status_code == 200
    assert resp.text == "hello world"
    assert resp.headers["content-type"].startswith("text/plain")
    assert resp.headers["x-test"] == "1"


@pytest.mark.filterwarnings(
    "ignore:Use 'content=<...>' to upload raw bytes/text content.:DeprecationWarning"
)
@pytest.mark.asyncio
async def test_empty_body(mount_handler, handler_factory):
    router = APIRouter()

    @router.post("/empty")
    async def empty(request: Request):
        body = await request.body()
        return JSONResponse({"body": body.decode()})

    client = TestClient(mount_handler(handler_factory(router)))
    resp = client.post("/empty")

    assert resp.status_code == 200
    assert resp.json()["body"] == ""


@pytest.mark.asyncio
async def test_streaming_response(mount_handler, handler_factory):
    router = APIRouter()

    async def gen():
        for i in range(3):
            yield json.dumps({"i": i}).encode() + b"\n"
            await asyncio.sleep(0)

    @router.get("/stream")
    async def stream():
        return StreamingResponse(gen(), media_type="application/x-ndjson")

    client = TestClient(mount_handler(handler_factory(router)))
    resp = client.get("/stream")

    lines = resp.text.strip().splitlines()
    assert len(lines) == 3
    assert json.loads(lines[0])["i"] == 0
