import asyncio
import inspect
import json
from typing import AsyncIterator, Callable, Optional

import logging
logger = logging.getLogger(__name__)

from fastapi.responses import StreamingResponse

from apibean.intercept.brokers.dispatchers import Dispatcher
from apibean.intercept.brokers.models import RequestContext, ResponseContext


class ProgressStreamDispatcher(Dispatcher):
    """
    Dispatcher that streams progress updates as NDJSON.

    Each progress update is emitted as a single JSON object per line,
    suitable for long-running tasks such as exports, batch processing,
    or background jobs.

    Output format (NDJSON):
        {"step": 0, "total": 10, "message": "starting"}
        {"step": 1, "total": 10, "message": "processing"}
        {"step": 9, "total": 10, "message": "done"}
    """

    name = "progress-stream"
    priority = 50

    def __init__(self, *,
        match_path: Optional[str] = None,
        progress_generator: Callable[[RequestContext], AsyncIterator[dict]],
        interval: float = 0.0,
    ):
        """
        Parameters
        ----------
        match_path:
            URL path to activate this dispatcher (exact match).

        progress_generator:
            Async generator yielding progress dicts.

        interval:
            Optional sleep interval (seconds) between chunks.
        """
        self._match_path = match_path
        self._progress_generator = progress_generator
        self._interval = interval

    def match(self, ctx: RequestContext) -> bool:
        """Return True if request path matches progress endpoint."""
        return ctx.path == self._match_path

    async def handle(self, ctx: RequestContext) -> ResponseContext:
        """
        Handle request by streaming progress updates.

        Returns a ResponseContext whose body is an async iterator
        producing NDJSON-encoded progress objects.
        """

        async def stream() -> AsyncIterator[bytes]:
            try:
                async for item in self._iterate_progress(ctx):
                    yield item
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.exception("Progress stream error", exc_info=e)

        return ResponseContext(
            status_code=200,
            headers={
                "content-type": "application/x-ndjson",
                "cache-control": "no-cache",
            },
            body=stream(),
        )

    async def _iterate_progress(self, ctx) -> AsyncIterator[bytes]:
        """Normalize progress_generator (sync or async) into async byte stream."""

        gen = self._progress_generator(ctx)

        # Case 1: async generator / async iterator
        if inspect.isasyncgen(gen) or hasattr(gen, "__aiter__"):
            async for item in gen:
                yield self._encode_item(item)
                await self._maybe_sleep()

        # Case 2: sync generator / iterable
        else:
            for item in gen:
                yield self._encode_item(item)
                await self._maybe_sleep()

    def _encode_item(self, item) -> bytes:
        return json.dumps(item, ensure_ascii=False).encode("utf-8") + b"\n"

    async def _maybe_sleep(self):
        if self._interval > 0:
            await asyncio.sleep(self._interval)
