import pytest


@pytest.fixture()
def default_handler():
    from apibean.intercept.servers.handlers import create_handler_from_router
    return create_handler_from_router
