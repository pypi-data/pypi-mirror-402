"""This module provides adapter child classes that convert Spotify API data into the internal data models used by Downmixer. Note that the return values of the `from_provider` and `from_provider_list` methods are instances of the internal models, not the adapter classes themselves."""

from typing import Any

from downmixer.types.library import Album, Artist, Playlist, Song, User

__all__ = [
    "SpotifyArtist",
    "SpotifyAlbum",
    "SpotifySong",
    "SpotifyPlaylist",
    "SpotifyUser",
]


class SpotifyArtist(Artist):
    """Represents an artist from Spotify, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Artist":
        """Create a SpotifyArtist instance from Spotify API data.

        Args:
            data (dict[str, Any]): The Spotify API artist data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            SpotifyArtist: The converted artist instance.
        """
        return Artist(
            name=data["name"],
            images=data["images"] if "images" in data.keys() else None,
            # TODO: Test the data structure of genres from Spotify
            genres=data["genres"] if "genres" in data.keys() else None,
            id=data["uri"],
            url=data["external_urls"]["spotify"],
        )

    @classmethod
    def from_provider_list(
        cls, data: list[dict[str, Any]], extra_data: dict[str, Any] = None
    ) -> list["Artist"]:
        """Convert a list of Spotify API artist data to SpotifyArtist instances.

        Args:
            data (list[dict[str, Any]]): List of Spotify API artist data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            list[SpotifyArtist]: List of converted artist instances.
        """
        return [cls.from_provider(x, extra_data) for x in data]


class SpotifyAlbum(Album):
    """Represents an album from Spotify, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Album":
        """Create a SpotifyAlbum instance from Spotify API data.

        Args:
            data (dict[str, Any]): The Spotify API album data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            SpotifyAlbum: The converted album instance.
        """
        return Album(
            available_markets=data["available_markets"],
            name=data["name"],
            artists=SpotifyArtist.from_provider_list(data["artists"]),
            date=data["release_date"],
            track_count=data["total_tracks"],
            cover=(data["images"][0]["url"] if len(data["images"]) > 0 else None),
            id=data["uri"],
            url=data["external_urls"]["spotify"],
        )

    @classmethod
    def from_provider_list(
        cls, data: list[Any], extra_data: dict = None
    ) -> list["Album"]:
        """Takes in a list of albums from the Spotify API and returns a list of SpotifyAlbums."""
        return [cls.from_provider(x["album"], extra_data) for x in data]


class SpotifySong(Song):
    """Represents a song from Spotify, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Song":
        """Create a SpotifySong instance from Spotify API data.

        Args:
            data (dict[str, Any]): The Spotify API track data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            SpotifySong: The converted song instance.

        Raises:
            ValueError: If data is None.
        """
        if data is None:
            raise ValueError("Data cannot be None")
        elif "album" in data.keys():
            album = data["album"]
        elif extra_data and "album" in extra_data.keys():
            album = extra_data["album"]
        else:
            album = None

        return Song(
            available_markets=data["available_markets"],
            name=data["name"],
            artists=SpotifyArtist.from_provider_list(data["artists"]),
            album=(SpotifyAlbum.from_provider(album) if album else None),
            duration=data["duration_ms"] / 1000,
            date=data["release_date"] if "release_date" in data.keys() else None,
            track_number=data["track_number"],
            isrc=(
                data["external_ids"]["isrc"] if "external_ids" in data.keys() else None
            ),
            id=data["uri"],
            url=data["external_urls"]["spotify"],
            cover=(
                album["images"][0]["url"]
                if album and len(album["images"]) > 0
                else None
            ),
        )

    @classmethod
    def from_provider_list(
        cls, data: list[dict], extra_data: dict[str, Any] = None
    ) -> list["Song"]:
        """Convert a list of Spotify API track data to SpotifySong instances.

        Args:
            data (list[dict]): List of Spotify API track data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            list[SpotifySong]: List of converted song instances.
        """
        try:
            return [cls.from_provider(x["track"], extra_data) for x in data]
        except (KeyError, ValueError):
            return [cls.from_provider(x, extra_data) for x in data]


class SpotifyPlaylist(Playlist):
    """Represents a playlist from Spotify, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Playlist":
        """Create a SpotifyPlaylist instance from Spotify API data.

        Args:
            data (dict[str, Any]): The Spotify API playlist data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            SpotifyPlaylist: The converted playlist instance.
        """
        return Playlist(
            name=data["name"],
            description=data["description"],
            tracks=(
                SpotifySong.from_provider_list(data["tracks"]["items"])
                if "items" in data["tracks"]
                else None
            ),
            images=data["images"],
            id=data["uri"],
            url=data["external_urls"]["spotify"],
            owner=SpotifyUser.from_provider(data["owner"]),
        )


class SpotifyUser(User):
    """Represents a Spotify user, converted to the internal model."""

    @classmethod
    def from_provider(cls, data: Any, extra_data: dict = None) -> "User":
        """Create a SpotifyUser instance from Spotify API data.

        Args:
            extra_data:
            data (dict[str, Any]): The Spotify API user data.

        Returns:
            SpotifyUser: The converted user instance.
        """
        return User(
            name=data["display_name"] if data["display_name"] else None,
            id=data["id"],
        )
