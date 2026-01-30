---
hide:
  - navigation
search:
  boost: 2
---

# Types

The `downmixer.types` module provides the core data structures used throughout Downmixer. These types standardize how song metadata, search results, and processing state are represented across different music platforms.

## Submodules

| Submodule                                      | Description                                                     |
|------------------------------------------------|-----------------------------------------------------------------|
| [`library`](../reference/types/library/)       | Core music metadata types (Song, Album, Artist, Playlist, User) |
| [`processing`](../reference/types/processing/) | Types for download/conversion workflow state                    |
| [`search`](../reference/types/search/)         | Generic search result wrapper                                   |
| [`exceptions`](../reference/types/exceptions/) | Custom exceptions and warnings                                  |

## LoggerLike Protocol

The module also defines `LoggerLike`, a protocol describing the logging interface used throughout Downmixer. It mirrors Python's standard [`logging.Logger`](https://docs.python.org/3/library/logging.html#logging.Logger) interface:

```python
class LoggerLike(Protocol):
    def debug(self, msg): ...
    def info(self, msg): ...
    def warning(self, msg): ...
    def error(self, msg, exc_info): ...
```

This allows any logger implementation compatible with the standard library to be used, or a completely custom 
implementation; as long as it follows this Protocol. The default Logger used by most modules in the app is 
[`ConsoleLogger`](../../reference/utils/logging/#downmixer.utils.logging.ConsoleLogger).

See the [reference](../reference/types/) for complete API documentation.
