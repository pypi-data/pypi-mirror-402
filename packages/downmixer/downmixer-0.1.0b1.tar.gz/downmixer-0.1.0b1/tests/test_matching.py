"""Unit types for the downmixer.matching module."""

import pytest

from downmixer.matching import (
    MatchQuality,
    MatchResult,
    _match_artist_list,
    _match_length,
    _match_simple,
    match,
)
from downmixer.matching.utils import ease, remap
from downmixer.types.library import Album, Artist, Song


class TestMatchQuality:
    """Tests for MatchQuality enum values."""

    def test_quality_values(self):
        """Test that MatchQuality enum has expected values."""
        assert MatchQuality.PERFECT.value == 500
        assert MatchQuality.GREAT.value == 475
        assert MatchQuality.GOOD.value == 400
        assert MatchQuality.MEDIOCRE.value == 300
        assert MatchQuality.BAD.value == 0


class TestMatchResult:
    """Tests for the MatchResult dataclass."""

    @pytest.fixture
    def perfect_match_result(self, sample_artist: Artist) -> MatchResult:
        """Create a perfect match result."""
        return MatchResult(
            method="QRatio",
            name_match=100.0,
            title_match=100.0,
            artists_match=[(sample_artist, 100.0)],
            result_artists_matches=[(sample_artist, 100.0)],
            album_match=100.0,
            length_match=100.0,
        )

    @pytest.fixture
    def mediocre_match_result(self, sample_artist: Artist) -> MatchResult:
        """Create a mediocre match result."""
        return MatchResult(
            method="QRatio",
            name_match=60.0,
            title_match=60.0,
            artists_match=[(sample_artist, 60.0)],
            result_artists_matches=[(sample_artist, 60.0)],
            album_match=60.0,
            length_match=60.0,
        )

    @pytest.fixture
    def bad_match_result(self, sample_artist: Artist) -> MatchResult:
        """Create a bad match result."""
        return MatchResult(
            method="QRatio",
            name_match=20.0,
            title_match=20.0,
            artists_match=[(sample_artist, 20.0)],
            result_artists_matches=[(sample_artist, 20.0)],
            album_match=20.0,
            length_match=20.0,
        )

    def test_sum_calculation(self, perfect_match_result: MatchResult):
        """Test that sum correctly adds all match scores."""
        assert perfect_match_result.sum == 500.0

    def test_sum_with_mediocre_values(self, mediocre_match_result: MatchResult):
        """Test sum with mediocre match values."""
        # 60 + 60 + 60 (artist avg) + 60 + 60 = 300
        assert mediocre_match_result.sum == 300.0

    def test_artists_match_avg_calculation(self, sample_artist: Artist):
        """Test average calculation for artist matches."""
        result = MatchResult(
            method="QRatio",
            name_match=100.0,
            title_match=100.0,
            artists_match=[(sample_artist, 80.0), (sample_artist, 100.0)],
            result_artists_matches=[(sample_artist, 90.0)],
            album_match=100.0,
            length_match=100.0,
        )
        # (80 + 100 + 90) / 3 = 90.0
        assert result.artists_match_avg == 90.0

    def test_artists_match_avg_empty_lists(self):
        """Test that empty artist lists return 0.0 average."""
        result = MatchResult(
            method="QRatio",
            name_match=100.0,
            title_match=100.0,
            artists_match=[],
            result_artists_matches=[],
            album_match=100.0,
            length_match=100.0,
        )
        assert result.artists_match_avg == 0.0

    def test_quality_perfect(self, perfect_match_result: MatchResult):
        """Test that a perfect sum returns PERFECT quality."""
        assert perfect_match_result.quality == MatchQuality.PERFECT

    def test_quality_great(self, sample_artist: Artist):
        """Test that a high sum returns GREAT quality."""
        result = MatchResult(
            method="QRatio",
            name_match=98.0,
            title_match=98.0,
            artists_match=[(sample_artist, 98.0)],
            result_artists_matches=[(sample_artist, 98.0)],
            album_match=98.0,
            length_match=98.0,
        )
        # Sum = 490, which is >= 475 but < 500
        assert result.quality == MatchQuality.GREAT

    def test_quality_good(self, sample_artist: Artist):
        """Test that a good sum returns GOOD quality."""
        result = MatchResult(
            method="QRatio",
            name_match=85.0,
            title_match=85.0,
            artists_match=[(sample_artist, 85.0)],
            result_artists_matches=[(sample_artist, 85.0)],
            album_match=85.0,
            length_match=85.0,
        )
        # Sum = 425, which is >= 400 but < 475
        assert result.quality == MatchQuality.GOOD

    def test_quality_mediocre(self, mediocre_match_result: MatchResult):
        """Test that a mediocre sum returns MEDIOCRE quality."""
        # Sum = 300, which is >= 300 but < 400
        assert mediocre_match_result.quality == MatchQuality.MEDIOCRE

    def test_quality_bad(self, bad_match_result: MatchResult):
        """Test that a low sum returns BAD quality."""
        # Sum = 100, which is < 300
        assert bad_match_result.quality == MatchQuality.BAD

    def test_all_above_threshold_true(self, perfect_match_result: MatchResult):
        """Test all_above_threshold returns True when all scores are above threshold."""
        assert perfect_match_result.all_above_threshold(90.0) is True

    def test_all_above_threshold_false(self, mediocre_match_result: MatchResult):
        """Test all_above_threshold returns False when some scores are below threshold."""
        assert mediocre_match_result.all_above_threshold(70.0) is False


class TestMatchSimple:
    """Tests for _match_simple function."""

    def test_identical_strings(self):
        """Test matching identical strings returns 100."""
        result = _match_simple("test", "test")
        assert result == 100.0

    def test_similar_strings(self):
        """Test matching similar strings returns high score."""
        result = _match_simple("testing", "test")
        assert result > 50.0

    def test_different_strings(self):
        """Test matching different strings returns low score."""
        result = _match_simple("apple", "orange")
        assert result < 50.0

    def test_empty_string(self):
        """Test matching with empty string."""
        result = _match_simple("test", "")
        assert result == 0.0

    def test_both_none_raises_error(self):
        """Test that both strings being None raises ValueError."""
        with pytest.raises(ValueError, match="Both strings cannot be None"):
            _match_simple(None, None)

    def test_first_none(self):
        """Test matching with first string as None."""
        result = _match_simple(None, "test")
        assert result == 0.0

    def test_second_none(self):
        """Test matching with second string as None."""
        result = _match_simple("test", None)
        assert result == 0.0

    def test_case_sensitivity(self):
        """Test that QRatio considers case differences."""
        result = _match_simple("Test", "test")
        # QRatio considers case differences, so not a perfect match
        assert result > 50.0  # Still a good match despite case difference


class TestMatchArtistList:
    """Tests for _match_artist_list function."""

    def test_identical_artists(self, sample_song: Song):
        """Test matching identical artist lists."""
        song_slug = sample_song.slug()
        artist_matches, result_matches = _match_artist_list(song_slug, song_slug)

        assert len(artist_matches) > 0
        assert artist_matches[0][1] == 100.0

    def test_different_artists(self, sample_song: Song, different_song: Song):
        """Test matching completely different artist lists."""
        song_slug = sample_song.slug()
        different_slug = different_song.slug()
        artist_matches, result_matches = _match_artist_list(song_slug, different_slug)

        # Should find matches but with lower scores
        for _, score in artist_matches:
            assert score < 100.0

    def test_multiple_artists(self, sample_song_multiple_artists: Song):
        """Test matching songs with multiple artists."""
        song_slug = sample_song_multiple_artists.slug()
        artist_matches, result_matches = _match_artist_list(song_slug, song_slug)

        assert len(artist_matches) == 2
        for _, score in artist_matches:
            assert score == 100.0


class TestMatchLength:
    """Tests for _match_length function."""

    def test_identical_lengths(self):
        """Test matching identical lengths returns 100."""
        result = _match_length(180.0, 180.0)
        assert result == 100

    def test_similar_lengths(self):
        """Test matching similar lengths returns high score."""
        result = _match_length(180.0, 182.0)
        assert result > 90

    def test_different_lengths(self):
        """Test matching very different lengths returns low score."""
        result = _match_length(180.0, 300.0)
        assert result < 50

    def test_zero_length(self):
        """Test matching with zero length."""
        result = _match_length(0.0, 0.0)
        assert result == 100

    def test_custom_ceiling(self):
        """Test matching with custom ceiling value."""
        # With larger ceiling, differences matter less
        result_default = _match_length(180.0, 200.0, ceiling=120)
        result_large = _match_length(180.0, 200.0, ceiling=240)
        assert result_large > result_default

    def test_result_clamped_to_0_100(self):
        """Test that result is always between 0 and 100."""
        result = _match_length(0.0, 1000.0)
        assert 0 <= result <= 100


class TestMatch:
    """Tests for the main match function."""

    def test_perfect_match(self, sample_song: Song):
        """Test matching a song with itself returns perfect scores."""
        result = match(sample_song, sample_song)

        assert result.method == "QRatio"
        assert result.quality == MatchQuality.PERFECT

    def test_similar_songs_match(self, sample_song: Song, similar_song: Song):
        """Test matching similar songs returns high scores."""
        result = match(sample_song, similar_song)

        assert result.quality in [MatchQuality.PERFECT, MatchQuality.GREAT]

    def test_different_songs_match(self, sample_song: Song, different_song: Song):
        """Test matching different songs returns low scores."""
        result = match(sample_song, different_song)

        assert result.quality in [MatchQuality.BAD, MatchQuality.MEDIOCRE]

    def test_match_without_album(self, sample_artist: Artist):
        """Test matching when result song has no album."""
        song1 = Song(
            name="Test Song",
            artists=[sample_artist],
            duration=180.0,
            album=Album(name="Test Album", artists=[sample_artist]),
        )
        song2 = Song(
            name="Test Song",
            artists=[sample_artist],
            duration=180.0,
            album=None,
        )
        result = match(song1, song2)

        # When album is None, album_match defaults to 50.0
        assert result.album_match == 50.0


class TestRemap:
    """Tests for the remap utility function."""

    def test_basic_remap(self):
        """Test basic remapping from one range to another."""
        result = remap(5.0, 0.0, 10.0, 0.0, 100.0)
        assert result == 50.0

    def test_remap_edge_min(self):
        """Test remapping at minimum edge."""
        result = remap(0.0, 0.0, 10.0, 0.0, 100.0)
        assert result == 0.0

    def test_remap_edge_max(self):
        """Test remapping at maximum edge."""
        result = remap(10.0, 0.0, 10.0, 0.0, 100.0)
        assert result == 100.0

    def test_remap_negative_range(self):
        """Test remapping with negative values."""
        result = remap(-5.0, -10.0, 0.0, 0.0, 100.0)
        assert result == 50.0

    def test_remap_reversed_input_range(self):
        """Test remapping with reversed input range."""
        result = remap(5.0, 10.0, 0.0, 0.0, 100.0)
        assert result == 50.0

    def test_remap_reversed_output_range(self):
        """Test remapping with reversed output range."""
        result = remap(5.0, 0.0, 10.0, 100.0, 0.0)
        assert result == 50.0

    def test_remap_both_reversed(self):
        """Test remapping with both ranges reversed."""
        result = remap(5.0, 10.0, 0.0, 100.0, 0.0)
        assert result == 50.0


class TestEase:
    """Tests for the ease utility function."""

    def test_ease_at_zero(self):
        """Test ease function at x=0."""
        result = ease(0.0)
        assert result == 1.0

    def test_ease_at_one(self):
        """Test ease function at x=1."""
        result = ease(1.0)
        # 1 - (4.8 * 1 * 1) = -3.8
        assert result == -3.8

    def test_ease_at_half(self):
        """Test ease function at x=0.5."""
        result = ease(0.5)
        # 1 - (4.8 * 0.25) = 1 - 1.2 = -0.2
        assert result == pytest.approx(-0.2)

    def test_ease_decreases_monotonically(self):
        """Test that ease function decreases as x increases."""
        values = [ease(x / 10) for x in range(11)]
        for i in range(len(values) - 1):
            assert values[i] > values[i + 1]
