"""Defines base provider classes and give default lyrics, info and audio providers. For more information on Downmixer's providers system, refer to the [Providers](../../providers/usage.md) page."""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol

from downmixer import utils
from downmixer.providers.connections import Connection
from downmixer.types import LoggerLike
from downmixer.types.exceptions import NotInitializedError
from downmixer.utils.logging import ConsoleLogger

logger = logging.getLogger("downmixer").getChild(__name__)


class BaseProvider:
    """Base class for all music providers.

    Providers are the main interface for interacting with music services. Each provider
    must define a `_name`, `_pretty_name` (publicly accessible via properties), and implement the required protocol
    methods for their supported capabilities.

    Additionally, a provider can specify default options dictionary with the
    `_default_options` parameter - this value will be merged with the options passed by the user using the
    [`merge_dicts_with_priority`](../utils/#downmixer.utils.merge_dicts_with_priority(dict2)) function.

    Attributes:
        connection: The active connection to the provider's service.
        client: The underlying API client from the connection.
    """

    _name: str = ""
    _pretty_name: str = ""
    _default_options: dict = {}

    connection: Connection = None
    client: object = None

    @property
    def name(self) -> str:
        """The internal identifier for this provider."""
        return self._name

    @property
    def pretty_name(self) -> str:
        """The human-readable name for this provider."""
        return self._pretty_name

    def __init__(
        self,
        connection: Connection,
        options: Optional[dict] = None,
        logger: "LoggerLike" = ConsoleLogger(),
    ):
        """Initializes the provider object. If applicable, does not authenticate to the service.

        Args:
            options: Dictionary of options to pass to the provider. See documentation for each provider for
                available options.
            logger: Logger-like object to use for logging. If None, uses the default logger.
        """
        if any(char.isspace() for char in self.name):
            raise ValueError(
                "Provider name cannot contain whitespace characters. Use the 'pretty_name' attribute for human readable names."
            )

        self.options = utils.merge_dicts_with_priority(self._default_options, options)
        self.logger = logger

        self.connection = connection
        self.client = self.connection.client
        if not self.connection.ready:
            NotInitializedError()

    def change_connection(self, new: Connection) -> None:
        """Change the provider's Connection object, ensuring that it's ready attributes are set.

        !!! warning
            It's not guaranteed that a connection change will go well. None of the built-in providers have issues with
            this, however be careful when using third-party or custom providers.

        Args:
            new (Connection): Connection object to be changed.
        """
        self.connection = new
        self.client = self.connection.client

    @classmethod
    def get_connections(cls) -> list[type[Connection]]:
        """Return the list of connection types supported by this provider.

        Returns:
            A list of Connection subclasses that can be used with this provider.
        """
        raise NotImplementedError

    def __getattr__(self, name: str):
        """Proxy attribute access to the underlying connection object."""
        return getattr(self.connection, name)


def list_providers() -> list[type[BaseProvider]]:
    """Discover and return all available provider classes.

    Scans the providers package for subpackages containing a `get_provider` function
    and collects all provider classes.

    Returns:
        A list of BaseProvider subclasses found in the providers package.
    """
    providers_path = str(Path(__file__).parent.absolute())
    current_package_name = sys.modules[__name__].__name__

    loaded: list[type[BaseProvider]] = []
    for loader, name, is_pkg in pkgutil.walk_packages([providers_path]):
        if is_pkg:
            imported = importlib.import_module(f"{current_package_name}.{name}")
            try:
                func = getattr(imported, "get_provider")
                loaded.append(func())
            except AttributeError:
                logger.error(
                    f"Module {current_package_name}.{name} does not contain a get_provider function"
                )
                continue

    return loaded


# noinspection PyProtocol
def list_protocols() -> list[type[Protocol]]:
    """Return all protocol classes defined in the protocols module.

    Returns:
        A list of Protocol subclasses (e.g., SupportsMetadata, SupportsAudioDownload).
    """
    current_package_name = sys.modules[__name__].__name__

    imported = importlib.import_module(f"{current_package_name}.protocols")
    found = []
    for name, obj in imported.__dict__.items():
        if not inspect.isclass(obj):
            continue

        if (
            issubclass(obj, Protocol)
            and obj is not Protocol
            and obj.__module__.startswith("downmixer")
        ):
            found.append(obj)

    return found


@dataclass
class ProviderInformation:
    """Information about a provider including its supported protocols and connections. This class facilitates
    parsing of providers and their supported protocols.

    Attributes:
        class_name: The name of the provider class.
        class_ref: A reference to the provider class itself.
        protocols: List of protocol classes the provider implements.
        connections: List of connection classes the provider supports.
    """

    class_name: str
    class_ref: type
    protocols: list[type[Protocol]] = field(default_factory=list)
    connections: list[type[Connection]] = field(default_factory=list)

    def __contains__(self, item):
        if isinstance(item, type):
            return item in self.protocols
        elif isinstance(item, Connection):
            return type(item) in self.connections
        elif isinstance(item, str):
            return type(item) in self.protocols
        else:
            return False

    def __hash__(self):
        return hash(self.class_name) + hash(self.class_ref)

    def __eq__(self, other):
        if self.class_name != other.class_name or self.class_ref != other.class_ref:
            return False
        return True


def get_all_providers_info() -> list[ProviderInformation]:
    """Get detailed information about all available providers.

    Returns:
        A list of ProviderInformation objects, each containing the provider's
        class name, class reference, implemented protocols, and supported connections.
    """
    protocol_list = list_protocols()
    provider_list = list_providers()

    found: list[ProviderInformation] = []
    for provider in provider_list:
        found.append(
            ProviderInformation(
                class_name=provider.__class__.__name__,
                class_ref=provider,
                protocols=[x for x in protocol_list if issubclass(provider, x)],
                connections=provider.get_connections(),
            )
        )

    return found
