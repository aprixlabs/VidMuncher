from app.core.updater import updater

from app.utils.localization import _

class UpdateFlow:
    """
    Update GUI manager: version check, progress popup, result dialogs.
    Needs PySide6. Create per-show to drop old widget refs.
    """

    def __init__(self, main_gui, update_btn):
        """
        main_gui   : QMainWindow — popups parent, geometry source.
        update_btn : QPushButton — 'Check for update' button.
        """
        self._gui = main_gui
        self._btn = update_btn

    # Public entry point

    def start_check(self, about_dialog):
        """Start async version check."""
        from PySide6.QtCore import QObject, Signal, QTimer

        class _Signaler(QObject):
            sig = Signal(bool, str, str, str, str, str, str, str, str, str)

        self._btn.setEnabled(False)
        self._btn.setText(_("about.checking_updates"))

        # Setup dots animation
        self._dots_count = 0
        self._base_text = _("about.checking_updates").rstrip('.')

        self._anim_timer = QTimer(self._btn)
        self._anim_timer.setInterval(400)
        self._anim_timer.timeout.connect(self._animate_dots)
        self._anim_timer.start()

        signaler = _Signaler()
        signaler.sig.connect(
            lambda hu, al, ar, yl, yr, fl, fr, dl, dr, err:
            self._on_check_result(hu, al, ar, yl, yr, fl, fr, dl, dr, err, about_dialog)
        )
        # Keep ref to prevent GC
        self._signaler = signaler

        updater.check_updates(
            lambda hu, al, ar, yl, yr, fl, fr, dl, dr, err: signaler.sig.emit(hu, al, ar, yl, yr, fl, fr, dl, dr, err)
        )

    # Internal handlers

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "." * self._dots_count
        self._btn.setText(f"{self._base_text}{dots}")

    def _reset_btn(self):
        if hasattr(self, '_anim_timer'):
            self._anim_timer.stop()
            self._anim_timer.deleteLater()
            del self._anim_timer

        self._btn.setEnabled(True)
        self._btn.setText(_("about.check_update"))

    def _on_check_result(self, has_update, app_local, app_remote, yt_local, yt_remote,
                         ff_local, ff_remote, deno_local, deno_remote, error, about_dialog):
        from app.config import APP_VERSION

        if not about_dialog.isVisible():
            return

        if error:
            self._show_message(
                about_dialog, _("about.update_check_failed"),
                _("about.update_check_failed_msg").format(error),
                "error"
            )
            self._reset_btn()
            return

        if has_update:
            self._reset_btn()
            app_text = (f"{app_local} &rarr; {app_remote}"
                        if app_local != app_remote and app_remote != "Unknown" else f"{app_local} ({_('about.up_to_date')})")
            yt_text = (f"{yt_local} &rarr; {yt_remote}"
                       if yt_local != yt_remote else f"{yt_local} ({_('about.up_to_date')})")
            ff_text = (f"{ff_local} &rarr; {ff_remote}"
                       if ff_local != ff_remote else f"{ff_local} ({_('about.up_to_date')})")
            deno_text = (f"{deno_local} &rarr; {deno_remote}"
                         if deno_local != deno_remote else f"{deno_local} ({_('about.up_to_date')})")
            msg = (
                f"<table border='0' cellspacing='0' cellpadding='2' align='center'>"
                f"<tr><td align='right' style='font-weight: 500;'>VidMuncher</td><td width='15'></td><td align='left'>{app_text}</td></tr>"
                f"<tr><td align='right' style='font-weight: 500;'>yt-dlp</td><td></td><td align='left'>{yt_text}</td></tr>"
                f"<tr><td align='right' style='font-weight: 500;'>FFmpeg</td><td></td><td align='left'>{ff_text}</td></tr>"
                f"<tr><td align='right' style='font-weight: 500;'>Deno</td><td></td><td align='left'>{deno_text}</td></tr>"
                f"</table>"
            )

            def on_yes():
                self._btn.setEnabled(False)
                if app_local != app_remote and app_remote != "Unknown":
                    # App update available -> Open releases page in browser
                    import webbrowser
                    webbrowser.open("https://github.com/aprixlabs/VidMuncher/releases/latest")
                    self._reset_btn()
                else:
                    # Component updates available -> Download in background
                    self._btn.setText(_("about.downloading_updates"))
                    self._show_update_progress(about_dialog)

            self._show_message(about_dialog, _("about.update_available"), msg, "ask", on_yes, ask_text=_('about.update_now'))
        else:
            self._show_message(
                about_dialog, _("about.up_to_date"),
                _("about.up_to_date_msg"),
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

        title_lbl = QLabel(_("setup.downloading_dependencies"))
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

        title = QLabel(_("setup.downloading_latest"))
        title.setFont(QFont("Poppins", 10, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        sub = QLabel(_("setup.wait_update"))
        sub.setFont(QFont("Poppins", 8))
        sub.setStyleSheet("color: #cccccc;")
        sub.setAlignment(Qt.AlignCenter)
        sub.hide() # We hide this to match the SetupDialog style which only has one title label

        layout.addSpacing(5)

        progress = QProgressBar()
        progress.setFixedHeight(12)
        progress.setTextVisible(False)
        progress.setRange(0, 100)
        progress.setValue(0)
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

        status_lbl = QLabel(_("setup.preparing"))
        status_lbl.setFont(QFont("Poppins", 8))
        status_lbl.setStyleSheet("color: #cccccc;")
        status_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_lbl)

        def on_popup_close():
            if updater.is_updating:
                updater.cancel_update()
            self._reset_btn()

        popup.rejected.connect(on_popup_close)

        class UpdaterSignals(QObject):
            progress = Signal(str, int)
            complete = Signal(bool, str)

        signals = UpdaterSignals()

        def on_progress(msg, pct):
            if msg:
                status_lbl.setText(msg)
            if pct is not None:
                progress.setValue(pct)

        def on_complete(success, msg):
            self._reset_btn()
            if success:
                QTimer.singleShot(200, lambda: popup.done(0))
                QTimer.singleShot(
                    250, lambda: self._show_message(about_dialog, _("about.update_complete"), msg, "info")
                )
            else:
                status_lbl.setText(f"{_('setup.update_fail_prefix')}{msg}")

        signals.progress.connect(on_progress)
        signals.complete.connect(on_complete)

        def progress_cb(msg, pct):
            signals.progress.emit(msg, pct)

        def complete_cb(success, msg):
            signals.complete.emit(success, msg)

        updater.download_updates(progress_cb, complete_cb)
        popup.exec()

    def _show_message(self, parent, title, message, msg_type="info", on_yes=None, ask_text=None):
        """Frameless rounded dialog."""
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame
        )
        from PySide6.QtGui import QFont, QCursor
        from PySide6.QtCore import Qt
        from app.config import HEADER_BG_COLOR, TEXT_COLOR, BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR

        # Apply dark overlay to parent (About dialog)
        if hasattr(parent, 'findChild'):
            about_frame = parent.findChild(QFrame, "MainFrame")
            if about_frame:
                overlay = QWidget(about_frame)
                overlay.setGeometry(about_frame.rect())
                overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
                overlay.show()
            else:
                overlay = QWidget(parent)
                overlay.setGeometry(parent.rect())
                overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
                overlay.show()
        else:
            overlay = QWidget(parent)
            overlay.setGeometry(parent.rect())
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
            overlay.show()

        dlg = QDialog(parent)
        # Center the dialog on top of the parent window
        parent_geo = parent.geometry()
        x = parent_geo.x() + (parent_geo.width() - 340) // 2
        y = parent_geo.y() + (parent_geo.height() - 200) // 2
        dlg.move(x, y)
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

        # Center the text unless it's the "Update Available" table which handles its own alignment
        if msg_type != "ask":
            msg_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(msg_lbl)
        layout.addStretch()

        if msg_type == "ask" and ask_text:
            ask_lbl = QLabel(f"<b>{ask_text}</b>")
            ask_lbl.setFont(QFont("Poppins", 10))
            ask_lbl.setStyleSheet(f"color: {TEXT_COLOR};")
            ask_lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(ask_lbl)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(10)

        _ok_style = f"""
            QPushButton {{
                background-color: {BUTTON_COLOR}; color: {TEXT_COLOR};
                border: none; border-radius: 6px;
                font-family: Poppins; font-weight: bold; font-size: 10pt;
            }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """
        _cancel_style = f"""
            QPushButton {{
                background-color: {BUTTON_DISABLED_COLOR}; color: {TEXT_COLOR};
                border: none; border-radius: 6px;
                font-family: Poppins; font-weight: bold; font-size: 10pt;
            }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """

        if msg_type == "ask" and on_yes:
            yes_btn = QPushButton(_("buttons.yes"))
            yes_btn.setFixedSize(90, 26)
            yes_btn.setCursor(QCursor(Qt.PointingHandCursor))
            yes_btn.setStyleSheet(_ok_style)
            yes_btn.clicked.connect(lambda: (dlg.accept(), on_yes()))

            no_btn = QPushButton(_("buttons.no"))
            no_btn.setFixedSize(90, 26)
            no_btn.setCursor(QCursor(Qt.PointingHandCursor))
            no_btn.setStyleSheet(_cancel_style)
            no_btn.clicked.connect(dlg.reject)

            btn_row.addWidget(yes_btn)
            btn_row.addWidget(no_btn)
        else:
            ok_btn = QPushButton(_("buttons.ok"))
            ok_btn.setFixedSize(90, 26)
            ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
            ok_btn.setStyleSheet(_ok_style)
            ok_btn.clicked.connect(dlg.accept)
            btn_row.addWidget(ok_btn)

        layout.addLayout(btn_row)
        dlg.exec()

        # Remove overlay after dialog is closed
        overlay.hide()
        overlay.deleteLater()
