# Making routers a package so FastAPI can import individual submodules easily

from . import auth  # noqa: F401  - re-export for convenience
from . import dashboard  # noqa: F401  - re-export for convenience
from . import upload  # noqa: F401  - re-export for convenience
from . import settings  # noqa: F401
from . import recommend  # noqa: F401
from . import tasks  # noqa: F401
from . import setup  # noqa: F401
from . import employees  # noqa: F401

__all__ = ["auth", "dashboard", "upload", "settings", "recommend", "tasks", "setup", "employees"]
