"""Tests for MediaFlow's conversion rules (no FFmpeg binary required)."""
from pathlib import Path
import threading

import pytest

from converter import (
    ConversionCancelled, ConversionError, Job, convert,
    encoding_args, unique_output,
)

def test_mp4_default_h264():
    args = encoding_args("mp4", "Auto", "Balanced", True)
    assert "libx264" in args
    assert "+faststart" in args

def test_webm_uses_vp9_and_opus():
    args = encoding_args("webm", "Auto", "High", True)
    assert "libvpx-vp9" in args
    assert "libopus" in args

def test_audio_mp3():
    args = encoding_args("mp3", "Auto", "Balanced", False)
    assert args[:2] == ["-vn", "-c:a"]
    assert "libmp3lame" in args

@pytest.mark.parametrize("fmt", ["webm", "mp4", "mkv", "mov"])
def test_audio_only_cannot_create_video(fmt):
    with pytest.raises(ConversionError):
        encoding_args(fmt, "Auto", "Balanced", False)

def test_incompatible_codec_rejected():
    with pytest.raises(ConversionError):
        encoding_args("mp4", "VP9", "Balanced", True)

def test_invalid_format_rejected():
    with pytest.raises(ConversionError):
        encoding_args("exe", "Auto", "Balanced", True)

def test_existing_output_gets_unique_name(tmp_path):
    (tmp_path / "clip.mp4").write_bytes(b"existing")
    assert unique_output(tmp_path, "clip", ".mp4") == tmp_path / "clip (1).mp4"

def test_pre_cancelled_job_creates_no_output(tmp_path):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"data")
    cancelled = threading.Event()
    cancelled.set()
    with pytest.raises(ConversionCancelled):
        convert(Job(source, tmp_path, "mp4"), cancel=cancelled)
    assert list(tmp_path.iterdir()) == [source]
