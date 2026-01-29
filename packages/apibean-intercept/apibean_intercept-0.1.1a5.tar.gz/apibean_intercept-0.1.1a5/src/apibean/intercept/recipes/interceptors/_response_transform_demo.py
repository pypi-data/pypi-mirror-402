from ._response_transform import ResponseTransformInterceptor

class ResponseTransformInterceptorDemo(ResponseTransformInterceptor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._count = 0

    def transform_headers(self, headers):
        # minh họa việc thay đổi headers
        self._count = (self._count or 0) + 1
        headers["x-rewrite-count"] = str(self._count)
        return headers

    def transform_body(self, body):
        # minh họa việc thay đổi body (JSON)
        body["_debug"] = f"rewritten by interceptor { self._count }"
