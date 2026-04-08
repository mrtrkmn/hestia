"""Video and audio transcoding via FFmpeg.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Callable

VIDEO_FORMATS = {"mp4", "mkv", "avi", "webm"}
AUDIO_FORMATS = {"mp3", "flac", "wav", "aac", "ogg"}


class MediaError(Exception):
    def __init__(self, filename: str, reason: str) -> None:
        self.filename = filename
        self.reason = reason
        super().__init__(f"{filename}: {reason}")


def transcode(
    data: bytes,
    filename: str,
    target_format: str,
    bitrate: str | None = None,
    resolution: str | None = None,
    codec: str | None = None,
    progress_callback: Callable[[int], None] | None = None,
) -> bytes:
    """Transcode video or audio to target format."""
    target_format = target_format.lower()
    all_formats = VIDEO_FORMATS | AUDIO_FORMATS
    if target_format not in all_formats:
        raise MediaError(filename, f"Unsupported target format: {target_format}")

    suffix = Path(filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as inp:
        inp.write(data)
        inp_path = inp.name

    out_path = inp_path + f".{target_format}"
    cmd = ["ffmpeg", "-y", "-i", inp_path]

    if codec:
        cmd += ["-c:v" if target_format in VIDEO_FORMATS else "-c:a", codec]
    if bitrate:
        cmd += ["-b:v" if target_format in VIDEO_FORMATS else "-b:a", bitrate]
    if resolution:
        cmd += ["-s", resolution]

    cmd.append(out_path)

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")[:300]
            raise MediaError(filename, f"FFmpeg failed: {stderr}")
        if progress_callback:
            progress_callback(100)
        return Path(out_path).read_bytes()
    except FileNotFoundError:
        raise MediaError(filename, "ffmpeg not installed")
    except subprocess.TimeoutExpired:
        raise MediaError(filename, "Transcoding timed out")
    finally:
        Path(inp_path).unlink(missing_ok=True)
        Path(out_path).unlink(missing_ok=True)
