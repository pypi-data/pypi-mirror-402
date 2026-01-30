"""Classes and methods to easily compare the compatibility of a result with a song being matched. Uses fuzzy string
comparison with the [RapidFuzz package](https://github.com/maxbachmann/RapidFuzz).

Matching is done individually on song name, title, primary artist, other artists, album name, and length - artist matches are
calculated down to a single score value (scores go from 0 to 100). Therefore, the sum can be a range of 0 to 500.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from rapidfuzz import fuzz

import downmixer.matching.utils
from downmixer.types.library import Artist, Song


class MatchQuality(Enum):
    """Thresholds to consider when getting the quality of a match. Values are based on the sum of all matches - if
    all are perfect, equals to 500."""

    PERFECT = 500
    """Both songs are exactly the same."""
    GREAT = 475
    """Extremely likely songs are the same. Different platforms usually have small discrepancies in the matching value."""
    GOOD = 400
    """Likely a different version of the same song, like a live version for example."""
    MEDIOCRE = 300
    """Probably a cover from another artist or something else from the same artist."""
    BAD = 0
    """Not the same song."""


@dataclass
class MatchResult:
    """Holds match results and provides convenient property methods to get/calculate quality and match score.

    Attributes:
        method: Comparison method used, such as `QRatio` from RapidFuzz.
        name_match: Score for similarity in the song's names.
        title_match: Score for similarity in the song's titles, taken from the `Song.title` property.
        artists_match: Score for similarity in the original song's artists, compared against the result song's.
        result_artists_matches: Score for similarity in the result song's artists, compared against the original song's.
        album_match: Score for similarity in the song's albums.
        length_match: Score for similarity in the song's lengths. Score is scaled according to the equation $y=1-(f*x^2)$, where $f$ is an arbitrary "falloff" value.
    """

    method: str
    name_match: float
    title_match: float
    artists_match: list[Tuple[Artist, float]]
    result_artists_matches: list[Tuple[Artist, float]]
    album_match: float
    length_match: float

    @property
    def quality(self) -> MatchQuality:
        """Returns the match quality from the enum `MatchQuality` based on the sum of points."""
        result = MatchQuality.PERFECT
        previous = MatchQuality.PERFECT
        for q in MatchQuality:
            if q.value <= self.sum < previous.value:
                result = q
            previous = q

        return result

    @property
    def artists_match_avg(self) -> float:
        """Averages the match score of the list of artists. Returns zero if list is empty."""
        match_values = [x[1] for x in self.artists_match]
        result_match_values = [x[1] for x in self.result_artists_matches]
        if len(match_values) == 0 and len(result_match_values) == 0:
            return 0.0
        else:
            return (sum(match_values) + sum(result_match_values)) / (
                len(self.artists_match) + len(self.result_artists_matches)
            )

    @property
    def sum(self) -> float:
        """Sums all matches (uses average artist match value). Maximum value is 400."""
        return (
            self.name_match
            + self.title_match
            + self.artists_match_avg
            + self.album_match
            + self.length_match
        )

    def all_above_threshold(self, threshold: float) -> bool:
        """Checks if all the scores are above the threshold value given.

        Args:
            threshold (float): Tha value that will be compared to all the values.

        Returns:
            True if every match score is higher than the threshold, false otherwise.
        """
        name_test = self.name_match >= threshold
        artists_test = self.artists_match_avg >= threshold
        album_test = self.album_match >= threshold
        length_test = self.length_match >= threshold

        return name_test and artists_test and album_test and length_test


def match(original_song: Song, result_song: Song) -> MatchResult:
    """Returns match values using RapidFuzz comparing the two given song objects.

    Args:
        original_song (Song): Song to be compared to. Should be slugified for better results.
        result_song (Song): Song being compared. Should be slugified for better results.

    Returns:
        MatchResult: Match scores of the comparison between original and result song.
    """
    song_slug = original_song.slug()
    result_slug = result_song.slug()

    name_match = _match_simple(song_slug.name, result_slug.name)
    title_match = _match_simple(song_slug.title, result_slug.title)
    artists_matches, result_artists_matches = _match_artist_list(song_slug, result_slug)
    if result_slug.album is not None:
        album_match = _match_simple(song_slug.album.name, result_slug.album.name)
    else:
        album_match = 50.0
    length_match = _match_length(original_song.duration, result_song.duration)

    return MatchResult(
        method="QRatio",
        name_match=name_match,
        title_match=title_match,
        artists_match=artists_matches,
        result_artists_matches=result_artists_matches,
        album_match=album_match,
        length_match=length_match,
    )


def _match_simple(str1: str | None, str2: str | None) -> float:
    """Calculates match score for two strings. The second string can be None and will be treated as empty if such."""
    if str1 is None and str2 is None:
        raise ValueError("Both strings cannot be None")

    try:
        result = fuzz.QRatio(
            str1 if str1 is not None else "", str2 if str2 is not None else ""
        )
        match_value = result
    except ValueError:
        match_value = 0.0
    return match_value


def _match_artist_list(
    song: Song, result: Song
) -> Tuple[list[Tuple[Artist, float]], list[Tuple[Artist, float]]]:
    """Uses _match_simple to calculate match score of all the artists from a song."""
    artist_matches = []
    for artist in song.artists:
        highest_ratio: Tuple[Optional[Artist], float] = (None, -1.0)
        for result_artist in result.artists:
            ratio = _match_simple(artist.name, result_artist.name)
            if ratio > highest_ratio[1]:
                highest_ratio = (artist, ratio)

        if highest_ratio[0] is not None:
            artist_matches.append(highest_ratio)

    result_artist_matches = []
    for result_artist in result.artists:
        highest_ratio: Tuple[Optional[Artist], float] = (None, -1.0)
        for artist in song.artists:
            ratio = _match_simple(artist.name, result_artist.name)
            if ratio > highest_ratio[1]:
                highest_ratio = (result_artist, ratio)

        if highest_ratio[0] is not None:
            result_artist_matches.append(highest_ratio)

    return artist_matches, result_artist_matches


def _match_length(len1: float, len2: float, ceiling: int = 120):
    """Calculates the difference between `len1` and `len2` using an equation and
    returns the y value of this graph. The `ceiling` parameter defines the scale of the x-axis.

    See the [`utils.ease`](./utils/#downmixer.matching.utils.ease)
    """
    x = downmixer.matching.utils.remap(abs(len1 - len2), 0, ceiling, 0, 1)
    y = downmixer.matching.utils.ease(x) * 100
    return max(min(100, round(y)), 0)
