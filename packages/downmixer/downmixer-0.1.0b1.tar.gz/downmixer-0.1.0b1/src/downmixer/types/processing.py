"""Types for representing downloaded and processed audio files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from downmixer.file_tools import AudioCodecs
from downmixer.matching import MatchResult, match
from downmixer.types.library import Song


@dataclass
class LocalFile:
    """Represents a downloaded audio file with metadata about its source and quality.

    This class links a downloaded file to both its source (the song from the download provider)
    and the original song being matched. It automatically calculates the match quality between
    source and original upon initialization.

    Attributes:
        source: The song metadata from the download provider (e.g., YouTube Music).
        original: The original song being matched against (e.g., from Spotify).
        path: Filesystem path to the downloaded audio file.
        audio_codec: The audio codec/format of the file.
        size: File size in bytes.
        bitrate: Audio bitrate in Kbps.
        match: Match result comparing source to original, auto-calculated on init.
    """

    source: Song
    original: Song

    path: Path
    audio_codec: AudioCodecs
    size: Optional[int] = None
    bitrate: Optional[float] = None

    match: MatchResult = None

    def __post_init__(self):
        self.match = match(self.source, self.original)
