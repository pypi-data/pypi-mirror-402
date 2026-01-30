from __future__ import annotations

from . import exceptions as exceptions
from .client import Rundeck
from .const import __version__
from .exceptions import (
    RundeckApiVersionUnsupportedError,
    RundeckAuthenticationError,
    RundeckConflictError,
    RundeckConnectionError,
    RundeckError,
    RundeckHTTPError,
    RundeckNotFoundError,
    RundeckOperationError,
    RundeckQuotaExceededError,
    RundeckServerError,
    RundeckTimeoutError,
    RundeckValidationError,
    raise_for_status,
)

__all__ = [
    "Rundeck",
    "__version__",
    "exceptions",
    "RundeckApiVersionUnsupportedError",
    "RundeckAuthenticationError",
    "RundeckConflictError",
    "RundeckConnectionError",
    "RundeckError",
    "RundeckHTTPError",
    "RundeckNotFoundError",
    "RundeckOperationError",
    "RundeckQuotaExceededError",
    "RundeckServerError",
    "RundeckTimeoutError",
    "RundeckValidationError",
    "raise_for_status",
]
