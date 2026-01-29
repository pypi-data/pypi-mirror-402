import pytest
import asyncio
import httpx
import json

from apibean.intercept.brokers.builder import InterceptBuilder
from apibean.intercept.brokers.models import ResponseContext, RequestContext
from apibean.intercept.recipes.dispatchers import ProgressStreamDispatcher


@pytest.mark.asyncio
async def test_normal_progress_streaming(default_handler, mount_handler):

    async def example_progress(ctx):
        total = 5
        for i in range(1, total + 1):
            yield {
                "step": i,
                "total": total,
                "percent": int(i / total * 100),
                "message": f"processing step {i}",
            }
            await asyncio.sleep(0.1)

    dispatcher = ProgressStreamDispatcher(
        match_path="/progress",
        progress_generator=example_progress,
    )

    builder = InterceptBuilder("http://upstream")
    builder.broker.dispatchers.append(dispatcher)
    app = mount_handler(default_handler(builder.router))
    transport = httpx.ASGITransport(app=app)

    lines = []
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream("GET", "/progress") as resp:
            async for line in resp.aiter_lines():
                lines.append(json.loads(line))
    assert lines == [
        {'step': 1, 'total': 5, 'percent': 20, 'message': 'processing step 1'},
        {'step': 2, 'total': 5, 'percent': 40, 'message': 'processing step 2'},
        {'step': 3, 'total': 5, 'percent': 60, 'message': 'processing step 3'},
        {'step': 4, 'total': 5, 'percent': 80, 'message': 'processing step 4'},
        {'step': 5, 'total': 5, 'percent': 100, 'message': 'processing step 5'},
    ]


@pytest.mark.asyncio
async def test_progress_generator_yield_nothing(default_handler, mount_handler):
    """Generator không yield gì → stream kết thúc ngay, không có line nào."""

    async def empty_progress(ctx):
        if False:
            yield None

    dispatcher = ProgressStreamDispatcher(
        match_path="/progress",
        progress_generator=empty_progress,
    )

    builder = InterceptBuilder("http://upstream")
    builder.broker.dispatchers.append(dispatcher)

    app = mount_handler(default_handler(builder.router))
    transport = httpx.ASGITransport(app=app)

    lines = []
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream("GET", "/progress") as resp:
            async for line in resp.aiter_lines():
                lines.append(line)

    assert not lines


@pytest.mark.asyncio
async def test_progress_generator_yield_non_dict(default_handler, mount_handler):
    """Generator yield list / primitive → vẫn được JSON dump bình thường."""

    async def progress(ctx):
        yield [1, 2, 3]
        yield "done"

    dispatcher = ProgressStreamDispatcher(
        match_path="/progress",
        progress_generator=progress,
    )

    builder = InterceptBuilder("http://upstream")
    builder.broker.dispatchers.append(dispatcher)

    app = mount_handler(default_handler(builder.router))
    transport = httpx.ASGITransport(app=app)

    lines = []
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream("GET", "/progress") as resp:
            async for line in resp.aiter_lines():
                lines.append(json.loads(line))

    assert lines == [[1, 2, 3], "done"]


@pytest.mark.asyncio
async def test_progress_generator_raise_exception(default_handler, mount_handler):
    """Generator raise exception → stream dừng, các chunk trước đó vẫn được gửi."""

    async def progress(ctx):
        yield {"step": 1}
        raise RuntimeError("boom")

    dispatcher = ProgressStreamDispatcher(
        match_path="/progress",
        progress_generator=progress,
    )

    builder = InterceptBuilder("http://upstream")
    builder.broker.dispatchers.append(dispatcher)

    app = mount_handler(default_handler(builder.router))
    transport = httpx.ASGITransport(app=app)

    lines = []
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream("GET", "/progress") as resp:
            async for line in resp.aiter_lines():
                lines.append(json.loads(line))

    assert lines == [{"step": 1}]


@pytest.mark.asyncio
async def test_progress_sync_generator(default_handler, mount_handler):
    """progress_generator là generator thường (sync), dispatcher phải xử lý được."""

    def progress(ctx):
        for i in range(3):
            yield {"step": i + 1}

    dispatcher = ProgressStreamDispatcher(
        match_path="/progress",
        progress_generator=progress,
    )

    builder = InterceptBuilder("http://upstream")
    builder.broker.dispatchers.append(dispatcher)

    app = mount_handler(default_handler(builder.router))
    transport = httpx.ASGITransport(app=app)

    lines = []
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream("GET", "/progress") as resp:
            async for line in resp.aiter_lines():
                lines.append(json.loads(line))

    assert lines == [{"step": 1}, {"step": 2}, {"step": 3}]


@pytest.mark.asyncio
async def test_progress_stream_headers(default_handler, mount_handler):
    """Kiểm tra headers đặc trưng: content-type -> "application/x-ndjson"""

    async def progress(ctx):
        yield {"ok": True}

    dispatcher = ProgressStreamDispatcher(
        match_path="/progress",
        progress_generator=progress,
    )

    builder = InterceptBuilder("http://upstream")
    builder.broker.dispatchers.append(dispatcher)

    app = mount_handler(default_handler(builder.router))
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        async with client.stream("GET", "/progress") as resp:
            assert resp.headers["content-type"].startswith("application/x-ndjson")
            assert "content-length" in resp.headers
