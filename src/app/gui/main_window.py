import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QFileDialog, QDialog
from PySide6.QtGui import QFontDatabase, QIcon, QFont, QPixmap, QCursor
from PySide6.QtCore import Qt, QThreadPool, Slot

from app.config import (
    APP_NAME, APP_VERSION, APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_BG_COLOR,
    HEADER_BG_COLOR, TEXT_COLOR, BUTTON_COLOR, BUTTON_ACTIVE_COLOR,
    ICON_PNG_PATH, ICON_PATH, ABOUT_ICON_PATH, HISTORY_ICON_PATH,
    FONT_REGULAR, FONT_MEDIUM, FONT_BOLD, FONT_BLACK, Layout, DEFAULT_DOWNLOAD_PATH
)

from app.utils.filesystem import sanitize_filename, get_extension_from_preset, get_unique_filename
from app.utils.validation import validate_url
from app.gui.workers import AnalysisWorker, DownloadController, ThumbnailController

# Dialogs
from app.gui.dialogs.setup import SetupDialog
from app.gui.dialogs.about import AboutDialog
from app.gui.dialogs.history import HistoryDialog, STATUS_COMPLETED, STATUS_ERROR, STATUS_CANCELLED
from app.gui.dialogs.settings_dialog import SettingsManagerDialog

# Widgets
from app.gui.widgets.titlebar import TitleBar
from app.gui.widgets.progress import ProgressPanel
from app.gui.widgets.queue import QueuePanel
from app.gui.widgets.header import HeaderWidget


class VidMuncherQtGUI(QMainWindow):
    """Main Qt GUI class for VidMuncher application"""

    def __init__(self):
        super().__init__()

        # Set Frameless and Translucent flags immediately at the start of init
        # to ensure the window manager can allocate alpha channels for transparency
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.threadpool = QThreadPool.globalInstance()
        self.download_ctrl = DownloadController(self.threadpool)
        self.analysis_manager = AnalysisWorker(self.threadpool)
        self.thumbnail_ctrl = ThumbnailController(self.threadpool)

        self.analysis_manager.update_progress.connect(self.update_progress)
        self.analysis_manager.analysis_finished.connect(self.on_analysis_finished)
        self.download_ctrl.update_progress.connect(self.update_progress)
        self.download_ctrl.download_finished.connect(self.on_download_finished)
        self.download_ctrl.encode_finished.connect(self.on_encode_finished)
        self.download_ctrl.task_completed.connect(self.complete_task)
        self.download_ctrl.add_history_entry.connect(self.add_history_entry)
        self.thumbnail_ctrl.thumbnail_ready.connect(self.on_thumbnail_ready)

        self.history_manager = HistoryDialog(self)
        self.about_manager = AboutDialog(self)
        self.settings_manager = SettingsManagerDialog(self)

        self.setup_ui()
        self.connect_signals()

    def get_qfont(self, font_tuple):
        family = font_tuple[0]
        size = font_tuple[1]
        weight = QFont.Bold if len(font_tuple) > 2 and "bold" in font_tuple[2] else QFont.Normal
        return QFont(family, size, weight)

    def setup_ui(self):
        self.setWindowTitle(APP_TITLE)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT + 35)

        # Enable native minimize animation on Windows if applicable
        if sys.platform == "win32":
            import ctypes
            hwnd = self.winId()
            hwnd_int = int(hwnd)
            GWL_STYLE = -16
            WS_MINIMIZEBOX = 0x00020000
            user32 = ctypes.windll.user32
            style = user32.GetWindowLongW(hwnd_int, GWL_STYLE)
            user32.SetWindowLongW(hwnd_int, GWL_STYLE, style | WS_MINIMIZEBOX)

        self.setStyleSheet(f"""
            QMainWindow {{ border: none; background-color: transparent; }}
            QWidget {{ color: {TEXT_COLOR}; font-family: 'Poppins'; }}
        """)

        self.setup_fonts()
        self.setup_window_icon()

        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainWidget")
        self.main_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.main_widget.setStyleSheet(f"""
            QWidget#MainWidget {{
                background-color: transparent;
                border-radius: 10px;
                border: none;
            }}
        """)
        self.setCentralWidget(self.main_widget)

        # Set margin to 1 so the 1px rounded border doesn't clip against window bounds
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar widget
        self.title_bar = TitleBar(self.main_widget)
        main_layout.addWidget(self.title_bar)

        self.title_bar.min_btn.clicked.connect(self.minimize_window)
        self.title_bar.close_btn.clicked.connect(self.close)

        self.central_widget = QWidget(self.main_widget)
        self.central_widget.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.central_widget.setAttribute(Qt.WA_StyledBackground, True)
        self.central_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {WINDOW_BG_COLOR};
                border: none;
            }}
        """)
        main_layout.addWidget(self.central_widget)

        # Instantiate panels. Do NOT size them to WINDOW_WIDTH/HEIGHT.
        # Let them be size 0x0. Their children have absolute geometries
        # relative to 0x0, which will land exactly where we want them
        # on the central widget. This avoids invisible overlay issues.
        self.queue_panel = QueuePanel(self.central_widget)
        self.progress_panel = ProgressPanel(self.central_widget)

        self.header_widget = HeaderWidget(self.central_widget)

        self.setup_copyright()

    def setup_fonts(self):
        for font_path in [FONT_REGULAR, FONT_MEDIUM, FONT_BOLD, FONT_BLACK]:
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))

    def setup_window_icon(self):
        icon_path = ICON_PNG_PATH.as_posix() if ICON_PNG_PATH.exists() else str(ICON_PATH)
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))

    def setup_copyright(self):
        self.copyright_label = QLabel(f"Copyright © 2026 - {APP_NAME} by Aprix Labs", self.central_widget)
        font = QFont("Poppins", 9)
        self.copyright_label.setFont(font)
        self.copyright_label.setStyleSheet(f"color: #76485D; background-color: transparent;")
        self.copyright_label.setAlignment(Qt.AlignCenter)
        self.copyright_label.setGeometry(Layout.COPYRIGHT_X - 150, Layout.COPYRIGHT_Y - 10, 300, 20)

    def connect_signals(self):
        self.header_widget.about_clicked.connect(self.show_about_dialog)
        self.header_widget.history_clicked.connect(self.show_history_dialog)
        self.header_widget.settings_clicked.connect(self.show_settings_dialog)

        # Queue panel signals
        self.queue_panel.preset_combo.currentTextChanged.connect(self.on_preset_change)
        self.queue_panel.encoder_combo.currentTextChanged.connect(self.on_encoder_change)
        self.queue_panel.browse_btn.clicked.connect(self.browse_save_path)

        # Progress panel signals
        self.progress_panel.analyze_button.clicked.connect(self.analyze_video)
        self.progress_panel.download_button.clicked.connect(self.download_video)
        self.progress_panel.cancel_button.clicked.connect(self.cancel_task)

        # Apply settings on load
        self.queue_panel.preset_combo.setCurrentText(self.settings_manager.settings_mgr.get("general", "default_preset"))
        self.queue_panel.encoder_combo.setCurrentText(self.settings_manager.settings_mgr.get("general", "default_encoder"))
        self.queue_panel.save_entry.setText(self.settings_manager.settings_mgr.get("general", "download_dir"))

    def minimize_window(self):
        if sys.platform == "win32":
            self.showMinimized()
        else:
            self.setWindowState(self.windowState() | Qt.WindowMinimized)

    def show_about_dialog(self):
        self.about_manager.show_about_dialog()

    def show_history_dialog(self):
        self.history_manager.show_history_dialog()

    def show_settings_dialog(self):
        self.settings_manager.show_dialog()

    @Slot(dict)
    def on_settings_saved(self, new_settings):
        # Update queue panel if user changed defaults and nothing is currently analyzed?
        # For now, just update the default download dir. We don't overwrite user selections mid-session unless needed.
        pass

    @Slot(str, str, str, str, str)
    def add_history_entry(self, title, url, final_path, preset, status):
        self.history_manager.add_entry(title, url, final_path, preset, status)

    def update_progress(self, text, progress=None):
        self.progress_panel.set_progress(text, progress)

    def is_encoding_enabled(self):
        return self.queue_panel.get_encoder() != "Auto"

    @Slot(str)
    def on_preset_change(self, selected):
        self.update_preview_path()

    @Slot(str)
    def on_encoder_change(self, selected):
        self.update_preview_path()

    def update_preview_path(self):
        if 'title' not in self.analysis_manager.video_data:
            return

        title = self.analysis_manager.video_data['title']
        safe_title = sanitize_filename(title)

        known_exts = {".mp4", ".mkv", ".webm", ".avi", ".m4v", ".wav", ".mp3", ".m4a"}
        while True:
            root, ext_part = os.path.splitext(safe_title)
            if ext_part.lower() in known_exts:
                safe_title = root
            else:
                break

        encoding_enabled = self.is_encoding_enabled()
        encoder_selection = self.queue_panel.get_encoder()
        preset = self.queue_panel.get_preset()
        ext = get_extension_from_preset(preset, encoding_enabled, encoder_selection)

        filename_with_ext = f"{safe_title}.{ext}"
        full_path_with_ext = os.path.join(DEFAULT_DOWNLOAD_PATH, filename_with_ext)
        unique_full_path = get_unique_filename(full_path_with_ext)

        self.queue_panel.save_entry.setText(unique_full_path)

    def browse_save_path(self):
        encoding_enabled = self.is_encoding_enabled()
        encoder_selection = self.queue_panel.get_encoder()
        preset = self.queue_panel.get_preset()
        extension = get_extension_from_preset(preset, encoding_enabled, encoder_selection)

        current_path = self.queue_panel.save_entry.text()
        default_name = os.path.splitext(os.path.basename(current_path))[0] if current_path else "video"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Video As",
            f"{default_name}.{extension}",
            f"Media Files (*.{extension})"
        )
        if path:
            if not os.path.splitext(path)[1]:
                path = f"{path}.{extension}"
            self.queue_panel.save_entry.setText(path)

    def analyze_video(self):
        url = self.queue_panel.get_url()
        if not url or url == Layout.URL_PLACEHOLDER.strip():
            return

        is_valid = validate_url(url)
        if not is_valid:
            self.progress_panel.set_error_message("Invalid URL format")
            return

        self.progress_panel.set_button_states(analyze_enabled=False, download_enabled=False)
        self.analysis_manager.analyze_video(url)

    @Slot(bool, object, str)
    def on_analysis_finished(self, success, data, err):
        if success and data:
            formatted_info = self.analysis_manager.format_video_info()
            self.queue_panel.set_video_info(formatted_info)

            thumbnail_url = data.get("thumbnail", "")
            if thumbnail_url:
                self.thumbnail_ctrl.download_thumbnail(thumbnail_url)

            self.update_preview_path()
            self.update_progress("Ready to download", 0)
            self.progress_panel.set_button_states(analyze_enabled=True, download_enabled=True)
        else:
            self.progress_panel.set_error_message(err or "Failed to get video info")
            self.queue_panel.reset_info()
            self.progress_panel.set_button_states(analyze_enabled=True, download_enabled=False)

    @Slot(QPixmap)
    def on_thumbnail_ready(self, pixmap):
        self.queue_panel.set_thumbnail(pixmap)

    def download_video(self):
        url = self.queue_panel.get_url()
        out_path = self.queue_panel.get_save_path()
        preset = self.queue_panel.get_preset()
        title = self.analysis_manager.video_data.get("title", "Unknown Title")
        encoder_selection = self.queue_panel.get_encoder()

        if not url or url == Layout.URL_PLACEHOLDER.strip():
            self.progress_panel.set_error_message("Please enter a valid URL")
            return

        self.progress_panel.set_button_states(analyze_enabled=False, download_enabled=False)
        self.progress_panel.download_button.hide()
        self.progress_panel.cancel_button.show()

        encoding_enabled = self.is_encoding_enabled()
        download_section = self.queue_panel.get_download_section()

        self.download_ctrl.download_video(url, out_path, preset, encoding_enabled, download_section, title, encoder_selection)

    @Slot(bool, str, str)
    def on_download_finished(self, success, final_path, err):
        pass

    @Slot(bool, str, str)
    def on_encode_finished(self, success, final_path, err):
        pass

    def complete_task(self, msg, success):
        self.download_ctrl.is_downloading = False
        self.progress_panel.cancel_button.setEnabled(True)
        self.progress_panel.cancel_button.hide()
        self.progress_panel.download_button.show()
        self.progress_panel.set_button_states(analyze_enabled=True, download_enabled=True)

        if success:
            self.progress_panel.set_progress(msg, 100)
        else:
            self.progress_panel.set_error_message(msg)

    def cancel_task(self):
        self.download_ctrl.cancel_current_task()
        self.analysis_manager.cancel_current_task()
        self.update_progress("Cancelling...")
        self.progress_panel.cancel_button.setEnabled(False)

def run():
    """Bootstrap Qt application"""
    from app.config import YTDLP_PATH, FFMPEG_PATH, BIN_PATH

    app = QApplication(sys.argv)

    if not BIN_PATH.exists():
        BIN_PATH.mkdir(parents=True, exist_ok=True)

    missing = not YTDLP_PATH.exists() or not FFMPEG_PATH.exists()

    if missing:
        dialog = SetupDialog()
        if dialog.exec() != QDialog.Accepted:
            sys.exit(0)

    window = VidMuncherQtGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
