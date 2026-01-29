"""
InterceptBuilder integrates InterceptBroker with FastAPI routing.

This module provides a lightweight proxy router that converts incoming
FastAPI requests into RequestContext objects, dispatches them through
InterceptBroker, and unwraps ResponseContext back into FastAPI responses.
"""

from typing import Any, Optional
from collections.abc import AsyncIterable
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse

from .broker import InterceptBroker
from .models import RequestContext, ResponseContext
from ..utils.http_util import sanitize_headers
from ..utils.http_util import HTTP_METHODS

class InterceptBuilder:
    """
    Build a FastAPI router backed by an InterceptBroker.

    InterceptBuilder exposes a catch-all proxy route that forwards all
    incoming requests through the broker, enabling dispatchers,
    interceptors, and upstream resolvers to participate in the request
    lifecycle.
    """

    def __init__(self, upstream_base: str):
        """
        Initialize the builder with a default upstream base URL.

        The upstream_base is configured as the fallback resolver for the
        internal ResolverChain.
        """
        self._router = APIRouter()
        self._broker = InterceptBroker()

        self._broker.resolver_chain.fallback_resolver = upstream_base

        @self._router.api_route("/{full_path:path}", methods=HTTP_METHODS)
        async def proxy(full_path: str, request: Request):
            req_ctx = await self._build_context(request)
            resp_ctx = await self._broker.dispatch(req_ctx)
            return await self._unwrap_context(resp_ctx)

    @property
    def broker(self):
        """
        Return the underlying InterceptBroker instance.
        """
        return self._broker

    @property
    def router(self):
        """
        Return the FastAPI APIRouter exposing the proxy route.
        """
        return self._router

    async def _build_context(self, request: Request) -> RequestContext:
        """
        Build a RequestContext from a FastAPI Request.

        The request body is parsed as JSON when possible, otherwise raw
        bytes are used. Empty bodies are normalized to None.
        """
        # body: try to parse JSON, fallback raw bytes
        try:
            body: Optional[Any] = await request.json()
        except Exception:
            body = await request.body()
            if body == b"":
                body = None

        # build base_url
        url = request.url
        if url.port:
            base_url = f"{url.scheme}://{url.hostname}:{url.port}"
        else:
            base_url = f"{url.scheme}://{url.hostname}"

        return RequestContext(
            method=request.method,
            path=url.path,
            headers=dict(request.headers),
            query=dict(request.query_params),
            body=body,
            base_url=base_url,
            raw_request=request,
        )

    async def _unwrap_context(self, resp_ctx: ResponseContext) -> Response | StreamingResponse:
        """
        Convert a ResponseContext into a FastAPI Response / StreamingResponse.

        Headers are sanitized to remove hop-by-hop and transport-level
        fields before returning the response.
        """
        headers = self._sanitize(resp_ctx.headers)
        body = resp_ctx.body

        # Streaming response
        if isinstance(body, AsyncIterable):
            return StreamingResponse(
                body,
                status_code=resp_ctx.status_code,
                headers=headers,
            )

        # Normal response
        return Response(
            content=body,
            status_code=resp_ctx.status_code,
            headers=headers,
        )

    def _sanitize(self, headers):
        return sanitize_headers(headers)
