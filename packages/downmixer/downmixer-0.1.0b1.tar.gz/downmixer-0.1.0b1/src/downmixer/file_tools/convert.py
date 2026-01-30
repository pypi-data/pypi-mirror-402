import copy
import logging
import os
from pathlib import Path

from ffmpeg.asyncio import FFmpeg

from downmixer.file_tools import Format
from downmixer.types.processing import LocalFile

logger = logging.getLogger("downmixer").getChild(__name__)


class Converter:
    """A convenience class to convert a local file to another format using ffmpeg."""

    def __init__(
        self, local_file: LocalFile, format: Format = Format.MP3, bitrate: str = "256k"
    ):
        """Holds information for FFmpeg to convert a download. By default, uses MP3 output format and 320kbps bitrate.

        Args:
            local_file (Download): Download object to be converted.
            format (Format): Output format from the Format enum.
            bitrate (str): Bitrate in kbps as a string denoting value with a 'k' in the end. Passed directly into FFmpeg.
        """
        # TODO: reconsider converter function in Downmixer
        # TODO: move local_file param to convert() func
        self.local_file = local_file
        self.format = format
        self.bitrate = bitrate

    async def convert(self, delete_original: bool = True) -> LocalFile:
        logger.info("Starting conversion")

        # TODO: Check if file already exists
        output = str(self.local_file.path).replace(
            self.local_file.path.suffix, "." + self.format.value
        )
        ffmpeg = (
            FFmpeg()
            .option("vn")
            .option("y")
            .input(str(self.local_file.path))
            .output(output, {"b:a": self.bitrate})
        )

        @ffmpeg.on("start")
        def on_start(arguments):
            logger.debug("Arguments: " + ", ".join(arguments))

        @ffmpeg.on("stderr")
        def on_stderr(line):
            logger.debug(line)

        @ffmpeg.on("progress")
        def on_progress(progress):
            logger.info(progress)

        @ffmpeg.on("terminated")
        def on_terminated():
            logger.critical("ffmpeg was terminated!")

        @ffmpeg.on("error")
        def on_error(code):
            logger.error(f"ffmpeg error code {code}")

        logger.info("Running ffmpeg")
        await ffmpeg.execute()
        if delete_original:
            os.remove(self.local_file.path)

        logger.debug("Creating copy of download object")
        edited_download = copy.copy(self.local_file)
        edited_download.path = Path(output)
        return edited_download
