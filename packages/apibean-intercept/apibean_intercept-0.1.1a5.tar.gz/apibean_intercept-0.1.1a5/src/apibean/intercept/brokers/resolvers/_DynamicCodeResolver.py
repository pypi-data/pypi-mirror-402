"""
Dynamic upstream resolver.

Provides rule-based upstream routing that can be registered
and modified at runtime, typically from interactive environments
such as Jupyter notebooks.
"""

from dataclasses import dataclass
from typing import Callable

from ..models import RequestContext
from ._BaseUpstreamResolver import UpstreamResolver


@dataclass
class DynamicRule:
    """
    A dynamically registered routing rule.
    """

    #: Rule identifier.
    name: str

    #: Predicate used to match a request context.
    match: Callable[[RequestContext], bool]

    #: Upstream base URL to resolve to.
    upstream: str

    #: Rule priority (lower value matches first).
    priority: int = 50


class DynamicCodeResolver(UpstreamResolver):
    """
    Resolver that evaluates dynamically registered routing rules.
    """

    #: Resolver identifier.
    name = "dynamic-code-resolver"

    #: High priority to run before static resolvers.
    priority = 10

    def __init__(self):
        """Initialize an empty rule set."""
        self._rules: list[DynamicRule] = []

    def register(
        self,
        name: str,
        *,
        match: Callable[[RequestContext], bool],
        upstream: str,
        priority: int = 50,
    ):
        """
        Register or override a dynamic routing rule.
        """
        # Remove existing rule with the same name
        self._rules = [r for r in self._rules if r.name != name]

        # Add new rule
        self._rules.append(
            DynamicRule(
                name=name,
                match=match,
                upstream=upstream,
                priority=priority,
            )
        )

        # Sort by priority (lower value first)
        self._rules.sort(key=lambda r: r.priority)

    def clear(self):
        """Remove all dynamic rules."""
        self._rules.clear()

    # ------------------------------------------------------------------
    # Resolver interface
    # ------------------------------------------------------------------

    def match(self, ctx: RequestContext) -> bool:
        """
        Return True if any rule matches the request.
        """
        return any(rule.match(ctx) for rule in self._rules)

    def resolve(self, ctx: RequestContext) -> str:
        """
        Resolve upstream using the first matching rule.
        """
        for rule in self._rules:
            if rule.match(ctx):
                return rule.upstream
        raise RuntimeError("DynamicCodeResolver matched but no rule resolved")
