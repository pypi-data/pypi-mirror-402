"""Protocol definitions for music provider capabilities.

This module defines Protocol classes that represent different capabilities a music
provider can implement. Providers can implement one or more of these protocols to
indicate what features they support (metadata fetching, audio downloading, library
access, or lyrics retrieval).
"""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from typing import List, Optional, Protocol, runtime_checkable

from downmixer.types.library import Album, Artist, Playlist, ResourceType, Song, User
from downmixer.types.processing import LocalFile
from downmixer.types.search import SearchResult


@runtime_checkable
class SupportsMetadata(Protocol):
    """Protocol for providers that can search and fetch music metadata.

    Implement this protocol to enable searching for music and retrieving detailed
    information about songs, albums, artists, playlists, and users from a provider.
    """

    def search(
        self, query: str, accepted_types: list[ResourceType] = None
    ) -> List[SearchResult]:
        """Search for music resources matching the given query.

        Args:
            query: The search query string.
            accepted_types: Optional list of resource types to filter results.
                If None, all resource types are included.

        Returns:
            A list of SearchResult objects matching the query.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_song(self, id: str) -> Song:
        """Fetch detailed information about a song.

        Args:
            id: The provider-specific identifier for the song.

        Returns:
            A Song object containing the song's metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_album(self, id: str) -> Album:
        """Fetch detailed information about an album.

        Args:
            id: The provider-specific identifier for the album.

        Returns:
            An Album object containing the album's metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_artist(self, id: str) -> Artist:
        """Fetch detailed information about an artist.

        Args:
            id: The provider-specific identifier for the artist.

        Returns:
            An Artist object containing the artist's metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_playlist(self, id: str) -> Playlist:
        """Fetch detailed information about a playlist.

        Args:
            id: The provider-specific identifier for the playlist.

        Returns:
            A Playlist object containing the playlist's metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_user(self, id: str) -> User:
        """Fetch detailed information about a user.

        Args:
            id: The provider-specific identifier for the user.

        Returns:
            A User object containing the user's profile information.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_list_songs(self, id: str) -> list[Song]:
        """Retrieves the all the songs from a playlist or album as a list.
        Args:
            id (str): A string containing a valid ID for the provider.

        Returns:
            All songs in the object.
        """
        raise NotImplementedError


@runtime_checkable
class SupportsAudioDownload(Protocol):
    """Protocol for providers that can download audio files.

    Implement this protocol to enable downloading song audio from a provider.
    """

    @abstractmethod
    def is_downloadable(self, song: Song) -> bool:
        """Check if a song can be downloaded from this provider.

        Args:
            song: The song to check for downloadability.

        Returns:
            True if the song can be downloaded, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_audio(
        self, song: SearchResult[Song] | str, path: Path
    ) -> Optional[LocalFile]:
        """Download the audio file for a song to the specified path.

        Args:
            song: A SearchResult containing a Song, or a song ID string.
            path: The folder (not filename) in which the file will be downloaded.

        Returns:
            A LocalFile object with the downloaded file information, or None if
            the download failed.
        """
        raise NotImplementedError


@runtime_checkable
class SupportsLibrary(Protocol):
    """Protocol for providers that can access a user's music library.

    Implement this protocol to enable fetching the authenticated user's saved
    playlists, albums, songs, and followed artists from a provider.
    """

    @abstractmethod
    def fetch_user_playlists(self) -> list[Playlist]:
        """Retrieves the all the user's playlists in a list.

        Returns:
            User's playlists as a list of Playlist objects.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_user_albums(self) -> list[Album]:
        """Retrieves the all the user's saved albums in a list.

        Returns:
            User's albums as a list of Album objects.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_user_songs(self) -> list[Song]:
        """Retrieves the all the user's liked/saved songs in a list (for example, on Spotify, should return user's
        saved tracks).

        Returns:
            User's playlists as a list of Playlist objects.
        """
        raise NotImplementedError

    @abstractmethod
    def fetch_user_artists(self) -> list[Artist]:
        """Retrieves the all the user's followed artists in a list.

        Returns:
            User's followed artists as a list of artist names.
        """
        raise NotImplementedError


@runtime_checkable
class SupportsLyrics(Protocol):
    """Protocol for providers that can fetch song lyrics.

    Implement this protocol to enable retrieving lyrics for songs from a provider.
    """

    @abstractmethod
    def fetch_lyrics(self, song: Song | str) -> str:
        """Fetch lyrics for a given song. Should return a string with lines separated by a `\n` (newline).

        Args:
            song: A Song object or a song ID string.

        Returns:
            The lyrics text for the song.
        """
        raise NotImplementedError

    @abstractmethod
    def list_supported_languages(self) -> list[str]:
        """List all supported languages for lyrics.

        Returns:
            A list of language codes supported by this provider.
        """
        raise NotImplementedError
