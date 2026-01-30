# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0b]

> ## ⚠️ Major Architecture Change
> This release introduces a Protocol-based provider system, replacing the
> previous inheritance-based design. Providers now implement capability
> Protocols (`SupportsMetadata`, `SupportsAudioDownload`, `SupportsLibrary`,
`SupportsLyrics`) instead of inheriting from type-specific base classes (
`BaseAudioProvider`, `BaseInfoProvider`, `BaseLyricsProvider`).
>
> Read the [documentation](https://neufter.pages.gay/downmixer) for more
> details.

### Added

- YouTube Music provider with full metadata, library, and audio download support
- Protocol-based capability system: `SupportsMetadata`, `SupportsAudioDownload`,
  `SupportsLibrary`, `SupportsLyrics`
- Connection classes (`Connection`, `AuthenticatedConnection`) for managing
  service connectivity
- `ProviderInformation` class for provider introspection
- `get_connections()` class method on providers
- `get_supported_protocols()` method with filtering support
- `ResourceType.UNKNOWN` for ambiguous resource types
- `source` parameter to `SearchResult` for matching reference
- `falloff` parameter to ease function in matching module
- New exceptions: `NotInitializedError`, `UnsupportedException`,
  `NotAuthenticatedException`
- `IncompleteSupportWarning` for partial feature support
- Comprehensive documentation: matching guide, usage page, provider architecture

### Changed

- **Breaking:** Providers now use Protocols instead of inheritance (
  `BaseAudioProvider` → `SupportsAudioDownload`, etc.)
- **Breaking:** Single generic `SearchResult[T]` replaces `AudioSearchResult`,
  `InfoSearchResult`, `LyricsSearchResult`, `InfoSearchResultList`
- **Breaking:** `LocalFile` replaces `Download` class (no longer inherits from
  search results)
- **Breaking:** Provider methods renamed: `get_song()` → `fetch_song()`,
  `download()` → `fetch_audio()`, `get_all_*()` → `fetch_*()`, etc.
- **Breaking:** Provider initialization now requires a `Connection` object
- **Breaking:** `initialized` and `authenticated` properties replaced by `ready`
- **Breaking:** Removed all async functions from providers (now synchronous)
- **Breaking:** Required Python version is now 3.10+
- Moved all exceptions to `types/exceptions` module
- `SearchResult` now delegates attributes transparently to wrapped items
- Replaced `LoggerWrapper` with `ConsoleLogger` as default logger
- Switched CI to `uv` package manager
- Modernized type hints (`Union` → `|` syntax)
- Qobuz provider fully reimplemented with new architecture

### Removed

- CLI module
- `BaseAudioProvider`, `BaseInfoProvider`, `BaseLyricsProvider` base classes
- `AudioSearchResult`, `InfoSearchResult`, `LyricsSearchResult`,
  `InfoSearchResultList` classes
- `Download` class (replaced by `LocalFile`)
- `providers/audio/` and `providers/lyrics/` directory structure
- AZLyrics provider
- Old `youtube_music` submodule from `providers/audio`

### Fixed

- `list_protocols()` returning extra classes
- Wrong type annotation on Qobuz `login()`
- Incorrect album ID handling in Qobuz
- `require_authentication` wrapper checking incorrect variables
- Search result parsing in Spotify and YouTube Music
- `from_provider_list` not passing `extra_data`

## [0.0.1a] - 2024-05-05

### Added

- Added basic provider structure and default providers
- Added documentation
- Processing module to be able to search, download and convert songs and
  playlists from Spotify