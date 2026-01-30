"""Connection classes for managing provider service connections.

This module defines the base connection classes that handle initialization and
authentication with music provider services. Connections manage the underlying
API clients and authentication state.
"""

from __future__ import annotations

import abc
from functools import wraps
from typing import Optional

from downmixer import utils
from downmixer.types import LoggerLike
from downmixer.types.exceptions import NotAuthenticatedException
from downmixer.types.library import ResourceType
from downmixer.utils.logging import ConsoleLogger


class Connection(metaclass=abc.ABCMeta):
    """Abstract base class for provider connections.

    A connection manages the lifecycle of connecting to a music provider's service,
    including initialization and URL validation. Subclasses must implement the
    abstract methods to handle provider-specific logic.

    Attributes:
        _default_options: Default configuration options for the connection.
        _initialized: Whether the connection has been initialized.
        _client: The underlying API client instance.
    """

    _default_options: dict = {}
    _initialized: bool = False
    _client: object = None

    def __init__(
        self, options: Optional[dict] = None, logger: "LoggerLike" = ConsoleLogger()
    ):
        """Initialize the connection with options and a logger.

        Args:
            options: Configuration options to merge with defaults.
            logger: Logger instance for logging messages.
        """
        self.options = utils.merge_dicts_with_priority(self._default_options, options)
        self.logger = logger

    @property
    def client(self):
        """The underlying API client instance."""
        return self._client

    @property
    def ready(self) -> bool:
        """Whether the connection is ready to be used."""
        return self._initialized

    @abc.abstractmethod
    def initialize(self) -> bool:
        """Initializes the connection to the provider. Should set the `initialized` attribute to True if successful."""
        raise NotImplementedError

    @abc.abstractmethod
    def check_valid_url(self, url: str, type_filter: list[ResourceType] = None) -> bool:
        """Check if a URL or URI is valid for this provider.

        Args:
            url: The URL or URI to validate.
            type_filter: Optional list of resource types to filter against.
                If provided, the URL must match one of these types to be valid.

        Returns:
            True if the URL is valid for this provider, False otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_resource_type(self, value: str) -> ResourceType | None:
        """Determine the resource type of a URL or URI for this provider.

        Args:
            value: The URL or URI to analyze.

        Returns:
            The ResourceType if recognized, or None if the URL is not valid.
        """
        raise NotImplementedError


class AuthenticatedConnection(Connection):
    """Connection class for providers that require user authentication.

    Extends Connection to add authentication state tracking. The connection
    is only considered ready when both initialized and authenticated.

    Attributes:
        _authenticated: Whether the user has been authenticated.
    """

    _authenticated: bool = False

    @property
    def ready(self) -> bool:
        """Whether the connection is initialized and authenticated."""
        return self._initialized and self._authenticated

    @abc.abstractmethod
    def authenticate(self, **kwargs) -> bool:
        """Authenticate the user with the provider.

        Should set the `_authenticated` attribute to True if successful.

        Returns:
            True if authentication was successful, False otherwise.
        """
        raise NotImplementedError

    def require_authentication(self, func):
        """Decorator to ensure a method is only called when authenticated.

        Args:
            func: The function to wrap.

        Returns:
            A wrapped function that raises NotAuthenticatedException if
            the connection is not authenticated.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self._authenticated or not self._initialized:
                raise NotAuthenticatedException(
                    "This platform requires authentication to perform this action."
                )
            return func(*args, **kwargs)

        return wrapper
