import httpx

from fastapi import Request
from fastapi.responses import StreamingResponse

from ...utils.http_util import sanitize_headers

METHODS_WITH_BODY = {"POST", "PUT", "PATCH", "DELETE"}


class HttpxInterceptAdapter:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    def _sanitize(self, headers):
        return sanitize_headers(headers)

    async def handle(self, request: Request) -> StreamingResponse:
        # Build httpx request
        req = self.client.build_request(
            method=request.method,
            url=request.url.path,
            headers=self._sanitize(request.headers),
            params=dict(request.query_params),
            content=(
                await request.body()
                if request.method.upper() in METHODS_WITH_BODY
                else None
            ),
        )

        # Send request in streaming mode
        resp = await self.client.send(req, stream=True)

        # Extract metadata immediately
        status_code = resp.status_code
        headers = self._sanitize(resp.headers)
        headers["x-handler-type"] = "httpx_client_stream"
        media_type = headers.get("content-type")

        # Streaming generator (owns response lifecycle)
        async def body():
            try:
                async for chunk in resp.aiter_bytes():
                    yield chunk
            finally:
                await resp.aclose()

        # Return StreamingResponse
        return StreamingResponse(
            body(),
            status_code=status_code,
            headers=headers,
            media_type=media_type,
        )
