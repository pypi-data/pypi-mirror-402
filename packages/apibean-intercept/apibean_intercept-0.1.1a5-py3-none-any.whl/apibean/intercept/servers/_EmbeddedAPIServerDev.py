import os
import platform
import psutil

from ._EmbeddedAPIServerBase import EmbeddedAPIServerBase
from ._ServerStatus import ServerStatus


class EmbeddedAPIServerDev(EmbeddedAPIServerBase):
    def __init__(self, *args, show_system_info: bool = True, **kwargs):
        self.show_system_info = show_system_info
        super().__init__(*args, **kwargs)

    def status(self, pretty: bool = False) -> ServerStatus:
        info = super().status(pretty=pretty)

        if not self.show_system_info:
            return info

        cpu_percent = psutil.cpu_percent(interval=0.1)
        virtual_mem = psutil.virtual_memory()
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return ServerStatus(**{
            **info,
            "system": {
                "platform": platform.system(),
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": virtual_mem.total,
                    "available": virtual_mem.available,
                    "used": virtual_mem.used,
                    "used_by_process": memory_info.rss,
                    "percent": virtual_mem.percent,
                }
            }
        }).enable_markdown(pretty)
