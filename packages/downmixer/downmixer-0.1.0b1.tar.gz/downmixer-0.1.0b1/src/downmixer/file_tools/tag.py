from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.request import urlopen

import mutagen
from mutagen.easyid3 import EasyID3

# noinspection PyProtectedMember
from mutagen.id3 import APIC, ID3, USLT

from downmixer.types.processing import LocalFile

logger = logging.getLogger("downmixer").getChild(__name__)

# TODO: rework this module
#   - add support for more file formats (FLAC, ALAC, OGG, WAV, etc.)
#   - change this method to use only Song an Path attributes to reduce code dependency
#   - is using matugen the best option? might be worth looking into ways of abstracting this process more


def tag_download(local_file: LocalFile, custom_tags: dict[str, str] | None = None):
    """Tag the Download with metadata from its `source` attribute, overriding existing metadata.

    Args:
        local_file (Download): Downloaded file to be tagged with song data.
        custom_tags (dict[str, str] | None): Dictionary of custom tags to add to the file.
    """
    logger.info(f"Tagging file {local_file.path}")
    _save_easy_tag(local_file, custom_tags=custom_tags)

    has_cover = (
        local_file.source.album.cover is not None
        and len(local_file.source.album.cover) != 0
    )
    if local_file.source.lyrics or has_cover:
        _save_advanced_tag(local_file, has_cover)


def _save_easy_tag(local_file: LocalFile, custom_tags: dict[str, str] | None = None):
    # Custom tags need to be created before their values are edited
    if custom_tags:
        logger.debug("Adding custom tags")
        for key, value in custom_tags.items():
            if not value or key.lower() in EasyID3.valid_keys:
                continue

            EasyID3.RegisterTXXXKey(key, key.upper())

    easy_id3 = mutagen.File(local_file.path, easy=True)

    logger.debug("Deleting old tag information")
    easy_id3.delete()

    # TODO: change this to allow choosing between tagging with original or result song
    song = local_file.source

    logger.debug(f"Filling with info from attached song '{song.title}'")
    easy_id3["title"] = song.name
    easy_id3["titlesort"] = song.name
    easy_id3["artist"] = song.all_artists
    easy_id3["isrc"] = _return_if_valid(song.isrc)
    easy_id3["album"] = _return_if_valid(song.album.name)
    easy_id3["date"] = _return_if_valid(song.date)
    easy_id3["originaldate"] = _return_if_valid(song.date)
    easy_id3["albumartist"] = _return_if_valid(song.album.artists)
    easy_id3["tracknumber"] = [
        _return_if_valid(song.track_number),
        _return_if_valid(song.album.track_count),
    ]
    # TODO: include all tags possible here, grab them from youtube/spotify if needed
    for key, value in custom_tags.items() if custom_tags else {}:
        if value:
            easy_id3[key] = value

    logger.info("Saving EasyID3 data to file")
    easy_id3.save()


def _save_advanced_tag(local_file: LocalFile, has_cover: bool):
    id3 = ID3(local_file.path)
    if local_file.original.lyrics:
        logger.debug("Adding lyrics")
        id3["USLT::'eng'"] = USLT(
            encoding=3,
            lang="eng",
            desc="Unsynced Lyrics",
            text=local_file.original.lyrics,
        )
    if has_cover:
        url = local_file.original.album.cover
        logger.debug(f"Downloading cover image from URL {url}")

        with urlopen(url) as raw_image:
            id3["APIC"] = APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=raw_image.read(),
            )
    logger.info("Saving ID3 data to file")
    id3.save()


def _return_if_valid(value: Any | None) -> Optional[Any]:
    if value is None:
        return ""
    else:
        return value
