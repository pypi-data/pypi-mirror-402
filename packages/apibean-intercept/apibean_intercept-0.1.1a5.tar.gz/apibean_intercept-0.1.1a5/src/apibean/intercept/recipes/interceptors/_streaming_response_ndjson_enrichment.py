import json
from typing import Callable

from ._streaming_response_transform import StreamingResponseTransformInterceptor

class NDJSONEnrichmentInterceptor(StreamingResponseTransformInterceptor):
    def __init__(self, transform_data: Callable):
        self._transform_data = transform_data

    async def transform_chunk(self, ctx, response, chunk):
        if not callable(self._transform_data):
            return chunk
        try:
            data = json.loads(chunk)
            self._transform_data(data, ctx, response)
            return json.dumps(data).encode("utf-8") + b"\n"
        except Exception:
            return chunk
