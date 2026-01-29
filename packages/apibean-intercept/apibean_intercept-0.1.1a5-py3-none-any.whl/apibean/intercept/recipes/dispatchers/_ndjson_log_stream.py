import asyncio
import json
import time
from typing import AsyncIterator, Callable, Optional

from apibean.intercept.brokers.dispatchers import Dispatcher
from apibean.intercept.brokers.models import RequestContext, ResponseContext


class NDJSONLogStreamDispatcher(Dispatcher):
    """
    Dispatcher that streams log messages as NDJSON.
    """

    name = "ndjson-log-stream"
    priority = 10

    def __init__(self,
        match_path: Optional[str] = None,
        transform_log: Optional[Callable] = None,
        amount: int = 5,
        interval: int = 1,
    ):
        self._match_path = match_path
        self._transform_log = transform_log or (lambda base_log: base_log)
        self._amount = amount if amount > 0 else 5
        self._interval = interval

    def match(self, ctx: RequestContext) -> bool:
        if self._match_path:
            return ctx.path == self._match_path
        return True

    async def handle(self, ctx: RequestContext) -> ResponseContext:
        async def stream() -> AsyncIterator[bytes]:
            async for item in self.log_generator(ctx):
                yield json.dumps(item, ensure_ascii=False).encode("utf-8") + b"\n"
                if self._interval > 0:
                    await asyncio.sleep(self._interval)
        return ResponseContext(
            status_code=200,
            headers={
                "content-type": "application/x-ndjson",
                "cache-control": "no-cache",
            },
            body=stream(),
        )

    async def log_generator(self, ctx: RequestContext):
        for i in range(self._amount):
            yield self._transform_log({
                "index": i,
                "ts": time.time(),
                "path": ctx.path,
            })
