import asyncio
import pytest

from apibean.intercept.recipes.interceptors import NDJSONEnrichmentInterceptor
from apibean.intercept.brokers.models import RequestContext, ResponseContext


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
async def test_ndjson_chunk_is_enriched():
    def enrich(data, ctx, response):
        data["extra"] = "ok"

    interceptor = NDJSONEnrichmentInterceptor(enrich)
    ctx = make_ctx()

    chunks = [b'{"a": 1}']
    resp = ResponseContext(
        status_code=200,
        headers={"content-type": "application/x-ndjson"},
        body=async_stream(chunks),
    )

    await interceptor.after_response(ctx, resp)

    result = []
    async for c in resp.body:
        result.append(c)

    assert result == [b'{"a": 1, "extra": "ok"}\n']


@pytest.mark.asyncio
async def test_multiple_ndjson_chunks():
    """nhiều chunk NDJSON được xử lý độc lập"""
    def enrich(data, ctx, response):
        data["x"] = True

    interceptor = NDJSONEnrichmentInterceptor(enrich)
    ctx = make_ctx()

    chunks = [b'{"i": 1}', b'{"i": 2}']
    resp = ResponseContext(
        status_code=200,
        headers={},
        body=async_stream(chunks),
    )

    await interceptor.after_response(ctx, resp)

    result = []
    async for c in resp.body:
        result.append(c)

    assert result == [
        b'{"i": 1, "x": true}\n',
        b'{"i": 2, "x": true}\n',
    ]


@pytest.mark.asyncio
async def test_invalid_json_chunk_pass_through():
    """chunk không phải JSON → giữ nguyên"""
    def enrich(data, ctx, response):
        data["x"] = 1

    interceptor = NDJSONEnrichmentInterceptor(enrich)
    ctx = make_ctx()

    chunks = [b'not-json\n']
    resp = ResponseContext(
        status_code=200,
        headers={},
        body=async_stream(chunks),
    )

    await interceptor.after_response(ctx, resp)

    result = []
    async for c in resp.body:
        result.append(c)

    assert result == [b'not-json\n']


@pytest.mark.asyncio
async def test_transform_exception_is_ignored():
    """transform_data raise exception → chunk giữ nguyên"""
    def enrich(data, ctx, response):
        raise RuntimeError("boom")

    interceptor = NDJSONEnrichmentInterceptor(enrich)
    ctx = make_ctx()

    chunk = b'{"a": 1}'
    resp = ResponseContext(
        status_code=200,
        headers={},
        body=async_stream([chunk]),
    )

    await interceptor.after_response(ctx, resp)

    result = []
    async for c in resp.body:
        result.append(c)

    assert result == [chunk]


@pytest.mark.asyncio
async def test_non_callable_transform_is_ignored():
    """transform_data không callable → passthrough"""
    interceptor = NDJSONEnrichmentInterceptor(transform_data=None)
    ctx = make_ctx()

    chunk = b'{"a": 1}'
    resp = ResponseContext(
        status_code=200,
        headers={},
        body=async_stream([chunk]),
    )

    await interceptor.after_response(ctx, resp)

    result = []
    async for c in resp.body:
        result.append(c)

    assert result == [chunk]
