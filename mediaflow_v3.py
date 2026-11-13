"""MediaFlow v0.3.0 — GiuClab desktop converter UI.

Original GiuClab widgets and styling, organized around an intuitive file
conversion workflow. Media processing is performed by converter.py/FFmpeg.
"""
from __future__ import annotations

import sys
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QThread, Signal
from PySide6.QtGui import QAction, QDesktopServices, QPixmap
from media_probe import probe_preview
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QScrollArea, QStackedWidget,
    QTabWidget, QVBoxLayout, QWidget, QSizePolicy
)

from converter import Job, convert, find_binary, ConversionCancelled, ConversionError

VERSION = "0.3.1"
FORMATS_VIDEO = ("MP4", "MKV", "MOV", "WebM")
FORMATS_AUDIO = ("MP3", "FLAC", "WAV")
INPUT_EXT = {
    ".3g2", ".3gp", ".asf", ".avi", ".divx", ".dv", ".f4v", ".flv", ".m2t",
    ".m2ts", ".m4v", ".mkv", ".mod", ".mov", ".mp4", ".mpe", ".mpeg",
    ".mpg", ".mts", ".mxf", ".ogv", ".rm", ".rmvb", ".tod", ".ts",
    ".vob", ".webm", ".wmv", ".y4m", ".264", ".265", ".h264", ".h265",
    ".hevc", ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
    ".aif", ".aiff", ".ape", ".ac3", ".amr", ".opus", ".alac", ".caf",
}

LANGUAGES = {"en": "English", "it": "Italiano", "de": "Deutsch", "fr": "Français"}
STRINGS = {
"en": {
"video":"Video converter", "audio":"Audio converter", "compress":"Video compressor",
"editor":"Video editor", "finished":"Finished", "queue":"Conversion",
"add":"Add files", "clear":"Clear list", "highspeed":"Fast encoding", "empty":"Drag media files here or use Add files",
"format":"Output format", "same":"Same as source", "quality":"Quality", "speed":"Encoding speed",
"all":"Convert all", "one":"Convert", "cancel":"Cancel", "ready":"Ready",
"working":"Converting", "done":"Completed", "failed":"Failed", "removed":"Remove",
"output":"Output folder", "browse":"Browse…", "selected":"Selected profile",
"video_tab":"Video", "audio_tab":"Audio", "device_tab":"Device",
"presets":"Choose an output profile", "choose":"Use this profile", "notyet":"Not implemented in this preview",
"devicehint":"Device-specific presets will be added in a later version.",
"settings":"Settings", "about":"About MediaFlow", "language":"Language",
"file":"File", "options":"Options", "help":"Help", "exit":"Exit", "support":"❤️ Support me",
"duration":"Duration", "size":"Size", "source":"Original", "target":"Output",
"no_input":"Add media files before starting conversion.", "ffmpeg":"FFmpeg and ffprobe are required.",
"running":"A conversion is running. Cancel it before closing or changing language.",
"saved":"Output saved", "errors":"Errors", "completed":"Conversion finished",
"failed_msg":"At least one conversion failed. Check the status shown on each file.",
"delayed":"Compression and editing are planned, but not yet available.",
"pick":"Choose output directory", "advanced":"Advanced", "canceling":"Cancelling…",
},
"it": {
"video":"Convertitore video", "audio":"Convertitore audio", "compress":"Compressore video",
"editor":"Editor video", "finished":"Completati", "queue":"Conversione",
"add":"Aggiungi file", "clear":"Svuota elenco", "highspeed":"Codifica veloce", "empty":"Trascina qui i file o scegli Aggiungi file",
"format":"Formato di uscita", "same":"Come sorgente", "quality":"Qualità", "speed":"Velocità di codifica",
"all":"Converti tutti", "one":"Converti", "cancel":"Annulla", "ready":"Pronto",
"working":"Conversione", "done":"Completato", "failed":"Errore", "removed":"Rimuovi",
"output":"Cartella di destinazione", "browse":"Sfoglia…", "selected":"Profilo selezionato",
"video_tab":"Video", "audio_tab":"Audio", "device_tab":"Dispositivo",
"presets":"Scegli un profilo di uscita", "choose":"Usa questo profilo", "notyet":"Non disponibile in questa anteprima",
"devicehint":"I profili specifici dei dispositivi arriveranno in una versione successiva.",
"settings":"Impostazioni", "about":"Informazioni su MediaFlow", "language":"Lingua",
"file":"File", "options":"Opzioni", "help":"Aiuto", "exit":"Esci", "support":"❤️ Support me",
"duration":"Durata", "size":"Dimensione", "source":"Originale", "target":"Uscita",
"no_input":"Aggiungi file prima di iniziare la conversione.", "ffmpeg":"Sono necessari FFmpeg e ffprobe.",
"running":"Conversione in corso. Annullala prima di chiudere o cambiare lingua.",
"saved":"File salvato", "errors":"Errori", "completed":"Conversione terminata",
"failed_msg":"Almeno una conversione non è riuscita. Controlla lo stato di ciascun file.",
"delayed":"Compressione ed editing sono previsti, ma non ancora disponibili.",
"pick":"Scegli la cartella di destinazione", "advanced":"Avanzate", "canceling":"Annullamento…",
},
"de": {
"video":"Videokonverter", "audio":"Audiokonverter", "compress":"Videokompressor",
"editor":"Videoeditor", "finished":"Fertig", "queue":"Konvertierung",
"add":"Dateien hinzufügen", "clear":"Liste leeren", "highspeed":"Schnelle Kodierung", "empty":"Mediendateien hierher ziehen oder Dateien hinzufügen",
"format":"Ausgabeformat", "same":"Wie Quelle", "quality":"Qualität", "speed":"Kodierungsgeschwindigkeit",
"all":"Alle konvertieren", "one":"Konvertieren", "cancel":"Abbrechen", "ready":"Bereit",
"working":"Konvertierung", "done":"Abgeschlossen", "failed":"Fehler", "removed":"Entfernen",
"output":"Ausgabeordner", "browse":"Durchsuchen…", "selected":"Ausgewähltes Profil",
"video_tab":"Video", "audio_tab":"Audio", "device_tab":"Gerät",
"presets":"Ausgabeprofil auswählen", "choose":"Profil übernehmen", "notyet":"In dieser Vorschau noch nicht verfügbar",
"devicehint":"Gerätespezifische Profile folgen in einer späteren Version.",
"settings":"Einstellungen", "about":"Über MediaFlow", "language":"Sprache",
"file":"Datei", "options":"Optionen", "help":"Hilfe", "exit":"Beenden", "support":"❤️ Unterstütze mich",
"duration":"Dauer", "size":"Größe", "source":"Original", "target":"Ausgabe",
"no_input":"Vor der Konvertierung Dateien hinzufügen.", "ffmpeg":"FFmpeg und ffprobe sind erforderlich.",
"running":"Konvertierung läuft. Vor dem Schließen oder Sprachwechsel abbrechen.",
"saved":"Datei gespeichert", "errors":"Fehler", "completed":"Konvertierung beendet",
"failed_msg":"Mindestens eine Konvertierung ist fehlgeschlagen. Dateistatus prüfen.",
"delayed":"Komprimierung und Bearbeitung sind noch nicht verfügbar.",
"pick":"Ausgabeordner auswählen", "advanced":"Erweitert", "canceling":"Abbruch läuft…",
},
"fr": {
"video":"Convertisseur vidéo", "audio":"Convertisseur audio", "compress":"Compresseur vidéo",
"editor":"Éditeur vidéo", "finished":"Terminés", "queue":"Conversion",
"add":"Ajouter des fichiers", "clear":"Vider la liste", "highspeed":"Encodage rapide", "empty":"Déposez les fichiers ici ou cliquez sur Ajouter des fichiers",
"format":"Format de sortie", "same":"Comme la source", "quality":"Qualité", "speed":"Vitesse d'encodage",
"all":"Tout convertir", "one":"Convertir", "cancel":"Annuler", "ready":"Prêt",
"working":"Conversion", "done":"Terminé", "failed":"Échec", "removed":"Retirer",
"output":"Dossier de destination", "browse":"Parcourir…", "selected":"Profil sélectionné",
"video_tab":"Vidéo", "audio_tab":"Audio", "device_tab":"Appareil",
"presets":"Choisir un profil de sortie", "choose":"Utiliser ce profil", "notyet":"Non disponible dans cette version",
"devicehint":"Les profils spécifiques aux appareils seront ajoutés ultérieurement.",
"settings":"Paramètres", "about":"À propos de MediaFlow", "language":"Langue",
"file":"Fichier", "options":"Options", "help":"Aide", "exit":"Quitter", "support":"❤️ Soutenez-moi",
"duration":"Durée", "size":"Taille", "source":"Original", "target":"Sortie",
"no_input":"Ajoutez des fichiers avant de lancer la conversion.", "ffmpeg":"FFmpeg et ffprobe sont requis.",
"running":"Conversion en cours. Annulez avant de fermer ou changer de langue.",
"saved":"Fichier enregistré", "errors":"Erreurs", "completed":"Conversion terminée",
"failed_msg":"Au moins une conversion a échoué. Vérifiez le statut de chaque fichier.",
"delayed":"La compression et l'édition ne sont pas encore disponibles.",
"pick":"Choisir le dossier de sortie", "advanced":"Avancé", "canceling":"Annulation…",
}
}

STYLE = """
QMainWindow, QWidget#root, QScrollArea#mainScroll { background: #F5F6FB; }
QWidget { color: #242936; font-family: 'Segoe UI', Arial; font-size: 12px; }
QFrame#sidebar, QFrame#fileCard, QFrame#emptyCard, QFrame#footer {
 background: white; border: 1px solid #DFE3ED; border-radius: 12px; }
QFrame#thumb { background: #E8EEFF; border: 1px solid #D1DCF8; border-radius: 9px; }
QLabel#brand { color: #385AD0; font-size: 23px; font-weight: 750; }
QLabel#pageTitle { font-size: 19px; font-weight: 750; }
QLabel#filename { font-size: 14px; font-weight: 700; }
QLabel#section { font-weight: 700; font-size: 13px; }
QLabel#muted { color: #677082; }
QPushButton { border: 1px solid #D6DDEC; border-radius: 9px; background: white;
 padding: 9px 12px; font-weight: 600; }
QPushButton:hover { background: #EDF2FF; border-color: #9EB3E8; }
QPushButton#primary, QPushButton#navOn { background: #385AD0; color: white; border: none; }
QPushButton#primary:hover, QPushButton#navOn:hover { background: #2D49AB; }
QPushButton#nav, QPushButton#navOn { text-align: left; padding: 11px 13px; }
QPushButton#nav { border: none; background: transparent; }
QPushButton#nav:hover { background: #EDF2FF; }
QPushButton:disabled { color: #8790A3; background: #E8EBF3; border: 1px solid #DFE3ED; }
QComboBox, QLineEdit, QListWidget { background: white; border: 1px solid #DFE3ED;
 border-radius: 8px; padding: 7px; min-height: 26px; }
QComboBox { padding-right: 28px; }
QProgressBar { background: #E1E5F0; height: 10px; border: none; border-radius: 5px; }
QProgressBar::chunk { background: #385AD0; border-radius: 5px; }
QScrollArea { border: none; background: transparent; }
QTabWidget::pane { border: 1px solid #DFE3ED; border-radius: 8px; background: white; }
QTabBar::tab { background: #F5F6FB; padding: 9px 18px; }
QTabBar::tab:selected { color: #385AD0; font-weight: 700; border-bottom: 2px solid #385AD0; }
"""


def tr(lang: str, key: str) -> str:
    return STRINGS[lang][key]


def muted(text: str) -> QLabel:
    w = QLabel(text)
    w.setObjectName("muted")
    return w


def column_card(name: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName(name)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(16, 14, 16, 14)
    lay.setSpacing(10)
    return frame, lay


@dataclass
class MediaItem:
    path: Path
    output_format: str = "MP4"
    codec: str = "Auto"
    quality: str = "High"
    status: str = ""
    output_path: str = ""
    details: str = ""
    thumbnail: bytes = b""


class Batch(QThread):
    started_file = Signal(int)
    progressed = Signal(int, float)
    finished_file = Signal(int, str)
    failed_file = Signal(int, str)
    batch_done = Signal(bool)

    def __init__(self, items: list[MediaItem], output: Path, speed: str, parent=None):
        super().__init__(parent)
        self.items = [MediaItem(**vars(item)) for item in items]
        self.output = output
        self.speed = speed
        self.cancel_event = threading.Event()

    def run(self):
        for i, item in enumerate(self.items):
            if self.cancel_event.is_set():
                break
            self.started_file.emit(i)
            try:
                dst = convert(Job(item.path, self.output, item.output_format.lower(),
                                  item.codec, item.quality, self.speed),
                              progress=lambda pct, idx=i: self.progressed.emit(idx, pct),
                              cancel=self.cancel_event)
                self.finished_file.emit(i, str(dst))
            except ConversionCancelled:
                break
            except (ConversionError, ValueError, OSError) as error:
                self.failed_file.emit(i, str(error))
        self.batch_done.emit(self.cancel_event.is_set())

    def cancel(self):
        self.cancel_event.set()


class PreviewWorker(QThread):
    preview_ready = Signal(str, str, bytes)

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.path = path

    def run(self):
        details, thumb = probe_preview(self.path)
        self.preview_ready.emit(str(self.path), details, thumb)


class ProfileDialog(QDialog):
    """Two-column profile selector; choices reflect implemented FFmpeg outputs."""
    def __init__(self, lang: str, current: MediaItem, parent=None):
        super().__init__(parent)
        self.lang = lang
        self.result_profile = None
        self.setWindowTitle(tr(lang, "presets"))
        self.resize(720, 535)
        self.setMinimumSize(560, 440)
        root = QVBoxLayout(self)
        title = QLabel(tr(lang, "presets"))
        title.setObjectName("pageTitle")
        root.addWidget(title)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.options = {}
        self.option_labels = {}
        for key, formats in (("video_tab", FORMATS_VIDEO), ("audio_tab", FORMATS_AUDIO)):
            page = QWidget()
            row = QHBoxLayout(page)
            row.setContentsMargins(8, 12, 8, 12)
            names = QListWidget()
            names.setFixedWidth(160)
            for fmt in formats:
                names.addItem(fmt)
            row.addWidget(names)
            details = QVBoxLayout()
            heading = QLabel(tr(lang, "same"))
            heading.setObjectName("section")
            details.addWidget(heading)
            box = QListWidget()
            box.addItem(tr(lang, "same") + "  ·  " + "Original resolution")
            box.setCurrentRow(0)
            box.itemDoubleClicked.connect(self.accept_selected)
            details.addWidget(box, 1)
            info = muted("The current converter preserves source dimensions. "
                         "Additional resolution profiles will follow.")
            info.setWordWrap(True)
            details.addWidget(info)
            row.addLayout(details, 1)
            names.currentRowChanged.connect(
                lambda _index, view=box: view.setCurrentRow(0))
            self.tabs.addTab(page, tr(lang, key))
            self.options[key] = names
            self.option_labels[key] = box
        device = QWidget()
        dl = QVBoxLayout(device)
        note = muted(tr(lang, "devicehint"))
        note.setWordWrap(True)
        dl.addWidget(note)
        dl.addStretch()
        self.tabs.addTab(device, tr(lang, "device_tab"))
        controls = QHBoxLayout()
        codec_col = QVBoxLayout()
        codec_col.addWidget(muted("Codec"))
        self.codec = QComboBox()
        self.codec.addItems(["Auto", "H.264", "H.265 / HEVC", "AV1", "VP9"])
        codec_col.addWidget(self.codec)
        controls.addLayout(codec_col, 1)
        quality_col = QVBoxLayout()
        quality_col.addWidget(muted(tr(lang, "quality")))
        self.quality = QComboBox()
        self.quality.addItems(["High", "Balanced", "Small file"])
        quality_col.addWidget(self.quality)
        controls.addLayout(quality_col, 1)
        root.addLayout(controls)
        self.codec.setCurrentText(current.codec)
        self.quality.setCurrentText(current.quality)
        self.tabs.setCurrentIndex(0 if current.output_format in FORMATS_VIDEO else 1)
        for key, formats in (("video_tab", FORMATS_VIDEO), ("audio_tab", FORMATS_AUDIO)):
            self.options[key].setCurrentRow(
                formats.index(current.output_format) if current.output_format in formats else 0)
        bottom = QHBoxLayout()
        bottom.addStretch()
        self.action = QPushButton(tr(lang, "choose"))
        self.action.setObjectName("primary")
        self.action.clicked.connect(self.accept_selected)
        bottom.addWidget(self.action)
        root.addLayout(bottom)

    def accept_selected(self, _=None):
        tab = self.tabs.currentIndex()
        if tab == 2:
            return
        formats = FORMATS_VIDEO if tab == 0 else FORMATS_AUDIO
        view = self.options["video_tab" if tab == 0 else "audio_tab"]
        choice = view.currentRow()
        if choice < 0:
            return
        fmt = formats[choice]
        self.result_profile = (fmt, self.codec.currentText() if tab == 0 else "Auto",
                               self.quality.currentText())
        self.accept()


class FileCard(QFrame):
    """Compact input-to-output media row with a real per-item action."""
    def __init__(self, item: MediaItem, lang: str, choose, remove, convert_one):
        super().__init__()
        self.item = item
        self.setObjectName("fileCard")
        self.setMinimumWidth(660)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 13, 14, 12)
        outer.setSpacing(7)

        main = QHBoxLayout()
        main.setSpacing(12)
        thumb = QFrame()
        thumb.setObjectName("thumb")
        thumb.setFixedSize(128, 94)
        thumb_layout = QVBoxLayout(thumb)
        symbol = QLabel("▶")
        symbol.setAlignment(Qt.AlignmentFlag.AlignCenter)
        symbol.setStyleSheet("color:#385AD0; font-size:27px; border:none;")
        thumb_layout.addWidget(symbol)
        self.thumb_icon = symbol
        if item.thumbnail:
            pixmap = QPixmap()
            if pixmap.loadFromData(item.thumbnail):
                symbol.setPixmap(pixmap.scaled(120, 86, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation))
        main.addWidget(thumb)

        original = QVBoxLayout()
        original.setSpacing(7)
        name = QLabel(item.path.name)
        name.setObjectName("filename")
        name.setToolTip(str(item.path))
        name.setWordWrap(False)
        original.addWidget(name)
        try:
            size = f"{item.path.stat().st_size/(1024*1024):.2f} MB"
        except OSError:
            size = "—"
        original.addWidget(muted(f"{item.path.suffix.upper().lstrip('.')}  ·  {size}"))
        self.details_label = muted(item.details)
        original.addWidget(self.details_label)
        original.addStretch()
        main.addLayout(original, 3)

        arrow = QLabel("⇄")
        arrow.setStyleSheet("color:#385AD0;font-size:21px;")
        main.addWidget(arrow)

        target = QVBoxLayout()
        target.setSpacing(8)
        self.profile = QPushButton()
        self.profile.setToolTip(tr(lang, "presets"))
        self.profile.clicked.connect(lambda: choose(item))
        target.addWidget(self.profile)
        self.state = muted(tr(lang, "ready"))
        target.addWidget(self.state)
        target.addStretch()
        main.addLayout(target, 3)

        buttons = QVBoxLayout()
        buttons.setSpacing(6)
        self.convert_button = QPushButton(tr(lang, "one"))
        self.convert_button.setObjectName("primary")
        self.convert_button.clicked.connect(lambda: convert_one(item))
        buttons.addWidget(self.convert_button)
        self.remove_button = QPushButton("×")
        self.remove_button.setToolTip(tr(lang, "removed"))
        self.remove_button.clicked.connect(lambda: remove(item))
        buttons.addWidget(self.remove_button)
        buttons.addStretch()
        main.addLayout(buttons)
        outer.addLayout(main)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        outer.addWidget(self.progress)
        self.refresh()

    def refresh(self):
        self.profile.setText(f"{self.item.output_format}   •   {self.item.codec}   ⚙")
        self.state.setText(self.item.status or "Ready")

class DropArea(QFrame):
    files_added = Signal(list)

    def __init__(self, text):
        super().__init__()
        self.setObjectName("emptyCard")
        self.setAcceptDrops(True)
        lay = QVBoxLayout(self)
        label = muted(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(label)
        self.setMinimumHeight(150)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.files_added.emit([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
        event.acceptProposedAction()


class MediaFlow(QMainWindow):
    def __init__(self, settings: QSettings, language: str):
        super().__init__()
        self.settings = settings
        self.lang = language if language in LANGUAGES else "en"
        self.items: list[MediaItem] = []
        self.paths: list[Path] = []
        self.cards: dict[str, FileCard] = {}
        self.output_folder = Path(settings.value("output_folder", str(Path.home()), type=str))
        if not self.output_folder.is_dir():
            self.output_folder = Path.home()
        self.worker: Batch | None = None
        self._worker_items: list[MediaItem] = []
        self._worker_source: list[MediaItem] = []
        self.preview_workers: list[PreviewWorker] = []
        self.setWindowTitle(f"MediaFlow v{VERSION} — © 2026 GiuClab")
        self.resize(1240, 810)
        self.setMinimumSize(790, 540)
        self.setStyleSheet(STYLE)
        self.build_ui()

    def build_ui(self):
        self.menuBar().clear()
        fm = self.menuBar().addMenu(tr(self.lang, "file"))
        fm.addAction(tr(self.lang, "add"), self.add_dialog)
        fm.addAction(tr(self.lang, "exit"), self.close)
        om = self.menuBar().addMenu(tr(self.lang, "options"))
        lm = om.addMenu(tr(self.lang, "language"))
        for code, name in LANGUAGES.items():
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(code == self.lang)
            act.triggered.connect(lambda _checked=False, value=code: self.set_language(value))
            lm.addAction(act)
        hm = self.menuBar().addMenu(tr(self.lang, "help"))
        hm.addAction(tr(self.lang, "about"), self.about)
        self.menuBar().addAction(tr(self.lang, "support"),
                                 lambda: webbrowser.open("https://ko-fi.com/giuclab/tip"))
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(12, 12, 12, 8)
        shell.setSpacing(12)

        side, sl = column_card("sidebar")
        side.setFixedWidth(216)
        brand = QLabel("◉  MediaFlow")
        brand.setObjectName("brand")
        sl.addWidget(brand)
        sl.addWidget(muted("GiuClab"))
        sl.addSpacing(18)
        self.nav_buttons = []
        self.stack = QStackedWidget()
        for idx, key in enumerate(("video", "audio", "compress", "editor")):
            button = QPushButton(tr(self.lang, key))
            button.clicked.connect(lambda _checked=False, i=idx: self.navigate(i))
            sl.addWidget(button)
            self.nav_buttons.append(button)
        sl.addStretch()
        options = QPushButton(tr(self.lang, "settings"))
        options.clicked.connect(self.options)
        sl.addWidget(options)
        about = QPushButton(tr(self.lang, "about"))
        about.clicked.connect(self.about)
        sl.addWidget(about)
        shell.addWidget(side)
        main = QWidget()
        main_lay = QVBoxLayout(main)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(10)

        toolbar = QHBoxLayout()
        add = QPushButton("+ " + tr(self.lang, "add"))
        add.setObjectName("primary")
        add.clicked.connect(self.add_dialog)
        toolbar.addWidget(add)
        toolbar.addStretch()
        self.tabs = []
        for idx, key in enumerate(("queue", "finished")):
            btn = QPushButton(tr(self.lang, key))
            btn.clicked.connect(lambda _checked=False, i=idx: self.select_tab(i))
            toolbar.addWidget(btn)
            self.tabs.append(btn)
        toolbar.addStretch()
        self.fast = QCheckBox(tr(self.lang, "highspeed"))
        self.fast.setChecked(self.settings.value("fast", True, type=bool))
        self.fast.toggled.connect(lambda val: self.settings.setValue("fast", val))
        toolbar.addWidget(self.fast)
        main_lay.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        content.setObjectName("root")
        cv = QVBoxLayout(content)
        cv.setContentsMargins(2, 2, 2, 8)
        cv.setSpacing(10)
        self.page_title = QLabel(tr(self.lang, "video"))
        self.page_title.setObjectName("pageTitle")
        cv.addWidget(self.page_title)
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(10)
        cv.addLayout(self.cards_layout)
        self.drop_area = DropArea(tr(self.lang, "empty"))
        self.drop_area.files_added.connect(self.import_files)
        cv.addWidget(self.drop_area)
        cv.addStretch(1)
        scroll.setWidget(content)
        main_lay.addWidget(scroll, 1)

        footer, foot = column_card("footer")
        outrow = QHBoxLayout()
        self.output_label = muted(f"{tr(self.lang, 'output')}: {self.output_folder}")
        self.output_label.setWordWrap(True)
        outrow.addWidget(self.output_label, 1)
        browse = QPushButton(tr(self.lang, "browse"))
        browse.clicked.connect(self.pick_output)
        outrow.addWidget(browse)
        self.all_button = QPushButton(tr(self.lang, "all"))
        self.all_button.setObjectName("primary")
        self.all_button.clicked.connect(self.convert_all)
        outrow.addWidget(self.all_button)
        foot.addLayout(outrow)
        self.total_progress = QProgressBar()
        self.total_progress.setValue(0)
        self.total_progress.setVisible(False)
        foot.addWidget(self.total_progress)
        self.cancel_button = QPushButton(tr(self.lang, "cancel"))
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_conversion)
        foot.addWidget(self.cancel_button)
        main_lay.addWidget(footer)
        main_lay.addWidget(muted(f"MediaFlow v{VERSION} — © 2026 GiuClab  |  Made with ❤️ by GiuClab"))
        shell.addWidget(main, 1)
        self.nav_index = 0
        self.tab_index = 0
        self.navigate(0)
        self.render_cards()

    def navigate(self, idx):
        self.nav_index = idx
        self.page_title.setText(tr(self.lang, ("video", "audio", "compress", "editor")[idx]))
        for j, button in enumerate(self.nav_buttons):
            button.setObjectName("navOn" if j == idx else "nav")
            button.style().unpolish(button)
            button.style().polish(button)
        if idx >= 2:
            self.drop_area.hide()
            self.all_button.setEnabled(False)
            self.statusBar().showMessage(tr(self.lang, "delayed"), 9000)
        else:
            self.drop_area.show()
            self.all_button.setEnabled(bool([i for i in self.items if not i.output_path]) and not self.is_busy())
        self.render_cards()

    def select_tab(self, idx):
        self.tab_index = idx
        self.render_cards()

    def is_busy(self):
        return self.worker is not None and self.worker.isRunning()

    def add_dialog(self):
        allowed = " ".join("*" + x for x in sorted(INPUT_EXT))
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr(self.lang, "add"), str(Path.home()),
            f"Common media ({allowed});;All files (*)")
        self.import_files(paths)

    def import_files(self, files):
        if self.is_busy():
            return
        seen = {str(item.path).casefold() for item in self.items}
        added = 0
        for raw in files:
            path = Path(raw)
            if path.is_file() and str(path).casefold() not in seen:
                fmt = "MP3" if self.nav_index == 1 else "MP4"
                self.items.append(MediaItem(path, output_format=fmt))
                seen.add(str(path).casefold())
                added += 1
        self.paths = [item.path for item in self.items]
        self.select_tab(0)
        if added:
            for item in self.items[-added:]:
                worker = PreviewWorker(item.path, self)
                worker.preview_ready.connect(self.on_preview_ready)
                worker.finished.connect(worker.deleteLater)
                worker.finished.connect(lambda w=worker: self.finish_preview_worker(w))
                self.preview_workers.append(worker)
                worker.start()
            self.statusBar().showMessage(f"{added} file(s)", 5000)

    def on_preview_ready(self, filename, details, thumbnail):
        item = next((it for it in self.items if str(it.path) == filename), None)
        if item is None:
            return
        item.details = details
        item.thumbnail = thumbnail
        card = self.cards.get(filename)
        if card:
            card.details_label.setText(details)
            if thumbnail:
                pixmap = QPixmap()
                if pixmap.loadFromData(thumbnail):
                    card.thumb_icon.setPixmap(
                        pixmap.scaled(120, 86, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))

    def finish_preview_worker(self, worker):
        if worker in self.preview_workers:
            self.preview_workers.remove(worker)

    def render_cards(self):
        while self.cards_layout.count():
            entry = self.cards_layout.takeAt(0)
            widget = entry.widget()
            if widget is not None:
                widget.deleteLater()
        self.cards = {}
        shown = [item for item in self.items
                 if (self.tab_index == 1) == bool(item.output_path) and self.nav_index < 2]
        self.drop_area.setVisible(not shown and self.nav_index < 2)
        self.page_title.setVisible(self.nav_index != 2 and self.nav_index != 3)
        for item in shown:
            card = FileCard(item, self.lang, self.choose_profile, self.remove_item, self.convert_one)
            self.cards_layout.addWidget(card)
            self.cards[str(item.path)] = card
        self.all_button.setEnabled(bool([i for i in self.items if not i.output_path]) and self.nav_index < 2 and not self.is_busy())

    def remove_item(self, item):
        if self.is_busy():
            return
        self.items = [x for x in self.items if x is not item]
        self.paths = [x.path for x in self.items]
        self.render_cards()

    def choose_profile(self, item):
        if self.is_busy():
            return
        dialog = ProfileDialog(self.lang, item, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_profile:
            item.output_format, item.codec, item.quality = dialog.result_profile
            self.render_cards()

    def pick_output(self):
        if self.is_busy():
            return
        folder = QFileDialog.getExistingDirectory(self, tr(self.lang, "pick"), str(self.output_folder))
        if folder:
            self.output_folder = Path(folder)
            self.settings.setValue("output_folder", folder)
            self.output_label.setText(f"{tr(self.lang,'output')}: {folder}")

    def convert_one(self, item):
        self.start_jobs([item])

    def convert_all(self):
        self.start_jobs([item for item in self.items if not item.output_path])

    def start_jobs(self, selection):
        if not selection or self.is_busy() or self.nav_index >= 2:
            return
        try:
            find_binary("ffmpeg")
            find_binary("ffprobe")
        except ConversionError as error:
            QMessageBox.warning(self, "MediaFlow", tr(self.lang, "ffmpeg") + "\n" + str(error))
            return
        self._worker_source = list(selection)
        self.worker = Batch(selection, self.output_folder,
                            "Fast" if self.fast.isChecked() else "Balanced", self)
        self.worker.started_file.connect(self.on_started)
        self.worker.progressed.connect(self.on_progress)
        self.worker.finished_file.connect(self.on_finished_file)
        self.worker.failed_file.connect(self.on_failed_file)
        self.worker.batch_done.connect(self.on_batch_done)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.on_thread_finished)
        self.all_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setVisible(True)
        self.total_progress.setVisible(True)
        self.total_progress.setValue(0)
        for item in selection:
            item.status = tr(self.lang, "ready")
        self.render_cards()
        self.worker.start()

    def on_started(self, index):
        item = self._worker_source[index]
        item.status = tr(self.lang, "working")
        card = self.cards.get(str(item.path))
        if card:
            card.refresh()

    def on_progress(self, index, pct):
        item = self._worker_source[index]
        card = self.cards.get(str(item.path))
        if card:
            card.progress.setValue(int(pct))
        self.total_progress.setValue(round(100 * (index + pct/100) / len(self._worker_source)))

    def on_finished_file(self, index, path):
        item = self._worker_source[index]
        item.output_path = path
        item.status = tr(self.lang, "done")
        self.statusBar().showMessage(f"{tr(self.lang,'saved')}: {path}", 10000)
        card = self.cards.get(str(item.path))
        if card:
            card.progress.setValue(100)
            card.refresh()

    def on_failed_file(self, index, error):
        item = self._worker_source[index]
        item.status = f"{tr(self.lang, 'failed')}: {error[:130]}"
        card = self.cards.get(str(item.path))
        if card:
            card.refresh()
        self.statusBar().showMessage(item.status, 12000)

    def on_batch_done(self, was_cancelled):
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        self.all_button.setEnabled(bool([i for i in self.items if not i.output_path]))
        if not was_cancelled and all(i.output_path for i in self._worker_source):
            self.total_progress.setValue(100)
        self.statusBar().showMessage(tr(self.lang, "completed"), 7000)
        self.total_progress.setVisible(False)

    def on_thread_finished(self):
        self.worker = None
        self.render_cards()

    def cancel_conversion(self):
        if self.is_busy():
            self.worker.cancel()
            self.cancel_button.setEnabled(False)
            self.statusBar().showMessage(tr(self.lang, "canceling"), 7000)

    def options(self):
        if self.is_busy():
            QMessageBox.information(self, "MediaFlow", tr(self.lang, "running"))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(tr(self.lang, "settings"))
        lay = QVBoxLayout(dialog)
        lay.addWidget(QLabel(tr(self.lang, "language")))
        combo = QComboBox()
        for code, name in LANGUAGES.items():
            combo.addItem(name, code)
        combo.setCurrentIndex(list(LANGUAGES).index(self.lang))
        lay.addWidget(combo)
        btn = QPushButton("OK")
        btn.clicked.connect(dialog.accept)
        lay.addWidget(btn)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.set_language(combo.currentData())

    def set_language(self, lang):
        if lang == self.lang:
            return
        if self.is_busy():
            QMessageBox.information(self, "MediaFlow", tr(self.lang, "running"))
            return
        self.lang = lang
        self.settings.setValue("ui/language", lang)
        self.build_ui()

    def about(self):
        QMessageBox.information(self, tr(self.lang, "about"),
            f"MediaFlow v{VERSION} — © 2026 GiuClab\n\n"
            + tr(self.lang, "delayed") + "\n"
            + "Windows 10/11 · FFmpeg · Development preview\n\n"
            + "Made with ❤️ by GiuClab")

    def closeEvent(self, event):
        if self.preview_workers:
            QMessageBox.information(self, "MediaFlow", "Media analysis is in progress.")
            event.ignore()
            return
        if self.is_busy():
            QMessageBox.information(self, "MediaFlow", tr(self.lang, "running"))
            event.ignore()
        else:
            event.accept()


def choose_language(settings):
    chosen = settings.value("ui/language", "", type=str)
    if chosen in LANGUAGES:
        return chosen
    dialog = QDialog()
    dialog.setWindowTitle("MediaFlow — Language / Lingua")
    lay = QVBoxLayout(dialog)
    lay.addWidget(QLabel("Choose your language / Scegli la lingua"))
    combo = QComboBox()
    for code, name in LANGUAGES.items():
        combo.addItem(name, code)
    lay.addWidget(combo)
    button = QPushButton("Continue / Continua")
    button.clicked.connect(dialog.accept)
    lay.addWidget(button)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        chosen = combo.currentData()
    else:
        chosen = "en"
    settings.setValue("ui/language", chosen)
    return chosen


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MediaFlow")
    app.setOrganizationName("GiuClab")
    app.setStyleSheet(STYLE)
    settings = QSettings("GiuClab", "MediaFlow")
    win = MediaFlow(settings, choose_language(settings))
    win.show()
    return app.exec()
