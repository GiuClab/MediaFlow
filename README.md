# MediaFlow

Desktop media converter and planned compressor/editor by GiuClab, styled after [VisiLens](https://github.com/GiuClab/VisiLens).

**Development snapshot v0.3.1:** local FFmpeg conversion is implemented in source. Compression and editing are not functional yet. No installer or release has been published.

## Windows portable test build

Open [GitHub Actions — Windows portable preview](https://github.com/GiuClab/MediaFlow/actions/workflows/portable.yml), select a successful run, and download the artifact named **MediaFlow-v0.3.1-Windows-x64-portable-TEST** at the bottom of the run page (GitHub sign-in may be required). The artifact ZIP contains another ZIP with the MediaFlow folder; extract both, then run `MediaFlow.exe`. Do not run the executable from inside the archive.

The preview contains FFmpeg and ffprobe. This is a development artifact, not an official release; it is retained for 14 days. If a run fails, it has no working download and its logs should be checked. See bundled FFmpeg license notices.

## MediaFlow v0.3.1 interface preview

The main window has been redesigned with an original GiuClab interpretation of a modern multimedia conversion workflow:

- Left sidebar: Video converter, Audio converter, Compressor and Editor (last two are placeholders).
- File cards displaying input name, type and size alongside selected output profile.
- Per-file Convert and Convert all actions, progress bars, Finished tab and output-folder selection.
- Output-profile dialog with Video, Audio and Device sections. The device section is informational and **not implemented**.
- Four languages (English, Italian, German, French) and GiuClab's light theme.
- A fast-encoding toggle controlling the existing FFmpeg encoding speed presets.

**Known limitations:** The preview attempts local video thumbnails and duration/resolution analysis asynchronously; audio-track selectors, device-specific presets, hardware acceleration and sophisticated profile editing are not implemented. Conversion is performed with the existing FFmpeg engine. This user interface is not a copy of Wondershare artwork or software.

## Requirements
- Windows 10/11, Python 3.10+, PySide6
- FFmpeg and ffprobe installed separately, both accessible on PATH (or next to the script).
- Appropriate encoders available in your FFmpeg build.

## Run
1. Create and activate a Python virtual environment.
2. Install dependencies: `python -m pip install -r requirements.txt`
3. Check FFmpeg: `ffmpeg -version` and `ffprobe -version`
4. Start: `python mediaflow.py`

## Input support

ASF, WMV, AVI, MP4, MKV, MOV, MPEG, WebM, FLV, MTS, TS and other video/audio input containers are accepted through the file picker or drag-and-drop. The extension is not the test of compatibility: FFprobe checks that the file contains decodable media. Some old/proprietary codecs may not work with a particular FFmpeg build. Output formats remain MP4, MKV, MOV, WebM, MP3, FLAC and WAV. Smaller windows scroll to keep controls accessible.

## Converter
- Batch video/audio conversion to MP4, MKV, MOV, WebM, MP3, FLAC or WAV.
- Automatic codec, H.264, HEVC, AV1 or VP9 where compatible; quality presets.
- Encoding speed: Fast (default), Balanced or Smaller file. Fast generally finishes sooner but may increase output size; AV1 and VP9 can still be slow on CPUs.
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
