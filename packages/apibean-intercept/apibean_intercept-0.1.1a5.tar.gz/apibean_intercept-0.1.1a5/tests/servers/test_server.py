from fastapi import APIRouter
from fastapi.testclient import TestClient

def test_init_defaults():
    """Test khởi tạo cơ bản"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    server = EmbeddedAPIServerBase(verbose=False)

    assert server.host == "0.0.0.0"
    assert server.port == 8000
    assert server._running is False
    assert server._thread is None
    assert server._handler is None


def test_create_app_contains_status_endpoint():
    """Test _create_app() wiring"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    server = EmbeddedAPIServerBase(control_base_path="ctrl", verbose=False)
    app = server._create_app()

    client = TestClient(app)
    resp = client.get("/ctrl/status")

    assert resp.status_code == 200
    data = resp.json()
    assert "running" in data
    assert "host" in data


def test_pretty_json_middleware_added():
    """Test PrettyJSONMiddleware được add"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase
    from apibean.intercept.servers.middlewares.PrettyJSONMiddleware import PrettyJSONMiddleware

    server = EmbeddedAPIServerBase(pretty_json_response=True, verbose=False)
    app = server._create_app()

    middleware_classes = [
        m.cls for m in app.user_middleware
    ]

    assert PrettyJSONMiddleware in middleware_classes


def test_pretty_json_middleware_is_disabled_by_default():
    """Test PrettyJSONMiddleware bị ẩn mặc định"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase
    from apibean.intercept.servers.middlewares.PrettyJSONMiddleware import PrettyJSONMiddleware

    server = EmbeddedAPIServerBase(verbose=False)
    app = server._create_app()

    middleware_classes = [
        m.cls for m in app.user_middleware
    ]

    assert PrettyJSONMiddleware not in middleware_classes


def test_start_sets_running_state(port_available, monkeypatch):
    """Test start() - happy path"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    monkeypatch.setattr(
        EmbeddedAPIServerBase,
        "_run_server",
        lambda self: setattr(self, "_running", True)
    )

    server = EmbeddedAPIServerBase(port=9001, verbose=False)
    server.start()

    assert server._thread is not None


def test_start_port_busy(monkeypatch):
    """Test start() khi port busy"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    monkeypatch.setattr(
        "apibean.intercept.servers._EmbeddedAPIServerBase.is_port_available",
        lambda *a, **k: False
    )

    messages = []

    server = EmbeddedAPIServerBase(port=9001)
    server._message_handler = messages.append
    server.start()

    out = "\n".join(messages)
    assert "already in use" in out
    assert server._thread is None


def test_stop_without_start(capsys):
    """Test stop() khi chưa start"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    server = EmbeddedAPIServerBase()
    server.stop()

    out = capsys.readouterr().out
    assert "not running" in out


def test_stop_running_server(monkeypatch):
    """Test stop() khi đang chạy"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    server = EmbeddedAPIServerBase(verbose=False)
    server._server = type("S", (), {"should_exit": False})()
    server._thread = type("T", (), {
        "is_alive": lambda self: True,
        "join": lambda self, timeout=None: None
    })()

    server.stop()

    assert server._server is None
    assert server._thread is None


def test_restart_calls_stop_and_start(monkeypatch):
    """Test restart()"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    server = EmbeddedAPIServerBase(verbose=False)

    calls = []
    monkeypatch.setattr(server, "stop", lambda: calls.append("stop"))
    monkeypatch.setattr(server, "start", lambda: calls.append("start"))

    server.restart()

    assert calls == ["stop", "start"]


def test_update_handler_sets_handler():
    """Test update_handler()"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    server = EmbeddedAPIServerBase(verbose=False)

    async def handler(req):
        return {"ok": True}

    server.update_handler(handler)

    assert server._handler is handler


def test_update_router_creates_handler(monkeypatch):
    """Test update_router()"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    router = APIRouter()

    @router.get("/hello")
    async def hello():
        return {"hello": "world"}

    monkeypatch.setattr(
        "apibean.intercept.servers._EmbeddedAPIServerBase.create_handler_from_router",
        lambda *a, **k: "HANDLER"
    )

    server = EmbeddedAPIServerBase(verbose=False)
    server.update_router(router)

    assert server._handler == "HANDLER"


def test_status_reflects_internal_state():
    """Test status()"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    server = EmbeddedAPIServerBase(host="127.0.0.1", port=1234, verbose=False)
    status = server.status()

    assert status.get("running") is False
    assert status.get("host") == "127.0.0.1"
    assert status.get("port") == 1234


def test_main_handler_fallback(monkeypatch):
    """Test main_handler fallback → default_handler"""
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    async def fake_default_handler(req, full_path, handler_name=None):
        return {"path": full_path}

    monkeypatch.setattr(
        "apibean.intercept.servers._EmbeddedAPIServerBase.default_handler",
        fake_default_handler
    )

    server = EmbeddedAPIServerBase(verbose=False)
    app = server._create_app()
    client = TestClient(app)

    resp = client.get("/anything")

    assert resp.status_code == 200
    assert resp.json()["path"] == "anything"
