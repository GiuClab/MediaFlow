# MediaFlow

Desktop media converter and planned compressor/editor by GiuClab, styled after [VisiLens](https://github.com/GiuClab/VisiLens).

**Development snapshot v0.2.0:** local FFmpeg conversion is implemented in source. Compression and editing are not functional yet. No installer or release has been published.

## Requirements
- Windows 10/11, Python 3.10+, PySide6
- FFmpeg and ffprobe installed separately, both accessible on PATH (or next to the script).
- Appropriate encoders available in your FFmpeg build.

## Run
1. Create and activate a Python virtual environment.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Check FFmpeg: `ffmpeg -version` and `ffprobe -version`
4. Start: `python mediaflow.py`

## Converter
- Batch video/audio conversion to MP4, MKV, MOV, WebM, MP3, FLAC or WAV.
- Automatic codec, H.264, HEVC, AV1 or VP9 where compatible; quality presets.
- Conversion in a Qt worker thread, status/progress display and cancellation.
- Never overwrite the input or an existing output; temporary files are cleaned up after errors or cancellation.
- No uploads; all media processing is local.

Some format/codec combinations are intentionally rejected. Video output requires a video input. FFmpeg builds may lack optional encoders. Hardware acceleration is not implemented. Cancellation may take time if FFmpeg stops emitting progress messages.

## Not yet implemented
- Compression and editing (their interfaces are placeholders).
- Media playback/preview, installer, portable executable or published release.
- Official icon and final license.

## Development tests
Install pytest and run: `python -m pytest -q`. The repository has a Windows GitHub Actions workflow. Unit tests cover validation and filenames, but do not establish that a full conversion has run on Windows.

## Languages
English (default), Italiano, Deutsch, Français.

## Licensing
MediaFlow licensing is undecided; FFmpeg and codec redistribution terms need review before a binary release.

Made with ❤️ by GiuClab

[Support this project](https://ko-fi.com/giuclab/tip)
