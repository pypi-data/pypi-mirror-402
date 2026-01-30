class SharePointError(Exception):
    """Base class for SharePoint related exceptions."""


class UserNotFoundError(SharePointError):
    """Raised when SharePoint returns a SPException indicating the user cannot be found.

    The SharePoint REST API may return an error with code ``-2146232832`` and a
    message like ``User cannot be found.``.  Raising a dedicated exception enables
    callers to handle this situation explicitly.
    """

    def __init__(self, message: str = "User cannot be found."):
        super().__init__(message)
