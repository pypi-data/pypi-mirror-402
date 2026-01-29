import pytest

from apibean.intercept.brokers.models import RequestContext
from apibean.intercept.brokers.resolvers import ResolverChain
from apibean.intercept.brokers.resolvers import UpstreamResolver


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

class DummyResolver(UpstreamResolver):
    """Simple resolver stub for testing."""

    def __init__(self, *, name, match_result, upstream):
        self.name = name
        self._match_result = match_result
        self._upstream = upstream

    def match(self, ctx: RequestContext) -> bool:
        return self._match_result

    def resolve(self, ctx: RequestContext) -> str:
        return self._upstream


def make_ctx(
    *,
    base_url="http://origin",
    path="/api/test",
):
    return RequestContext(
        method="GET",
        path=path,
        headers={},
        query={},
        body=None,
        base_url=base_url,
        raw_request=None,
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_first_matching_resolver_is_used():
    chain = ResolverChain()

    r1 = DummyResolver(
        name="r1",
        match_result=False,
        upstream="http://up1",
    )
    r2 = DummyResolver(
        name="r2",
        match_result=True,
        upstream="http://up2",
    )

    chain.register(r1)
    chain.register(r2)

    ctx = make_ctx()

    assert chain.resolve(ctx) == "http://up2"


def test_resolver_order_is_respected():
    chain = ResolverChain()

    r1 = DummyResolver(
        name="r1",
        match_result=True,
        upstream="http://first",
    )
    r2 = DummyResolver(
        name="r2",
        match_result=True,
        upstream="http://second",
    )

    chain.register(r1)
    chain.register(r2)

    ctx = make_ctx()

    # First resolver wins
    assert chain.resolve(ctx) == "http://first"


def test_fallback_resolver_used_when_no_match():
    chain = ResolverChain()

    r1 = DummyResolver(
        name="r1",
        match_result=False,
        upstream="http://never",
    )
    chain.register(r1)

    fallback = DummyResolver(
        name="fallback",
        match_result=True,
        upstream="http://fallback",
    )
    chain.fallback_resolver = fallback

    ctx = make_ctx()

    assert chain.resolve(ctx) == "http://fallback"


def test_fallback_resolver_set_by_string():
    chain = ResolverChain()

    chain.fallback_resolver = "http://default-upstream"

    ctx = make_ctx()

    assert chain.resolve(ctx) == "http://default-upstream"


def test_no_match_and_no_fallback_raises():
    chain = ResolverChain()

    r1 = DummyResolver(
        name="r1",
        match_result=False,
        upstream="http://never",
    )
    chain.register(r1)

    ctx = make_ctx()

    with pytest.raises(RuntimeError, match="No upstream resolver matched"):
        chain.resolve(ctx)


def test_guard_detects_proxy_loop():
    chain = ResolverChain()

    r1 = DummyResolver(
        name="loop-resolver",
        match_result=True,
        upstream="http://origin",  # same as ctx.base_url
    )
    chain.register(r1)

    ctx = make_ctx(base_url="http://origin")

    with pytest.raises(RuntimeError, match="Proxy loop detected"):
        chain.resolve(ctx)


def test_guard_allows_different_upstream():
    chain = ResolverChain()

    r1 = DummyResolver(
        name="safe-resolver",
        match_result=True,
        upstream="http://other",
    )
    chain.register(r1)

    ctx = make_ctx(base_url="http://origin")

    assert chain.resolve(ctx) == "http://other"
