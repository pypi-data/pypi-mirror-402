from typing import Optional

from fastapi import FastAPI, Request, Response

from .abstract import Dispatcher
from ...brokers.models import RequestContext, ResponseContext
from ...servers.handlers import create_handler_from_app


class FastAPIAppDispatcher(Dispatcher):
    """
    Dispatcher adapter for an existing FastAPI application.

    This dispatcher allows embedding a pre-defined FastAPI app
    into the InterceptBroker dispatch chain, enabling interception,
    routing, and composition without running a separate server.
    """

    priority = 50  # usually higher priority than fallback proxy

    def __init__(
        self,
        app: FastAPI,
        *,
        match_prefix: Optional[str] = None,
        name: str = "fastapi-app",
    ):
        """
        :param app: Existing FastAPI application
        :param match_prefix: Optional path prefix to match (e.g. "/internal")
        :param name: Logical name for debugging
        """
        self.app = app
        self.match_prefix = match_prefix
        self.name = name

        # Build an ASGI-compatible handler once
        self._handler = self._build_handler(app)

    def _build_handler(self, app: FastAPI):
        """
        Wrap FastAPI app into a callable(Request) -> Response.
        """
        return create_handler_from_app(app)

    def match(self, ctx: RequestContext) -> bool:
        """
        Match request based on optional path prefix.
        """
        if self.match_prefix is None:
            return True
        return ctx.path.startswith(self.match_prefix)

    async def handle(self, ctx: RequestContext) -> ResponseContext:
        """
        Execute the embedded FastAPI app and convert its response
        into a ResponseContext.
        """
        response: Response = await self._handler(ctx.raw_request)

        return ResponseContext(
            status_code=response.status_code,
            headers=response.headers,
            body=response.body,
        )
