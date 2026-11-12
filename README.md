# MediaFlow — UI prototype v0.1.0

GiuClab desktop UI prototype, following the visual conventions of [VisiLens](https://github.com/GiuClab/VisiLens).

## Requirements
- Windows 10/11, Python 3.10+, PySide6.
- No FFmpeg needed for this stage.

## Run
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python mediaflow.py
```

## Implemented
- Sidebar: Converter, Compressor, Editor.
- Local file import via picker or drag and drop.
- Synchronized file lists with removal and clearing.
- UI controls for format, codec, quality and compression.
- Output directory picker.
- First-run language selection and later switching (EN/IT/DE/FR).

## Not implemented yet
- Actual conversion, compression or export.
- Media playback or preview.
- Trimming, merging, rotation or audio extraction.
- Hardware acceleration, update checker, installer or portable build.

Processing buttons are intentionally disabled. This prototype never modifies input files.

Project name and license are still provisional. The official MediaFlow icon has not been designed.

Made with ❤️ by GiuClab

[Support on Ko-fi](https://ko-fi.com/giuclab/tip)
