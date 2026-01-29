import pytest

from fastapi import APIRouter, FastAPI, Request, Response

@pytest.fixture()
def mount_handler():
    def mount_handler_(handler, is_asgi_app: bool = True):
        if not is_asgi_app:
            app = FastAPI()
            app.include_router(handler)
            return app
        async def asgi_app(scope, receive, send):
            request = Request(scope, receive=receive)
            response = await handler(request)
            await response(scope, receive, send)
        return asgi_app
    return mount_handler_
