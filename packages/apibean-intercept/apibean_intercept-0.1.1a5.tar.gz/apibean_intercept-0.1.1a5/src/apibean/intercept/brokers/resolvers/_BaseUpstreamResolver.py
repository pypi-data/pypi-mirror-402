"""
Upstream resolver base.

Defines the abstract interface for resolving an upstream base URL
from a request context.
"""
from abc import ABC, abstractmethod

from ..models import RequestContext


class UpstreamResolver(ABC):
    """
    Base class for upstream resolvers.

    An upstream resolver decides where a request should be forwarded.
    """

    #: Resolver identifier.
    name: str = "base"

    @abstractmethod
    def match(self, ctx: RequestContext) -> bool:
        """
        Return True if this resolver applies to the request.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve(self, ctx: RequestContext) -> str:
        """
        Return the upstream base URL.

        Must not resolve to the request's own base URL.
        """
        raise NotImplementedError
