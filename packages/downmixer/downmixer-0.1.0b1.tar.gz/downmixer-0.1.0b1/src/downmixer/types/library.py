"""Data classes to hold standardized metadata about songs, artists, and albums."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

from slugify import slugify

__all__ = [
    "Album",
    "AlbumType",
    "Artist",
    "ResourceType",
    "Song",
    "User",
    "Playlist",
    "BaseLibraryItem",
]


class AlbumType(Enum):
    """Classification of album release types."""

    ALBUM = auto()
    """A full-length album release."""
    SINGLE = auto()
    """A single track or EP release."""
    COMPILATION = auto()
    """A compilation or "greatest hits" collection."""


class ResourceType(Enum):
    """Enum representing the type of resource being handled. The UNKNOWN value is used when a provider has IDs that are
    valid for multiple types, but can't determine which exact type."""

    SONG = auto()
    ALBUM = auto()
    ARTIST = auto()
    PLAYLIST = auto()
    USER = auto()
    UNKNOWN = auto()


class BaseLibraryItem:
    """Base class for all library item types.

    Provides common functionality for converting provider-specific data into
    standardized Downmixer types. Subclasses should set `_resource_type` and
    override `from_provider()` in their provider-specific adapter classes.
    """

    _resource_type: ResourceType

    @classmethod
    def get_resource_type(cls) -> ResourceType:
        """Returns the resource type for this class."""
        return cls._resource_type

    @classmethod
    def from_provider(cls, data: Any, extra_data: dict = None):
        """Create an instance of this class from data coming from a provider's API.

        Args:
            data (Any): Data from the provider's API.
            extra_data (dict, optional): Extra data from provider's API to be used to make instances of this class.

        Returns:
             An instance of this class.
        """
        pass

    @classmethod
    def from_provider_list(cls, data: list[Any], extra_data: dict = None) -> list:
        """Creates a list of instances of this class from a list of objects with data coming from a provider's API.

        Args:
            data (list[Any]): List of objects with data from the provider's API.
            extra_data (dict, optional): Extra data from provider's API to be used to make instances of this class.

        Returns:
            A list with instances of this class.
        """
        return [cls.from_provider(x, extra_data) for x in data]


@dataclass
class User(BaseLibraryItem):
    """Base class for a user of a music library."""

    _resource_type = ResourceType.USER

    id: str = None
    name: Optional[str] = None
    handle: Optional[str] = None

    def __hash__(self):
        if self.id:
            return hash(self.id)
        elif self.handle:
            return hash(self.handle)
        else:
            return hash(self.name)

    def __str__(self):
        return f"{self.name} ({self.id})" if self.name else self.id


@dataclass
class Artist(BaseLibraryItem):
    """Holds info about an artist."""

    _resource_type = ResourceType.ARTIST

    name: str
    images: Optional[list[str]] = None
    genres: Optional[list[str]] = None
    id: Optional[str] = None
    url: Optional[str] = None

    def slug(self) -> "Artist":
        """Returns self with sluggified text attributes."""
        return Artist(
            name=slugify(self.name),
            images=self.images,
            genres=[slugify(x) for x in self.genres] if self.genres else None,
            id=self.id,
            url=self.url,
        )

    @classmethod
    def from_dict(cls, d: dict) -> "Artist":
        """Create an Artist instance from a dictionary.

        Args:
            d: Dictionary with artist information.

        Returns:
            Artist instance populated from the dict.
        """
        return Artist(
            name=d.get("name"),
            images=d.get("images"),
            genres=d.get("genres"),
            id=d.get("id"),
            url=d.get("url"),
        )

    def to_dict(self) -> dict:
        """Convert the Artist instance to a dictionary."""
        return {
            "name": self.name,
            "images": self.images,
            "genres": self.genres,
            "id": self.id,
            "url": self.url,
        }

    def __hash__(self):
        if self.id:
            return hash(self.id)
        else:
            return hash(self.name)

    def __str__(self):
        return self.name


@dataclass
class Album(BaseLibraryItem):
    """Holds info about an album. `cover` should be a string containing a valid URL."""

    _resource_type = ResourceType.ALBUM

    name: str
    available_markets: Optional[list[str]] = None
    artists: Optional[list[Artist]] = None
    date: Optional[str] = None
    track_count: Optional[int] = None
    cover: Optional[str] = None
    upc: Optional[str] = None
    id: Optional[str] = None
    url: Optional[str] = None

    def __hash__(self):
        if self.id:
            return hash(self.id)
        else:
            return hash(self.full_title)

    @property
    def title(self) -> str:
        """str: Title of the album, including artist, in the format '[primary artist] - [album name]'."""
        return self.artists[0].name + " - " + self.name

    @property
    def full_title(self) -> str:
        """str: Full title of the album, including all artists, in the format [artist 1, artist 2, ...] - [album name]."""
        return self.all_artists + " - " + self.name

    @property
    def all_artists(self) -> str:
        """str: All artists' names, separated by a comma."""
        return ", ".join(x.name for x in self.artists)

    @classmethod
    def from_dict(cls, d: dict) -> "Album":
        """Create an Album instance from a dictionary.

        Args:
            d: Dictionary with album information.

        Returns:
            Album instance populated from the dict.
        """
        return Album(
            name=d.get("name"),
            available_markets=d.get("available_markets"),
            artists=(
                [Artist(**a) for a in d.get("artists", [])] if d.get("artists") else []
            ),
            date=d.get("date"),
            track_count=d.get("track_count"),
            cover=d.get("cover"),
            id=d.get("id"),
            url=d.get("url"),
        )

    def to_dict(self) -> dict:
        """Convert the Album instance to a dictionary."""
        return {
            "name": self.name,
            "available_markets": self.available_markets,
            "artists": (
                [artist.to_dict() for artist in self.artists] if self.artists else None
            ),
            "date": self.date,
            "track_count": self.track_count,
            "cover": self.cover,
            "id": self.id,
            "url": self.url,
        }

    def slug(self) -> "Album":
        """Returns self with sluggified text attributes."""
        return Album(
            name=slugify(self.name),
            available_markets=self.available_markets,
            artists=[x.slug for x in self.artists] if self.artists else None,
            date=self.date,
            track_count=self.track_count,
            cover=self.cover,
            id=self.id,
            url=self.url,
        )

    def __str__(self):
        return self.full_title


@dataclass
class Song(BaseLibraryItem):
    """Holds info about a song."""

    _resource_type = ResourceType.SONG

    name: str
    artists: list[Artist]
    duration: float = 0  # in seconds
    album: Optional[Album] = None
    available_markets: Optional[list[str]] = None
    date: Optional[str] = None
    track_number: Optional[int] = None
    isrc: Optional[str] = None
    lyrics: Optional[str] = None
    id: Optional[str] = None
    url: Optional[str] = None
    cover: Optional[str] = None

    def slug(self) -> "Song":
        """Returns self with sluggified text attributes."""
        return Song(
            name=slugify(self.name),
            artists=[x.slug() for x in self.artists],
            album=self.album.slug() if self.album else None,
            available_markets=self.available_markets,
            date=self.date,
            duration=self.duration,
            track_number=self.track_number,
            isrc=self.isrc,
            id=self.id,
            url=self.url,
            lyrics=slugify(self.lyrics) if self.lyrics else None,
        )

    @property
    def title(self) -> str:
        """str: Title of the song, including artist, in the format '[primary artist] - [song name]'."""
        return self.artists[0].name + " - " + self.name

    @property
    def full_title(self) -> str:
        """str: Full title of the song, including all artists, in the format [artist 1, artist 2, ...] - [song name]."""
        return self.all_artists + " - " + self.name

    @property
    def all_artists(self) -> str:
        """str: All artists' names, separated by a comma."""
        return ", ".join(x.name for x in self.artists)

    @classmethod
    def from_dict(cls, d: dict) -> "Song":
        """Create a Song instance from a dictionary.

        Args:
            d: Dictionary with song information.

        Returns:
            Song instance populated from the dict.
        """
        return Song(
            name=d.get("name"),
            artists=(
                [Artist.from_dict(a) for a in d.get("artists", [])]
                if d.get("artists")
                else []
            ),
            duration=d.get("duration", 0),
            album=Album.from_dict(d.get("album")) if d.get("album") else None,
            available_markets=d.get("available_markets"),
            date=d.get("date"),
            track_number=d.get("track_number"),
            isrc=d.get("isrc"),
            lyrics=d.get("lyrics"),
            id=d.get("id"),
            url=d.get("url"),
            cover=d.get("cover"),
        )

    def to_dict(self, minimal: bool = False) -> dict:
        """Convert the Song instance to a dictionary.

        Args:
            minimal: Provide only the most essential information about the song.
        """
        if minimal:
            return {
                "name": self.name,
                "artists": (
                    [artist.to_dict() for artist in self.artists]
                    if self.artists
                    else None
                ),
                "album": self.album.to_dict() if self.album else None,
                "isrc": self.isrc,
                "id": self.id,
            }
        else:
            return {
                "name": self.name,
                "artists": (
                    [artist.to_dict() for artist in self.artists]
                    if self.artists
                    else None
                ),
                "duration": self.duration,
                "album": self.album.to_dict() if self.album else None,
                "available_markets": self.available_markets,
                "date": self.date,
                "track_number": self.track_number,
                "isrc": self.isrc,
                "lyrics": self.lyrics,
                "id": self.id,
                "url": self.url,
                "cover": self.cover,
            }

    def __hash__(self):
        if self.id:
            return hash(self.id)
        else:
            return hash(self.full_title)

    def __str__(self):
        return self.full_title


@dataclass
class Playlist(BaseLibraryItem):
    """Holds info about a playlist."""

    _resource_type = ResourceType.PLAYLIST

    name: str
    description: Optional[str] = None
    tracks: Optional[list[Song]] = None
    images: Optional[list[dict]] = None
    id: Optional[str] = None
    url: Optional[str] = None
    owner: Optional[User] = None

    def __hash__(self):
        if self.id:
            return hash(self.id)
        else:
            return hash(self.title)

    @property
    def title(self) -> str:
        return self.name + " by " + (self.owner.name if self.owner else "Unknown")

    def __str__(self):
        return self.title
