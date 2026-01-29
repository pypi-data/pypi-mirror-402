import pytest
from unittest.mock import MagicMock

@pytest.fixture
def fake_uvicorn_server(monkeypatch):
    server = MagicMock()
    server.should_exit = False
    server.serve = MagicMock(return_value=None)

    class FakeServer:
        def __init__(self, config):
            self.should_exit = False
            self.config = config
        async def serve(self):
            return None

    monkeypatch.setattr("uvicorn.Server", FakeServer)
    return server


@pytest.fixture
def port_available(monkeypatch):
    monkeypatch.setattr(
        "apibean.intercept.utils.net_util.is_port_available",
        lambda *a, **k: True
    )
