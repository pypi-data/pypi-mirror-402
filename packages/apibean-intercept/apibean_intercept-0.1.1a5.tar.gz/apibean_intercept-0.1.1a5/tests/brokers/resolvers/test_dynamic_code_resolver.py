import pytest

from apibean.intercept.brokers.resolvers import (
    DynamicCodeResolver,
)
from apibean.intercept.brokers.models import RequestContext


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def make_ctx(
    *,
    path="/api/test",
    method="GET",
    headers=None,
    query=None,
    body=None,
):
    """Create a minimal RequestContext for testing."""
    return RequestContext(
        method=method,
        path=path,
        headers=headers or {},
        query=query or {},
        body=body,
        base_url="http://origin",
        raw_request=None,
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_empty_resolver_does_not_match():
    resolver = DynamicCodeResolver()
    ctx = make_ctx()

    assert resolver.match(ctx) is False


def test_register_single_rule_and_match():
    resolver = DynamicCodeResolver()

    resolver.register(
        name="match-all",
        match=lambda ctx: True,
        upstream="http://upstream",
    )

    ctx = make_ctx()
    assert resolver.match(ctx) is True


def test_resolve_returns_correct_upstream():
    resolver = DynamicCodeResolver()

    resolver.register(
        name="api-rule",
        match=lambda ctx: ctx.path.startswith("/api"),
        upstream="http://api-upstream",
    )

    ctx = make_ctx(path="/api/users")
    assert resolver.resolve(ctx) == "http://api-upstream"


def test_priority_ordering():
    resolver = DynamicCodeResolver()

    resolver.register(
        name="low-priority",
        match=lambda ctx: True,
        upstream="http://low",
        priority=100,
    )

    resolver.register(
        name="high-priority",
        match=lambda ctx: True,
        upstream="http://high",
        priority=10,
    )

    ctx = make_ctx()
    assert resolver.resolve(ctx) == "http://high"


def test_override_rule_by_name():
    resolver = DynamicCodeResolver()

    resolver.register(
        name="rule",
        match=lambda ctx: True,
        upstream="http://old",
        priority=50,
    )

    resolver.register(
        name="rule",  # same name → override
        match=lambda ctx: True,
        upstream="http://new",
        priority=50,
    )

    ctx = make_ctx()
    assert resolver.resolve(ctx) == "http://new"
    assert len(resolver._rules) == 1


def test_clear_rules():
    resolver = DynamicCodeResolver()

    resolver.register(
        name="rule",
        match=lambda ctx: True,
        upstream="http://upstream",
    )

    resolver.clear()
    ctx = make_ctx()

    assert resolver.match(ctx) is False
    assert resolver._rules == []


def test_match_true_but_resolve_raises():
    """
    This test covers the edge case where match() returns True
    but resolve() fails to find a matching rule.
    """
    resolver = DynamicCodeResolver()

    # Trick: match() returns True, but no rule actually matches in resolve()
    resolver._rules.append(
        type(
            "FakeRule",
            (),
            {
                "name": "fake",
                "priority": 0,
                "match": staticmethod(lambda ctx: False),
                "upstream": "http://never",
            },
        )()
    )

    ctx = make_ctx()

    assert resolver.match(ctx) is False  # sanity check

    with pytest.raises(RuntimeError):
        resolver.resolve(ctx)
