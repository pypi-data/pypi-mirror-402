from typing import AsyncIterator, Optional

from ...brokers.interceptors import Interceptor
from ...brokers.models import ResponseContext, RequestContext


class StreamingResponseTransformInterceptor(Interceptor):
    """
    Interceptor for transforming streaming response bodies.

    This interceptor wraps the response body iterator and allows
    transforming chunks as they are streamed.
    """

    name = "streaming-response-transform"
    priority = 90  # run before non-streaming transformers

    async def after_response(
        self,
        ctx: RequestContext,
        response: ResponseContext,
        upstream: str | None = None,
    ) -> None:
        if not self.is_streaming(response):
            return

        original_stream = response.body
        response.body = self.wrap_stream(ctx, response, original_stream)

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def is_streaming(self, response: ResponseContext) -> bool:
        """
        Return True if the response body is a stream / async iterator.
        """
        return hasattr(response.body, "__aiter__")

    def wrap_stream(
        self,
        ctx: RequestContext,
        response: ResponseContext,
        stream: AsyncIterator[bytes],
    ) -> AsyncIterator[bytes]:
        """
        Wrap the original async byte stream.
        """
        async def generator():
            async for chunk in stream:
                try:
                    new_chunk = await self.transform_chunk(
                        ctx, response, chunk
                    )
                    if new_chunk is not None:
                        yield new_chunk
                except Exception as exc:
                    self.on_error(exc, response)
                    yield chunk  # fail-soft: forward original chunk

        return generator()

    async def transform_chunk(
        self,
        ctx: RequestContext,
        response: ResponseContext,
        chunk: bytes,
    ) -> Optional[bytes]:
        """
        Transform a single response chunk.

        Return:
        - bytes: transformed chunk
        - None: drop chunk
        """
        return chunk

    def on_error(self, exc: Exception, response: ResponseContext) -> None:
        """
        Called when chunk transform fails.
        """
        pass
