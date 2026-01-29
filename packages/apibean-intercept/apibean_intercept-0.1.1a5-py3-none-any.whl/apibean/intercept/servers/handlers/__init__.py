from typing import Literal

from fastapi import APIRouter

HANDLER_TYPE = Literal[
    'httpx_client',
    'httpx_client_stream',
    'asgi_sender',
    'asgi_sender_stream',
    'test_client'
]

def create_handler_from_router(router: APIRouter, default_router: APIRouter|None = None,
    handler_type: str | None = 'httpx_client',
):
    if handler_type == 'asgi_sender':
        from ._AsgiSender import create_handler_from_router as create_handler_from_router_rr
        return create_handler_from_router_rr(router, default_router=default_router)

    if handler_type == 'asgi_sender_stream':
        from ._AsgiSenderStream import create_handler_from_router as create_handler_from_router_aas
        return create_handler_from_router_aas(router, default_router=default_router)

    if handler_type == 'httpx_client':
        from ._HttpxClient import create_handler_from_router as create_handler_from_router_hc
        return create_handler_from_router_hc(router, default_router=default_router)

    if handler_type == 'httpx_client_stream':
        from ._HttpxClientStream import create_handler_from_router as create_handler_from_router_hcs
        return create_handler_from_router_hcs(router, default_router=default_router)

    from ._TestClient import create_handler_from_router as create_handler_from_router_tc
    return create_handler_from_router_tc(router, default_router=default_router)


from fastapi import FastAPI, Request, Response

def create_handler_from_app(app: FastAPI):
    from ._AsgiSenderAdapter import ASGIInterceptAdapter
    adapter = ASGIInterceptAdapter(app)
    async def asgi_handler(req: Request) -> Response:
        return await adapter.handle(req)
    return asgi_handler
