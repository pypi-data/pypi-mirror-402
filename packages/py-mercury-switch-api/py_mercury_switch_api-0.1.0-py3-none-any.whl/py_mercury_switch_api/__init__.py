"""Mercury Switch API."""

__version__ = "0.1.0"

from .connector import MercurySwitchConnector
from .exceptions import (
    LoginFailedError,
    MercurySwitchConnectionError,
    MercurySwitchModelNotDetectedError,
    PageNotLoadedError,
)

__all__ = [
    "MercurySwitchConnector",
    "LoginFailedError",
    "MercurySwitchConnectionError",
    "MercurySwitchModelNotDetectedError",
    "PageNotLoadedError",
]
