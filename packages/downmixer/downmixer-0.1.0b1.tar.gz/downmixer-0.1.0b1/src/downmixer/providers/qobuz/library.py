"""This module provides adapter child classes that convert Qobuz API data into the internal data models used by Downmixer. Note that the return values of the `from_provider` and `from_provider_list` methods are instances of the internal models, not the adapter classes themselves."""

from typing import Any

from downmixer.types.library import Album, Artist, Playlist, Song, User

__all__ = [
    "QobuzArtist",
    "QobuzAlbum",
    "QobuzSong",
    "QobuzPlaylist",
    "QobuzUser",
]


class QobuzArtist(Artist):
    """Represents an artist from Qobuz, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Artist":
        """Create a QobuzArtist instance from Qobuz API data.

        Args:
            data (dict[str, Any]): The Qobuz API artist data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            QobuzArtist: The converted artist instance.
        """
        return Artist(
            id=data.get("id"),
            name=data.get("name"),
        )

    @classmethod
    def from_provider_list(
        cls, data: list[dict[str, Any]], extra_data: dict[str, Any] = None
    ) -> list["Artist"]:
        """Convert a list of Qobuz API artist data to QobuzArtist instances.

        Args:
            data (list[dict[str, Any]]): List of Qobuz API artist data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            list[QobuzArtist]: List of converted artist instances.
        """
        return [cls.from_provider(x, extra_data) for x in data]


class QobuzAlbum(Album):
    """Represents an album from Qobuz, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Album":
        """Create a QobuzAlbum instance from Qobuz API data.

        Args:
            data (dict[str, Any]): The Qobuz API album data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            QobuzAlbum: The converted album instance.
        """
        return Album(
            id=data.get("id"),
            name=data.get("title"),
            track_count=data.get("tracks_count"),
            date=data.get("released_at"),
            artists=[QobuzArtist.from_provider(data["artist"])],
            upc=data.get("upc"),
            cover=data.get("image").get(
                "large"
            ),  # TODO: support albums without "large" images
        )

    @classmethod
    def from_provider_list(
        cls, data: list[Any], extra_data: dict = None
    ) -> list["Album"]:
        """Takes in a list of albums from the Qobuz API and returns a list of QobuzAlbums."""
        return [cls.from_provider(x["album"], extra_data) for x in data]


class QobuzSong(Song):
    """Represents a song from Qobuz, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Song":
        """Create a QobuzSong instance from Qobuz API data.

        Args:
            data (dict[str, Any]): The Qobuz API track data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            QobuzSong: The converted song instance.

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
            name=data.get("title"),
            artists=[QobuzArtist.from_provider(data.get("performer"))],
            album=(QobuzAlbum.from_provider(album) if album else None),
            duration=data.get("duration"),
            track_number=data.get("track_number"),
            isrc=(data.get("isrc")),
            id=data.get("id"),
            date=data.get("release_date_original"),
        )

    @classmethod
    def from_provider_list(
        cls, data: list[dict], extra_data: dict[str, Any] = None
    ) -> list["Song"]:
        """Convert a list of Qobuz API track data to QobuzSong instances.

        Args:
            data (list[dict]): List of Qobuz API track data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            list[QobuzSong]: List of converted song instances.
        """
        try:
            return [cls.from_provider(x["track"], extra_data) for x in data]
        except (KeyError, ValueError):
            return [cls.from_provider(x, extra_data) for x in data]


class QobuzPlaylist(Playlist):
    """Represents a playlist from Qobuz, converted to the internal model."""

    @classmethod
    def from_provider(
        cls, data: dict[str, Any], extra_data: dict[str, Any] = None
    ) -> "Playlist":
        """Create a QobuzPlaylist instance from Qobuz API data.

        Args:
            data (dict[str, Any]): The Qobuz API playlist data.
            extra_data (dict[str, Any], optional): Additional data for conversion. Defaults to None.

        Returns:
            QobuzPlaylist: The converted playlist instance.
        """
        return Playlist(
            name=data.get("name"),
            description=data.get("description"),
            # tracks=(
            #     QobuzSong.from_provider_list(data.get("tracks", {}).get("items"))
            #     if data.get("tracks", {}).get("items")
            #     else None
            # ),
            images=data.get("image_rectangle", [None])[0],
            id=data.get("id"),
            # url=data.get("external_urls", {}).get("spotify"),
            owner=QobuzUser.from_provider(data.get("owner")),
        )


class QobuzUser(User):
    """Represents a Qobuz user, converted to the internal model."""

    @classmethod
    def from_provider(cls, data: dict, extra_data: dict = None) -> "User":
        """Create a QobuzUser instance from Qobuz API data.

        Args:
            extra_data:
            data (dict[str, Any]): The Qobuz API user data.

        Returns:
            QobuzUser: The converted user instance.
        """
        return User(
            name=data.get("name"),
            id=data.get("id"),
        )
