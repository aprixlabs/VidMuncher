"""
SetupDialog — First-time dependency download dialog.
Shown at startup when yt-dlp or FFmpeg binaries are missing.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QWidget, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QObject

from app.config import HEADER_BG_COLOR, BUTTON_COLOR


from app.utils.localization import _

class _SetupSignals(QObject):
    check_finished   = Signal(bool, str, str, str, str, str)
    progress         = Signal(str, int)
    download_finished = Signal(bool, str)


class SetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 110 + 30)
        self.setMaximumSize(320, 110 + 30)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("QDialog { background: transparent; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_frame = QFrame(self)
        main_frame.setObjectName("MainFrame")
        main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {HEADER_BG_COLOR};
                border-radius: 10px;
                
            }}
        """)
        main_layout.addWidget(main_frame)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        title_bar = QWidget(main_frame)
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl_tb = QLabel(_("setup.first_time_setup"))
        title_lbl_tb.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl_tb.setStyleSheet("color: #cccccc;")
        title_lbl_tb.setAlignment(Qt.AlignCenter)
        title_lbl_tb.setAttribute(Qt.WA_TransparentForMouseEvents)
        title_layout.addWidget(title_lbl_tb, 1)

        close_btn_tb = QPushButton("", title_bar)
        close_btn_tb.setFixedSize(12, 12)
        close_btn_tb.setStyleSheet(
            "QPushButton { border-radius: 6px; background-color: #FF5F56; border: none; }"
            "QPushButton:hover { background-color: #E0443E; }"
        )
        close_btn_tb.setCursor(Qt.PointingHandCursor)
        close_btn_tb.clicked.connect(self.reject)
        title_layout.addWidget(close_btn_tb)

        def mp(event):
            if event.button() == Qt.LeftButton:
                win = self.windowHandle()
                if win:
                    win.startSystemMove()
                event.accept()
        title_bar.mousePressEvent = mp
        frame_layout.addWidget(title_bar)

        content = QWidget(main_frame)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        frame_layout.addWidget(content)

        self.title_label = QLabel(_("setup.downloading_dependencies"))
        self.title_label.setFont(QFont("Poppins", 10, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #1a000e;
                height: 12px;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {BUTTON_COLOR};
                border-radius: 4px;
            }}
        """)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel(_("setup.checking_requirements"))
        self.status_label.setFont(QFont("Poppins", 8))
        self.status_label.setStyleSheet("color: #cccccc;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self._signals = _SetupSignals()
        self._signals.check_finished.connect(self.on_check_finished)
        self._signals.progress.connect(self.on_progress)
        self._signals.download_finished.connect(self.on_download_finished)

        QTimer.singleShot(100, self.start_check)

    def start_check(self):
        from app.core.updater import updater
        self.updater = updater
        # Updater callback sends 8 args now:
        # has_update, yt_local, yt_remote, ff_local, ff_remote, deno_local, deno_remote, err
        self.updater.check_updates(
            lambda hu, yl, yr, fl, fr, dl, dr, e:
            self._signals.check_finished.emit(hu, yl, yr, fl, fr, e or "")
        )

    @Slot(bool, str, str, str, str, str)
    def on_check_finished(self, has_update, yt_local, yt_remote, ff_local, ff_remote, error):
        import os
        from app.config import YTDLP_PATH, FFMPEG_PATH, DENO_PATH

        missing_binaries = not os.path.exists(YTDLP_PATH) or not os.path.exists(FFMPEG_PATH) or not os.path.exists(DENO_PATH)

        if has_update or missing_binaries:
            self.status_label.setText("Fetching components...")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

            # If we hit API rate limit but binaries are missing, force download bypass
            if missing_binaries and error:
                self.updater._pending_updates['ytdlp'] = True
                self.updater._pending_updates['ffmpeg'] = True
                self.updater._pending_updates['deno'] = True

            self.updater.download_updates(
                lambda msg, pct: self._signals.progress.emit(msg, pct),
                lambda succ, msg: self._signals.download_finished.emit(succ, msg)
            )
        else:
            self.accept()

    @Slot(str, int)
    def on_progress(self, msg, pct):
        if msg:
            self.status_label.setText(msg)
        if pct is not None:
            self.progress_bar.setValue(pct)

    @Slot(bool, str)
    def on_download_finished(self, success, msg):
        import os
        from app.config import YTDLP_PATH, FFMPEG_PATH, DENO_PATH

        missing_binaries = not os.path.exists(YTDLP_PATH) or not os.path.exists(FFMPEG_PATH) or not os.path.exists(DENO_PATH)

        if success and not missing_binaries:
            self.status_label.setText("Setup complete!")
            self.progress_bar.setValue(100)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText("Setup failed. Please check internet connection.")
            self.status_label.setStyleSheet("color: #FF5F56;")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, self.reject)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'updater') and self.updater.is_updating:
                self.updater.cancel_update()
        except Exception:
            pass
        event.accept()
