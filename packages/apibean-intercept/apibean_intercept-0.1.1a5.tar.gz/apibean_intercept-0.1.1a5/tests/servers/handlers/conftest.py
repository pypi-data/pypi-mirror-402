import pytest

from apibean.intercept.servers.handlers._AsgiSender import create_handler_from_router as create_handler_from_router_as
from apibean.intercept.servers.handlers._AsgiSenderStream import create_handler_from_router as create_handler_from_router_ass
from apibean.intercept.servers.handlers._HttpxClient import create_handler_from_router as create_handler_from_router_hc
from apibean.intercept.servers.handlers._HttpxClientStream import create_handler_from_router as create_handler_from_router_hcs
from apibean.intercept.servers.handlers._TestClient import create_handler_from_router as create_handler_from_router_tc

@pytest.fixture(
    params=[
        pytest.param(create_handler_from_router_as, id="asgi_sender"),
        pytest.param(create_handler_from_router_ass, id="asgi_sender_stream"),
        pytest.param(create_handler_from_router_hc, id="httpx_client"),
        pytest.param(create_handler_from_router_hcs, id="httpx_client_stream"),
        pytest.param(create_handler_from_router_tc, id="test_client"),
    ]
)
def handler_factory(request):
    """
    Parametrized factory for create_handler_from_router implementations.

    Each test using this fixture will be executed
    against all supported handler implementations.
    """
    return request.param
