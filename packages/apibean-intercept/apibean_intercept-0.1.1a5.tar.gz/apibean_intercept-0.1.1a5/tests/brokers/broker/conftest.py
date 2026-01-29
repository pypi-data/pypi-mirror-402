import pytest

from apibean.intercept.brokers.models import RequestContext, ResponseContext


@pytest.fixture
def make_ctx():
    def _make():
        return RequestContext(
            method="GET",
            path="/hello",
            headers={"x-test": "1"},
            query={},
            body=None,
            base_url="http://proxy",
            raw_request=None,
        )
    return _make
