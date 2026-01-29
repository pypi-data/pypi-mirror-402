import httpx

from typing import Callable, Awaitable

from fastapi import APIRouter, FastAPI, Request, Response

from ._HttpxClientAdapter import HttpxInterceptAdapter


def create_handler_from_router(router: APIRouter, default_router: APIRouter|None = None) \
        -> Callable[[Request], Awaitable[Response]]:

    app = FastAPI()
    app.include_router(router)
    if default_router:
        app.include_router(default_router)

    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
        base_url="http://internal")

    adapter = HttpxInterceptAdapter(client)

    async def handler(req: Request) -> Response:
        return await adapter.handle(req)

    return handler
