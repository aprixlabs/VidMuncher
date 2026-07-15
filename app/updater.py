import os
import urllib.request
import zipfile
import tempfile
import threading
import shutil
from app.config import BIN_PATH, YTDLP_PATH, FFMPEG_PATH
from app.utils import debug_print

import sys
import tarfile

if sys.platform == "win32":
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    FFMPEG_EXT = ".zip"
else:
    # Linux
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"
    FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    FFMPEG_EXT = ".tar.xz"

CHUNK_SIZE = 65536  # 64 KB per read chunk

def download_file(url, dest_path, cancel_event=None):
    """Download a file in chunks, respecting cancel_event if provided."""
    req = urllib.request.Request(url, headers={'User-Agent': 'VidMuncher-Updater/1.0'})
    with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
        while True:
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Download cancelled by user.")
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            out_file.write(chunk)

class DependencyUpdater:
    def __init__(self):
        self.is_updating = False
        self._cancel_event = threading.Event()
        self._partial_files = []

    def cancel_update(self):
        """Signal the update thread to stop and clean up partial files."""
        self._cancel_event.set()
        debug_print("Update cancellation requested.")

    def check_updates(self, result_callback):
        """
        Check for updates and return local and remote versions.
        result_callback: function(has_update, local_ver, remote_ver, error_msg)
        """
        def check_thread():
            try:
                import json
                import subprocess

                debug_print("Updater: checking yt-dlp version from GitHub...")
                req = urllib.request.Request(
                    "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
                    headers={'User-Agent': 'VidMuncher-Updater/1.0'}
                )
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    remote_ver = data.get('tag_name', 'Unknown')

                req_ff = urllib.request.Request(
                    "https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/latest",
                    headers={'User-Agent': 'VidMuncher-Updater/1.0'}
                )
                ffmpeg_needs_update = False
                remote_ff_ver = "Unknown"
                local_ff_ver = "Not installed"
                with urllib.request.urlopen(req_ff) as response:
                    ff_data = json.loads(response.read().decode('utf-8'))
                    ff_published = ff_data.get('published_at', '')
                    if ff_published:
                        remote_ff_ver = ff_published[:10]
                    
                if os.path.exists(FFMPEG_PATH):
                    if ff_published:
                        from datetime import datetime, timezone
                        try:
                            dt = datetime.strptime(ff_published, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            remote_time = dt.timestamp()
                            local_time = os.path.getmtime(FFMPEG_PATH)
                            local_ff_ver = datetime.fromtimestamp(local_time).strftime("%Y-%m-%d")
                            if remote_time > local_time + 3600:
                                ffmpeg_needs_update = True
                        except Exception:
                            pass
                else:
                    ffmpeg_needs_update = True

                local_ver = "Not installed"
                if os.path.exists(YTDLP_PATH):
                    try:
                        creationflags = 0x08000000 if os.name == 'nt' else 0
                        result = subprocess.run(
                            [str(YTDLP_PATH), '--version'],
                            capture_output=True, text=True, creationflags=creationflags
                        )
                        local_ver = result.stdout.strip()
                    except:
                        pass

                has_update = (local_ver != remote_ver) or ffmpeg_needs_update
                debug_print(f"Updater: check done — yt-dlp local={local_ver!r} remote={remote_ver!r}, ffmpeg needs_update={ffmpeg_needs_update}")
                result_callback(has_update, local_ver, remote_ver, local_ff_ver, remote_ff_ver, None)
            except Exception as e:
                debug_print(f"Updater: check failed — {e}")
                result_callback(False, "Unknown", "Unknown", "Unknown", "Unknown", str(e))

        threading.Thread(target=check_thread, daemon=True).start()

    def download_updates(self, progress_callback, complete_callback):
        """Download and install yt-dlp and FFmpeg in a background thread."""
        if self.is_updating:
            return

        self.is_updating = True
        self._cancel_event.clear()
        self._partial_files.clear()

        def update_thread():
            try:
                debug_print(f"Updater: starting download — yt-dlp from {YTDLP_URL}")
                os.makedirs(BIN_PATH, exist_ok=True)

                progress_callback("Downloading latest yt-dlp...", 10)
                self._partial_files.append(str(YTDLP_PATH))
                download_file(YTDLP_URL, str(YTDLP_PATH), self._cancel_event)
                self._partial_files.clear()
                progress_callback("yt-dlp updated successfully.", 40)

                progress_callback("Downloading latest FFmpeg...", 50)
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = os.path.join(temp_dir, f"ffmpeg{FFMPEG_EXT}")
                    self._partial_files.append(str(FFMPEG_PATH))
                    download_file(FFMPEG_URL, zip_path, self._cancel_event)

                    progress_callback("Extracting FFmpeg...", 80)
                    
                    if FFMPEG_EXT == ".zip":
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            ffmpeg_exe_path = None
                            for file_info in zip_ref.infolist():
                                if file_info.filename.endswith("bin/ffmpeg.exe"):
                                    ffmpeg_exe_path = file_info.filename
                                    break

                            if ffmpeg_exe_path:
                                with zip_ref.open(ffmpeg_exe_path) as source:
                                    with open(FFMPEG_PATH, "wb") as target:
                                        shutil.copyfileobj(source, target)
                            else:
                                raise Exception("FFmpeg binary not found in the downloaded zip archive.")
                    elif FFMPEG_EXT == ".tar.xz":
                        with tarfile.open(zip_path, "r:xz") as tar_ref:
                            ffmpeg_bin_path = None
                            for member in tar_ref.getmembers():
                                if member.name.endswith("bin/ffmpeg"):
                                    ffmpeg_bin_path = member
                                    break
                            
                            if ffmpeg_bin_path:
                                source = tar_ref.extractfile(ffmpeg_bin_path)
                                with open(FFMPEG_PATH, "wb") as target:
                                    shutil.copyfileobj(source, target)
                            else:
                                raise Exception("ffmpeg not found in the downloaded tar archive.")
                                
                    if sys.platform != "win32":
                        os.chmod(YTDLP_PATH, 0o755)
                        os.chmod(FFMPEG_PATH, 0o755)

                self._partial_files.clear()
                progress_callback("Update complete!", 100)
                debug_print("Updater: all dependencies updated successfully.")
                complete_callback(True, "All dependencies updated successfully!")

            except InterruptedError:
                debug_print("Update cancelled — cleaning up partial files.")
                self._cleanup_partial_files()
                complete_callback(False, "Update cancelled.")
            except Exception as e:
                debug_print(f"Update failed: {str(e)}")
                self._cleanup_partial_files()
                complete_callback(False, f"Update failed: {str(e)}")
            finally:
                self.is_updating = False
                self._partial_files.clear()

        threading.Thread(target=update_thread, daemon=True).start()

    def _cleanup_partial_files(self):
        """Remove any partially downloaded files to prevent corruption."""
        for path in self._partial_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    debug_print(f"Removed partial file: {path}")
            except Exception as e:
                debug_print(f"Failed to remove partial file {path}: {e}")
        self._partial_files.clear()

updater = DependencyUpdater()


class UpdateUIManager:
    """
    Manages all update-related GUI: version check, progress popup, result dialogs.
    Requires PySide6; instantiated per-show to avoid holding stale widget refs.
    """

    def __init__(self, main_gui, update_btn):
        """
        main_gui   : QMainWindow — used as parent for popups and for geometry.
        update_btn : QPushButton — the 'Check for update' button in About dialog.
        """
        self._gui = main_gui
        self._btn = update_btn

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #

    def start_check(self, about_dialog):
        """Begin async version check; called when user clicks the button."""
        from PySide6.QtCore import QObject, Signal

        class _Signaler(QObject):
            sig = Signal(bool, str, str, str, str, str)

        self._btn.setEnabled(False)
        self._btn.setText("Checking for updates...")

        signaler = _Signaler()
        signaler.sig.connect(
            lambda hu, yl, yr, fl, fr, err:
            self._on_check_result(hu, yl, yr, fl, fr, err, about_dialog)
        )
        # Keep reference so GC doesn't collect it
        self._signaler = signaler

        updater.check_updates(
            lambda hu, yl, yr, fl, fr, err: signaler.sig.emit(hu, yl, yr, fl, fr, err)
        )

    # ------------------------------------------------------------------ #
    # Internal handlers
    # ------------------------------------------------------------------ #

    def _reset_btn(self):
        self._btn.setEnabled(True)
        self._btn.setText("Check for update")

    def _on_check_result(self, has_update, yt_local, yt_remote,
                         ff_local, ff_remote, error, about_dialog):
        from app.config import APP_VERSION

        if not about_dialog.isVisible():
            return

        if error:
            self._show_message(
                about_dialog, "Update Check Failed",
                f"The application could not check for updates.\n"
                f"Please verify your network connection and try again.\n\n"
                f"Details: {error}",
                "error"
            )
            self._reset_btn()
            return

        if has_update:
            self._reset_btn()
            yt_text = (f"{yt_local} &rarr; {yt_remote}"
                       if yt_local != yt_remote else f"{yt_local} (Up to date)")
            ff_text = (f"{ff_local} &rarr; {ff_remote}"
                       if ff_local != ff_remote else f"{ff_local} (Up to date)")
            msg = (
                f"<table border='0' cellspacing='0' cellpadding='2' align='center'>"
                f"<tr><td align='right' style='font-weight: 500;'>VidMuncher</td><td width='15'></td><td align='left'>{APP_VERSION}</td></tr>"
                f"<tr><td align='right' style='font-weight: 500;'>yt-dlp</td><td></td><td align='left'>{yt_text}</td></tr>"
                f"<tr><td align='right' style='font-weight: 500;'>FFmpeg</td><td></td><td align='left'>{ff_text}</td></tr>"
                f"</table><br>"
                f"<div align='center'><b>Update now?</b></div>"
            )

            def on_yes():
                self._btn.setEnabled(False)
                self._btn.setText("Downloading updates...")
                self._show_update_progress(about_dialog)

            self._show_message(about_dialog, "Update Available", msg, "ask", on_yes)
        else:
            self._show_message(
                about_dialog, "Up to Date",
                "VidMuncher and all dependencies are on their latest versions.",
                "info"
            )
            self._reset_btn()

    def _show_update_progress(self, about_dialog):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame, QWidget, QPushButton
        from PySide6.QtGui import QFont, QCursor
        from PySide6.QtCore import Qt, QTimer, QObject, Signal
        from app.config import HEADER_BG_COLOR, TEXT_COLOR, BUTTON_COLOR, WINDOW_WIDTH, WINDOW_HEIGHT

        popup = QDialog(self._gui)
        popup.setFixedSize(400, 170)
        popup.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        popup.setAttribute(Qt.WA_TranslucentBackground)
        popup.setStyleSheet("QDialog { background: transparent; }")

        px = self._gui.x() + (WINDOW_WIDTH // 2) - 200
        py = self._gui.y() + (WINDOW_HEIGHT // 2) - 85
        popup.move(px, py)

        main_layout = QVBoxLayout(popup)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_frame = QFrame(popup)
        main_frame.setObjectName("MainFrame")
        main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {HEADER_BG_COLOR};
                border-radius: 10px;
                border: 1px solid #1a000e;
            }}
        """)
        main_layout.addWidget(main_frame)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget(main_frame)
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
            }
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel("Downloading Updates")
        title_lbl.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl.setStyleSheet("color: #cccccc;")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        tb_layout.addWidget(title_lbl, 1)

        close_btn = QPushButton("", title_bar)
        close_btn.setFixedSize(12, 12)
        close_btn.setStyleSheet(
            "QPushButton { border-radius: 6px; background-color: #FF5F56; border: none; }"
            "QPushButton:hover { background-color: #E0443E; }"
        )
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(popup.close)
        tb_layout.addWidget(close_btn)

        def mp(event):
            if event.button() == Qt.LeftButton:
                win = popup.windowHandle()
                if win:
                    win.startSystemMove()
                event.accept()
        title_bar.mousePressEvent = mp
        frame_layout.addWidget(title_bar)

        content = QWidget(main_frame)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 20, 30, 15)
        layout.setSpacing(5)
        frame_layout.addWidget(content)

        title = QLabel("Downloading latest components...")
        title.setFont(QFont("Poppins", 11, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("Please wait while yt-dlp and FFmpeg are being updated.")
        sub.setFont(QFont("Poppins", 9))
        sub.setStyleSheet("color: #cccccc;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)
        layout.addSpacing(12)

        progress = QProgressBar()
        progress.setFixedHeight(18)
        progress.setTextVisible(False)
        progress.setRange(0, 0)
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #1a000e;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {BUTTON_COLOR};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(progress)
        layout.addSpacing(8)

        status_lbl = QLabel("Preparing...")
        status_lbl.setFont(QFont("Poppins", 9))
        status_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_lbl)

        def on_popup_close():
            if updater.is_updating:
                updater.cancel_update()
            self._reset_btn()
            popup.done(0)

        popup.rejected.connect(on_popup_close)

        class UpdaterSignals(QObject):
            progress = Signal(str, int)
            complete = Signal(bool, str)

        signals = UpdaterSignals()

        def on_progress(msg, pct):
            status_lbl.setText(msg)

        def on_complete(success, msg):
            self._reset_btn()
            if success:
                QTimer.singleShot(200, lambda: popup.done(0))
                QTimer.singleShot(
                    250, lambda: self._show_message(about_dialog, "Update Complete", msg, "info")
                )
            else:
                status_lbl.setText(f"Failed: {msg}")

        signals.progress.connect(on_progress)
        signals.complete.connect(on_complete)

        def progress_cb(msg, pct):
            signals.progress.emit(msg, pct)

        def complete_cb(success, msg):
            signals.complete.emit(success, msg)

        updater.download_updates(progress_cb, complete_cb)
        popup.exec()

    def _show_message(self, parent, title, message, msg_type="info", on_yes=None):
        """Frameless rounded message/confirm dialog."""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame
        )
        from PySide6.QtGui import QFont, QCursor
        from PySide6.QtCore import Qt
        from app.config import HEADER_BG_COLOR, TEXT_COLOR, BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR

        dlg = QDialog(parent)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dlg.setAttribute(Qt.WA_TranslucentBackground)
        dlg.setStyleSheet("QDialog { background: transparent; }")

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        main_frame = QFrame(dlg)
        main_frame.setObjectName("MainFrame")
        main_frame.setMinimumWidth(340)
        main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {HEADER_BG_COLOR};
                border-radius: 10px;
                border: 1px solid #1a000e;
            }}
        """)
        main_layout.addWidget(main_frame)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget(main_frame)
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
            }
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl.setStyleSheet("color: #cccccc;")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        tb_layout.addWidget(title_lbl, 1)

        close_btn = QPushButton("", title_bar)
        close_btn.setFixedSize(12, 12)
        close_btn.setStyleSheet(
            "QPushButton { border-radius: 6px; background-color: #FF5F56; border: none; }"
            "QPushButton:hover { background-color: #E0443E; }"
        )
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dlg.reject)
        tb_layout.addWidget(close_btn)

        def mp(event):
            if event.button() == Qt.LeftButton:
                win = dlg.windowHandle()
                if win:
                    win.startSystemMove()
                event.accept()
        title_bar.mousePressEvent = mp
        frame_layout.addWidget(title_bar)

        # Content
        content = QWidget(main_frame)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        frame_layout.addWidget(content)

        msg_lbl = QLabel(message)
        msg_lbl.setFont(QFont("Poppins", 10))
        msg_lbl.setTextFormat(Qt.RichText)
        msg_lbl.setWordWrap(True)
        msg_lbl.setFixedWidth(310)
        layout.addWidget(msg_lbl)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(10)

        _ok_style = f"""
            QPushButton {{
                background-color: {BUTTON_COLOR}; color: {TEXT_COLOR};
                border: none; border-radius: 6px;
                font-family: Poppins; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """
        _cancel_style = f"""
            QPushButton {{
                background-color: {BUTTON_DISABLED_COLOR}; color: {TEXT_COLOR};
                border: none; border-radius: 6px;
                font-family: Poppins; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """

        if msg_type == "ask" and on_yes:
            yes_btn = QPushButton("Yes")
            yes_btn.setFixedSize(90, 35)
            yes_btn.setCursor(QCursor(Qt.PointingHandCursor))
            yes_btn.setStyleSheet(_ok_style)
            yes_btn.clicked.connect(lambda: (dlg.accept(), on_yes()))

            no_btn = QPushButton("No")
            no_btn.setFixedSize(90, 35)
            no_btn.setCursor(QCursor(Qt.PointingHandCursor))
            no_btn.setStyleSheet(_cancel_style)
            no_btn.clicked.connect(dlg.reject)

            btn_row.addWidget(yes_btn)
            btn_row.addWidget(no_btn)
        else:
            ok_btn = QPushButton("OK")
            ok_btn.setFixedSize(90, 35)
            ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
            ok_btn.setStyleSheet(_ok_style)
            ok_btn.clicked.connect(dlg.accept)
            btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)
        dlg.exec()
