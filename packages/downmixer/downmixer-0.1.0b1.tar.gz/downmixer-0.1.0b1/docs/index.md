---
hide:
  - navigation
---

# Home


## Getting started

For a complete introduction to using Downmixer, see the [Usage guide](usage.md).

Downmixer is divided into a few modules that cover the basic process of gathering song/playlist information, downloading
individual songs, converting them and tagging them appropriately. These modules are:

- `file_tools` - Converting and tagging audio files
- `matching` - Fuzzy matching between songs from different providers
- `providers` - Provider system with protocol-based architecture (see [providers page](providers/index.md))
- `processing` - Contains `BasicProcessor`, an example implementation for downloading and processing songs/playlists
- `types` - Data type definitions (Song, Album, Artist, Playlist, LocalFile, SearchResult)
- `log` - Logging infrastructure with colored formatters
- `utils` - Utility functions used across the library

Except for `processing`, these packages are designed to be independent and composable - implement them in your application
however best fits your needs. The `processing` module provides `BasicProcessor`, an example implementation showing how to
orchestrate the library's components to build a complete download workflow.

### File Tools

This package uses [FFmpeg](https://ffmpeg.org/) and [Mutagen](https://github.com/quodlibet/mutagen) to convert and tag
downloaded files respectively.

## Commands

Downmixer is a library and cannot be used as a program with a CLI. Please write your own Python scripts to use it.
