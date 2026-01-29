"""
Interceptor base definitions.

This module defines the abstract base class for interceptors that hook into
the request/response lifecycle of the intercept engine.
"""

from abc import ABC
from typing import Optional
from fastapi import Response

from ..models import RequestContext, ResponseContext


class Interceptor(ABC):
    """
    Base class for request/response interceptors.

    Interceptors observe or modify requests before dispatching to an upstream
    and responses after they are returned.
    """

    #: Identifier used for logging and diagnostics.
    name: str = "interceptor"

    #: Execution order (lower value runs earlier).
    priority: int = 100

    async def before_request(self, ctx: RequestContext) -> None:
        """
        Called before the request is dispatched upstream.

        Implementations may inspect or mutate the request context.
        """
        pass

    async def after_response(self, ctx: RequestContext,
        response: ResponseContext,
        upstream: str | None = None
    ) -> None:
        """
        Called after an upstream response is received.

        Implementations may inspect or mutate the response context.
        """
        pass
