"""
Intercept broker.

Coordinates request dispatching, interceptor execution,
upstream resolution, and request forwarding.
"""
from typing import Optional

import httpx

from .dispatchers import Dispatcher
from .interceptors import Interceptor
from .resolvers import ResolverChain
from .models import RequestContext, ResponseContext
from ..utils.http_util import sanitize_headers

class InterceptBroker:
    """
    Central dispatch engine for intercepted requests.

    Executes interceptors, selects a dispatcher or upstream,
    and returns a unified response context.
    """

    def __init__(
        self,
        *,
        dispatchers: list[Dispatcher] | None = None,
        interceptors: list[Interceptor] | None = None,
        resolver_chain: ResolverChain | None = None,
    ):
        """
        Initialize the broker.

        Dispatchers and interceptors are sorted by priority.
        """
        self._dispatchers = sorted(dispatchers or [], key=lambda e: e.priority)
        self._interceptors = sorted(interceptors or [], key=lambda e: e.priority)
        self._resolver_chain = resolver_chain or ResolverChain()

    @property
    def dispatchers(self):
        """Return registered dispatchers."""
        return self._dispatchers

    @property
    def interceptors(self):
        """Return registered interceptors."""
        return self._interceptors

    @property
    def resolver_chain(self):
        """Return the resolver chain."""
        return self._resolver_chain

    async def dispatch(self, ctx: RequestContext) -> Optional[ResponseContext]:
        """
        Dispatch a request through interceptors and dispatchers.

        Execution order:
        1. before_request interceptors
        2. matching dispatcher OR upstream forwarding
        3. after_response interceptors
        """
        # Run request interceptors
        for it in self._interceptors:
            await it.before_request(ctx)

        response = None

        # Try dispatchers first
        for ext in self._dispatchers:
            if ext.match(ctx):
                response = await ext.handle(ctx)
                break

        # Fallback to upstream forwarding
        if response is None:
            upstream = self._resolver_chain.resolve(ctx)
            response = await self._forward(ctx, upstream)

        # Run response interceptors
        for it in self._interceptors:
            await it.after_response(ctx, response)

        return response

    async def _forward(self, ctx: RequestContext, upstream: str) -> ResponseContext:
        """
        Forward the request to an upstream server.

        Returns a normalized ResponseContext.
        """
        async with httpx.AsyncClient() as client:
            # Filter hop-by-hop headers
            headers = self._sanitize(ctx.headers)

            resp = await client.request(
                ctx.method,
                url=upstream + ctx.path,
                headers=headers,
                params=ctx.query,
                json=ctx.body,
            )

            return ResponseContext(
                resp.status_code,
                dict(resp.headers),
                resp.content,
            )

    def _sanitize(self, headers):
        return sanitize_headers(headers)
