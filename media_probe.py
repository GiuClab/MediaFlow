"""Read media metadata and a thumbnail using local ffprobe/FFmpeg."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from converter import find_binary, _flags


def probe_preview(path: Path) -> tuple[str, bytes]:
    """Return compact original-media facts and PNG bytes; degrade gracefully."""
    details = ""
    thumbnail = b""
    try:
        command = [find_binary("ffprobe"), "-v", "error", "-show_entries",
                   "format=duration:stream=codec_type,width,height",
                   "-of", "json", str(path)]
        result = subprocess.run(command, capture_output=True, timeout=15,
                                check=False, creationflags=_flags())
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            streams = payload.get("streams", [])
            video = next((stream for stream in streams
                          if stream.get("codec_type") == "video"), {})
            width, height = video.get("width"), video.get("height")
            length = payload.get("format", {}).get("duration")
            bits = []
            if width and height:
                bits.append(f"{width}×{height}")
            if length:
                try:
                    sec = int(float(length))
                    bits.append(f"{sec//3600:02}:{sec//60%60:02}:{sec%60:02}")
                except (ValueError, TypeError, OverflowError):
                    pass
            details = "   ·   ".join(bits)
            if not video:
                return details, b""
            shot = subprocess.run(
                [find_binary("ffmpeg"), "-hide_banner", "-loglevel", "error",
                 "-ss", "1", "-i", str(path), "-frames:v", "1",
                 "-vf", "scale=240:-2", "-f", "image2pipe", "-vcodec", "png", "pipe:1"],
                capture_output=True, timeout=20, check=False, creationflags=_flags())
            if shot.returncode == 0 and len(shot.stdout) <= 5_000_000:
                thumbnail = shot.stdout
    except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return details, thumbnail
