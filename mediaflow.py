"""MediaFlow UI prototype — © 2026 GiuClab.

The application converts media with FFmpeg; editing and compression remain planned.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path
from converter import Job, convert, find_binary, ConversionError, ConversionCancelled

from PySide6.QtCore import Qt, QSettings, Signal, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget, QProgressBar,
)

APP_VERSION = "0.2.0"
EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv",
              ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"}
LANGS = {"en": "English", "it": "Italiano", "de": "Deutsch", "fr": "Français"}

# All strings shown by the prototype have equivalents in all four languages.
TEXT = {
 "en": {
  "converter":"Converter", "compressor":"Compressor", "editor":"Editor", "settings":"Settings",
  "about":"About", "add":"Add files", "remove":"Remove selected", "clear":"Clear list",
  "drop":"Drag media files here or click Add files", "empty":"No files imported",
  "files":"Files", "output":"Output settings", "format":"Output format", "quality":"Quality",
  "codec":"Video codec", "resolution":"Resolution", "preset":"Compression preset",
  "tools":"Editing tools", "trim":"Trim", "merge":"Merge", "rotate":"Rotate",
  "audio":"Extract audio", "destination":"Output folder", "browse":"Browse…",
  "not_ready":"Not yet implemented — UI prototype only", "convert":"Convert all",
  "compress":"Compress all", "export":"Export", "preview":"Preview available in a later version",
  "status":"Prototype: no files will be modified", "hint":"The processing engine will be added in a later phase.",
  "title_c":"Video and audio conversion", "title_p":"Media compression", "title_e":"Quick media editing",
  "sub_c":"Choose output format, codec and quality for imported files.",
  "sub_p":"Choose a compression preset for imported files.",
  "sub_e":"Quick operations without a multitrack timeline.",
  "menu_file":"File", "menu_options":"Options", "menu_help":"Help", "menu_exit":"Exit",
  "menu_language":"Language", "menu_about":"About MediaFlow", "menu_support":"❤️ Support me",
  "choose_lang":"Choose your language", "continue":"Continue", "close":"Close",
  "about_body":"MediaFlow is a GiuClab UI prototype for Windows. Conversion, compression and editing are not implemented yet. No files are modified.\n\nMade with ❤️ by GiuClab",
  "count":"Files imported", "invalid":"Unsupported files skipped", "allfiles":"Media files",
  "notfound":"The selected file no longer exists.", "drophelp":"You can drop files from Windows Explorer here.",
 },
 "it": {
  "converter":"Convertitore", "compressor":"Compressore", "editor":"Editor", "settings":"Impostazioni",
  "about":"Informazioni", "add":"Aggiungi file", "remove":"Rimuovi selezionati", "clear":"Svuota elenco",
  "drop":"Trascina qui i file multimediali o premi Aggiungi file", "empty":"Nessun file importato",
  "files":"File", "output":"Impostazioni di uscita", "format":"Formato di uscita", "quality":"Qualità",
  "codec":"Codec video", "resolution":"Risoluzione", "preset":"Profilo di compressione",
  "tools":"Strumenti di modifica", "trim":"Taglia", "merge":"Unisci", "rotate":"Ruota",
  "audio":"Estrai audio", "destination":"Cartella di destinazione", "browse":"Sfoglia…",
  "not_ready":"Funzione non ancora disponibile — solo prototipo", "convert":"Converti tutti",
  "compress":"Comprimi tutti", "export":"Esporta", "preview":"Anteprima disponibile in una versione successiva",
  "status":"Prototipo: nessun file verrà modificato", "hint":"Il motore di elaborazione sarà aggiunto in una fase successiva.",
  "title_c":"Conversione video e audio", "title_p":"Compressione multimediale", "title_e":"Modifica rapida dei file",
  "sub_c":"Scegli formato, codec e qualità per i file importati.",
  "sub_p":"Scegli un profilo di compressione per i file importati.",
  "sub_e":"Operazioni rapide senza una timeline multitraccia.",
  "menu_file":"File", "menu_options":"Opzioni", "menu_help":"Aiuto", "menu_exit":"Esci",
  "menu_language":"Lingua", "menu_about":"Informazioni su MediaFlow", "menu_support":"❤️ Support me",
  "choose_lang":"Scegli la lingua", "continue":"Continua", "close":"Chiudi",
  "about_body":"MediaFlow è un prototipo dell'interfaccia GiuClab per Windows. Conversione, compressione ed editing non sono ancora implementati. Nessun file viene modificato.\n\nMade with ❤️ by GiuClab",
  "count":"File importati", "invalid":"File non supportati ignorati", "allfiles":"File multimediali",
  "notfound":"Il file selezionato non esiste più.", "drophelp":"Puoi trascinare qui i file da Esplora file.",
 },
 "de": {
  "converter":"Konverter", "compressor":"Kompressor", "editor":"Editor", "settings":"Einstellungen",
  "about":"Info", "add":"Dateien hinzufügen", "remove":"Auswahl entfernen", "clear":"Liste leeren",
  "drop":"Mediendateien hierher ziehen oder Dateien hinzufügen klicken", "empty":"Keine Dateien importiert",
  "files":"Dateien", "output":"Ausgabeeinstellungen", "format":"Ausgabeformat", "quality":"Qualität",
  "codec":"Video-Codec", "resolution":"Auflösung", "preset":"Komprimierungsprofil",
  "tools":"Bearbeitungswerkzeuge", "trim":"Schneiden", "merge":"Zusammenfügen", "rotate":"Drehen",
  "audio":"Audio extrahieren", "destination":"Ausgabeordner", "browse":"Durchsuchen…",
  "not_ready":"Noch nicht implementiert — nur UI-Prototyp", "convert":"Alle konvertieren",
  "compress":"Alle komprimieren", "export":"Exportieren", "preview":"Vorschau in einer späteren Version verfügbar",
  "status":"Prototyp: Dateien werden nicht verändert", "hint":"Die Verarbeitung wird in einer späteren Phase hinzugefügt.",
  "title_c":"Video- und Audiokonvertierung", "title_p":"Medienkomprimierung", "title_e":"Schnelle Medienbearbeitung",
  "sub_c":"Ausgabeformat, Codec und Qualität für importierte Dateien wählen.",
  "sub_p":"Komprimierungsprofil für importierte Dateien wählen.",
  "sub_e":"Schnelle Funktionen ohne Mehrspur-Timeline.",
  "menu_file":"Datei", "menu_options":"Optionen", "menu_help":"Hilfe", "menu_exit":"Beenden",
  "menu_language":"Sprache", "menu_about":"Über MediaFlow", "menu_support":"❤️ Unterstütze mich",
  "choose_lang":"Sprache wählen", "continue":"Weiter", "close":"Schließen",
  "about_body":"MediaFlow ist ein GiuClab-Oberflächenprototyp für Windows. Konvertierung, Komprimierung und Bearbeitung sind noch nicht implementiert. Es werden keine Dateien verändert.\n\nMade with ❤️ by GiuClab",
  "count":"Importierte Dateien", "invalid":"Nicht unterstützte Dateien übersprungen", "allfiles":"Mediendateien",
  "notfound":"Die ausgewählte Datei ist nicht mehr vorhanden.", "drophelp":"Dateien können aus dem Windows-Explorer hier abgelegt werden.",
 },
 "fr": {
  "converter":"Convertisseur", "compressor":"Compresseur", "editor":"Éditeur", "settings":"Paramètres",
  "about":"À propos", "add":"Ajouter des fichiers", "remove":"Retirer la sélection", "clear":"Vider la liste",
  "drop":"Déposez vos fichiers multimédias ici ou cliquez sur Ajouter", "empty":"Aucun fichier importé",
  "files":"Fichiers", "output":"Paramètres de sortie", "format":"Format de sortie", "quality":"Qualité",
  "codec":"Codec vidéo", "resolution":"Résolution", "preset":"Profil de compression",
  "tools":"Outils de modification", "trim":"Couper", "merge":"Fusionner", "rotate":"Pivoter",
  "audio":"Extraire l'audio", "destination":"Dossier de destination", "browse":"Parcourir…",
  "not_ready":"Pas encore disponible — prototype uniquement", "convert":"Tout convertir",
  "compress":"Tout compresser", "export":"Exporter", "preview":"Aperçu disponible dans une version ultérieure",
  "status":"Prototype : aucun fichier ne sera modifié", "hint":"Le moteur de traitement sera ajouté plus tard.",
  "title_c":"Conversion vidéo et audio", "title_p":"Compression multimédia", "title_e":"Édition rapide des médias",
  "sub_c":"Choisissez le format, le codec et la qualité des fichiers importés.",
  "sub_p":"Choisissez un profil de compression pour les fichiers importés.",
  "sub_e":"Opérations rapides sans montage multipiste.",
  "menu_file":"Fichier", "menu_options":"Options", "menu_help":"Aide", "menu_exit":"Quitter",
  "menu_language":"Langue", "menu_about":"À propos de MediaFlow", "menu_support":"❤️ Soutenez-moi",
  "choose_lang":"Choisissez votre langue", "continue":"Continuer", "close":"Fermer",
  "about_body":"MediaFlow est un prototype d'interface GiuClab pour Windows. La conversion, la compression et le montage ne sont pas encore disponibles. Aucun fichier n'est modifié.\n\nMade with ❤️ by GiuClab",
  "count":"Fichiers importés", "invalid":"Fichiers non pris en charge ignorés", "allfiles":"Fichiers multimédias",
  "notfound":"Le fichier sélectionné n'existe plus.", "drophelp":"Vous pouvez déposer des fichiers depuis l'Explorateur Windows.",
 },
}

EXTRA = {
"en": ("Cancel conversion", "Ready", "Converting", "Completed", "Cancelled", "Errors", "Conversion is running. Cancel it before closing.", "FFmpeg and ffprobe must be installed and available on PATH."),
"it": ("Annulla conversione", "Pronto", "Conversione", "Completato", "Annullato", "Errori", "Conversione in corso. Annullala prima di chiudere.", "Installa FFmpeg e ffprobe e aggiungi la cartella bin al PATH."),
"de": ("Konvertierung abbrechen", "Bereit", "Konvertierung", "Abgeschlossen", "Abgebrochen", "Fehler", "Konvertierung läuft. Vor dem Schließen abbrechen.", "FFmpeg und ffprobe installieren und bin zum PATH hinzufügen."),
"fr": ("Annuler la conversion", "Prêt", "Conversion", "Terminé", "Annulé", "Erreurs", "Conversion en cours. Annulez avant de fermer.", "Installez FFmpeg et ffprobe et ajoutez bin au PATH."),
}
EXTRA_KEYS = ("cancel_job", "ready_job", "working_job", "done_job", "cancelled_job", "errors_job", "running_job", "missing_ffmpeg")
for code, phrases in EXTRA.items():
    TEXT[code].update(dict(zip(EXTRA_KEYS, phrases)))


class ConversionThread(QThread):
    started_file = Signal(int, str)
    progressed = Signal(int, float)
    completed_file = Signal(str)
    failed_file = Signal(str)
    completed_batch = Signal(int, int, bool)

    def __init__(self, jobs, parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self.cancel_event = threading.Event()

    def run(self):
        success = errors = 0
        for index, job in enumerate(self.jobs):
            if self.cancel_event.is_set():
                break
            self.started_file.emit(index, job.source.name)
            try:
                path = convert(job, lambda pct, i=index: self.progressed.emit(i, pct), self.cancel_event)
                success += 1
                self.completed_file.emit(str(path))
            except ConversionCancelled:
                break
            except (ConversionError, OSError, ValueError) as exc:
                errors += 1
                self.failed_file.emit(str(exc))
        self.completed_batch.emit(success, errors, self.cancel_event.is_set())

    def cancel(self):
        self.cancel_event.set()

STYLE = """
QMainWindow, QWidget#root { background: #F5F6FB; }
QWidget { font-family: 'Segoe UI', Arial; color: #242936; font-size: 12px; }
QFrame#card, QFrame#sidebar { background: #FFFFFF; border: 1px solid #DFE3ED; border-radius: 12px; }
QFrame#dropzone { background: #F9FAFE; border: 2px dashed #B8C5E5; border-radius: 12px; }
QLabel#title { font-size: 22px; font-weight: 750; }
QLabel#section { font-size: 14px; font-weight: 700; }
QLabel#muted { color: #677082; }
QLabel#logo { color: #385AD0; font-size: 22px; font-weight: 800; }
QPushButton { border: 1px solid #D6DDEC; border-radius: 9px; background: white; padding: 9px 12px; font-weight: 600; }
QPushButton:hover { background: #EDF2FF; border-color: #9EB3E8; }
QPushButton#primary, QPushButton#navSelected { color: white; background: #385AD0; border: none; }
QPushButton#primary:hover, QPushButton#navSelected:hover { background: #2D49AB; }
QPushButton:disabled { background: #E4E8F2; border: 1px solid #D6DDEC; color: #8790A3; }
QPushButton#nav { text-align: left; border: none; padding: 12px; }
QPushButton#navSelected { text-align: left; padding: 12px; }
QListWidget, QComboBox { background: white; border: 1px solid #DFE3ED; border-radius: 8px; padding: 6px; }
QListWidget::item { padding: 9px; }
QListWidget::item:selected { background: #DBE5FF; color: #2445A1; }
"""


def t(lang: str, key: str) -> str:
    return TEXT[lang][key]


def card() -> tuple[QFrame, QVBoxLayout]:
    f = QFrame()
    f.setObjectName("card")
    lay = QVBoxLayout(f)
    lay.setContentsMargins(18, 18, 18, 18)
    lay.setSpacing(12)
    return f, lay


def label(text: str, kind: str = "") -> QLabel:
    w = QLabel(text)
    if kind:
        w.setObjectName(kind)
    w.setWordWrap(True)
    return w


class DropList(QListWidget):
    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DragDropMode.DropOnly)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        self.files_dropped.emit(paths)
        event.acceptProposedAction()


class MediaFlow(QMainWindow):
    def __init__(self, settings: QSettings, language: str) -> None:
        super().__init__()
        self.settings = settings
        self.lang = language
        self.paths: list[Path] = []
        self.output_dir = str((Path.home() / "Videos") if (Path.home() / "Videos").is_dir() else Path.home())
        self.worker = None
        self.controls = {}
        self.go_buttons = []
        self.setWindowTitle(f"MediaFlow v{APP_VERSION} — © 2026 GiuClab")
        self.resize(1150, 760)
        self.setMinimumSize(860, 600)
        self.setStyleSheet(STYLE)
        self.build()

    def build(self) -> None:
        self.menuBar().clear()
        self.controls = {}
        self.go_buttons = []
        self.file_views = []
        file_menu = self.menuBar().addMenu(t(self.lang,"menu_file"))
        file_menu.addAction(t(self.lang,"add"), self.add_dialog)
        file_menu.addSeparator()
        file_menu.addAction(t(self.lang,"menu_exit"), self.close)
        opt_menu = self.menuBar().addMenu(t(self.lang,"menu_options"))
        language_menu = opt_menu.addMenu(t(self.lang,"menu_language"))
        for code, name in LANGS.items():
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(code == self.lang)
            act.triggered.connect(lambda checked=False, code=code: self.set_language(code))
            language_menu.addAction(act)
        help_menu = self.menuBar().addMenu(t(self.lang,"menu_help"))
        help_menu.addAction(t(self.lang,"menu_about"), self.show_about)
        self.menuBar().addAction(t(self.lang,"menu_support"), lambda: __import__("webbrowser").open("https://ko-fi.com/giuclab/tip"))

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outside = QVBoxLayout(root)
        outside.setContentsMargins(14,14,14,8)
        outside.setSpacing(12)
        body = QHBoxLayout()
        body.setSpacing(14)
        outside.addLayout(body,1)

        sidebar, side = card()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(215)
        side.addWidget(label("◉  MediaFlow", "logo"))
        side.addWidget(label("GiuClab", "muted"))
        side.addSpacing(18)
        self.nav = []
        self.stack = QStackedWidget()
        for index, key in enumerate(("converter", "compressor", "editor")):
            btn = QPushButton(t(self.lang,key))
            btn.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            side.addWidget(btn)
            self.nav.append(btn)
            self.stack.addWidget(self.make_page(index))
        side.addStretch()
        settings_btn = QPushButton(t(self.lang,"settings"))
        settings_btn.clicked.connect(self.show_settings)
        side.addWidget(settings_btn)
        about_btn = QPushButton(t(self.lang,"about"))
        about_btn.clicked.connect(self.show_about)
        side.addWidget(about_btn)
        body.addWidget(sidebar)
        body.addWidget(self.stack, 1)
        outside.addWidget(label(f"MediaFlow v{APP_VERSION} — © 2026 GiuClab | Made with ❤️ by GiuClab", "muted"))
        self.navigate(0)
        self.update_file_views()

    def make_page(self, index: int) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(12)
        suffix = ("c","p","e")[index]
        layout.addWidget(label(t(self.lang,"title_"+suffix),"title"))
        layout.addWidget(label(t(self.lang,"sub_"+suffix),"muted"))

        top, tl = card()
        header = QHBoxLayout()
        header.addWidget(label(t(self.lang,"files"),"section"))
        header.addStretch()
        add = QPushButton("+ " + t(self.lang,"add"))
        add.setObjectName("primary")
        add.clicked.connect(self.add_dialog)
        header.addWidget(add)
        remove = QPushButton(t(self.lang,"remove"))
        header.addWidget(remove)
        clear = QPushButton(t(self.lang,"clear"))
        header.addWidget(clear)
        tl.addLayout(header)
        drop = QFrame()
        drop.setObjectName("dropzone")
        dl = QVBoxLayout(drop)
        dl.addWidget(label(t(self.lang,"drop"),"muted"))
        files = DropList()
        files.setMinimumHeight(120)
        files.files_dropped.connect(self.import_files)
        dl.addWidget(files)
        tl.addWidget(drop,1)
        count = label("", "muted")
        tl.addWidget(count)
        self_file_view = files
        remove.clicked.connect(lambda: self.remove_selected(self_file_view))
        clear.clicked.connect(self.clear_files)
        if not hasattr(self,"file_views"):
            self.file_views=[]
        self.file_views.append((files,count))
        layout.addWidget(top, 1)

        settings_card, sl = card()
        sl.addWidget(label(t(self.lang,"tools") if index==2 else t(self.lang,"output"),"section"))
        if index == 0:
            self.make_combo(sl,"format",["MP4", "MKV", "MOV", "WebM", "MP3", "FLAC", "WAV"])
            self.make_combo(sl,"codec",["Auto", "H.264", "H.265 / HEVC", "AV1", "VP9"])
            self.make_combo(sl,"quality",["High", "Balanced", "Small file"])
        elif index == 1:
            self.make_combo(sl,"preset",["Best quality", "Balanced", "Smallest file"])
            self.make_combo(sl,"resolution",["Original", "1080p", "720p", "480p"])
        else:
            sl.addWidget(label(t(self.lang,"preview"),"muted"))
            buttons = QHBoxLayout()
            for key in ("trim", "merge", "rotate", "audio"):
                b=QPushButton(t(self.lang,key))
                b.setEnabled(False)
                b.setToolTip(t(self.lang,"not_ready"))
                buttons.addWidget(b)
            sl.addLayout(buttons)
        layout.addWidget(settings_card)
        footer = QHBoxLayout()
        folder = QLabel(t(self.lang,"destination") + ": " + self.output_dir)
        folder.setObjectName("muted")
        folder.setWordWrap(True)
        footer.addWidget(folder,1)
        browse = QPushButton(t(self.lang,"browse"))
        browse.clicked.connect(lambda: self.pick_output(folder))
        footer.addWidget(browse)
        go = QPushButton(t(self.lang,("convert","compress","export")[index]))
        if index == 0:
            go.setObjectName("primary")
            go.setEnabled(bool(self.paths))
            go.clicked.connect(self.start_conversion)
        else:
            go.setEnabled(False)
            go.setToolTip(t(self.lang,"not_ready"))
        self.go_buttons.append(go)
        footer.addWidget(go)
        layout.addLayout(footer)
        if index == 0:
            self.job_status = label(t(self.lang,"ready_job"), "muted")
            layout.addWidget(self.job_status)
            self.job_progress = QProgressBar()
            self.job_progress.setRange(0, 100)
            layout.addWidget(self.job_progress)
            self.cancel_button = QPushButton(t(self.lang,"cancel_job"))
            self.cancel_button.setEnabled(False)
            self.cancel_button.clicked.connect(self.cancel_conversion)
            layout.addWidget(self.cancel_button)
        layout.addWidget(label(t(self.lang,"hint"),"muted"))
        return page

    def make_combo(self, layout: QVBoxLayout, key: str, values: list[str]) -> None:
        row=QHBoxLayout()
        row.addWidget(label(t(self.lang,key)))
        combo=QComboBox()
        combo.addItems(values)
        if self.stack.count() == 0:
            self.controls[key] = combo
        combo.setMinimumWidth(180)
        row.addWidget(combo)
        layout.addLayout(row)

    def navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav):
            btn.setObjectName("navSelected" if i==index else "nav")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def add_dialog(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self,t(self.lang,"add"),str(Path.home()),"Media files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.wmv *.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma);;All files (*)")
        self.import_files(files)

    def import_files(self, files: list[str]) -> None:
        existing = {str(p).casefold() for p in self.paths}
        rejected=0
        for raw in files:
            p=Path(raw)
            if not p.is_file() or p.suffix.lower() not in EXTENSIONS:
                rejected+=1
                continue
            if str(p).casefold() not in existing:
                self.paths.append(p)
                existing.add(str(p).casefold())
        self.update_file_views()
        if rejected:
            self.statusBar().showMessage(f"{t(self.lang,'invalid')}: {rejected}",6000)

    def update_file_views(self) -> None:
        for view,count in self.file_views:
            view.clear()
            for p in self.paths:
                try:
                    size=f"{p.stat().st_size/(1024*1024):.1f} MB"
                except OSError:
                    size="—"
                view.addItem(f"{p.name}    ·    {p.suffix.upper().lstrip('.')}    ·    {size}")
                view.item(view.count()-1).setToolTip(str(p))
            count.setText(f"{t(self.lang,'count')}: {len(self.paths)}")
        if self.go_buttons:
            self.go_buttons[0].setEnabled(bool(self.paths) and not (self.worker and self.worker.isRunning()))

    def remove_selected(self, view: QListWidget) -> None:
        indexes={i.row() for i in view.selectedIndexes()}
        self.paths=[p for n,p in enumerate(self.paths) if n not in indexes]
        self.update_file_views()

    def clear_files(self) -> None:
        self.paths.clear()
        self.update_file_views()

    def pick_output(self, target: QLabel) -> None:
        folder=QFileDialog.getExistingDirectory(self,t(self.lang,"destination"),self.output_dir)
        if folder:
            self.output_dir=folder
            target.setText(t(self.lang,"destination") + ": " + folder)

    def set_language(self, code: str) -> None:
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "MediaFlow", t(self.lang, "running_job"))
            return
        if code==self.lang:
            return
        self.lang=code
        self.settings.setValue("ui/language",code)
        saved=self.stack.currentIndex()
        self.file_views=[]
        self.build()
        self.navigate(saved)

    def start_conversion(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        if not self.paths:
            return
        try:
            find_binary("ffmpeg")
            find_binary("ffprobe")
        except ConversionError as exc:
            QMessageBox.warning(self, "MediaFlow", t(self.lang, "missing_ffmpeg") + "\n" + str(exc))
            return
        selected = self.controls
        jobs = [Job(p, Path(self.output_dir),
                    selected["format"].currentText().lower(),
                    selected["codec"].currentText(),
                    selected["quality"].currentText()) for p in self.paths]
        self.worker = ConversionThread(jobs, self)
        self.worker.started_file.connect(self.on_started_file)
        self.worker.progressed.connect(self.on_progressed)
        self.worker.completed_file.connect(self.on_completed_file)
        self.worker.failed_file.connect(self.on_failed_file)
        self.worker.completed_batch.connect(self.on_completed_batch)
        self.worker.finished.connect(self.worker.deleteLater)
        self.go_buttons[0].setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.job_progress.setValue(0)
        self.worker.start()

    def on_started_file(self, index, name):
        self.job_status.setText(f"{t(self.lang, 'working_job')} {index+1}/{len(self.worker.jobs)}: {name}")

    def on_progressed(self, index, percent):
        total = len(self.worker.jobs)
        self.job_progress.setValue(round(100 * (index + percent / 100) / total))

    def on_completed_file(self, path):
        self.statusBar().showMessage(path, 12000)

    def on_failed_file(self, error):
        self.statusBar().showMessage(error, 15000)

    def on_completed_batch(self, success, errors, cancelled):
        self.go_buttons[0].setEnabled(bool(self.paths))
        self.cancel_button.setEnabled(False)
        state = "cancelled_job" if cancelled else "done_job"
        self.job_status.setText(f"{t(self.lang, state)}: {success} | {t(self.lang, 'errors_job')}: {errors}")
        if not cancelled and not errors:
            self.job_progress.setValue(100)
        if errors:
            QMessageBox.warning(self, "MediaFlow", self.job_status.text())

    def cancel_conversion(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.cancel_button.setEnabled(False)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "MediaFlow", t(self.lang, "running_job"))
            event.ignore()
        else:
            event.accept()

    def show_settings(self) -> None:
        dlg=QDialog(self)
        dlg.setWindowTitle(t(self.lang,"settings"))
        lay=QVBoxLayout(dlg)
        lay.addWidget(label(t(self.lang,"menu_language")))
        combo=QComboBox()
        for code,name in LANGS.items():
            combo.addItem(name,code)
        combo.setCurrentIndex(list(LANGS).index(self.lang))
        lay.addWidget(combo)
        button=QPushButton(t(self.lang,"continue"))
        button.clicked.connect(dlg.accept)
        lay.addWidget(button)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            self.set_language(combo.currentData())

    def show_about(self) -> None:
        QMessageBox.information(self,t(self.lang,"menu_about"),
                                f"MediaFlow v{APP_VERSION} — © 2026 GiuClab\n\n"+t(self.lang,"about_body"))


def choose_language(settings: QSettings) -> str:
    previous=settings.value("ui/language", "", type=str)
    if previous in LANGS:
        return previous
    dlg=QDialog()
    dlg.setWindowTitle("MediaFlow — Language / Lingua")
    dlg.setMinimumWidth(350)
    lay=QVBoxLayout(dlg)
    lay.addWidget(label("Choose your language / Scegli la lingua", "section"))
    combo=QComboBox()
    for code,name in LANGS.items():
        combo.addItem(name,code)
    lay.addWidget(combo)
    button=QPushButton("Continue / Continua")
    button.setObjectName("primary")
    button.clicked.connect(dlg.accept)
    lay.addWidget(button)
    if dlg.exec()!=QDialog.DialogCode.Accepted:
        return "en"
    selected=combo.currentData()
    settings.setValue("ui/language",selected)
    return selected


def main() -> int:
    app=QApplication(sys.argv)
    app.setApplicationName("MediaFlow")
    app.setOrganizationName("GiuClab")
    app.setStyleSheet(STYLE)
    settings=QSettings("GiuClab","MediaFlow")
    lang=choose_language(settings)
    window=MediaFlow(settings,lang)
    window.show()
    return app.exec()


if __name__=="__main__":
    raise SystemExit(main())
