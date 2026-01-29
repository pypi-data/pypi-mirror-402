from abc import ABC, abstractmethod
from typing import Optional
from fastapi.responses import Response

from ..models import RequestContext, ResponseContext

class Dispatcher(ABC):
    """
    Dispatcher that can intercept or fully handle an API request.
    """

    name: str = "dispatcher"
    priority: int = 100

    @abstractmethod
    def match(self, ctx: RequestContext) -> bool:
        """Return True if this dispatcher applies."""
        raise NotImplementedError

    async def handle(self, ctx: RequestContext) -> Optional[ResponseContext]:
        """
        Handle request.
        Return Response to short-circuit proxy,
        or None to continue proxying.
        """
        return None
