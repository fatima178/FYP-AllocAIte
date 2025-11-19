# Making routers a package so FastAPI can import individual submodules easily

from . import auth  # noqa: F401  - re-export for convenience
from . import dashboard  # noqa: F401  - re-export for convenience
from . import upload  # noqa: F401  - re-export for convenience

__all__ = ["auth", "dashboard", "upload"]
