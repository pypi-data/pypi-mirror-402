"""Unit types for the downmixer.providers.yt_music module."""

import pytest

from downmixer.providers.yt_music import ALBUM_MARKER, YOUTUBE_URL_REGEX
from downmixer.providers.yt_music.library import (
    YTMusicAlbum,
    YTMusicArtist,
    YTMusicPlaylist,
    YTMusicSong,
    YTMusicUser,
)
from downmixer.types.library import Album, Artist, Playlist, Song, User


class TestConstants:
    """Tests for module constants."""

    def test_album_marker_value(self):
        """Test that ALBUM_MARKER has expected value."""
        assert ALBUM_MARKER == "MPRE"

    def test_youtube_url_regex_exists(self):
        """Test that YOUTUBE_URL_REGEX is defined."""
        assert YOUTUBE_URL_REGEX is not None
        assert isinstance(YOUTUBE_URL_REGEX, str)


class TestYTMusicArtist:
    """Tests for YTMusicArtist adapter class."""

    @pytest.fixture
    def artist_data(self):
        """Sample YTMusic API artist data."""
        return {
            "artist": "Test Artist",
            "browseId": "UCxxxxxxxxxxxxxxxxx",
        }

    def test_from_provider(self, artist_data):
        """Test from_provider creates Artist correctly."""
        result = YTMusicArtist.from_provider(artist_data)
        assert isinstance(result, Artist)
        assert result.name == "Test Artist"
        assert result.id == "UCxxxxxxxxxxxxxxxxx"

    def test_from_provider_list(self, artist_data):
        """Test from_provider_list creates list of Artists."""
        result = YTMusicArtist.from_provider_list([artist_data, artist_data])
        assert len(result) == 2
        assert all(isinstance(a, Artist) for a in result)


class TestYTMusicAlbum:
    """Tests for YTMusicAlbum adapter class."""

    @pytest.fixture
    def album_data(self):
        """Sample YTMusic API album data."""
        return {
            "title": "Test Album",
            "browseId": "MPRExxxxxxxxxxxxxxxxx",
            "year": "2024",
            "artists": [
                {"name": "Test Artist", "id": "UCxxxxxxxxxxxxxxxxx"},
            ],
        }

    @pytest.fixture
    def album_data_without_browse_id(self):
        """Sample YTMusic API album data without browseId."""
        return {
            "title": "Test Album",
            "year": "2024",
            "artists": [
                {"name": "Test Artist", "id": "UCxxxxxxxxxxxxxxxxx"},
            ],
        }

    def test_from_provider(self, album_data):
        """Test from_provider creates Album correctly."""
        result = YTMusicAlbum.from_provider(album_data)
        assert isinstance(result, Album)
        assert result.name == "Test Album"
        assert result.id == "MPRExxxxxxxxxxxxxxxxx"
        assert result.date == "2024"

    def test_from_provider_with_extra_data(self, album_data_without_browse_id):
        """Test from_provider uses extra_data for album_browse_id."""
        extra_data = {"album_browse_id": "MPREfromextradata"}
        result = YTMusicAlbum.from_provider(album_data_without_browse_id, extra_data)
        assert result.id == "MPREfromextradata"

    def test_from_provider_creates_artists(self, album_data):
        """Test from_provider creates Artist list correctly."""
        result = YTMusicAlbum.from_provider(album_data)
        assert len(result.artists) == 1
        assert result.artists[0].name == "Test Artist"

    def test_from_provider_empty_artists(self, album_data):
        """Test from_provider handles empty artists list."""
        album_data["artists"] = []
        result = YTMusicAlbum.from_provider(album_data)
        assert result.artists is None

    def test_from_provider_no_artists_key(self, album_data):
        """Test from_provider handles missing artists key."""
        del album_data["artists"]
        result = YTMusicAlbum.from_provider(album_data)
        assert result.artists is None


class TestYTMusicSong:
    """Tests for YTMusicSong adapter class."""

    @pytest.fixture
    def song_data(self):
        """Sample YTMusic API song data."""
        return {
            "title": "Test Song",
            "videoId": "xxxxxxxxxxx",
            "duration_seconds": 210,
            "artists": [
                {"name": "Test Artist", "id": "UCxxxxxxxxxxxxxxxxx"},
            ],
            "album": {
                "name": "Test Album",
                "id": "MPRExxxxxxxxxxxxxxxxx",
            },
        }

    @pytest.fixture
    def song_data_no_album(self):
        """Sample YTMusic API song data without album."""
        return {
            "title": "Test Song",
            "videoId": "xxxxxxxxxxx",
            "duration_seconds": 180,
            "artists": [
                {"name": "Test Artist", "id": "UCxxxxxxxxxxxxxxxxx"},
            ],
        }

    def test_from_provider(self, song_data):
        """Test from_provider creates Song correctly."""
        result = YTMusicSong.from_provider(song_data)
        assert isinstance(result, Song)
        assert result.name == "Test Song"
        assert result.id == "xxxxxxxxxxx"
        assert result.duration == 210

    def test_from_provider_with_dict_album(self, song_data):
        """Test from_provider handles album as dict."""
        result = YTMusicSong.from_provider(song_data)
        assert result.album is not None
        assert result.album.name == "Test Album"
        assert result.album.id == "MPRExxxxxxxxxxxxxxxxx"

    def test_from_provider_with_extra_data_album(self, song_data_no_album):
        """Test from_provider uses album from extra_data."""
        extra_data = {
            "album": {
                "title": "Extra Album",
                "browseId": "MPREextra",
                "year": "2024",
                "artists": [{"name": "Artist", "id": "UC123"}],
            },
            "album_browse_id": "MPREextra",
        }
        result = YTMusicSong.from_provider(song_data_no_album, extra_data)
        assert result.album is not None
        assert result.album.name == "Extra Album"

    def test_from_provider_no_album(self, song_data_no_album):
        """Test from_provider handles missing album."""
        result = YTMusicSong.from_provider(song_data_no_album)
        assert result.album is None

    def test_from_provider_creates_artists(self, song_data):
        """Test from_provider creates Artist list correctly."""
        result = YTMusicSong.from_provider(song_data)
        assert len(result.artists) == 1
        assert result.artists[0].name == "Test Artist"

    def test_from_provider_empty_artists(self, song_data):
        """Test from_provider handles empty artists list."""
        song_data["artists"] = []
        result = YTMusicSong.from_provider(song_data)
        assert result.artists is None

    def test_from_provider_missing_fields(self):
        """Test from_provider handles minimal data."""
        minimal_data = {"title": "Minimal Song"}
        result = YTMusicSong.from_provider(minimal_data)
        assert result.name == "Minimal Song"
        assert result.id is None
        assert result.duration is None
        assert result.artists is None


class TestYTMusicPlaylist:
    """Tests for YTMusicPlaylist adapter class."""

    @pytest.fixture
    def playlist_data(self):
        """Sample YTMusic API playlist data."""
        return {
            "title": "Test Playlist",
            "browseId": "VLPLxxxxxxxxxxxxxxxxx",
            "author": "Test Author",
            "description": "A test playlist",
            "tracks": [
                {
                    "title": "Track 1",
                    "videoId": "vid1",
                    "artists": [{"name": "Artist", "id": "UC1"}],
                }
            ],
        }

    @pytest.fixture
    def playlist_data_with_id(self):
        """Sample YTMusic API playlist data with 'id' instead of 'browseId'."""
        return {
            "title": "Test Playlist",
            "id": "PLxxxxxxxxxxxxxxxxx",
            "author": "Test Author",
            "description": "A test playlist",
        }

    def test_from_provider(self, playlist_data):
        """Test from_provider creates Playlist correctly."""
        result = YTMusicPlaylist.from_provider(playlist_data)
        assert isinstance(result, Playlist)
        assert result.name == "Test Playlist"
        assert result.id == "VLPLxxxxxxxxxxxxxxxxx"
        assert result.description == "A test playlist"

    def test_from_provider_with_id_fallback(self, playlist_data_with_id):
        """Test from_provider falls back to 'id' when 'browseId' is missing."""
        result = YTMusicPlaylist.from_provider(playlist_data_with_id)
        assert result.id == "PLxxxxxxxxxxxxxxxxx"

    def test_from_provider_creates_owner(self, playlist_data):
        """Test from_provider creates owner User correctly."""
        result = YTMusicPlaylist.from_provider(playlist_data)
        assert result.owner is not None
        assert result.owner.name == "Test Author"

    def test_from_provider_no_author(self, playlist_data):
        """Test from_provider handles missing author."""
        playlist_data["author"] = None
        result = YTMusicPlaylist.from_provider(playlist_data)
        assert result.owner is None

    def test_from_provider_creates_tracks(self, playlist_data):
        """Test from_provider creates tracks list."""
        result = YTMusicPlaylist.from_provider(playlist_data)
        assert result.tracks is not None
        assert len(result.tracks) == 1
        assert result.tracks[0].name == "Track 1"

    def test_from_provider_no_tracks(self, playlist_data):
        """Test from_provider handles missing tracks."""
        del playlist_data["tracks"]
        result = YTMusicPlaylist.from_provider(playlist_data)
        assert result.tracks is None


class TestYTMusicUser:
    """Tests for YTMusicUser adapter class."""

    @pytest.fixture
    def user_data(self):
        """Sample YTMusic API user data."""
        return {
            "title": "Test User",
            "browseId": "UCxxxxxxxxxxxxxxxxx",
            "name": "@testuser",
        }

    def test_from_provider(self, user_data):
        """Test from_provider creates User correctly."""
        result = YTMusicUser.from_provider(user_data)
        assert isinstance(result, User)
        assert result.name == "Test User"
        assert result.id == "UCxxxxxxxxxxxxxxxxx"
        assert result.handle == "@testuser"

    def test_from_provider_missing_fields(self):
        """Test from_provider handles missing fields."""
        minimal_data = {}
        result = YTMusicUser.from_provider(minimal_data)
        assert result.name is None
        assert result.id is None
        assert result.handle is None
