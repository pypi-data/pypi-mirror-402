"""
Default upstream resolver.

Always resolves to a fixed upstream URL.
"""

from ..models import RequestContext
from ._BaseUpstreamResolver import UpstreamResolver


class DefaultUpstreamResolver(UpstreamResolver):
    """Fallback resolver with a static upstream."""

    #: Resolver identifier.
    name = "default"

    #: Lowest priority (used last).
    priority = 1000

    def __init__(self, upstream: str):
        """Initialize with a fixed upstream base URL."""
        self.upstream = upstream

    def match(self, ctx: RequestContext) -> bool:
        """Always match."""
        return True

    def resolve(self, ctx: RequestContext) -> str:
        """Return the configured upstream URL."""
        return self.upstream
