"""Unit types for the downmixer.providers.qobuz module."""

import pytest

from downmixer.providers.qobuz import QL_DOWNGRADE, QobuzProvider, RESOURCE_TYPE_MAP
from downmixer.providers.qobuz.library import (
    QobuzAlbum,
    QobuzArtist,
    QobuzPlaylist,
    QobuzSong,
    QobuzUser,
)
from downmixer.types.library import Album, Artist, Playlist, ResourceType, Song, User


class TestConstants:
    """Tests for module constants."""

    def test_resource_type_map_song(self):
        """Test that SONG maps to 'track'."""
        assert RESOURCE_TYPE_MAP[ResourceType.SONG] == "track"

    def test_resource_type_map_album(self):
        """Test that ALBUM maps to 'album'."""
        assert RESOURCE_TYPE_MAP[ResourceType.ALBUM] == "album"

    def test_resource_type_map_playlist(self):
        """Test that PLAYLIST maps to 'playlist'."""
        assert RESOURCE_TYPE_MAP[ResourceType.PLAYLIST] == "playlist"

    def test_resource_type_map_artist(self):
        """Test that ARTIST maps to 'artist'."""
        assert RESOURCE_TYPE_MAP[ResourceType.ARTIST] == "artist"

    def test_ql_downgrade_value(self):
        """Test that QL_DOWNGRADE has expected value."""
        assert QL_DOWNGRADE == "FormatRestrictedByFormatAvailability"


class TestQobuzProviderGetTitle:
    """Tests for QobuzProvider._get_title static method."""

    def test_title_without_version(self):
        """Test _get_title with no version."""
        data = {"title": "Test Album"}
        result = QobuzProvider._get_title(data)
        assert result == "Test Album"

    def test_title_with_version(self):
        """Test _get_title appends version."""
        data = {"title": "Test Album", "version": "Deluxe Edition"}
        result = QobuzProvider._get_title(data)
        assert result == "Test Album (Deluxe Edition)"

    def test_title_with_version_already_in_title(self):
        """Test _get_title doesn't duplicate version in title."""
        data = {"title": "Test Album (Deluxe Edition)", "version": "Deluxe Edition"}
        result = QobuzProvider._get_title(data)
        assert result == "Test Album (Deluxe Edition)"

    def test_title_with_version_case_insensitive(self):
        """Test _get_title version check is case insensitive."""
        data = {"title": "Test Album (DELUXE EDITION)", "version": "deluxe edition"}
        result = QobuzProvider._get_title(data)
        assert result == "Test Album (DELUXE EDITION)"

    def test_title_with_none_version(self):
        """Test _get_title handles None version."""
        data = {"title": "Test Album", "version": None}
        result = QobuzProvider._get_title(data)
        assert result == "Test Album"


class TestQobuzProviderIsQualityMet:
    """Tests for QobuzProvider._is_quality_met method."""

    @pytest.fixture
    def provider(self):
        """Create a QobuzProvider-like object for testing."""

        class MockProvider:
            options = {"quality": 6, "downgrade_quality": False}

            def _is_quality_met(self, song_info) -> bool:
                if int(self.options["quality"]) != 5:
                    restrictions = song_info.get("restrictions")
                    if isinstance(restrictions, list):
                        if any(
                            restriction.get("code") == QL_DOWNGRADE
                            for restriction in restrictions
                        ):
                            return False
                return True

        return MockProvider()

    def test_quality_met_no_restrictions(self, provider):
        """Test _is_quality_met with no restrictions."""
        song_info = {"title": "Test Song"}
        assert provider._is_quality_met(song_info) is True

    def test_quality_met_empty_restrictions(self, provider):
        """Test _is_quality_met with empty restrictions list."""
        song_info = {"restrictions": []}
        assert provider._is_quality_met(song_info) is True

    def test_quality_not_met_with_downgrade_restriction(self, provider):
        """Test _is_quality_met with downgrade restriction."""
        song_info = {"restrictions": [{"code": QL_DOWNGRADE}]}
        assert provider._is_quality_met(song_info) is False

    def test_quality_met_with_other_restrictions(self, provider):
        """Test _is_quality_met with non-downgrade restrictions."""
        song_info = {"restrictions": [{"code": "SomeOtherRestriction"}]}
        assert provider._is_quality_met(song_info) is True

    def test_quality_met_at_quality_5(self, provider):
        """Test _is_quality_met always passes at quality 5 (MP3)."""
        provider.options["quality"] = 5
        song_info = {"restrictions": [{"code": QL_DOWNGRADE}]}
        # At quality 5, restrictions are ignored
        assert provider._is_quality_met(song_info) is True


class TestQobuzArtist:
    """Tests for QobuzArtist adapter class."""

    @pytest.fixture
    def artist_data(self):
        """Sample Qobuz API artist data."""
        return {
            "id": 12345,
            "name": "Test Artist",
        }

    def test_from_provider(self, artist_data):
        """Test from_provider creates Artist correctly."""
        result = QobuzArtist.from_provider(artist_data)
        assert isinstance(result, Artist)
        assert result.name == "Test Artist"
        assert result.id == 12345

    def test_from_provider_missing_fields(self):
        """Test from_provider handles missing fields."""
        data = {}
        result = QobuzArtist.from_provider(data)
        assert result.name is None
        assert result.id is None

    def test_from_provider_list(self, artist_data):
        """Test from_provider_list creates list of Artists."""
        result = QobuzArtist.from_provider_list([artist_data, artist_data])
        assert len(result) == 2
        assert all(isinstance(a, Artist) for a in result)


class TestQobuzAlbum:
    """Tests for QobuzAlbum adapter class."""

    @pytest.fixture
    def album_data(self):
        """Sample Qobuz API album data."""
        return {
            "id": "album123",
            "title": "Test Album",
            "tracks_count": 12,
            "released_at": 1704067200,  # Unix timestamp
            "artist": {"id": 12345, "name": "Test Artist"},
            "upc": "123456789012",
            "image": {"large": "https://example.com/cover.jpg"},
        }

    def test_from_provider(self, album_data):
        """Test from_provider creates Album correctly."""
        result = QobuzAlbum.from_provider(album_data)
        assert isinstance(result, Album)
        assert result.name == "Test Album"
        assert result.id == "album123"
        assert result.track_count == 12
        assert result.upc == "123456789012"
        assert result.cover == "https://example.com/cover.jpg"

    def test_from_provider_creates_artist(self, album_data):
        """Test from_provider creates artist correctly."""
        result = QobuzAlbum.from_provider(album_data)
        assert len(result.artists) == 1
        assert result.artists[0].name == "Test Artist"

    def test_from_provider_list_unwraps_album(self, album_data):
        """Test from_provider_list unwraps album from wrapper."""
        wrapped = [{"album": album_data}]
        result = QobuzAlbum.from_provider_list(wrapped)
        assert len(result) == 1
        assert result[0].name == "Test Album"


class TestQobuzSong:
    """Tests for QobuzSong adapter class."""

    @pytest.fixture
    def song_data(self):
        """Sample Qobuz API track data."""
        return {
            "id": 12345678,
            "title": "Test Song",
            "performer": {"id": 12345, "name": "Test Artist"},
            "album": {
                "id": "album123",
                "title": "Test Album",
                "tracks_count": 12,
                "artist": {"id": 12345, "name": "Test Artist"},
                "image": {"large": "https://example.com/cover.jpg"},
            },
            "duration": 210,
            "track_number": 5,
            "isrc": "USRC12345678",
            "release_date_original": "2024-01-01",
        }

    def test_from_provider(self, song_data):
        """Test from_provider creates Song correctly."""
        result = QobuzSong.from_provider(song_data)
        assert isinstance(result, Song)
        assert result.name == "Test Song"
        assert result.id == 12345678
        assert result.duration == 210
        assert result.track_number == 5
        assert result.isrc == "USRC12345678"
        assert result.date == "2024-01-01"

    def test_from_provider_none_raises_error(self):
        """Test from_provider raises ValueError when data is None."""
        with pytest.raises(ValueError, match="cannot be None"):
            QobuzSong.from_provider(None)

    def test_from_provider_creates_artist_from_performer(self, song_data):
        """Test from_provider uses 'performer' for artist."""
        result = QobuzSong.from_provider(song_data)
        assert len(result.artists) == 1
        assert result.artists[0].name == "Test Artist"

    def test_from_provider_with_album(self, song_data):
        """Test from_provider creates album correctly."""
        result = QobuzSong.from_provider(song_data)
        assert result.album is not None
        assert result.album.name == "Test Album"

    def test_from_provider_without_album(self, song_data):
        """Test from_provider handles missing album."""
        del song_data["album"]
        result = QobuzSong.from_provider(song_data)
        assert result.album is None

    def test_from_provider_with_extra_data_album(self, song_data):
        """Test from_provider uses album from extra_data."""
        album = song_data.pop("album")
        extra_data = {"album": album}
        result = QobuzSong.from_provider(song_data, extra_data=extra_data)
        assert result.album is not None
        assert result.album.name == "Test Album"

    def test_from_provider_list_with_track_wrapper(self, song_data):
        """Test from_provider_list unwraps track from wrapper."""
        wrapped = [{"track": song_data}]
        result = QobuzSong.from_provider_list(wrapped)
        assert len(result) == 1
        assert result[0].name == "Test Song"

    def test_from_provider_list_without_track_wrapper(self, song_data):
        """Test from_provider_list handles direct track data."""
        result = QobuzSong.from_provider_list([song_data])
        assert len(result) == 1
        assert result[0].name == "Test Song"


class TestQobuzPlaylist:
    """Tests for QobuzPlaylist adapter class."""

    @pytest.fixture
    def playlist_data(self):
        """Sample Qobuz API playlist data."""
        return {
            "id": 12345678,
            "name": "Test Playlist",
            "description": "A test playlist",
            "image_rectangle": ["https://example.com/playlist.jpg"],
            "owner": {"id": 98765, "name": "Test Owner"},
        }

    def test_from_provider(self, playlist_data):
        """Test from_provider creates Playlist correctly."""
        result = QobuzPlaylist.from_provider(playlist_data)
        assert isinstance(result, Playlist)
        assert result.name == "Test Playlist"
        assert result.id == 12345678
        assert result.description == "A test playlist"

    def test_from_provider_creates_owner(self, playlist_data):
        """Test from_provider creates owner User correctly."""
        result = QobuzPlaylist.from_provider(playlist_data)
        assert result.owner is not None
        assert result.owner.name == "Test Owner"
        assert result.owner.id == 98765

    def test_from_provider_extracts_image(self, playlist_data):
        """Test from_provider extracts first image from image_rectangle."""
        result = QobuzPlaylist.from_provider(playlist_data)
        assert result.images == "https://example.com/playlist.jpg"

    def test_from_provider_missing_image_rectangle(self, playlist_data):
        """Test from_provider handles missing image_rectangle."""
        # When image_rectangle is missing, it defaults to [None][0] = None
        del playlist_data["image_rectangle"]
        result = QobuzPlaylist.from_provider(playlist_data)
        assert result.images is None


class TestQobuzUser:
    """Tests for QobuzUser adapter class."""

    @pytest.fixture
    def user_data(self):
        """Sample Qobuz API user data."""
        return {
            "id": 12345,
            "name": "Test User",
        }

    def test_from_provider(self, user_data):
        """Test from_provider creates User correctly."""
        result = QobuzUser.from_provider(user_data)
        assert isinstance(result, User)
        assert result.name == "Test User"
        assert result.id == 12345

    def test_from_provider_missing_fields(self):
        """Test from_provider handles missing fields."""
        data = {}
        result = QobuzUser.from_provider(data)
        assert result.name is None
        assert result.id is None
