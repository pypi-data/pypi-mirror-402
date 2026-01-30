"""Unit types for the downmixer.providers.spotify module."""

import pytest

from downmixer.providers.spotify import RESOURCE_TYPE_MAP, SpotifyConnection, _get_all
from downmixer.providers.spotify.library import (
    SpotifyAlbum,
    SpotifyArtist,
    SpotifyPlaylist,
    SpotifySong,
    SpotifyUser,
)
from downmixer.types.library import Album, Artist, Playlist, ResourceType, Song, User


class TestResourceTypeMap:
    """Tests for the RESOURCE_TYPE_MAP constant."""

    def test_song_maps_to_track(self):
        """Test that SONG maps to 'track'."""
        assert RESOURCE_TYPE_MAP[ResourceType.SONG] == "track"

    def test_album_maps_to_album(self):
        """Test that ALBUM maps to 'album'."""
        assert RESOURCE_TYPE_MAP[ResourceType.ALBUM] == "album"

    def test_playlist_maps_to_playlist(self):
        """Test that PLAYLIST maps to 'playlist'."""
        assert RESOURCE_TYPE_MAP[ResourceType.PLAYLIST] == "playlist"

    def test_artist_maps_to_artist(self):
        """Test that ARTIST maps to 'artist'."""
        assert RESOURCE_TYPE_MAP[ResourceType.ARTIST] == "artist"


class TestGetAll:
    """Tests for the _get_all helper function."""

    def test_single_page_result(self):
        """Test _get_all with a single page of results."""

        def mock_func(limit, offset):
            return {"items": [1, 2, 3], "next": None}

        result = _get_all(mock_func)
        assert result == [1, 2, 3]

    def test_multiple_pages(self):
        """Test _get_all with multiple pages of results."""
        call_count = 0

        def mock_func(limit, offset):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"items": [1, 2], "next": "next_url"}
            elif call_count == 2:
                return {"items": [3, 4], "next": "next_url"}
            else:
                return {"items": [5], "next": None}

        result = _get_all(mock_func, limit=2)
        assert result == [1, 2, 3, 4, 5]
        assert call_count == 3

    def test_empty_result(self):
        """Test _get_all with empty results."""

        def mock_func(limit, offset):
            return {"items": [], "next": None}

        result = _get_all(mock_func)
        assert result == []

    def test_passes_args(self):
        """Test that _get_all passes additional args to the function."""
        received_args = []

        def mock_func(*args, limit, offset):
            received_args.extend(args)
            return {"items": ["item"], "next": None}

        _get_all(mock_func, 50, "arg1", "arg2")
        assert received_args == ["arg1", "arg2"]

    def test_passes_kwargs(self):
        """Test that _get_all passes keyword args to the function."""
        received_kwargs = {}

        def mock_func(limit, offset, **kwargs):
            received_kwargs.update(kwargs)
            return {"items": ["item"], "next": None}

        _get_all(mock_func, 50, custom_arg="custom_value")
        assert received_kwargs["custom_arg"] == "custom_value"

    def test_custom_limit(self):
        """Test that _get_all uses custom limit value."""
        received_limits = []

        def mock_func(limit, offset):
            received_limits.append(limit)
            return {"items": [1], "next": None}

        _get_all(mock_func, limit=25)
        assert received_limits[0] == 25

    def test_offset_increments(self):
        """Test that offset increments correctly."""
        received_offsets = []

        def mock_func(limit, offset):
            received_offsets.append(offset)
            if len(received_offsets) < 3:
                return {"items": [1], "next": "next"}
            return {"items": [1], "next": None}

        _get_all(mock_func, limit=10)
        assert received_offsets == [0, 10, 20]


class TestSpotifyConnectionCheckValidUrl:
    """Tests for SpotifyConnection.check_valid_url method."""

    @pytest.fixture
    def connection(self):
        """Create a SpotifyConnection instance for testing."""
        conn = SpotifyConnection()
        return conn

    def test_valid_track_uri(self, connection):
        """Test valid Spotify track URI."""
        assert (
            connection.check_valid_url("spotify:track:6rqhFgbbKwnb9MLmUQDhG6") is True
        )

    def test_valid_track_url(self, connection):
        """Test valid Spotify track URL."""
        url = "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"
        assert connection.check_valid_url(url) is True

    def test_valid_album_uri(self, connection):
        """Test valid Spotify album URI."""
        assert (
            connection.check_valid_url("spotify:album:6rqhFgbbKwnb9MLmUQDhG6") is True
        )

    def test_valid_album_url(self, connection):
        """Test valid Spotify album URL."""
        url = "https://open.spotify.com/album/6rqhFgbbKwnb9MLmUQDhG6"
        assert connection.check_valid_url(url) is True

    def test_valid_playlist_uri(self, connection):
        """Test valid Spotify playlist URI."""
        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
        assert connection.check_valid_url(uri) is True

    def test_valid_playlist_url(self, connection):
        """Test valid Spotify playlist URL."""
        url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
        assert connection.check_valid_url(url) is True

    def test_valid_artist_uri(self, connection):
        """Test valid Spotify artist URI."""
        # Use type_filter to avoid iterating over USER which is not in RESOURCE_TYPE_MAP
        # Artist ID must be 20-24 chars long
        assert (
            connection.check_valid_url(
                "spotify:artist:6rqhFgbbKwnb9MLmUQDhG6",
                type_filter=[ResourceType.ARTIST],
            )
            is True
        )

    def test_invalid_url(self, connection):
        """Test invalid URL."""
        # Use type_filter to avoid iterating over USER which is not in RESOURCE_TYPE_MAP
        assert (
            connection.check_valid_url(
                "https://example.com/track/123",
                type_filter=[ResourceType.SONG],
            )
            is False
        )

    def test_invalid_id_too_short(self, connection):
        """Test URL with ID that's too short."""
        # Use type_filter to avoid iterating over USER which is not in RESOURCE_TYPE_MAP
        assert (
            connection.check_valid_url(
                "spotify:track:short",
                type_filter=[ResourceType.SONG],
            )
            is False
        )

    def test_type_filter_track_only(self, connection):
        """Test type filter with track only."""
        assert (
            connection.check_valid_url(
                "spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
                type_filter=[ResourceType.SONG],
            )
            is True
        )
        assert (
            connection.check_valid_url(
                "spotify:album:6rqhFgbbKwnb9MLmUQDhG6",
                type_filter=[ResourceType.SONG],
            )
            is False
        )

    def test_type_filter_multiple(self, connection):
        """Test type filter with multiple types."""
        assert (
            connection.check_valid_url(
                "spotify:album:6rqhFgbbKwnb9MLmUQDhG6",
                type_filter=[ResourceType.SONG, ResourceType.ALBUM],
            )
            is True
        )


class TestSpotifyConnectionGetResourceType:
    """Tests for SpotifyConnection.get_resource_type method."""

    @pytest.fixture
    def connection(self):
        """Create a SpotifyConnection instance for testing."""
        return SpotifyConnection()

    def test_track_uri(self, connection):
        """Test resource type detection for track URI."""
        result = connection.get_resource_type("spotify:track:6rqhFgbbKwnb9MLmUQDhG6")
        assert result == ResourceType.SONG

    def test_track_url(self, connection):
        """Test resource type detection for track URL."""
        url = "https://open.spotify.com/track/6rqhFgbbKwnb9MLmUQDhG6"
        result = connection.get_resource_type(url)
        assert result == ResourceType.SONG

    def test_album_uri(self, connection):
        """Test resource type detection for album URI."""
        result = connection.get_resource_type("spotify:album:6rqhFgbbKwnb9MLmUQDhG6")
        assert result == ResourceType.ALBUM

    def test_album_url(self, connection):
        """Test resource type detection for album URL."""
        url = "https://open.spotify.com/album/6rqhFgbbKwnb9MLmUQDhG6"
        result = connection.get_resource_type(url)
        assert result == ResourceType.ALBUM

    def test_playlist_uri(self, connection):
        """Test resource type detection for playlist URI."""
        uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
        result = connection.get_resource_type(uri)
        assert result == ResourceType.PLAYLIST

    def test_artist_uri(self, connection):
        """Test resource type detection for artist URI."""
        # Artist ID must be 20-24 chars for the regex to match
        result = connection.get_resource_type("spotify:artist:6rqhFgbbKwnb9MLmUQDh")
        assert result == ResourceType.ARTIST

    def test_valid_url_returns_resource_type(self, connection):
        """Test that a valid URL returns the correct ResourceType."""
        # Test with a valid track URL that matches the pattern
        result = connection.get_resource_type("spotify:track:6rqhFgbbKwnb9MLmUQDhG6")
        assert result == ResourceType.SONG


class TestSpotifyArtist:
    """Tests for SpotifyArtist adapter class."""

    @pytest.fixture
    def artist_data(self):
        """Sample Spotify API artist data."""
        return {
            "name": "Test Artist",
            "images": [{"url": "https://example.com/image.jpg"}],
            "genres": ["rock", "indie"],
            "uri": "spotify:artist:1234567890123456789012",
            "external_urls": {"spotify": "https://open.spotify.com/artist/123"},
        }

    def test_from_provider(self, artist_data):
        """Test from_provider creates Artist correctly."""
        result = SpotifyArtist.from_provider(artist_data)
        assert isinstance(result, Artist)
        assert result.name == "Test Artist"
        assert result.id == "spotify:artist:1234567890123456789012"
        assert result.url == "https://open.spotify.com/artist/123"

    def test_from_provider_without_images(self, artist_data):
        """Test from_provider handles missing images."""
        del artist_data["images"]
        result = SpotifyArtist.from_provider(artist_data)
        assert result.images is None

    def test_from_provider_without_genres(self, artist_data):
        """Test from_provider handles missing genres."""
        del artist_data["genres"]
        result = SpotifyArtist.from_provider(artist_data)
        assert result.genres is None

    def test_from_provider_list(self, artist_data):
        """Test from_provider_list creates list of Artists."""
        result = SpotifyArtist.from_provider_list([artist_data, artist_data])
        assert len(result) == 2
        assert all(isinstance(a, Artist) for a in result)


class TestSpotifyAlbum:
    """Tests for SpotifyAlbum adapter class."""

    @pytest.fixture
    def album_data(self):
        """Sample Spotify API album data."""
        return {
            "name": "Test Album",
            "available_markets": ["US", "GB"],
            "artists": [
                {
                    "name": "Test Artist",
                    "uri": "spotify:artist:123",
                    "external_urls": {"spotify": "https://open.spotify.com/artist/123"},
                }
            ],
            "release_date": "2024-01-01",
            "total_tracks": 12,
            "images": [{"url": "https://example.com/cover.jpg"}],
            "uri": "spotify:album:1234567890123456789012",
            "external_urls": {"spotify": "https://open.spotify.com/album/123"},
        }

    def test_from_provider(self, album_data):
        """Test from_provider creates Album correctly."""
        result = SpotifyAlbum.from_provider(album_data)
        assert isinstance(result, Album)
        assert result.name == "Test Album"
        assert result.track_count == 12
        assert result.date == "2024-01-01"
        assert len(result.artists) == 1

    def test_from_provider_empty_images(self, album_data):
        """Test from_provider handles empty images list."""
        album_data["images"] = []
        result = SpotifyAlbum.from_provider(album_data)
        assert result.cover is None

    def test_from_provider_list_unwraps_album(self, album_data):
        """Test from_provider_list unwraps album from wrapper."""
        wrapped = [{"album": album_data}]
        result = SpotifyAlbum.from_provider_list(wrapped)
        assert len(result) == 1
        assert result[0].name == "Test Album"


class TestSpotifySong:
    """Tests for SpotifySong adapter class."""

    @pytest.fixture
    def song_data(self):
        """Sample Spotify API track data."""
        return {
            "name": "Test Song",
            "available_markets": ["US", "GB"],
            "artists": [
                {
                    "name": "Test Artist",
                    "uri": "spotify:artist:123",
                    "external_urls": {"spotify": "https://open.spotify.com/artist/123"},
                }
            ],
            "album": {
                "name": "Test Album",
                "available_markets": ["US"],
                "artists": [
                    {
                        "name": "Test Artist",
                        "uri": "spotify:artist:123",
                        "external_urls": {
                            "spotify": "https://open.spotify.com/artist/123"
                        },
                    }
                ],
                "release_date": "2024-01-01",
                "total_tracks": 12,
                "images": [{"url": "https://example.com/cover.jpg"}],
                "uri": "spotify:album:123",
                "external_urls": {"spotify": "https://open.spotify.com/album/123"},
            },
            "duration_ms": 210000,
            "track_number": 5,
            "external_ids": {"isrc": "USRC12345678"},
            "uri": "spotify:track:1234567890123456789012",
            "external_urls": {"spotify": "https://open.spotify.com/track/123"},
        }

    def test_from_provider(self, song_data):
        """Test from_provider creates Song correctly."""
        result = SpotifySong.from_provider(song_data)
        assert isinstance(result, Song)
        assert result.name == "Test Song"
        assert result.duration == 210.0  # ms converted to seconds
        assert result.track_number == 5
        assert result.isrc == "USRC12345678"

    def test_from_provider_none_raises_error(self):
        """Test from_provider raises ValueError when data is None."""
        with pytest.raises(ValueError, match="cannot be None"):
            SpotifySong.from_provider(None)

    def test_from_provider_without_album(self, song_data):
        """Test from_provider handles missing album."""
        del song_data["album"]
        result = SpotifySong.from_provider(song_data)
        assert result.album is None

    def test_from_provider_with_extra_data_album(self, song_data):
        """Test from_provider uses album from extra_data."""
        album = song_data.pop("album")
        extra_data = {"album": album}
        result = SpotifySong.from_provider(song_data, extra_data=extra_data)
        assert result.album is not None
        assert result.album.name == "Test Album"

    def test_from_provider_without_external_ids(self, song_data):
        """Test from_provider handles missing external_ids."""
        del song_data["external_ids"]
        result = SpotifySong.from_provider(song_data)
        assert result.isrc is None

    def test_from_provider_without_release_date(self, song_data):
        """Test from_provider handles missing release_date."""
        result = SpotifySong.from_provider(song_data)
        assert result.date is None  # release_date is in album, not track

    def test_from_provider_list_with_track_wrapper(self, song_data):
        """Test from_provider_list unwraps track from playlist item."""
        wrapped = [{"track": song_data}]
        result = SpotifySong.from_provider_list(wrapped)
        assert len(result) == 1
        assert result[0].name == "Test Song"

    def test_from_provider_list_without_track_wrapper(self, song_data):
        """Test from_provider_list handles direct track data."""
        result = SpotifySong.from_provider_list([song_data])
        assert len(result) == 1
        assert result[0].name == "Test Song"


class TestSpotifyPlaylist:
    """Tests for SpotifyPlaylist adapter class."""

    @pytest.fixture
    def playlist_data(self):
        """Sample Spotify API playlist data."""
        return {
            "name": "Test Playlist",
            "description": "A test playlist",
            "tracks": {"items": []},
            "images": [{"url": "https://example.com/playlist.jpg"}],
            "uri": "spotify:playlist:1234567890123456789012",
            "external_urls": {"spotify": "https://open.spotify.com/playlist/123"},
            "owner": {
                "display_name": "Test User",
                "id": "testuser123",
            },
        }

    def test_from_provider(self, playlist_data):
        """Test from_provider creates Playlist correctly."""
        result = SpotifyPlaylist.from_provider(playlist_data)
        assert isinstance(result, Playlist)
        assert result.name == "Test Playlist"
        assert result.description == "A test playlist"
        assert result.owner.name == "Test User"


class TestSpotifyUser:
    """Tests for SpotifyUser adapter class."""

    @pytest.fixture
    def user_data(self):
        """Sample Spotify API user data."""
        return {
            "display_name": "Test User",
            "id": "testuser123",
        }

    def test_from_provider(self, user_data):
        """Test from_provider creates User correctly."""
        result = SpotifyUser.from_provider(user_data)
        assert isinstance(result, User)
        assert result.name == "Test User"
        assert result.id == "testuser123"

    def test_from_provider_no_display_name(self, user_data):
        """Test from_provider handles missing display_name."""
        user_data["display_name"] = None
        result = SpotifyUser.from_provider(user_data)
        assert result.name is None
        assert result.id == "testuser123"
