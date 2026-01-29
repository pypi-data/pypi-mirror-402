import json
from typing import Any

from ...brokers.interceptors import Interceptor
from ...brokers.models import ResponseContext, RequestContext


class ResponseTransformInterceptor(Interceptor):
    """
    Interceptor that allows transforming response headers and body.

    Default behavior:
    - Only applies to JSON responses.
    - Parses JSON body into Python object.
    - Calls transform hooks.
    - Serializes JSON back to bytes.
    """

    name = "response-transform"
    priority = 100

    async def after_response(
        self,
        ctx: RequestContext,
        response: ResponseContext,
        upstream: str | None = None,
    ) -> None:
        if not self.can_transform(ctx, response):
            return

        try:
            data = self.parse_body(response)
            self.transform(data, response)
            self.serialize(response, data)
        except Exception as exc:
            # Fail-soft: do not break proxy pipeline
            self.on_error(exc, response)

    # ---- Hooks -------------------------------------------------

    def can_transform(
        self,
        ctx: RequestContext,
        response: ResponseContext,
    ) -> bool:
        """Return True if this response should be transformed."""
        content_type = response.headers.get("content-type", "")
        return content_type.startswith("application/json")

    def transform(self, data: Any, response: ResponseContext) -> None:
        """Transform headers and body."""
        self.transform_headers(response.headers)
        self.transform_body(data)

    def transform_headers(self, headers: dict) -> None:
        """Override to mutate response headers."""
        pass

    def transform_body(self, data: Any) -> None:
        """Override to mutate parsed response body."""
        pass

    # ---- Parsing / Serialization ------------------------------

    def parse_body(self, response: ResponseContext) -> Any:
        """Parse response body into Python object."""
        body = response.body

        if body is None:
            return None

        if isinstance(body, (bytes, bytearray)):
            return json.loads(body.decode("utf-8"))

        if isinstance(body, str):
            return json.loads(body)

        if isinstance(body, (dict, list)):
            return body

        raise TypeError(f"Unsupported body type: {type(body)}")

    def serialize(self, response: ResponseContext, data: Any) -> None:
        """Serialize Python object back into response body."""
        response.body = json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ).encode("utf-8")

    # ---- Error handling ---------------------------------------

    def on_error(self, exc: Exception, response: ResponseContext) -> None:
        """Called when transform fails."""
        # Default: ignore error, keep original response
        pass
