"""Qobuz provider implementation.

This module provides the QobuzProvider and QobuzConnection classes for
interacting with the Qobuz API. It supports fetching metadata, searching,
and downloading high-quality audio files.
"""

import hashlib
import time
from pathlib import Path
from typing import List, Optional

import requests
from requests import HTTPError

from downmixer.file_tools import AudioCodecs
from downmixer.providers import BaseProvider
from downmixer.providers.connections import AuthenticatedConnection, Connection
from downmixer.providers.qobuz import bundle
from downmixer.providers.qobuz.client import QobuzClient
from downmixer.providers.qobuz.library import (
    QobuzAlbum,
    QobuzArtist,
    QobuzPlaylist,
    QobuzSong,
)
from downmixer.types.exceptions import IncompleteSupportWarning, UnsupportedException
from downmixer.types.library import Album, Artist, Playlist, ResourceType, Song, User
from downmixer.types.processing import LocalFile
from downmixer.types.search import SearchResult

RESOURCE_TYPE_MAP = {
    ResourceType.SONG: "track",
    ResourceType.ALBUM: "album",
    ResourceType.PLAYLIST: "playlist",
    ResourceType.ARTIST: "artist",
}
QL_DOWNGRADE = "FormatRestrictedByFormatAvailability"


class QobuzConnection(AuthenticatedConnection):
    """Connection class for Qobuz API.

    Manages authentication with Qobuz and provides URL validation.
    Requires a paid Qobuz subscription for audio downloads.

    Attributes:
        _client: The QobuzClient instance for API requests.
    """

    _client: QobuzClient = None

    def check_valid_url(self, url: str, type_filter: list[ResourceType] = None) -> bool:
        """Check if a URL or ID is valid for Qobuz.

        Args:
            url: The URL or ID to validate.
            type_filter: Optional list of resource types to filter against.

        Returns:
            True if the URL/ID is valid for the given types.
        """
        resource_type = self.get_resource_type(url)
        if type_filter is None and resource_type:
            return True

        if isinstance(resource_type, ResourceType):
            if resource_type in type_filter:
                return True
        elif isinstance(resource_type, list):
            for r in resource_type:
                if r in type_filter:
                    return True

        return False

    def get_resource_type(self, value: str) -> ResourceType | None:
        """Determine the resource type of a Qobuz ID.

        Args:
            value: The Qobuz ID to analyze.

        Returns:
            The ResourceType if recognized, UNKNOWN if multiple types match,
            or None if not found.
        """
        value = str(value)
        if not value.isdigit():
            try:
                self._client.request("album/get", album_id=value)
                return ResourceType.ALBUM
            except HTTPError as e:
                if 400 <= e.response.status_code < 500:
                    pass
                else:
                    raise e

        resource_types = self._get_all_resource_types(value)
        if resource_types is None:
            return None
        elif len(resource_types) == 1:
            return resource_types[0]
        elif len(resource_types) > 1:
            return ResourceType.UNKNOWN

        return None

    def _get_all_resource_types(
        self, value: str, inpatient: bool = False
    ) -> list[ResourceType] | None:
        """Get a list of ResourceTypes matching the ID `value`.

        Args:
            value: ID to be tested
            inpatient: If true, will return after the first match is found. Avoids wasting
                requests if you just want to check if an ID matches multiple types but don't care which.

        Returns:
            list[ResourceType]: List with all matched ResourceTypes.
        """
        IncompleteSupportWarning(
            "Qobuz IDs can be valid for more than one type. Use check_valid_url() and its type_filter param instead."
        )

        test_methods: list[tuple[ResourceType, str, str]] = [
            (ResourceType.SONG, "track/get", "track_id"),
            (ResourceType.PLAYLIST, "playlist/get", "playlist_id"),
            (ResourceType.ARTIST, "artist/get", "artist_id"),
            (ResourceType.ALBUM, "album/get", "album_id"),
        ]

        results: list[ResourceType] = []
        for t in test_methods:
            try:
                result = self._client.request(t[1], **{t[2]: value})
                if inpatient and len(results) > 1:
                    return results
                else:
                    results.append(t[0])

            except HTTPError as e:
                if 400 <= e.response.status_code < 500:
                    continue
                else:
                    raise e

        if len(results) >= 1:
            return results

        return None

    def initialize(self) -> bool:
        """Initialize the Qobuz client with API credentials.

        Fetches the app bundle and creates a QobuzClient instance.

        Returns:
            True if initialization was successful.
        """
        qobuz_bundle = bundle.Bundle()
        self._client = QobuzClient(qobuz_bundle, self.logger)

        self._initialized = True
        return True

    def authenticate(self, **kwargs) -> bool:
        """Authenticate with Qobuz using email and password.

        Credentials should be provided in the connection options.

        Returns:
            True if authentication was successful.
        """
        password = self.options["password"].encode("utf-8")

        success = self._client.login(self.options["email"], password)
        self._authenticated = success
        return success


def _download(filename: Path, url: str) -> None:
    """Download a file from a URL to the specified path.

    Args:
        filename: The path to save the downloaded file.
        url: The URL to download from.

    Raises:
        ConnectionError: If the download was interrupted.
    """
    r = requests.get(url, allow_redirects=True, stream=True)
    total = int(r.headers.get("content-length", 0))
    download_size = 0
    with open(filename, "wb") as file:
        for data in r.iter_content(chunk_size=1024):
            size = file.write(data)
            download_size += size

    if total != download_size:
        # https://stackoverflow.com/questions/69919912/requests-iter-content-thinks-file-is-complete-but-its-not
        raise ConnectionError("File download was interrupted for " + str(filename))


class QobuzProvider(BaseProvider):
    """Qobuz music provider.

    Provides access to Qobuz's high-quality music catalog. Implements
    SupportsMetadata and SupportsAudioDownload protocols for fetching
    metadata and downloading lossless audio files.

    Attributes:
        client: The QobuzClient instance for API requests.
    """

    _name = "qobuz"
    _pretty_name = "Qobuz"

    _default_options = {
        "quality": 6,
        "downgrade_quality": False,
    }

    client: QobuzClient

    @staticmethod
    def _get_title(data: dict) -> str:
        """Extract the full album title including version suffix.

        Args:
            data: Album data dictionary from the API.

        Returns:
            The album title with version appended if present.
        """
        album_title = data["title"]
        version = data.get("version")
        if version:
            album_title = (
                f"{album_title} ({version})"
                if version.lower() not in album_title.lower()
                else album_title
            )
        return album_title

    def _get_track_url(self, id: str, format_id: int, secret=None) -> dict:
        """Get the download URL for a track.

        Args:
            id: The Qobuz track ID.
            format_id: Quality format ID (5=MP3, 6=CD, 7=24bit/96kHz, 27=24bit/192kHz).
            secret: Optional app secret override.

        Returns:
            API response containing the download URL and quality info.

        Raises:
            ValueError: If an invalid quality ID is provided.
        """
        unix = time.time()
        track_id = id
        fmt_id = format_id
        if int(fmt_id) not in (5, 6, 7, 27):
            raise ValueError("Invalid quality id: choose between 5, 6, 7 or 27")
        r_sig = "trackgetFileUrlformat_id{}intentstreamtrack_id{}{}{}".format(
            fmt_id, track_id, unix, self.client.sec if secret is None else secret
        )
        r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
        params = {
            "request_ts": unix,
            "request_sig": r_sig_hashed,
            "track_id": track_id,
            "format_id": fmt_id,
            "intent": "stream",
        }

        return self.client.request("track/getFileUrl", **params)

    def _is_quality_met(self, song_info: dict) -> bool:
        """Check if the requested quality is available for a track.

        Args:
            song_info: Track info from the API including restrictions.

        Returns:
            True if the quality is available, False if restricted.
        """
        if int(self.options["quality"]) != 5:
            restrictions = song_info.get("restrictions")
            if isinstance(restrictions, list):
                if any(
                    restriction.get("code") == QL_DOWNGRADE
                    for restriction in restrictions
                ):
                    return False

        return True

    def fetch_album(self, id: str) -> Album:
        """Fetch album metadata from Qobuz.

        Args:
            id: The Qobuz album ID.

        Returns:
            An Album object with the album's metadata.
        """
        result = self.client.request("album/get", album_id=id)
        return QobuzAlbum.from_provider(result)

    def fetch_artist(self, id: str) -> Artist:
        """Fetch artist metadata from Qobuz.

        Args:
            id: The Qobuz artist ID.

        Returns:
            An Artist object with the artist's metadata.
        """
        result = self.client.request("artist/get", artist_id=id)
        return QobuzArtist.from_provider(result)

    def fetch_list_songs(self, id: str) -> list[Song]:
        """Fetch all songs from a playlist or album.

        Args:
            id: The Qobuz playlist or album ID.

        Returns:
            A list of Song objects from the playlist or album.

        Raises:
            ValueError: If the ID is not a valid playlist or album.
        """
        resource_type = self.connection.get_resource_type(id)
        if resource_type == ResourceType.PLAYLIST:
            result = self.client.request(
                "playlist/get",
                playlist_id=id,
                extra="tracks",
            )
            return QobuzSong.from_provider_list(result["tracks"]["items"])
        elif resource_type == ResourceType.ALBUM:
            result = self.client.request("album/get", album_id=id)
            return QobuzSong.from_provider_list(result["tracks"]["items"])

        raise ValueError(f"ID {id} is not a valid playlist or album ID.")

    def fetch_playlist(self, id: str) -> Playlist:
        """Fetch playlist metadata from Qobuz.

        Args:
            id: The Qobuz playlist ID.

        Returns:
            A Playlist object with the playlist's metadata.
        """
        result = self.client.request("playlist/get", playlist_id=id)
        return QobuzPlaylist.from_provider(result)

    def fetch_song(self, id: str) -> Song:
        """Fetch song/track metadata from Qobuz.

        Args:
            id: The Qobuz track ID.

        Returns:
            A Song object with the track's metadata.
        """
        result = self.client.request("track/get", track_id=id)
        return QobuzSong.from_provider(result)

    def fetch_user(self, id: str) -> User:
        """Fetch user profile from Qobuz.

        Raises:
            UnsupportedException: Qobuz does not support user fetching.
        """
        raise UnsupportedException("Qobuz does not support user fetch requests.")

    def search(
        self, query: str, accepted_types: list[ResourceType] = None, limit: int = 20
    ) -> List[SearchResult]:
        """Search for music on Qobuz.

        Args:
            query: The search query string.
            accepted_types: Resource types to search for. Defaults to songs only.
            limit: Maximum number of results per type.

        Returns:
            A list of SearchResult objects matching the query.

        Raises:
            ValueError: If searching for users (not supported).
        """
        if accepted_types is None:
            accepted_types = [ResourceType.SONG]
        elif accepted_types == [ResourceType.USER]:
            raise ValueError("User searches not supported for Qobuz")

        results = {}
        for t in accepted_types:
            t_ = RESOURCE_TYPE_MAP[t]
            endpoint = f"{t_}/search"
            result = self.client.request(endpoint, query=query, limit=limit, offset=0)

            results[t] = result[t_.lower() + "s"]["items"]

        parsed_results: list[SearchResult] = []
        if results.get(ResourceType.SONG, None):
            parsed_results += [
                SearchResult(self.name, QobuzSong.from_provider(i))
                for i in results[ResourceType.SONG]
            ]
        if results.get(ResourceType.ALBUM, None):
            parsed_results += [
                SearchResult(self.name, QobuzAlbum.from_provider(i))
                for i in results[ResourceType.ALBUM]
            ]
        if results.get(ResourceType.PLAYLIST, None):
            parsed_results += [
                SearchResult(self.name, QobuzPlaylist.from_provider(i))
                for i in results[ResourceType.PLAYLIST]
            ]
        if results.get(ResourceType.ARTIST, None):
            parsed_results += [
                SearchResult(self.name, QobuzArtist.from_provider(i))
                for i in results[ResourceType.ARTIST]
            ]

        return parsed_results

    def fetch_audio(
        self, song: SearchResult[Song] | str, path: Path
    ) -> Optional[LocalFile]:
        """Download audio for a song from Qobuz.

        Downloads the track in the configured quality format (MP3 or FLAC).

        Args:
            song: A SearchResult containing a Song with the track ID.
            path: The folder to save the downloaded file.

        Returns:
            A LocalFile object with the downloaded file information,
            or None if the track is a demo or doesn't meet quality requirements.
        """
        song_id = song.id
        parse = self._get_track_url(song_id, self.options["quality"])

        if "sample" in parse or not parse["sampling_rate"]:
            self.logger.info(f"Demo. Skipping")
            return None

        quality_met = self._is_quality_met(parse)

        if not self.options["downgrade_quality"] and not quality_met:
            self.logger.info(
                f"Skipping {song.title} as it doesn't meet quality requirement."
            )
            return None

        is_mp3 = True if int(self.options["quality"]) == 5 else False
        extension = ".mp3" if is_mp3 else ".flac"

        try:
            url = parse["url"]
        except KeyError:
            self.logger.warning(f"Track not available for download")
            return None

        filename: Path = path.joinpath(str(song.id) + extension)

        _download(filename, url)
        self.logger.info(f"Completed")

        bitrate = (parse["bit_depth"] * (parse["sampling_rate"] * 1000) * 2) / 1000

        return LocalFile(
            source=song.result,
            original=song.source,
            path=filename,
            bitrate=bitrate,
            size=path.stat().st_size,
            audio_codec=AudioCodecs(extension[1:]),
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
        """Return the connection types supported by QobuzProvider."""
        return [QobuzConnection]


def get_provider() -> type[QobuzProvider]:
    """Return the QobuzProvider class for provider discovery."""
    return QobuzProvider
