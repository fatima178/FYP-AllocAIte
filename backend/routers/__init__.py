# Making routers a package so FastAPI can import individual submodules easily

from . import upload  # noqa: F401 - re-export for convenience

__all__ = ["upload"]
