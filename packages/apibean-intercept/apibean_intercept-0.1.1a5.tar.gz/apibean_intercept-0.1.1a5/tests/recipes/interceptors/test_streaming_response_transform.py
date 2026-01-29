import pytest
import asyncio

from apibean.intercept.brokers.models import ResponseContext, RequestContext
from apibean.intercept.recipes.interceptors import StreamingResponseTransformInterceptor


def make_ctx():
    return RequestContext(
        method="GET",
        path="/stream",
        headers={},
        query={},
        body=None,
        base_url="http://localhost",
        raw_request=None,
    )


async def async_stream(chunks):
    for c in chunks:
        await asyncio.sleep(0)
        yield c


@pytest.mark.asyncio
async def test_stream_is_wrapped():
    """streaming body được wrap"""
    interceptor = StreamingResponseTransformInterceptor()
    ctx = make_ctx()

    original_chunks = [b"a", b"b", b"c"]
    stream = async_stream(original_chunks)

    resp = ResponseContext(
        status_code=200,
        headers={},
        body=stream,
    )

    await interceptor.after_response(ctx, resp)

    collected = []
    async for c in resp.body:
        collected.append(c)

    assert collected == original_chunks


@pytest.mark.asyncio
async def test_transform_chunk_applied():
    """transform_chunk được áp dụng (ví dụ là upper())"""
    class TestInterceptor(StreamingResponseTransformInterceptor):
        async def transform_chunk(self, ctx, response, chunk):
            return chunk.upper()

    interceptor = TestInterceptor()
    ctx = make_ctx()

    resp = ResponseContext(
        status_code=200,
        headers={},
        body=async_stream([b"a", b"b"]),
    )

    await interceptor.after_response(ctx, resp)

    result = []
    async for c in resp.body:
        result.append(c)

    assert result == [b"A", b"B"]


@pytest.mark.asyncio
async def test_chunk_error_fails_soft():
    """lỗi trong chunk → bỏ qua (fail-soft)"""
    class TestInterceptor(StreamingResponseTransformInterceptor):
        async def transform_chunk(self, ctx, response, chunk):
            raise RuntimeError("boom")

    interceptor = TestInterceptor()
    ctx = make_ctx()

    original = [b"x", b"y"]
    resp = ResponseContext(
        status_code=200,
        headers={},
        body=async_stream(original),
    )

    await interceptor.after_response(ctx, resp)

    result = []
    async for c in resp.body:
        result.append(c)

    assert result == original


@pytest.mark.asyncio
async def test_non_streaming_response_ignored():
    """non-streaming response bị bỏ qua"""
    interceptor = StreamingResponseTransformInterceptor()
    ctx = make_ctx()

    resp = ResponseContext(
        status_code=200,
        headers={},
        body=b"plain",
    )

    await interceptor.after_response(ctx, resp)

    assert resp.body == b"plain"
