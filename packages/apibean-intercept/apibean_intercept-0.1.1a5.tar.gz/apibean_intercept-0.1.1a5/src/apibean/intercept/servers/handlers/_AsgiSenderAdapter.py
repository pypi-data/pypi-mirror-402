import asyncio

from typing import List, Dict, Any, Optional

from fastapi import Request, Response
from fastapi.responses import StreamingResponse


class ASGIResponseCollector:
    """
    Collects ASGI response messages and reconstructs a Response or
    StreamingResponse.

    Supports:
    - http.response.start
    - http.response.body (multiple chunks)
    """

    def __init__(self):
        self.start_message: Optional[Dict[str, Any]] = None
        self.body_messages: List[Dict[str, Any]] = []
        self._body_event = asyncio.Event()

    async def send(self, message: Dict[str, Any]):
        msg_type = message["type"]

        if msg_type == "http.response.start":
            self.start_message = message

        elif msg_type == "http.response.body":
            self.body_messages.append(message)
            self._body_event.set()

    def build_response(self) -> Response:
        """
        Build a Starlette Response or StreamingResponse
        from collected ASGI messages.
        """
        if not self.start_message:
            return Response("No response", status_code=500)

        status = self.start_message["status"]
        headers = {
            k.decode("latin-1"): v.decode("latin-1")
            for k, v in self.start_message.get("headers", [])
        }
        headers["x-handler-type"] = "asgi_sender_stream"

        # Single body (non-streaming)
        if len(self.body_messages) == 1 and not self.body_messages[0].get("more_body"):
            return Response(
                content=self.body_messages[0].get("body", b""),
                status_code=status,
                headers=headers,
            )

        # Streaming response
        async def body_iterator():
            for msg in self.body_messages:
                chunk = msg.get("body", b"")
                if chunk:
                    yield chunk
                if not msg.get("more_body", False):
                    break

        return StreamingResponse(
            body_iterator(),
            status_code=status,
            headers=headers,
        )


class ASGIInterceptAdapter:
    """
    Adapter that executes an ASGI app and intercepts its response.

    This allows:
    - routing
    - proxying
    - response inspection / modification
    """

    def __init__(self, asgi_app):
        self.app = asgi_app

    async def handle(self, request: Request) -> Response:
        collector = ASGIResponseCollector()
        await self.app(request.scope, request.receive, collector.send)
        return collector.build_response()
