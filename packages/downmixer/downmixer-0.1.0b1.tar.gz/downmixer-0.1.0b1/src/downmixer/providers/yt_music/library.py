"""YouTube Music library adapter classes.

This module provides adapter classes that convert YouTube Music API data into
the internal data models used by Downmixer. The return values of `from_provider`
methods are instances of the internal models, not the adapter classes themselves.
"""

from typing import Any

from downmixer.types.library import Album, Artist, Playlist, Song, User

__all__ = [
    "YTMusicUser",
    "YTMusicArtist",
    "YTMusicSong",
    "YTMusicAlbum",
    "YTMusicPlaylist",
]


class YTMusicArtist(Artist):
    """Adapter for converting YouTube Music artist data to the internal model."""

    @classmethod
    def from_provider(cls, data: Any, extra_data: dict = None) -> Artist:
        """Create an Artist instance from YouTube Music API data.

        Args:
            data: The YouTube Music API artist data.
            extra_data: Additional data for conversion (unused).

        Returns:
            An Artist instance with the artist's metadata.
        """
        return Artist(name=data["artist"], id=data["browseId"])


class YTMusicAlbum(Album):
    """Adapter for converting YouTube Music album data to the internal model."""

    @classmethod
    def from_provider(cls, data: Any, extra_data: dict = None) -> Album:
        """Create an Album instance from YouTube Music API data.

        Args:
            data: The YouTube Music API album data.
            extra_data: Additional data containing album_browse_id if not in data.

        Returns:
            An Album instance with the album's metadata.
        """
        if data.get("browseId"):
            id = data["browseId"]
        else:
            id = extra_data["album_browse_id"]

        return Album(
            name=data["title"],
            id=id,
            date=data.get("year"),
            artists=(
                [Artist(name=a["name"], id=a["id"]) for a in data["artists"]]
                if data.get("artists") and len(data["artists"]) > 0
                else None
            ),
        )


class YTMusicSong(Song):
    """Adapter for converting YouTube Music song/video data to the internal model."""

    @classmethod
    def from_provider(cls, data: Any, extra_data: dict = None) -> Song:
        """Create a Song instance from YouTube Music API data.

        Args:
            data: The YouTube Music API track/video data.
            extra_data: Additional data containing album info if not in data.

        Returns:
            A Song instance with the song's metadata.
        """
        extracted_album = data.get("album")
        if type(extracted_album) is dict:
            album = Album(name=extracted_album["name"], id=extracted_album["id"])
        elif extra_data and "album" in extra_data.keys():
            album = YTMusicAlbum.from_provider(extra_data["album"], extra_data)
        else:
            album = None

        return Song(
            name=data.get("title"),
            artists=(
                [Artist(name=a["name"], id=a["id"]) for a in data["artists"]]
                if data.get("artists") and len(data["artists"]) > 0
                else None
            ),
            duration=data.get("duration_seconds"),
            album=album,
            id=data.get("videoId"),
        )


class YTMusicPlaylist(Playlist):
    """Adapter for converting YouTube Music playlist data to the internal model."""

    @classmethod
    def from_provider(cls, data: Any, extra_data: dict = None) -> Playlist:
        """Create a Playlist instance from YouTube Music API data.

        Args:
            data: The YouTube Music API playlist data.
            extra_data: Additional data for conversion (unused).

        Returns:
            A Playlist instance with the playlist's metadata.
        """
        return Playlist(
            name=data.get("title"),
            id=data.get("browseId", data.get("id")),
            owner=User(name=data["author"]) if data["author"] else None,
            description=data.get("description"),
            tracks=(
                [YTMusicSong.from_provider(x) for x in data["tracks"]]
                if data.get("tracks")
                else None
            ),
        )


class YTMusicUser(User):
    """Adapter for converting YouTube Music user/channel data to the internal model."""

    @classmethod
    def from_provider(cls, data: Any, extra_data: dict = None) -> User:
        """Create a User instance from YouTube Music API data.

        Args:
            data: The YouTube Music API user/channel data.
            extra_data: Additional data for conversion (unused).

        Returns:
            A User instance with the user's profile information.
        """
        return User(
            name=data.get("title"),
            id=data.get("browseId"),
            handle=data.get("name"),
        )
