"""Core type definitions and protocols used throughout Downmixer.

This module provides common types including the `LoggerLike` protocol for logging interfaces.
Submodules contain specific type definitions:

- `library`: Core music metadata types (Song, Album, Artist, Playlist, User)
- `processing`: Types for download/conversion workflow state (LocalFile)
- `search`: Generic search result wrapper (SearchResult)
- `exceptions`: Custom exceptions and warnings
"""

from __future__ import annotations

from typing import Protocol


class LoggerLike(Protocol):
    """Defines the logging interface supported by all modules. Is essentially the same as standard lib's
    [`logging.Logger`](https://docs.python.org/3.14/library/logging.html#logging.Logger).
    """

    def debug(self, msg): ...
    def info(self, msg): ...
    def warning(self, msg): ...
    def error(self, msg, exc_info): ...
