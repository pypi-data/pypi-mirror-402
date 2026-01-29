import pytest

from apibean.intercept.brokers.models import ResponseContext, RequestContext
from apibean.intercept.recipes.interceptors import ResponseTransformInterceptor


def make_ctx():
    return RequestContext(
        method="GET",
        path="/test",
        headers={},
        query={},
        body=None,
        base_url="http://localhost",
        raw_request=None,
    )


def make_json_response(body: dict):
    return ResponseContext(
        status_code=200,
        headers={"content-type": "application/json"},
        body=body,
    )


@pytest.mark.asyncio
async def test_skip_non_json_response():
    """Không transform nếu không phải JSON"""
    interceptor = ResponseTransformInterceptor()

    ctx = make_ctx()
    resp = ResponseContext(
        status_code=200,
        headers={"content-type": "text/plain"},
        body=b"hello",
    )

    await interceptor.after_response(ctx, resp)

    assert resp.body == b"hello"


@pytest.mark.asyncio
async def test_transform_body_applied():
    """transform_body được gọi và áp dụng vào body"""
    class TestInterceptor(ResponseTransformInterceptor):
        def transform_body(self, data):
            data["x"] = 1

    interceptor = TestInterceptor()
    ctx = make_ctx()
    resp = make_json_response({"a": 0})

    await interceptor.after_response(ctx, resp)

    assert b'"x": 1' in resp.body


@pytest.mark.asyncio
async def test_transform_headers_applied():
    """transform_headers được áp dụng"""
    class TestInterceptor(ResponseTransformInterceptor):
        def transform_headers(self, headers):
            headers["x-test"] = "ok"

    interceptor = TestInterceptor()
    ctx = make_ctx()
    resp = make_json_response({"a": 1})

    await interceptor.after_response(ctx, resp)

    assert resp.headers["x-test"] == "ok"


@pytest.mark.asyncio
async def test_parse_and_serialize_bytes_body():
    """body bytes → parse → serialize đúng"""
    class TestInterceptor(ResponseTransformInterceptor):
        def transform_body(self, data):
            data["added"] = True

    interceptor = TestInterceptor()
    ctx = make_ctx()

    resp = ResponseContext(
        status_code=200,
        headers={"content-type": "application/json"},
        body=b'{"a": 1}',
    )

    await interceptor.after_response(ctx, resp)

    assert b'"added": true' in resp.body


@pytest.mark.asyncio
async def test_transform_error_is_ignored():
    """lỗi trong transform không làm đứt đoạn response"""
    class TestInterceptor(ResponseTransformInterceptor):
        def transform_body(self, data):
            raise RuntimeError("boom")

    interceptor = TestInterceptor()
    ctx = make_ctx()
    original_body = b'{"a": 1}'

    resp = ResponseContext(
        status_code=200,
        headers={"content-type": "application/json"},
        body=original_body,
    )

    await interceptor.after_response(ctx, resp)

    # body giữ nguyên (fail-soft)
    assert resp.body == original_body
