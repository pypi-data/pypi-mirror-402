---
hide:
  - navigation
search:
  boost: 2
---

# Providers

Since Downmixer is made to be as platform-agnostic as possible, it works with a **provider** system. Providers
communicate with various music services and implement one or more capability protocols to indicate what features
they support.

## Architecture

Providers are built on two main concepts:

### Connections

Connections handle the lifecycle of connecting to a music service, including initialization and authentication. They
also include the client, which is usually a third-party library that directly talks to the service's API (like `spotipy`
for Spotify, `ytmusicapi` for YouTubeMusic, etc.).
There are two base connection types:

- [`Connection`](../reference/providers/connections/#downmixer.providers.connections.Connection): Base class for services that don't require user authentication
- [`AuthenticatedConnection`](../reference/providers/connections/#downmixer.providers.connections.AuthenticatedConnection): Extended class for services requiring user login

Connections are passed to providers when they're instantiated:

```py 
provider = YourProvider(connection=YourConnection)
```

But they can also be changed at any point in their lifetime using 
[`Base.Provider.change_connection()`](../reference/providers#downmixer.providers.BaseProvider.change_connection). 
Beware of implementation details with clients, they might not like having their tokens and whatnot suddenly changing.

### Protocols

Protocols define the capabilities a provider can offer. A provider can implement multiple protocols:

| Protocol                                                                                                         | Description                                                                |
|------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`SupportsMetadata`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsMetadata)           | Search and fetch metadata for songs, albums, artists, playlists, and users |
| [`SupportsAudioDownload`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsAudioDownload) | Download audio files for songs                                             |
| [`SupportsLibrary`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsLibrary)             | Access user's saved library (playlists, albums, songs, artists)            |
| [`SupportsLyrics`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsLyrics)               | Fetch song lyrics                                                          |

## Bundled Providers

### Spotify

**Module:** [`downmixer.providers.spotify`](../reference/providers/spotify/)

:   **Implements**: `SupportsMetadata`, `SupportsLibrary`
    
    The Spotify provider uses the [spotipy](https://spotipy.readthedocs.io/) library to interact with the Spotify API.
    Supports searching, fetching metadata, and accessing user libraries. Requires OAuth authentication.

### YouTube Music

**Module:** [`downmixer.providers.yt_music`](../reference/providers/yt_music/)

:   **Implements**: `SupportsMetadata`, `SupportsLibrary`, `SupportsAudioDownload`
    
:   The YouTube Music provider uses [ytmusicapi](https://ytmusicapi.readthedocs.io/) for metadata and
    [yt-dlp](https://github.com/yt-dlp/yt-dlp) for audio downloads. Can operate without authentication for
    basic functionality.

### Qobuz

**Module:** [`downmixer.providers.qobuz`](../reference/providers/qobuz/)

:   **Implements**: `SupportsMetadata`, `SupportsAudioDownload`
    
    The Qobuz provider offers high-quality audio downloads (up to 24-bit/192kHz FLAC). Requires a paid
    Qobuz subscription for audio downloads.

## Creating Custom Providers

Providers must be packages with:

1. A class derived from [`BaseProvider`](../reference/providers/#downmixer.providers.BaseProvider) in their `__init__.py`
2. A `get_provider()` function returning the provider class
3. A [`library.py` file](library.py%20file.md) with adapter classes for converting API data to internal models
4. One or more [`Connection`](../reference/providers/connections/#downmixer.providers.connections.Connection) subclasses for service connectivity

See the [reference](../reference/providers/index.md) for complete API documentation.
