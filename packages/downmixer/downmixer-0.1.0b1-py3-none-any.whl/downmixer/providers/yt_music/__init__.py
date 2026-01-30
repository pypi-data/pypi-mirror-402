"""YouTube Music provider implementation.

This module provides the YTMusicProvider and YTMusicBasicConnection classes for
interacting with YouTube Music. It supports fetching metadata, searching, accessing
user libraries, and downloading audio using yt-dlp.
"""

import re
from pathlib import Path
from typing import Callable, List, Optional

import yt_dlp
import ytmusicapi
from ytmusicapi.exceptions import YTMusicServerError, YTMusicUserError

from downmixer.file_tools import AudioCodecs
from downmixer.providers import BaseProvider, Connection
from downmixer.providers.yt_music.library import (
    YTMusicAlbum,
    YTMusicArtist,
    YTMusicPlaylist,
    YTMusicSong,
    YTMusicUser,
)
from downmixer.types.library import Album, Artist, Playlist, ResourceType, Song, User
from downmixer.types.processing import LocalFile
from downmixer.types.search import SearchResult
from downmixer.utils.logging import ConsoleLogger

ALBUM_MARKER = "MPRE"
YOUTUBE_URL_REGEX = r"/^(?:(?:https|http):\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})(?:\S+)?$/"


class YTMusicBasicConnection(Connection):
    """Connection class for YouTube Music API.

    Manages the ytmusicapi client and yt-dlp downloader for interacting
    with YouTube Music without user authentication.

    Attributes:
        client: The ytmusicapi YTMusic client instance.
        _dl_client: The yt-dlp YoutubeDL instance for downloading.
    """

    client: ytmusicapi.YTMusic
    _dl_client: yt_dlp.YoutubeDL

    def check_valid_url(self, url: str, type_filter: list[ResourceType] = None) -> bool:
        """Check if a URL is a valid YouTube URL.

        Args:
            url: The URL to validate.
            type_filter: Not used for YouTube Music validation.

        Returns:
            True if the URL matches YouTube URL patterns.
        """
        match = re.match(YOUTUBE_URL_REGEX, url)
        return bool(match)

    def get_resource_type(self, value: str) -> ResourceType | None:
        """Determine the resource type of a YouTube Music ID.

        Attempts to identify whether the given ID corresponds to a song,
        album, playlist, artist, or user by testing against the API.

        Args:
            value: The YouTube Music ID or browse ID to analyze.

        Returns:
            The ResourceType if recognized, or None if not found.
        """
        if value.startswith("MPRE"):
            return ResourceType.ALBUM

        test_methods: list[tuple[ResourceType, Callable]] = [
            (ResourceType.SONG, self.client.get_song),
            (ResourceType.ALBUM, self.client.get_album_browse_id),
            (ResourceType.PLAYLIST, self.client.get_playlist),
            (ResourceType.ARTIST, self.client.get_artist),
            (ResourceType.USER, self.client.get_user),
        ]

        for t in test_methods:
            try:
                result = t[1](value)
                if result is None:
                    continue
                elif isinstance(result, str) and result.startswith("MPRE"):
                    continue
                elif result.get("playabilityStatus", {}).get("status") == "ERROR":
                    continue
                else:
                    return t[0]
            except (ValueError, KeyError, YTMusicUserError, YTMusicServerError) as e:
                self.logger.debug(f"Error while checking URL {e}")
                continue

        return None

    @property
    def dl_client(self) -> yt_dlp.YoutubeDL:
        """The yt-dlp downloader client instance."""
        return self._dl_client

    def initialize(self) -> bool:
        """Initialize the YouTube Music and yt-dlp clients.

        Creates a YTMusic client with German language setting (required for
        proper ISRC lookups) and a YoutubeDL client for downloading.

        Returns:
            True if initialization was successful.
        """
        # For some reason some songs like 70tjloUDVlGYkapPPTWRxU weren't found via ISRC if the language param was not
        # specified 🤷🏻‍♀️. Selecting English bought a completely fucked up result too. I copied "de" (aka German)
        # from spotDL
        self._client = ytmusicapi.YTMusic(language="de")
        self._dl_client = yt_dlp.YoutubeDL(self.options)
        self._initialized = True

        return self._initialized


class YTMusicProvider(BaseProvider):
    """YouTube Music provider.

    Provides access to YouTube Music's catalog and user library. Implements
    SupportsMetadata, SupportsLibrary, and SupportsAudioDownload protocols
    for fetching metadata, accessing libraries, and downloading audio.

    Attributes:
        client: The ytmusicapi YTMusic client for API calls.
        dl_client: The yt-dlp client for audio downloads.
    """

    _name = "yt_music"
    _pretty_name = "YouTube Music"

    _default_options = {
        "encoding": "UTF-8",
        "format": "bestaudio",
        "continuedl": True,
        "retries": 10,
    }

    client: ytmusicapi.YTMusic
    dl_client: yt_dlp.YoutubeDL

    def __init__(
        self,
        connection: YTMusicBasicConnection,
        options: Optional[dict] = None,
        logger: "LoggerLike" = ConsoleLogger(),
    ):
        """Initialize the YouTube Music provider.

        Args:
            connection: An initialized YTMusicBasicConnection instance.
            options: Optional configuration options.
            logger: Logger instance for logging messages.

        Raises:
            AssertionError: If connection is not a YTMusicBasicConnection.
        """
        assert isinstance(
            connection, YTMusicBasicConnection
        ), "YTMusicProvider requires a YTMusicBasicConnection instance."

        super().__init__(connection, options, logger)

        self.dl_client = self.connection.dl_client

    def _get_browse_id(self, id: str) -> str | None:
        """Convert an album ID to a browse ID if necessary.

        Args:
            id: An album ID or browse ID.

        Returns:
            The browse ID for the album.
        """
        if not id.startswith(ALBUM_MARKER):
            browse_id = self.client.get_album_browse_id(id)
        else:
            browse_id = id
        return browse_id

    def fetch_album(self, id: str) -> Album:
        """Fetch album metadata from YouTube Music.

        Args:
            id: The YouTube Music album ID or browse ID.

        Returns:
            An Album object with the album's metadata.
        """
        browse_id = self._get_browse_id(id)
        result = self.client.get_album(browse_id)
        return YTMusicAlbum.from_provider(result)

    def fetch_artist(self, id: str) -> Artist:
        """Fetch artist metadata from YouTube Music.

        Args:
            id: The YouTube Music artist ID.

        Returns:
            An Artist object with the artist's metadata.
        """
        result = self.client.get_artist(id)
        return YTMusicArtist.from_provider(result)

    def fetch_list_songs(self, id: str) -> list[Song]:
        """Fetch all songs from a playlist or album.

        Args:
            id: The YouTube Music playlist or album ID.

        Returns:
            A list of Song objects from the playlist or album.

        Raises:
            ValueError: If the ID is not a valid playlist or album.
        """
        resource_type = self.connection.get_resource_type(id)
        if resource_type == ResourceType.PLAYLIST:
            results = self.client.get_playlist(id, limit=None)
            return YTMusicSong.from_provider_list(results["tracks"])
        elif resource_type == ResourceType.ALBUM:
            browse_id = self._get_browse_id(id)
            results = self.client.get_album(browse_id)

            return YTMusicSong.from_provider_list(
                results["tracks"],
                extra_data={"album": results, "album_browse_id": browse_id},
            )

        raise ValueError(f"ID {id} is not a valid playlist or album URL/URI.")

    def fetch_playlist(self, id: str) -> Playlist:
        """Fetch playlist metadata from YouTube Music.

        Args:
            id: The YouTube Music playlist ID.

        Returns:
            A Playlist object with the playlist's metadata.
        """
        result = self.client.get_playlist(id, limit=None)
        return YTMusicPlaylist.from_provider(result)

    def fetch_song(self, id: str) -> Song:
        """Fetch song metadata from YouTube Music.

        Args:
            id: The YouTube Music video ID.

        Returns:
            A Song object with the song's metadata.
        """
        result = self.client.get_song(id)
        return YTMusicSong.from_provider(result)

    def fetch_user(self, id: str) -> User:
        """Fetch user profile from YouTube Music.

        Args:
            id: The YouTube Music user/channel ID.

        Returns:
            A User object with the user's profile information.
        """
        result = self.client.get_user(id)
        return YTMusicUser.from_provider(result)

    def search(
        self, query: str, accepted_types: list[ResourceType] = None
    ) -> List[SearchResult]:
        """Search for music on YouTube Music.

        Args:
            query: The search query string.
            accepted_types: Not used; YouTube Music search returns all types.

        Returns:
            A list of SearchResult objects matching the query.
        """
        # ignoring accepted_types since YTMusic search doesn't support filtering uploads

        parsed_results: list[SearchResult] = []
        results = self.client.search(query)
        for r in results:
            if (
                r["resultType"] == "song"
                or r["resultType"] == "video"
                and r["videoType"] == "MUSIC_VIDEO_TYPE_OMV"
            ):
                parsed_results.append(
                    SearchResult(self.name, YTMusicSong.from_provider(r))
                )
            elif r["resultType"] == "album":
                parsed_results.append(
                    SearchResult(self.name, YTMusicAlbum.from_provider(r))
                )
            elif r["resultType"] == "artist":
                parsed_results.append(
                    SearchResult(self.name, YTMusicArtist.from_provider(r))
                )
            elif r["resultType"] == "playlist":
                parsed_results.append(
                    SearchResult(self.name, YTMusicPlaylist.from_provider(r))
                )

        return parsed_results

    def fetch_user_albums(self) -> list[Album]:
        """Fetch the current user's saved albums.

        Returns:
            A list of Album objects from the user's library.
        """
        result = self.client.get_library_albums()
        return YTMusicAlbum.from_provider_list(result)

    def fetch_user_artists(self) -> list[Artist]:
        """Fetch the current user's followed artists.

        Returns:
            A list of Artist objects the user follows.
        """
        result = self.client.get_library_artists()
        return YTMusicArtist.from_provider_list(result)

    def fetch_user_playlists(self) -> list[Playlist]:
        """Fetch the current user's playlists.

        Returns:
            A list of Playlist objects from the user's library.
        """
        result = self.client.get_library_playlists()
        return YTMusicPlaylist.from_provider_list(result)

    def fetch_user_songs(self) -> list[Song]:
        """Fetch the current user's saved songs.

        Returns:
            A list of Song objects from the user's library.
        """
        result = self.client.get_library_songs()
        return YTMusicSong.from_provider_list(result)

    def fetch_audio(
        self, result: SearchResult[Song] | str, path: Path
    ) -> Optional[LocalFile]:
        """Download audio for a song using yt-dlp.

        Args:
            result: A SearchResult containing a Song with download URL.
            path: The folder to save the downloaded file.

        Returns:
            A LocalFile object with the downloaded file information.
        """
        self.logger.info(
            f"Starting download for search result '{result.item.title}' with URL {result.download_url}"
        )

        # Set output path of YoutubeDL on the fly
        self.dl_client.params["outtmpl"]["default"] = (
            str(path.absolute()) + "/%(id)s.%(ext)s"
        )
        url = result.download_url
        metadata = self.connection.dl_client.extract_info(url=url, download=True)
        self.logger.info("Finished downloading")

        downloaded = metadata["requested_downloads"][0]

        self.logger.debug("Creating download object")
        p = Path(downloaded["filepath"])
        return LocalFile(
            source=result.result,
            original=result.source,
            path=p,
            bitrate=downloaded["abr"],
            audio_codec=AudioCodecs(downloaded["acodec"]),
            size=p.stat().st_size,
        )

    def is_downloadable(self, song: Song) -> bool:
        """Check if a song can be downloaded.

        Args:
            song: The song to check.

        Returns:
            True if the song can be downloaded (not implemented).
        """
        pass

    @classmethod
    def get_connections(cls) -> list[type[Connection]]:
        """Return the connection types supported by YTMusicProvider."""
        return [YTMusicBasicConnection]


def get_provider() -> type[YTMusicProvider]:
    """Return the YTMusicProvider class for provider discovery."""
    return YTMusicProvider
