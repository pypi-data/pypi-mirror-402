import pytest

from fastapi.responses import StreamingResponse

from apibean.intercept.brokers.builder import InterceptBuilder
from apibean.intercept.brokers.models import RequestContext, ResponseContext
from apibean.intercept.utils.http_util import HTTP_METHODS

http_methods = [method.lower() for method in HTTP_METHODS]

def test_builder_initialization(builder):
    """
    Đảm bảo InterceptBuilder khởi tạo đầy đủ các thành phần cốt lõi.

    Test này xác nhận:
    - APIRouter được tạo sẵn để gắn vào FastAPI app
    - InterceptBroker được khởi tạo và sẵn sàng dispatch request
    """
    assert builder.router is not None
    assert builder.broker is not None


def test_proxy_calls_broker_dispatch(client, builder, monkeypatch):
    """
    Đảm bảo proxy route chuyển tiếp request vào InterceptBroker.

    Test này xác nhận:
    - Router nhận request bất kỳ path
    - broker.dispatch() được gọi đúng một lần
    - ResponseContext trả về được unwrap thành Response
    """
    called = {}

    async def fake_dispatch(ctx):
        called["ctx"] = ctx
        return ResponseContext(
            status_code=200,
            headers={"x-test": "1"},
            body=b"OK",
        )

    monkeypatch.setattr(builder.broker, "dispatch", fake_dispatch)

    resp = client.get("/hello")

    assert resp.status_code == 200
    assert resp.text == "OK"
    assert "ctx" in called


def test_build_context_json_body(client, builder, monkeypatch):
    """
    Đảm bảo body JSON được parse đúng khi client gửi application/json.

    Test này bảo vệ logic:
    - request.json() được ưu tiên
    - ctx.body là object Python, không phải raw bytes
    """
    captured = {}

    async def fake_dispatch(ctx):
        captured["body"] = ctx.body
        return ResponseContext(200, {}, b"OK")

    monkeypatch.setattr(builder.broker, "dispatch", fake_dispatch)

    resp = client.post("/json", json={"a": 1})

    assert resp.status_code == 200
    assert captured["body"] == {"a": 1}


def test_build_context_raw_body(client, builder, monkeypatch):
    """
    Đảm bảo fallback sang raw bytes nếu body không phải JSON.

    Test này xác nhận:
    - JSON parse fail không gây crash
    - ctx.body giữ nguyên bytes gốc
    """
    captured = {}

    async def fake_dispatch(ctx):
        captured["body"] = ctx.body
        return ResponseContext(200, {}, b"OK")

    monkeypatch.setattr(builder.broker, "dispatch", fake_dispatch)

    resp = client.post(
        "/raw",
        content=b"raw-bytes",
        headers={"content-type": "application/octet-stream"},
    )

    assert resp.status_code == 200
    assert captured["body"] == b"raw-bytes"


def test_build_context_empty_body(client, builder, monkeypatch):
    """
    Đảm bảo request không có body được chuẩn hóa thành None.

    Điều này giúp downstream logic:
    - Không phải xử lý b"" (empty bytes)
    - Phân biệt rõ body trống và body có dữ liệu
    """
    captured = {}

    async def fake_dispatch(ctx):
        captured["body"] = ctx.body
        return ResponseContext(200, {}, b"OK")

    monkeypatch.setattr(builder.broker, "dispatch", fake_dispatch)

    resp = client.post("/empty")

    assert resp.status_code == 200
    assert captured["body"] is None


def test_build_context_base_url(client, builder, monkeypatch):
    """
    Đảm bảo base_url được build đúng từ request URL.

    Test này xác nhận:
    - base_url chỉ gồm scheme + host (+ port nếu có)
    - Không bao gồm path hay query string
    """
    captured = {}

    async def fake_dispatch(ctx):
        captured["base_url"] = ctx.base_url
        return ResponseContext(200, {}, b"OK")

    monkeypatch.setattr(builder.broker, "dispatch", fake_dispatch)

    client.get("/test")

    # TestClient dùng http://testserver
    assert captured["base_url"] == "http://testserver"


def test_unwrap_context_sanitize_headers(client, builder, monkeypatch):
    """
    Đảm bảo ResponseContext được unwrap và sanitize headers đúng cách.

    Test này bảo vệ:
    - Header hợp lệ được giữ lại
    - Header hop-by-hop / transport-level bị loại bỏ
    """
    async def fake_dispatch(ctx):
        return ResponseContext(
            status_code=200,
            headers={
                "x-ok": "1",
                "content-length": "999",
                "connection": "keep-alive",
            },
            body=b"OK",
        )

    monkeypatch.setattr(builder.broker, "dispatch", fake_dispatch)

    resp = client.get("/headers")

    assert resp.status_code == 200
    assert resp.headers.get("x-ok") == "1"
    assert resp.headers.get("content-length") == "2"
    assert "connection" not in resp.headers


@pytest.mark.parametrize("method", http_methods)
def test_supported_methods(client, builder, monkeypatch, method):
    """
    Đảm bảo proxy route hỗ trợ đầy đủ các HTTP methods khai báo.

    Test này xác nhận:
    - Router không bị giới hạn method
    - ctx.method phản ánh đúng HTTP verb của request
    """
    async def fake_dispatch(ctx):
        return ResponseContext(200, {}, ctx.method.encode())

    monkeypatch.setattr(builder.broker, "dispatch", fake_dispatch)

    fn = getattr(client, method)
    resp = fn("/method")

    assert resp.status_code == 200

    if method.lower() == "head":
        assert resp.content == b""
    else:
        assert resp.content.decode().upper() == method.upper()


@pytest.mark.asyncio
async def test_streaming_response_unwrapped_as_streaming_response(builder, async_generator):
    resp_ctx = ResponseContext(
        200,
        {"content-type": "application/x-ndjson"},
        body=async_generator(),
    )

    response = await builder._unwrap_context(resp_ctx)

    assert isinstance(response, StreamingResponse)
