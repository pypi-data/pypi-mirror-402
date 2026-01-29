"""
Upstream resolver chain.

Evaluates registered resolvers in order and selects the first
matching upstream, with optional fallback handling.
"""

from ..models import RequestContext
from ._BaseUpstreamResolver import UpstreamResolver
from ._DefaultUpstreamResolver import DefaultUpstreamResolver


class ResolverChain:
    """
    Chain of upstream resolvers.

    Resolvers are evaluated sequentially. The first resolver
    whose `match()` returns True will be used.
    """

    def __init__(self):
        #: Optional fallback resolver used when no resolver matches.
        self._fallback_resolver: UpstreamResolver | None = None

        #: Ordered list of registered resolvers.
        self._resolvers: list[UpstreamResolver] = []

    @property
    def fallback_resolver(self):
        """Return the fallback resolver."""
        return self._fallback_resolver

    @fallback_resolver.setter
    def fallback_resolver(self, ref: UpstreamResolver | str | None):
        """
        Set fallback resolver.

        Accepts:
        - UpstreamResolver instance
        - upstream URL string (wrapped as DefaultUpstreamResolver)
        - None to disable fallback
        """
        if isinstance(ref, UpstreamResolver) or ref is None:
            self._fallback_resolver = ref
            return

        if isinstance(ref, str):
            self._fallback_resolver = DefaultUpstreamResolver(ref)
            return

        raise ValueError("invalid fallback_resolver")

    def register(self, resolver: UpstreamResolver):
        """
        Register a resolver into the chain.
        """
        self._resolvers.append(resolver)

    def resolve(self, ctx: RequestContext) -> str:
        """
        Resolve upstream for the given request context.

        Raises RuntimeError if no resolver matches and no fallback is set.
        """
        for r in self._resolvers:
            if r.match(ctx):
                upstream = r.resolve(ctx)
                self._guard(ctx, upstream, r)
                return upstream

        if self._fallback_resolver:
            return self._fallback_resolver.resolve(ctx)

        raise RuntimeError("No upstream resolver matched")

    def _guard(self, ctx: RequestContext, upstream: str, resolver):
        """
        Guard against proxy loops.

        Raises RuntimeError if upstream resolves to the request base URL.
        """
        if upstream.rstrip("/") == ctx.base_url.rstrip("/"):
            raise RuntimeError(
                f"Proxy loop detected by resolver '{resolver.name}'"
            )
