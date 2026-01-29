from typing import Callable, Awaitable, List

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from starlette.types import Message


def create_handler_from_router(router: APIRouter, default_router: APIRouter|None = None) \
        -> Callable[[Request], Awaitable[Response]]:
    """
    Build an async request handler from a FastAPI APIRouter.

    Internally, this function mounts the router into a temporary FastAPI app,
    then executes that app manually as an ASGI callable in order to:
      - intercept request/response flow
      - extract the generated response
      - return it as a normal Starlette Response object

    This pattern is useful for proxying, interception, and dynamic dispatch.
    """

    # Create a temporary FastAPI application.
    # This app is NOT served by uvicorn; it is only executed programmatically.
    app = FastAPI()

    # Mount the main router (user-defined API routes).
    app.include_router(router)

    # Optionally mount a fallback router (e.g. default / catch-all handler).
    if default_router is not None:
        app.include_router(default_router)

    async def handler(req: Request) -> Response:
        """
        This handler adapts an ASGI-based FastAPI app into a callable
        that accepts a Request and returns a Response.
        """

        # Buffers to capture ASGI "send" messages.
        # In ASGI, responses are emitted via the `send()` callable.
        response_start: Message | None = None
        body_chunks: List[bytes] = []
        is_streaming = False

        async def send(message: Message) -> None:
            """
            ASGI send callable.

            FastAPI / Starlette will call this function with messages like:
              - http.response.start
              - http.response.body

            We intercept and store them so we can reconstruct a Response object.
            """
            nonlocal response_start, is_streaming

            if message["type"] == "http.response.start":
                response_start = message

            elif message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))
                if message.get("more_body", False):
                    is_streaming = True

        # Execute the FastAPI app as a raw ASGI application.
        #
        # app itself is an ASGI callable with signature:
        #   await app(scope, receive, send)
        #
        # Here we reuse the original request's scope and receive channel,
        # but override `send` to capture the response instead of sending it
        # to a real network socket.
        await app(req.scope, req.receive, send)

        if response_start is None:
            # No ASGI response_start was produced — this should not normally happen.
            return Response("No response", status_code=500)

        # Handle ASGI response start message.
        #
        # http.response.start contains status code and headers,
        # but the actual body is sent separately via http.response.body.
        status_code = response_start.get("status")
        headers = dict(response_start.get("headers", []))

        # Decode headers from ASGI format (bytes -> str)
        headers = {
            k.decode("latin-1"): v.decode("latin-1")
            for k, v in headers.items()
        }
        headers["x-handler-type"] = "asgi_sender"

        # Streaming response
        if is_streaming:
            async def body_iter():
                for chunk in body_chunks:
                    yield chunk

            return StreamingResponse(
                body_iter(),
                status_code=status_code,
                headers=headers,
            )

        # Single body (non-streaming)
        return Response(
            content=b"".join(body_chunks),
            status_code=status_code,
            headers=headers,
        )

    return handler
