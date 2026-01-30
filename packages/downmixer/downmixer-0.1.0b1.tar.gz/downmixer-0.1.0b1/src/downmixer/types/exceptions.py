"""Custom exceptions and warnings used throughout Downmixer."""

from __future__ import annotations


class NotInitializedError(BaseException):
    """Raised when an operation is attempted on a provider that hasn't been initialized.

    This typically occurs when trying to use a provider's methods before calling
    its initialization or authentication flow.
    """

    pass


class UnsupportedException(BaseException):
    """Raised when a requested operation is not supported by a provider.

    This occurs when calling a method that requires a protocol the provider
    doesn't implement (e.g., requesting lyrics from a provider that doesn't
    implement `SupportsLyrics`).
    """

    pass


class IncompleteSupportWarning(Warning):
    """Warning issued when a provider partially supports a feature.

    This is used to indicate that while an operation may succeed, some
    functionality or data may be missing or degraded compared to full support.
    """

    pass


class NotConnectedException(Exception):
    """Exception raised when trying to use a provider without being connected."""

    pass


class NotAuthenticatedException(Exception):
    """Exception raised when trying to use a provider without being authenticated."""

    pass
