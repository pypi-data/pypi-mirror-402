import threading
import asyncio

from typing import Callable, Optional

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import Response

import uvicorn

from .handlers import HANDLER_TYPE
from .handlers import create_handler_from_router
from .handlers import create_handler_from_app

from .fastapi_util import default_handler
from .fastapi_util import default_router

from .middlewares.PrettyJSONMiddleware import PrettyJSONMiddleware

from ..utils.http_util import HTTP_METHODS
from ..utils.net_util import is_port_available

from ._ServerStatus import ServerStatus


class EmbeddedAPIServerBase:
    def __init__(self, host="0.0.0.0", port=8000, log_level:str="error",
            control_base_path: str = "__notebook__",
            pretty_json_response: bool = False,
            verbose: bool = True,
            message_handler: Optional[Callable] = None):
        # service settings
        self.host = host
        self.port = port
        self.log_level = log_level
        self.control_base_path = control_base_path
        self.pretty_json_response = pretty_json_response
        self.verbose = verbose
        self._message_handler = message_handler
        # private properties
        self._lifecycle_lock = threading.RLock()
        self._handler_lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server: Optional[uvicorn.Server] = None
        self._running: bool = False
        self._handler = None

    def _create_app(self) -> FastAPI:
        app = FastAPI()

        if self.pretty_json_response:
            app.add_middleware(PrettyJSONMiddleware)

        @app.get(f"/{self.control_base_path}/status")
        async def status_endpoint():
            return self.status()

        @app.api_route("/{full_path:path}", methods=HTTP_METHODS, include_in_schema=False)
        async def main_handler(request: Request, full_path: str):
            with self._handler_lock:
                handler = self._handler
            if handler:
                return await handler(request)
            return await default_handler(request, full_path, handler_name="universal")

        return app

    def _run_server(self):
        with self._lifecycle_lock:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            app = self._create_app()
            config = uvicorn.Config(app, host=self.host, port=self.port, log_level=self.log_level,
                    date_header=False,
                    server_header=False,
                    loop="asyncio")
            self._server = uvicorn.Server(config)
            self._running = True

        try:
            self._loop.run_until_complete(self._server.serve())
        finally:
            with self._lifecycle_lock:
                self._running = False
                self._loop.close()
                self._loop = None
                self._server = None

    def _print_info(self, msg: str):
        if self._message_handler is not None:
            self._message_handler(msg)
        elif self.verbose:
            print(msg)

    def start(self):
        with self._lifecycle_lock:
            if self._running:
                self._print_info("⚠️ Server is already running.")
                return

            if not is_port_available(port=self.port, host=self.host):
                self._print_info(f"❌ Address ('{self.host}', {self.port}) already in use")
                return

            self._thread = threading.Thread(target=self._run_server, daemon=True)
            self._thread.start()

            self._print_info(f"✅ Server started at http://{self.host}:{self.port}")

    def stop(self):
        with self._lifecycle_lock:
            if not self._server:
                self._print_info("⚠️ Server not running.")
                return
            self._print_info("🛑 Stopping server...")
            self._server.should_exit = True

            self_thread = self._thread

        # join ngoài lock → tránh deadlock
        if self_thread and self_thread.is_alive():
            self_thread.join(timeout=5)

        with self._lifecycle_lock:
            self._thread = None
            self._server = None
            self._loop = None
            self._running = False
            

    def restart(self):
        with self._lifecycle_lock:
            self.stop()
            self.start()

    def status(self, pretty: bool = False) -> ServerStatus:
        return ServerStatus(**{
            "running": self._running,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "host": self.host,
            "port": self.port,
            "handler_set": self._handler is not None
        }).enable_markdown(pretty)

    def update_handler(self, func: Optional[Callable[..., dict]]):
        with self._handler_lock:
            self._handler = func
        self._print_info("✅ Handler updated.")

    def update_router(self, target: APIRouter | FastAPI | None,
        handler_type: HANDLER_TYPE | None = None
    ):
        if target is None:
            self.update_handler(None)
            return

        if isinstance(target, APIRouter):
            handler = create_handler_from_router(
                target,
                default_router=default_router,
                handler_type=handler_type,
            )
            self.update_handler(handler)
            return

        if isinstance(target, FastAPI):
            self.update_handler(create_handler_from_app(target))
            return

        raise TypeError("update_router() accepts FastAPI, APIRouter or None")
