---
hide:
  - navigation
---

# `library.py` file

Every provider implementing the [SupportsLibrary](../../reference/providers/protocols/#downmixer.providers.protocols.SupportsLibrary) or [SupportsMetadata](../../reference/providers/protocols/#downmixer.providers.protocols.SupportsMetadata) protocol should include a `library.py` file containing adapter classes that convert provider API data into Downmixer's internal data models.

## Purpose

Different music services return data in different formats. The `library.py` file bridges this gap by:

1. Defining subclasses of the base library types
2. Overriding the `from_provider` method to parse API-specific data structures
3. Returning instances of the base types (not the subclass)

## Required Classes

The following `BaseLibraryItem` subclasses should be overridden as needed:

| Class                                                                        | Description                                          |
|------------------------------------------------------------------------------|------------------------------------------------------|
| [`Artist`](../reference/types/library.md#downmixer.types.library.Artist)     | Artist metadata (name, images, genres)               |
| [`Album`](../reference/types/library.md#downmixer.types.library.Album)       | Album metadata (name, artists, cover, date)          |
| [`Song`](../reference/types/library.md#downmixer.types.library.Song)         | Song metadata (name, artists, album, duration, ISRC) |
| [`Playlist`](../reference/types/library.md#downmixer.types.library.Playlist) | Playlist metadata (name, tracks, owner)              |
| [`User`](../reference/types/library.md#downmixer.types.library.User)         | User metadata (name, handle)                         |

## Methods to Override

### `from_provider`

The [`from_provider`](../reference/types/library.md#downmixer.types.library.BaseLibraryItem.from_provider) class method is the primary method to override. It receives raw API data and returns an instance of the base library type.

```python
class SpotifyArtist(Artist):
    @classmethod
    def from_provider(cls, data: dict, extra_data: dict = None) -> Artist:
        return Artist(
            name=data["name"],
            images=data.get("images"),
            id=data["uri"],
            url=data["external_urls"]["spotify"],
        )
```

### `from_provider_list`

Override [`from_provider_list`](../reference/types/library.md#downmixer.types.library.BaseLibraryItem.from_provider_list) when the API returns lists in a non-standard format (e.g., wrapped in additional objects):

```python
@classmethod
def from_provider_list(cls, data: list, extra_data: dict = None) -> list[Song]:
    # Handle Spotify's {"track": {...}} wrapper
    return [cls.from_provider(x["track"], extra_data) for x in data]
```

The default implementation simply iterates and calls `from_provider` on each item.

## Example

See the bundled providers for complete implementations:

- [`downmixer.providers.spotify.library`](../reference/providers/spotify/library.md)
- [`downmixer.providers.yt_music.library`](../reference/providers/yt_music/library.md)
- [`downmixer.providers.qobuz.library`](../reference/providers/qobuz/library.md)

See the [types reference](../reference/types/library.md) for complete API documentation of the base classes.
