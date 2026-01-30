<style>
    .logo {
        filter: invert(100%);
    }

    @media (prefers-color-scheme: dark) {
        .logo {
            filter: invert(0%);
        }
    }
</style>
<p style="text-align: center">
    <img alt="Downmixer logo" class="logo" src="https://git.gay/neufter/downmixer/raw/branch/pages/assets/logo_white.svg" style="width: 20vw; max-width: 500px"/>
</p>

downmixer is a library to support connecting between streaming services. It can
match _any_ song, from _any_ streaming
service (or any arbitrary library of files), with the _same song_ or as close as
possible when it straight up isn't
available.

It's flexible, and provides a comprehensive API that can be extended for almost
any use case. Making your own **provider
** (the bridge between services and downmixer) is as easy as...

[//]: # (@formatter:off)
```python
import ... from ...


# Every provider needs a separate connection object
class MyProviderConnection(Connection):
    def initialize(self) -> bool:
        # Implement your APIs here
        pass

    # [...]


class MyProvider(BaseProvider):
    def fetch_song(self, id: str) -> Song:
        # Implement your APIs here
        pass

    def fetch_album(self, id: str) -> Album:
        # Implement your APIs here
        pass

    # [...]

    def fetch_audio(self, song: SearchResult | str, path: Path) -> LocalFile:
        # Implement your APIs here
        pass
```
[//]: # (@formatter:on)

Providers inherit from a base class, which has only the basic skeleton of a
downmixer Provider; the actual interface the class will have is determined by
the Protocols it implements.

You can make your classes inherit all the protocols it uses, but duck typing
is recommended and used by the built-in Providers.

With your own providers, you can then automate tasks easily with any other
service:

[//]: # (@formatter.off)

```python
import

...
from ...


async def download_song(song_id: str, output: Path):
    # Initialize Spotify connection (requires OAuth)
    spotify_conn = SpotifyConnection()
    spotify_conn.initialize()
    spotify_conn.authenticate()
    spotify = SpotifyProvider(spotify_conn)

    # Get metadata from Spotify
    song = spotify.fetch_song(song_id)

    # Initialize your custom provider
    custom_conn = MyProviderConnection()
    custom_conn.initialize()
    custom = MyProvider(custom_conn)

    # First search the song on your provider
    results = custom.search(song.title, [ResourceType.SONG])
    # Then download it! 
    local_file = custom.fetch_audio(results[0], output)

    # Convert and tag
    converted = await Converter(local_file).convert()
    tag.tag_download(converted)

    return converted


# You can run it like this:
asyncio.run(download_song("spotify:track:abc123", Path("./downloads")))
```

[//]: # (@formatter.on)

The [documentation](https://neufter.github.io/downmixer) is comprehensive and
has a few guides to get you started.

## Installation

Install the package with:

```shell
pip install downmixer
```

## Building

Uses [uv](https://docs.astral.sh/uv/) package manager. To build from source,
run:

```shell
git clone https://github.com/neufter/downmixer
cd downmixer
uv build
```
