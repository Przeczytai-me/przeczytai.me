"""MP3 merging for same-codec TTS segments.

Byte concatenation avoids buffering and new dependencies, but it can cause playback artifacts or
incorrect duration reporting. If that occurs in production, replace this helper with ffmpeg's
concat demuxer in the processor image.
"""

from pathlib import Path

from mutagen.mp3 import MP3


class AudioMergeError(Exception):
    pass


def mp3_duration_seconds(path: Path) -> float:
    return float(MP3(path).info.length)


def merge_mp3_files(paths: list[Path], output: Path) -> None:
    for index, path in enumerate(paths):
        if not path.is_file() or path.stat().st_size == 0:
            raise AudioMergeError(f"Invalid MP3 part at index {index}")

    with output.open("wb") as merged:
        for path in paths:
            with path.open("rb") as part:
                while chunk := part.read(64 * 1024):
                    merged.write(chunk)
