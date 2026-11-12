"""UI regression tests for small windows and ASF input handling."""
import os

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QScrollArea

from mediaflow import MediaFlow


def test_asf_can_be_imported_and_settings_remain_usable(tmp_path):
    app = QApplication.instance() or QApplication([])
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MediaFlow(settings, "en")
    window.resize(760, 500)
    window.show()
    app.processEvents()
    try:
        video = tmp_path / "example.asf"
        video.write_bytes(b"dummy")
        window.import_files([str(video)])
        assert window.paths == [video]
        assert window.file_views[0][0].count() == 1
        assert isinstance(window.stack.currentWidget(), QScrollArea)
        assert window.controls["format"].minimumHeight() >= 36
        assert window.controls["speed"].minimumHeight() >= 36
    finally:
        window.close()
