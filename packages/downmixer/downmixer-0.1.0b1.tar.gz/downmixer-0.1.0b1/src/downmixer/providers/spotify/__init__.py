"""Spotify provider implementation.

This module provides the SpotifyProvider and SpotifyConnection classes for
interacting with the Spotify API. It supports fetching metadata for songs,
albums, artists, playlists, and users, as well as accessing the user's library.
"""

from __future__ import annotations

import importlib
import re
from typing import Any, Callable, Optional

import spotipy
from spotipy import SpotifyException, SpotifyOauthError, SpotifyStateError

from downmixer.providers import (
    BaseProvider,
)
from downmixer.providers.connections import AuthenticatedConnection, Connection
from downmixer.providers.spotify.library import (
    SpotifyAlbum,
    SpotifyArtist,
    SpotifyPlaylist,
    SpotifySong,
    SpotifyUser,
)
from downmixer.types import LoggerLike
from downmixer.types.library import Album, Artist, Playlist, ResourceType, Song, User
from downmixer.types.search import SearchResult
from downmixer.utils.logging import ConsoleLogger

RESOURCE_TYPE_MAP = {
    ResourceType.SONG: "track",
    ResourceType.ALBUM: "album",
    ResourceType.PLAYLIST: "playlist",
    ResourceType.ARTIST: "artist",
}


def _get_all(func: Callable, limit: int = 50, *args, **kwargs) -> list[Any]:
    """Helpers function to get all items from a paginated Spotify API endpoint.

    Args:
        func: The function mapping to an API endpoint to get the items. This function must accept `limit` and `offset` parameters.
        limit: Item limit per request. Defaults to 50, which is the maximum for most endpoints.
        *args: Args to pass to the function.
        **kwargs: Keyword args to pass to the function.

    Returns:
        list[Any]: List of all items returned by the endpoint.
    """
    counter = 0
    next_url = ""
    items = []

    while next_url is not None:
        results = func(*args, **kwargs, limit=limit, offset=limit * counter)
        next_url = results["next"]
        counter += 1
        items += results["items"]

    return items


class SpotifyConnection(AuthenticatedConnection):
    """Connection class for Spotify API.

    Manages authentication with Spotify using spotipy's auth managers.
    Supports OAuth, client credentials, and implicit grant flows.

    Attributes:
        _default_options: Default auth manager configuration.
        _client: The spotipy Spotify client instance.
        auth_manager: The spotipy auth manager handling token management.
    """

    _default_options = {
        "auth_manager_class": "SpotifyOAuth",
        "auth_manager_options": {
            "scope": "user-library-read,user-follow-read,playlist-read-private,playlist-read-collaborative"
        },
    }

    _client: spotipy.Spotify = None

    auth_manager: (
        spotipy.SpotifyOAuth
        | spotipy.SpotifyClientCredentials
        | spotipy.SpotifyImplicitGrant
    )

    def initialize(self) -> bool:
        """Initialize the Spotify auth manager.

        Creates an auth manager instance based on the configured class name.

        Returns:
            True if initialization was successful.

        Raises:
            SpotifyException: If there's an error creating the auth manager.
            SpotifyOauthError: If there's an OAuth-related error.
            SpotifyStateError: If there's a state validation error.
        """
        module = importlib.import_module("spotipy")
        auth_class = getattr(module, self.options["auth_manager_class"])

        self.logger.debug(f"Initializing auth class {auth_class.__name__}")
        try:
            self.auth_manager = auth_class(**self.options["auth_manager_options"])
            self._initialized = True
            return True
        except (SpotifyException, SpotifyOauthError, SpotifyStateError) as e:
            self.logger.error("Error while creating spotipy auth manager: %s", e)
            raise e

    def authenticate(self, **kwargs) -> bool:
        """Authenticate and create the Spotify client.

        Creates a Spotify client using the initialized auth manager.

        Args:
            **kwargs: Additional arguments passed to the Spotify client constructor.

        Returns:
            True if authentication was successful.

        Raises:
            SpotifyException: If client creation fails.
        """
        self.logger.debug(f"Initializing Spotify client")

        try:
            self._client = spotipy.Spotify(auth_manager=self.auth_manager, **kwargs)
            self._authenticated = True
            return True
        except SpotifyException as e:
            # TODO: handle exceptions more specifically
            self.logger.error("Failed to initialize Spotify client: %s", e)
            raise e

    def check_valid_url(self, url: str, type_filter: list[ResourceType] = None) -> bool:
        """Check if a URL is a valid Spotify resource URL for the given types.

        Args:
            url (str): The URL to check.
            type_filter (list[ResourceType], optional): List of resource types to check against. Defaults to all types.

        Returns:
            bool: True if the URL is valid for the given types, False otherwise.
        """
        if type_filter is None:
            type_filter = [e for e in ResourceType]

        for t in type_filter:
            regex = r"spotify.*" + RESOURCE_TYPE_MAP[t] + r"(?::|\/)(\w{20,24})"
            if re.search(regex, url) is not None:
                return True

        return False

    def get_resource_type(self, value: str) -> ResourceType | None:
        """Determine the resource type from a Spotify URL or URI.

        Args:
            value: A Spotify URL or URI string.

        Returns:
            The ResourceType if recognized, or None if invalid.
        """
        if not self.check_valid_url(value):
            return None

        pattern = r"spotify(?:.com)?(?::|\/)(\w*)(?::|\/)(?:\w{20,24})"
        matches = re.search(pattern, value)

        if matches is None:
            return None
        else:
            match_lower = matches.group(1).lower()
            index = list(RESOURCE_TYPE_MAP.values()).index(match_lower)
            return list(RESOURCE_TYPE_MAP.keys())[index]


class SpotifyProvider(BaseProvider):
    """Spotify music provider.

    Provides access to Spotify's music catalog and user library. Implements
    SupportsMetadata and SupportsLibrary protocols for fetching songs, albums,
    artists, playlists, and user library data.

    Attributes:
        client: The spotipy Spotify client for API calls.
    """

    _name = "spotify"
    _pretty_name = "Spotify"

    client: spotipy.Spotify

    def __init__(
        self,
        connection: SpotifyConnection,
        options: Optional[dict] = None,
        logger: "LoggerLike" = ConsoleLogger(),
    ):
        """Initialize the Spotify provider.

        Args:
            connection: An authenticated SpotifyConnection instance.
            options: Optional configuration options.
            logger: Logger instance for logging messages.

        Raises:
            AssertionError: If connection is not a SpotifyConnection.
        """
        assert isinstance(
            connection, SpotifyConnection
        ), "SpotifyProvider requires a SpotifyConnection instance."

        super().__init__(connection, options, logger)

    def fetch_list_songs(self, id: str) -> list[Song]:
        """Fetch all songs from a playlist or album.

        Args:
            id: The Spotify URI or URL of a playlist or album.

        Returns:
            A list of Song objects from the playlist or album.

        Raises:
            ValueError: If the ID is not a valid playlist or album.
        """
        resource_type = self.connection.get_resource_type(id)

        match resource_type:
            case ResourceType.PLAYLIST:
                results = _get_all(self.client.playlist_items, limit=50, playlist_id=id)
                return SpotifySong.from_provider_list(results)
            case ResourceType.ALBUM:
                album_info = self.client.album(id)
                results = _get_all(self.client.album_tracks, limit=50, album_id=id)

                return SpotifySong.from_provider_list(
                    results, extra_data={"album": album_info}
                )

        raise ValueError(f"ID {id} is not a valid playlist or album URL/URI.")

    def fetch_album(self, id: str) -> Album:
        """Fetch album metadata from Spotify.

        Args:
            id: The Spotify URI or URL of the album.

        Returns:
            An Album object with the album's metadata.
        """
        result = self.client.album(id)
        return SpotifyAlbum.from_provider(result)

    def fetch_artist(self, id: str) -> Artist:
        """Fetch artist metadata from Spotify.

        Args:
            id: The Spotify URI or URL of the artist.

        Returns:
            An Artist object with the artist's metadata.
        """
        result = self.client.artist(id)
        return SpotifyArtist.from_provider(result)

    def fetch_playlist(self, id: str) -> Playlist:
        """Fetch playlist metadata from Spotify.

        Args:
            id: The Spotify URI or URL of the playlist.

        Returns:
            A Playlist object with the playlist's metadata.
        """
        result = self.client.playlist(id)
        return SpotifyPlaylist.from_provider(result)

    def fetch_song(self, id: str) -> Song:
        """Fetch song/track metadata from Spotify.

        Args:
            id: The Spotify URI or URL of the track.

        Returns:
            A Song object with the track's metadata.
        """
        result = self.client.track(id)
        return SpotifySong.from_provider(result)

    def fetch_user(self, id: str) -> User:
        """Fetch user profile from Spotify.

        Args:
            id: The Spotify user ID.

        Returns:
            A User object with the user's profile information.
        """
        result = self.client.user(id)
        return SpotifyUser.from_provider(result)

    def search(
        self, query: str, accepted_types: list[ResourceType] = None
    ) -> list[SearchResult]:
        """Search for music on Spotify.

        Args:
            query: The search query string.
            accepted_types: Resource types to search for. Defaults to songs only.

        Returns:
            A list of SearchResult objects matching the query.
        """
        if accepted_types is None:
            accepted_types = [ResourceType.SONG]

        types = []
        for r in accepted_types:
            if r == ResourceType.SONG:
                types.append("track")
            elif r == ResourceType.ALBUM:
                types.append("album")
            elif r == ResourceType.PLAYLIST:
                types.append("playlist")
            elif r == ResourceType.ARTIST:
                types.append("artist")

        results = self.client.search(q=query, type=",".join(types))
        parsed_results: list[SearchResult] = []
        if results.get("tracks", None):
            parsed_results += [
                SearchResult(self.name, SpotifySong.from_provider(i))
                for i in results["tracks"]["items"]
            ]
        if results.get("albums", None):
            parsed_results += [
                SearchResult(self.name, SpotifyAlbum.from_provider(i))
                for i in results["albums"]["items"]
            ]
        if results.get("playlists", None):
            parsed_results += [
                SearchResult(self.name, SpotifyPlaylist.from_provider(i))
                for i in results["playlists"]["items"]
            ]
        if results.get("artists", None):
            parsed_results += [
                SearchResult(self.name, SpotifyArtist.from_provider(i))
                for i in results["artists"]["items"]
            ]

        return parsed_results

    def fetch_user_albums(self) -> list[Album]:
        """Fetch the current user's saved albums.

        Returns:
            A list of Album objects from the user's library.
        """
        results = _get_all(self.client.current_user_saved_albums, limit=50)
        return SpotifyAlbum.from_provider_list(results)

    def fetch_user_artists(self) -> list[Artist]:
        """Fetch the current user's followed artists.

        Returns:
            A list of Artist objects the user follows.
        """
        results = _get_all(self.client.current_user_followed_artists, limit=50)
        return SpotifyArtist.from_provider_list(results)

    def fetch_user_playlists(self) -> list[Playlist]:
        """Fetch the current user's playlists.

        Returns:
            A list of Playlist objects from the user's library.
        """
        results = _get_all(self.client.current_user_playlists)
        return SpotifyPlaylist.from_provider_list(results)

    def fetch_user_songs(self) -> list[Song]:
        """Fetch the current user's saved tracks.

        Returns:
            A list of Song objects from the user's library.
        """
        results = _get_all(self.client.current_user_saved_tracks, limit=50)
        return SpotifySong.from_provider_list(results)

    @classmethod
    def get_connections(cls) -> list[type[Connection]]:
        """Return the connection types supported by SpotifyProvider."""
        return [SpotifyConnection]


def get_provider() -> type[SpotifyProvider]:
    """Return the SpotifyProvider class for provider discovery."""
    return SpotifyProvider
