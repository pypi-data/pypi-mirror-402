"""Custom exceptions for Mercury Switch API."""


class MercurySwitchError(Exception):
    """Base exception for Mercury Switch API."""


class MercurySwitchConnectionError(MercurySwitchError):
    """Connection error while requesting page."""


class LoginFailedError(MercurySwitchError):
    """Invalid credentials."""


class NotLoggedInError(MercurySwitchError):
    """Not logged in."""


class PageNotLoadedError(MercurySwitchError):
    """Failed to load the page."""


class MercurySwitchModelNotDetectedError(MercurySwitchError):
    """None of the models passed the tests."""


class MultipleModelsDetectedError(MercurySwitchError):
    """Detection of switch model was not unique."""
