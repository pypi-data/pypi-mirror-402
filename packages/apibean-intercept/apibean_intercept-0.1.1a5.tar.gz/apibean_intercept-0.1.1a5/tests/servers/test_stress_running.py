import pytest
import threading
import time

from fastapi import APIRouter

@pytest.fixture
def server_for_stress(monkeypatch):
    from apibean.intercept.servers._EmbeddedAPIServerBase import EmbeddedAPIServerBase

    # Luôn cho phép port
    monkeypatch.setattr(
        "apibean.intercept.servers._EmbeddedAPIServerBase.is_port_available",
        lambda *a, **k: True
    )

    # Giả lập _run_server không block
    def fake_run_server(self):
        self._running = True
        time.sleep(0.01)  # giả lập server sống 1 chút
        self._running = False

    monkeypatch.setattr(
        EmbeddedAPIServerBase,
        "_run_server",
        fake_run_server
    )

    return EmbeddedAPIServerBase(port=9999, verbose=False)


def test_start_stop_stress_sequential(server_for_stress):
    """start/stop liên tục (single thread): không crash, không deadlock, stop luôn clean"""
    server = server_for_stress

    for _ in range(20):
        server.start()
        time.sleep(0.005)
        server.stop()

    time.sleep(0.01)
    status = server.status()
    assert status.get("running") is False
    assert status.get("thread_alive") is False


def test_multiple_start_calls(server_for_stress):
    """gọi start nhiều lần liên tiếp (đảm bảo start() idempotent)"""
    messages = []

    server = server_for_stress
    server._message_handler = messages.append

    server.start()
    server.start()
    server.start()

    out = "/".join(messages)
    assert "already running" in out or "Server started" in out

    server.stop()


def test_concurrent_start_stop_threads(server_for_stress):
    """
    start / stop từ nhiều thread:
    -   mô phỏng notebook / UI / CLI gọi đồng thời,
    -   phát hiện race condition sớm
    """
    server = server_for_stress

    errors = []

    def worker():
        try:
            for _ in range(5):
                server.start()
                time.sleep(0.002)
                server.stop()
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=worker)
        for _ in range(5)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout=2)

    time.sleep(0.01)

    assert errors == []

    status = server.status()
    assert status.get("running") is False


def test_restart_stress(server_for_stress):
    """restart liên tục"""
    server = server_for_stress

    for _ in range(10):
        server.restart()
        time.sleep(0.005)

    status = server.status()
    assert status.get("running") is True

    time.sleep(0.05)

    status = server.status()
    assert status.get("running") is False


def test_update_handler_during_lifecycle(server_for_stress):
    """update_handler trong lúc start/stop"""
    server = server_for_stress

    async def handler(req):
        return {"ok": True}

    for _ in range(10):
        server.update_handler(handler)
        server.start()
        server.stop()

    assert server._handler is handler


def test_update_router_concurrent(server_for_stress, monkeypatch):
    """gọi update_router song song liên tục để loại trừ Router rebind"""
    monkeypatch.setattr(
        "apibean.intercept.servers._EmbeddedAPIServerBase.create_handler_from_router",
        lambda *a, **k: lambda req: {"ok": True}
    )

    router = APIRouter()

    errors = []

    def worker():
        try:
            server_for_stress.update_router(router)
            server_for_stress.start()
            server_for_stress.stop()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=2)

    assert errors == []
