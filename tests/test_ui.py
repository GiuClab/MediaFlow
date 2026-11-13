"""Smoke tests for redesigned GUI (no FFmpeg needed)."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from mediaflow import MediaFlow
from mediaflow_v3 import ProfileDialog


def test_asf_import_in_small_window(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MediaFlow(settings, "en")
    window.resize(800, 560)
    window.show()
    app.processEvents()
    try:
        video = tmp_path / "example.asf"
        video.write_bytes(b"dummy")
        window.import_files([str(video)])
        app.processEvents()
        assert window.paths == [video]
        assert len(window.cards) == 1
        assert window.items[0].output_format == "MP4"
        assert window.nav_index == 0
        assert window.all_button.isEnabled()
        window.choose_profile  # selector wired up
        window.select_tab(1)
        assert len(window.cards) == 0
        window.select_tab(0)
        assert len(window.cards) == 1
    finally:
        for worker in list(window.preview_workers):
            worker.wait(30000)
        app.processEvents()
        window.close()


def test_audio_profile_selection(tmp_path):
    app = QApplication.instance() or QApplication([])
    from mediaflow_v3 import MediaItem
    item = MediaItem(tmp_path / "sample.asf")
    dialog = ProfileDialog("it", item)
    dialog.tabs.setCurrentIndex(1)
    dialog.options["audio_tab"].setCurrentRow(0)
    dialog.accept_selected()
    assert dialog.result_profile == ("MP3", "Auto", "High")
    dialog.close()
