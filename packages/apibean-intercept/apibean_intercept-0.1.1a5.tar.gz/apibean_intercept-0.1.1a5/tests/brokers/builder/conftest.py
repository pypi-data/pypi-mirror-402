import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apibean.intercept.brokers.builder import InterceptBuilder
from apibean.intercept.brokers.models import ResponseContext


@pytest.fixture
def app():
    app = FastAPI()
    return app


@pytest.fixture
def builder():
    return InterceptBuilder(upstream_base="http://upstream")


@pytest.fixture
def client(app, builder):
    app.include_router(builder.router)
    return TestClient(app)


import asyncio
import json
import time
from typing import AsyncIterator

@pytest.fixture
def async_generator():
    async def stream() -> AsyncIterator[bytes]:
        for i in range(5):
            log = {
                "level": "INFO",
                "message": f"log message {i}",
                "timestamp": time.time(),
            }
            yield json.dumps(log).encode("utf-8") + b"\n"
            await asyncio.sleep(1)
    return stream
