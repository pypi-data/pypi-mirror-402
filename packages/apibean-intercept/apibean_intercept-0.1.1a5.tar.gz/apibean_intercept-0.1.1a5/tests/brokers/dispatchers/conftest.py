import pytest

from fastapi import FastAPI

from apibean.intercept.brokers.builder import InterceptBuilder

@pytest.fixture
def simple_fastapi_app():
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/text")
    async def text():
        return "hello"

    return app


@pytest.fixture
def builder():
    return InterceptBuilder(
        upstream_base="http://upstream"
    )
