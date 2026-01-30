"""Unit types for the downmixer.types.processing module."""

from pathlib import Path

import pytest

from downmixer.file_tools import AudioCodecs
from downmixer.matching import MatchQuality
from downmixer.types.library import Album, Artist, Song
from downmixer.types.processing import LocalFile


class TestLocalFile:
    """Tests for the LocalFile dataclass."""

    @pytest.fixture
    def source_song(self) -> Song:
        """Create a source song for testing."""
        artist = Artist(name="Test Artist", id="artist1")
        album = Album(name="Test Album", artists=[artist])
        return Song(
            name="Test Song",
            artists=[artist],
            duration=180.0,
            album=album,
            id="source_song",
        )

    @pytest.fixture
    def original_song(self) -> Song:
        """Create an original song for testing (the song we're trying to match)."""
        artist = Artist(name="Test Artist", id="artist1")
        album = Album(name="Test Album", artists=[artist])
        return Song(
            name="Test Song",
            artists=[artist],
            duration=180.0,
            album=album,
            id="original_song",
        )

    @pytest.fixture
    def different_source_song(self) -> Song:
        """Create a different source song for testing lower match scores."""
        artist = Artist(name="Different Artist", id="artist2")
        album = Album(name="Different Album", artists=[artist])
        return Song(
            name="Different Song",
            artists=[artist],
            duration=300.0,
            album=album,
            id="different_song",
        )

    def test_local_file_creation(self, source_song: Song, original_song: Song):
        """Test basic LocalFile creation."""
        local_file = LocalFile(
            source=source_song,
            original=original_song,
            path=Path("/tmp/test.mp3"),
            audio_codec=AudioCodecs.MP4A_40_2,
        )
        assert local_file.source == source_song
        assert local_file.original == original_song
        assert local_file.path == Path("/tmp/test.mp3")
        assert local_file.audio_codec == AudioCodecs.MP4A_40_2

    def test_local_file_optional_fields(self, source_song: Song, original_song: Song):
        """Test LocalFile with optional fields."""
        local_file = LocalFile(
            source=source_song,
            original=original_song,
            path=Path("/tmp/test.flac"),
            audio_codec=AudioCodecs.FLAC,
            size=1024000,
            bitrate=320.0,
        )
        assert local_file.size == 1024000
        assert local_file.bitrate == 320.0

    def test_local_file_post_init_calculates_match(
        self, source_song: Song, original_song: Song
    ):
        """Test that __post_init__ calculates the match result."""
        local_file = LocalFile(
            source=source_song,
            original=original_song,
            path=Path("/tmp/test.mp3"),
            audio_codec=AudioCodecs.MP4A_40_2,
        )
        # Match should be calculated automatically
        assert local_file.match is not None
        assert local_file.match.method == "QRatio"

    def test_local_file_perfect_match(self, source_song: Song, original_song: Song):
        """Test LocalFile with identical source and original."""
        local_file = LocalFile(
            source=source_song,
            original=original_song,
            path=Path("/tmp/test.mp3"),
            audio_codec=AudioCodecs.MP4A_40_2,
        )
        # Same song should have perfect or great match
        assert local_file.match.quality in [MatchQuality.PERFECT, MatchQuality.GREAT]

    def test_local_file_low_match(
        self, different_source_song: Song, original_song: Song
    ):
        """Test LocalFile with different source and original."""
        local_file = LocalFile(
            source=different_source_song,
            original=original_song,
            path=Path("/tmp/test.mp3"),
            audio_codec=AudioCodecs.MP4A_40_2,
        )
        # Different songs should have lower match quality
        assert local_file.match.quality in [MatchQuality.BAD, MatchQuality.MEDIOCRE]

    def test_local_file_different_codecs(self, source_song: Song, original_song: Song):
        """Test LocalFile with different audio codecs."""
        codecs = [
            AudioCodecs.MP4A_40_2,
            AudioCodecs.MP4A_40_5,
            AudioCodecs.OPUS,
            AudioCodecs.FLAC,
        ]
        for codec in codecs:
            local_file = LocalFile(
                source=source_song,
                original=original_song,
                path=Path(f"/tmp/test.{codec.name.lower()}"),
                audio_codec=codec,
            )
            assert local_file.audio_codec == codec

    def test_local_file_path_types(self, source_song: Song, original_song: Song):
        """Test LocalFile accepts different path representations."""
        # Using Path object
        local_file = LocalFile(
            source=source_song,
            original=original_song,
            path=Path("/tmp/music/test.mp3"),
            audio_codec=AudioCodecs.MP4A_40_2,
        )
        assert isinstance(local_file.path, Path)
        assert local_file.path.name == "test.mp3"

    def test_local_file_size_none_default(self, source_song: Song, original_song: Song):
        """Test that size defaults to None."""
        local_file = LocalFile(
            source=source_song,
            original=original_song,
            path=Path("/tmp/test.mp3"),
            audio_codec=AudioCodecs.MP4A_40_2,
        )
        assert local_file.size is None

    def test_local_file_bitrate_none_default(
        self, source_song: Song, original_song: Song
    ):
        """Test that bitrate defaults to None."""
        local_file = LocalFile(
            source=source_song,
            original=original_song,
            path=Path("/tmp/test.mp3"),
            audio_codec=AudioCodecs.MP4A_40_2,
        )
        assert local_file.bitrate is None


class TestAudioCodecs:
    """Tests for the AudioCodecs enum."""

    def test_audio_codecs_exist(self):
        """Test that all expected audio codecs exist."""
        assert AudioCodecs.MP4A_40_5
        assert AudioCodecs.MP4A_40_2
        assert AudioCodecs.OPUS
        assert AudioCodecs.FLAC

    def test_audio_codecs_unique_values(self):
        """Test that all audio codecs have unique values."""
        values = [codec.value for codec in AudioCodecs]
        assert len(values) == len(set(values))
