"""Safe, sequential FFmpeg conversion engine for MediaFlow.

Uses only local FFmpeg/ffprobe executables. No shell invocation or uploads.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

AUDIO_FORMATS = {"mp3", "flac", "wav"}
VIDEO_FORMATS = {"mp4", "mkv", "mov", "webm"}
FORMATS = AUDIO_FORMATS | VIDEO_FORMATS
CODECS = {"Auto", "H.264", "H.265 / HEVC", "AV1", "VP9"}
QUALITIES = {"High", "Balanced", "Small file"}

class ConversionError(Exception):
    """A media file could not be converted safely."""

class ConversionCancelled(Exception):
    """A requested conversion was cancelled."""

@dataclass(frozen=True)
class Job:
    source: Path
    destination_dir: Path
    output_format: str
    codec: str = "Auto"
    quality: str = "Balanced"

def find_binary(name: str) -> str:
    """Search bundled tools beside the EXE/script, then PATH."""
    stem = name + (".exe" if os.name == "nt" else "")
    base = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    for path in (base / stem, base / "ffmpeg" / stem):
        if path.is_file():
            return str(path)
    found = shutil.which(name)
    if not found:
        raise ConversionError(f"{name} not found. Install FFmpeg and add its bin folder to PATH.")
    return found

def inspect_media(source: Path, ffprobe: str | None = None) -> tuple[bool, float]:
    binary = ffprobe or find_binary("ffprobe")
    cmd = [binary, "-v", "error", "-show_entries", "stream=codec_type:format=duration",
           "-of", "json", str(source)]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=30, check=False, creationflags=_flags())
        if proc.returncode:
            raise ConversionError(proc.stderr.decode("utf-8", "replace")[-500:] or "ffprobe failed")
        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        if not any(s.get("codec_type") in ("audio", "video") for s in streams):
            raise ConversionError("No supported media streams found")
        video = any(s.get("codec_type") == "video" for s in streams)
        raw_duration = data.get("format", {}).get("duration") or 0
        duration = max(0.0, float(raw_duration))
        return video, duration
    except (OSError, subprocess.TimeoutExpired, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ConversionError(f"Cannot inspect media: {exc}") from exc

def _flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0

def encoding_args(fmt: str, codec: str, quality: str, has_video: bool) -> list[str]:
    fmt = fmt.lower()
    if fmt not in FORMATS:
        raise ConversionError(f"Unsupported output format: {fmt}")
    if codec not in CODECS or quality not in QUALITIES:
        raise ConversionError("Unsupported codec or quality")
    if fmt in VIDEO_FORMATS and not has_video:
        raise ConversionError("An audio-only file cannot be converted to a video format")

    if fmt in AUDIO_FORMATS:
        if fmt == "mp3":
            return ["-vn", "-c:a", "libmp3lame", "-q:a", {"High":"2", "Balanced":"4", "Small file":"6"}[quality]]
        if fmt == "flac":
            return ["-vn", "-c:a", "flac"]
        return ["-vn", "-c:a", "pcm_s16le"]

    supported = {
        "mp4": {"Auto", "H.264", "H.265 / HEVC", "AV1"},
        "mkv": {"Auto", "H.264", "H.265 / HEVC", "AV1", "VP9"},
        "mov": {"Auto", "H.264", "H.265 / HEVC"},
        "webm": {"Auto", "AV1", "VP9"},
    }
    if codec not in supported[fmt]:
        raise ConversionError(f"{codec} cannot be used with {fmt.upper()} in MediaFlow")
    selected = ("VP9" if fmt == "webm" else "H.264") if codec == "Auto" else codec
    implementation = {"H.264":"libx264", "H.265 / HEVC":"libx265",
                      "AV1":"libaom-av1", "VP9":"libvpx-vp9"}[selected]
    crf = {"High":"20", "Balanced":"25", "Small file":"31"}[quality]
    if selected == "H.265 / HEVC":
        crf = {"High":"23", "Balanced":"28", "Small file":"33"}[quality]
    if selected == "AV1":
        crf = {"High":"27", "Balanced":"34", "Small file":"40"}[quality]
    if selected == "VP9":
        crf = {"High":"25", "Balanced":"32", "Small file":"40"}[quality]
    args = ["-c:v", implementation, "-crf", crf]
    if selected in ("VP9", "AV1"):
        args += ["-b:v", "0"]
    if selected == "H.264":
        args += ["-preset", "medium", "-pix_fmt", "yuv420p"]
    elif selected == "H.265 / HEVC":
        args += ["-preset", "medium", "-pix_fmt", "yuv420p"]
    elif selected == "AV1":
        args += ["-cpu-used", "5"]
    else:
        args += ["-deadline", "good", "-cpu-used", "3"]
    if fmt == "webm":
        args += ["-c:a", "libopus", "-b:a", "128k"]
    else:
        args += ["-c:a", "aac", "-b:a", "192k"]
    if fmt == "mp4" or fmt == "mov":
        args += ["-movflags", "+faststart"]
    return args

def unique_output(directory: Path, stem: str, suffix: str) -> Path:
    target = directory / (stem + suffix)
    index = 1
    while target.exists():
        target = directory / f"{stem} ({index}){suffix}"
        index += 1
    return target

def convert(job: Job, progress: Callable[[float], None] | None = None,
            cancel: threading.Event | None = None,
            ffmpeg: str | None = None, ffprobe: str | None = None) -> Path:
    """Convert into a temporary file and publish only after successful completion."""
    source = Path(job.source).resolve()
    directory = Path(job.destination_dir).resolve()
    if not source.is_file():
        raise ConversionError(f"Input file missing: {source.name}")
    if not directory.is_dir():
        raise ConversionError(f"Output directory does not exist: {directory}")
    if cancel and cancel.is_set():
        raise ConversionCancelled()
    binary = ffmpeg or find_binary("ffmpeg")
    has_video, duration = inspect_media(source, ffprobe)
    fmt = job.output_format.lower()
    options = encoding_args(fmt, job.codec, job.quality, has_video)
    # Never overwrite an existing file, including a file with the input's name.
    stem = source.stem
    if source.parent == directory and source.suffix.lower() == "." + fmt:
        stem += "_converted"
    desired = unique_output(directory, stem, "." + fmt)
    temporary = directory / f".mediaflow-{uuid.uuid4().hex}.{fmt}"
    cmd = [binary, "-hide_banner", "-nostdin", "-nostats", "-v", "error",
           "-progress", "pipe:1", "-y", "-i", str(source)]
    if fmt in AUDIO_FORMATS:
        cmd += ["-map", "0:a:0"]
    else:
        cmd += ["-map", "0:v:0", "-map", "0:a:0?"]
    cmd += options + [str(temporary)]
    proc: subprocess.Popen | None = None
    try:
        with tempfile.TemporaryFile(mode="w+b") as errors:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=errors,
                                    creationflags=_flags())
            if proc.stdout is None:
                raise ConversionError("Cannot read FFmpeg progress")
            for raw in proc.stdout:
                if cancel and cancel.is_set():
                    proc.kill()
                    proc.wait()
                    raise ConversionCancelled()
                line = raw.decode("utf-8", "replace").strip()
                if duration and progress and line.startswith("out_time="):
                    stamp = line.split("=", 1)[1]
                    match = re.fullmatch(r"(\d+):(\d+):(\d+(?:\.\d+)?)", stamp)
                    if match:
                        seconds = int(match[1])*3600 + int(match[2])*60 + float(match[3])
                        progress(min(99.0, 100.0*seconds/duration))
            returncode = proc.wait()
            if cancel and cancel.is_set():
                raise ConversionCancelled()
            if returncode:
                errors.seek(0)
                detail = errors.read().decode("utf-8", "replace")[-1500:]
                raise ConversionError(f"FFmpeg failed ({returncode}): {detail or 'unknown error'}")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise ConversionError("FFmpeg produced no output")
        # Hard-link publication is atomic and fails rather than overwriting an existing file.
        for _ in range(1000):
            try:
                os.link(temporary, desired)
                break
            except FileExistsError:
                desired = unique_output(directory, stem, "." + fmt)
        else:
            raise ConversionError("Too many output files with the same name")
        if progress:
            progress(100.0)
        return desired
    except OSError as exc:
        raise ConversionError(f"Unable to run FFmpeg or save output: {exc}") from exc
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait()
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
