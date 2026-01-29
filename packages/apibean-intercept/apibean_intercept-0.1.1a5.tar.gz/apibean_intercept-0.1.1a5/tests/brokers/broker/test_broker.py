import pytest

from apibean.intercept.brokers.broker import InterceptBroker
from apibean.intercept.brokers.models import RequestContext, ResponseContext


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

class DummyDispatcher:
    name = "dummy"
    priority = 50

    def __init__(self, *, match=True, response=None):
        self._match = match
        self._response = response or ResponseContext(
            200, {"x-dispatcher": "1"}, b"OK"
        )
        self.called = False

    def match(self, ctx):
        return self._match

    async def handle(self, ctx):
        self.called = True
        return self._response


class RecordingInterceptor:
    name = "recorder"

    def __init__(self, calls, priority=100):
        self.priority = priority
        self.calls = calls

    async def before_request(self, ctx):
        self.calls.append("before")

    async def after_response(self, ctx, response):
        self.calls.append("after")


class RewriteInterceptor:
    priority = 50

    async def before_request(self, ctx):
        pass

    async def after_response(self, ctx, response):
        response.body = b"REWRITTEN"


class AbortInterceptor:
    priority = 10

    async def before_request(self, ctx):
        raise RuntimeError("blocked")

    async def after_response(self, ctx, response):
        pass


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

# Luồng xử lý trong source code
#
# dispatch(ctx):
#   ├─ for interceptor: before_request(ctx)
#   ├─ for dispatcher:
#   │     if match → handle → response → break
#   ├─ if response is None:
#   │     resolver_chain.resolve → upstream
#   │     _forward(ctx, upstream)
#   ├─ for interceptor: after_response(ctx, response)
#   └─ return response

# Lưu ý:
#
# * `after_response` luôn chạy, kể cả response từ dispatcher hay forward
# * `_forward()` trả về ResponseContext
# * Dispatcher cũng phải trả ResponseContext

@pytest.mark.asyncio
async def test_dispatcher_match_used(make_ctx):
    """
    Kiểm tra dispatcher được dùng khi match(ctx) trả về True.

    Nếu có dispatcher khớp request, broker phải gọi handle()
    và KHÔNG forward request lên upstream.
    """
    dispatcher = DummyDispatcher(match=True)
    broker = InterceptBroker(dispatchers=[dispatcher])

    ctx = make_ctx()
    resp = await broker.dispatch(ctx)

    assert dispatcher.called is True
    assert resp.status_code == 200
    assert resp.body == b"OK"


@pytest.mark.asyncio
async def test_dispatcher_fallback_forward_used(make_ctx, monkeypatch):
    """
    Kiểm tra cơ chế fallback khi không dispatcher nào match.

    Broker phải resolve upstream từ ResolverChain
    và forward request bằng cơ chế HTTP client.
    """
    dispatcher = DummyDispatcher(match=False)

    broker = InterceptBroker(dispatchers=[dispatcher])

    async def fake_forward(ctx, upstream):
        return ResponseContext(404, {}, b"FORWARDED")

    monkeypatch.setattr(broker, "_forward", fake_forward)
    monkeypatch.setattr(
        broker.resolver_chain,
        "resolve",
        lambda ctx: "http://upstream",
    )

    ctx = make_ctx()
    resp = await broker.dispatch(ctx)

    assert dispatcher.called is False
    assert resp.status_code == 404
    assert resp.body == b"FORWARDED"


@pytest.mark.asyncio
async def test_interceptors_called(make_ctx):
    calls = []

    interceptor = RecordingInterceptor(calls)
    dispatcher = DummyDispatcher()

    broker = InterceptBroker(
        dispatchers=[dispatcher],
        interceptors=[interceptor],
    )

    ctx = make_ctx()
    await broker.dispatch(ctx)

    assert calls == ["before", "after"]


@pytest.mark.asyncio
async def test_interceptor_priority_order(make_ctx):
    """
    Kiểm tra interceptor được gọi theo thứ tự priority.

    Interceptor có priority thấp hơn phải được gọi trước.
    """
    calls = []

    low = RecordingInterceptor(calls, priority=200)
    high = RecordingInterceptor(calls, priority=10)

    broker = InterceptBroker(
        dispatchers=[DummyDispatcher()],
        interceptors=[low, high],
    )

    ctx = make_ctx()
    await broker.dispatch(ctx)

    assert calls == [
        "before",  # high
        "before",  # low
        "after",   # high
        "after",   # low
    ]


@pytest.mark.asyncio
async def test_interceptor_rewrite(make_ctx):
    broker = InterceptBroker(
        dispatchers=[DummyDispatcher()],
        interceptors=[RewriteInterceptor()],
    )

    ctx = make_ctx()
    resp = await broker.dispatch(ctx)

    assert resp.body == b"REWRITTEN"


@pytest.mark.asyncio
async def test_interceptor_abort(make_ctx):
    broker = InterceptBroker(
        dispatchers=[DummyDispatcher()],
        interceptors=[AbortInterceptor()],
    )

    with pytest.raises(RuntimeError):
        await broker.dispatch(make_ctx())
