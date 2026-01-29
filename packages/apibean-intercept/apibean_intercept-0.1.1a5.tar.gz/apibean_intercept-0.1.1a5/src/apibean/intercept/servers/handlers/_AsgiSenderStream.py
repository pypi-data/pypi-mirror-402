from typing import Callable, Awaitable

from fastapi import APIRouter, FastAPI, Request, Response

from ._AsgiSenderAdapter import ASGIInterceptAdapter


def create_handler_from_router(router: APIRouter, default_router: APIRouter|None = None) \
        -> Callable[[Request], Awaitable[Response]]:

    app = FastAPI()
    app.include_router(router)
    if default_router:
        app.include_router(default_router)

    adapter = ASGIInterceptAdapter(app)

    async def handler(req: Request) -> Response:
        return await adapter.handle(req)

    return handler
