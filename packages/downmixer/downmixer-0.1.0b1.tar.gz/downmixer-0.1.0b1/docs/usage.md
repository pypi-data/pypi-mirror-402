---
hide:
  - navigation
search:
  boost: 2
---

# Usage

Downmixer is a Python library for downloading and processing music from various streaming platforms. It's designed to be modular and composable - you pick the components you need and combine them into your own workflow.

There is no CLI. Instead, you write Python scripts that use Downmixer's building blocks to create exactly the processing pipeline you need. The [`BasicProcessor`](../reference/processing/) class is provided as a reference implementation, but you're encouraged to build your own.

## Quick Start

If you'd like a simple command-line tool to download Spotify tracks using YTMusic (ala spotDL), you can create a 
simple script like described below. First, download downmixer using `pip`:

```shell
pip install downmixer
```

Note that you will need a [Spotify Developer account](https://developer.spotify.com) and an [app set up](https://developer.spotify.com/documentation/web-api/tutorials/getting-started?h=create#create-an-app) on your Dashboard. Including a .env file is the easiest way to provide that info.

```dotenv linenums="1"
SPOTIPY_CLIENT_ID='<your client ID>'
SPOTIPY_CLIENT_SECRET='<your client secret>'
SPOTIPY_REDIRECT_URI='<a redirect URI set up on your app>'
```

```py linenums="1"
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from downmixer.processing import BasicProcessor
from downmixer.providers.spotify import SpotifyProvider, SpotifyConnection
from downmixer.providers.yt_music import YTMusicProvider, YTMusicBasicConnection

# load Spotify API credentials
load_dotenv()

spotify_conn = SpotifyConnection()
spotify_conn.initialize()  # REMEMBER TO INITIALIZE THE CONNECTION!
spotify_conn.authenticate()  # providers will NOT initialize them automatically.
spotify = SpotifyProvider(spotify_conn)

ytmusic_conn = YTMusicBasicConnection()
ytmusic_conn.initialize()  # YouTube Music connection doesn't need to be authenticated.

processor = BasicProcessor(
    info_provider=SpotifyProvider(spotify_conn),
    audio_provider=YTMusicProvider(ytmusic_conn),
    lyrics_provider=None,  # Downmixer does not have any built-in lyrics providers.
    output_folder=Path("./music"),
    temp_folder=Path("./temp"),
    threads=3,
    max_retries=10,
)

# Process a single song
asyncio.run(processor.process_song("spotify:track:abc123"))

# Process an entire playlist with concurrency
asyncio.run(processor.process_playlist("spotify:playlist:xyz789"))
```

## Core Concepts

### Providers

[Providers](../providers/) communicate with music services and implement capability protocols:

| Protocol                                                                                                         | Description                                          |
|------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| [`SupportsMetadata`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsMetadata)           | Search and fetch song/album/artist/playlist metadata |
| [`SupportsAudioDownload`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsAudioDownload) | Download audio files                                 |
| [`SupportsLibrary`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsLibrary)             | Access user's saved library                          |
| [`SupportsLyrics`](../reference/providers/protocols/#downmixer.providers.protocols.SupportsLyrics)               | Fetch song lyrics                                    |

You can mix providers - for example, use Spotify for metadata (high quality) and YouTube Music for downloads (free).

### Library Types

Standardized data structures in [`downmixer.types.library`](../reference/types/library/):

- `Song`, `Album`, `Artist`, `Playlist`, `User` - music metadata
- `SearchResult` - wraps results with provider info, delegates attribute access
- `LocalFile` - represents a downloaded file with source metadata and match quality

### File Tools

Audio processing utilities in [`downmixer.file_tools`](../reference/file_tools/):

- [`Converter`](../reference/file_tools/convert/) - FFmpeg-based format conversion (MP3, FLAC, WAV, OPUS)
- [`tag_download()`](../reference/file_tools/tag/) - ID3 tagging with cover art and lyrics
- [`make_sane_filename()`](../reference/file_tools/utils/) - sanitize filenames for filesystem compatibility

### Matching

When you download audio, Downmixer automatically calculates how well the downloaded track matches your original request. See the [matching documentation](../matching/) for details on how match quality is scored.

## Processing Workflow

A typical processing pipeline follows these steps:

1. **Fetch metadata** - Use `fetch_song()` or `fetch_playlist()` to get track info
2. **Search for audio** - Call `search()` on an audio provider to find downloadable matches
3. **Download** - Use `fetch_audio()` to download, returns a `LocalFile`
4. **Convert** - Pass to `Converter` for format/bitrate changes
5. **Fetch lyrics** (optional) - Get lyrics with `fetch_lyrics()`
6. **Tag** - Apply metadata with `tag_download()`
7. **Save** - Sanitize filename and move to output folder

Custom pipelines of course can take any shape or form - Downmixer's modularity allows for great flexibility 
in suiting many types of pipelines for different purposes.

For example, a pipeline of a library transferring app (like Soundiiz, TuneMyMusic, etc.) could look like this:

1. **Fetch user library** - Use `fetch_user_playlists()`, `fetch_user_albums()`, or `fetch_user_songs()` from the source provider
2. **Get playlist contents** - Call `fetch_list_songs()` to retrieve all tracks
3. **Search destination** - For each song, use `search()` on the destination provider to find matches
4. **Match validation** - Compare metadata (title, artist, duration) to verify correct matches
5. **Add to library** - Use the destination provider's API to add matched songs to the user's library

[`Connection`](../../reference/providers/connections) objects also allow flexibility in the methods you can provide
for authentication (or non-authentication). On a platform like YouTube Music, you can have a `YTMusicBasicConnection`
that does not require an account, but is limited; _and_ a `YTMusicAuthenticatedConnection` that can make full use of
a YouTube Premium account. 

You can also swap a Provider's Connection object on the fly by using 
[`Base.Provider.change_connection()`](../reference/providers#downmixer.providers.BaseProvider.change_connection), 
and nothing stops you from making _infinite_ provider instances with _dozens_ of different Connections!

## Building Custom Workflows

### Check Protocol Support

Use `issubclass()` to check what a provider class supports:

```python
from downmixer.providers.protocols import SupportsLyrics, SupportsAudioDownload

if issubclass(type(provider), SupportsLyrics):
    lyrics = provider.fetch_lyrics(song)

if issubclass(type(provider), SupportsAudioDownload):
    if provider.is_downloadable(song):
        local_file = provider.fetch_audio(song, temp_folder)
```

### Custom Conversion Settings

Configure the converter for different output formats:

!!! warning
    
    The current implementation of `Converter` is **not** tested with formats besides MP3. This class will
    receive a rewrite soon.

```python
from downmixer.file_tools.convert import Converter
from downmixer.file_tools import Format

converter = Converter(
    local_file,
    output_format=Format.FLAC,
    bitrate="320k",
    delete_original=True,
)
converted = await converter.convert()
```

### Custom ID3 Tags

Add custom metadata when tagging:

```python
from downmixer.file_tools import tag

tag.tag_download(local_file, custom_tags={
    "comment": "Downloaded with Downmixer",
    "genre": "Electronic",
})
```

### Filter by Match Quality

Check match quality before processing:

```python
from downmixer.matching import MatchQuality

if local_file.match.quality in (MatchQuality.PERFECT, MatchQuality.GREAT):
    # High confidence match, proceed with processing
    tag.tag_download(local_file)
else:
    # Low confidence, maybe skip or flag for review
    print(f"Low match quality: {local_file.match.quality}")
```

## Reference

- [Providers](../providers/) - Provider system and bundled implementations
- [Matching](../matching/) - How match quality works
- [Types](../types/) - Data type definitions
- [API Reference](../reference/) - Complete API documentation
