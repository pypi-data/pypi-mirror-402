"""Types for wrapping search results from providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from downmixer.types.library import BaseLibraryItem, ResourceType

T = TypeVar("T", bound=BaseLibraryItem)


@dataclass
class SearchResult(Generic[T]):
    """A wrapper for search results that tracks their provider origin.

    This generic class wraps any `BaseLibraryItem` subtype (Song, Album, Artist, etc.)
    and associates it with the provider it came from. It also supports transparent
    attribute access to the wrapped result.

    Attributes:
        provider: Name of the provider that returned this result (e.g., "spotify", "youtube_music").
        result: The actual library item returned by the search.
        source: Optional reference to the original item being searched for, useful for matching.

    Example:
        >>> result = SearchResult(provider="spotify", result=song)
        >>> result.name  # Delegates to song.name
        "Never Gonna Give You Up"
        >>> result.resource_type
        ResourceType.SONG
    """

    provider: str
    result: T
    source: Optional[T] = None

    @property
    def resource_type(self) -> ResourceType:
        """Returns the resource type of the wrapped result."""
        return type(self.result).get_resource_type()

    def __getattr__(self, name: str):
        """Delegate attribute access to the wrapped result object."""
        return getattr(self.result, name)

    def __dir__(self):
        """Include wrapped result's attributes in dir() for better introspection/IDE completion."""
        return sorted(set(super().__dir__() + list(dir(self.result))))
