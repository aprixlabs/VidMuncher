import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame
)
from PySide6.QtGui import QFont, QPixmap, QCursor
from PySide6.QtCore import Qt

from app.config import (
    APP_NAME, APP_VERSION, HEADER_BG_COLOR, TEXT_COLOR,
    BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR,
    ICON_PNG_PATH, KOFI_LOGO_PATH, SOCIABUZZ_LOGO_PATH,
    WINDOW_WIDTH, WINDOW_HEIGHT
)
from app.gui.dialogs.update import UpdateFlow
from app.utils.debug import debug_print


class AboutDialog:
    """Manages the About dialog and its update check flow."""

    def __init__(self, main_gui):
        self.gui = main_gui


    def show_about_dialog(self):
        parent = self.gui

        # Apply dark overlay to main window
        if hasattr(parent, 'central_widget'):
            overlay = QWidget(parent.central_widget)
            overlay.setGeometry(parent.central_widget.rect())
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
            overlay.show()

        dlg = QDialog(parent)
        parent_geo = parent.geometry()
        x = parent_geo.x() + (parent_geo.width() - 420) // 2
        y = parent_geo.y() + (parent_geo.height() - (480 + 30)) // 2
        dlg.move(x, y)
        dlg.setMinimumSize(420, 480 + 30)
        dlg.setMaximumSize(420, 480 + 30)
        dlg.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dlg.setAttribute(Qt.WA_TranslucentBackground)
        dlg.setStyleSheet("QDialog { background: transparent; }")

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_frame = QFrame(dlg)
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
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-top-left-radius: 9px;
                border-top-right-radius: 9px;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl_tb = QLabel(f"About {APP_NAME}")
        title_lbl_tb.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl_tb.setStyleSheet("color: #cccccc;")
        title_lbl_tb.setAlignment(Qt.AlignCenter)
        title_lbl_tb.setAttribute(Qt.WA_TransparentForMouseEvents)
        title_layout.addWidget(title_lbl_tb, 1)

        close_btn_tb = QPushButton("", title_bar)
        close_btn_tb.setFixedSize(14, 14)
        close_btn_tb.setStyleSheet("QPushButton { border-radius: 7px; background-color: #FF5F56; border: none; } QPushButton:hover { background-color: #E0443E; }")
        close_btn_tb.setCursor(Qt.PointingHandCursor)
        close_btn_tb.clicked.connect(dlg.reject)
        title_layout.addWidget(close_btn_tb)

        def mp(event):
            if event.button() == Qt.LeftButton:
                window = dlg.windowHandle()
                if window:
                    window.startSystemMove()
                event.accept()
        title_bar.mousePressEvent = mp
        frame_layout.addWidget(title_bar)

        content = QWidget(main_frame)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        frame_layout.addWidget(content)

        # App icon
        if ICON_PNG_PATH.exists():
            try:
                icon_lbl = QLabel()
                icon_lbl.setAlignment(Qt.AlignCenter)
                icon_lbl.setStyleSheet("background: transparent;")
                pm = QPixmap(ICON_PNG_PATH.as_posix()).scaled(
                    80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                icon_lbl.setPixmap(pm)
                layout.addSpacing(20)
                layout.addWidget(icon_lbl)
                layout.addSpacing(10)
            except Exception as e:
                debug_print(f"Failed to load about icon: {e}")

        # App title
        title_lbl = QLabel(f"VidMuncher {APP_VERSION}")
        title_lbl.setFont(QFont("Poppins", 14, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setCursor(QCursor(Qt.PointingHandCursor))
        title_lbl.setStyleSheet("background: transparent;")
        title_lbl.mousePressEvent = lambda _: webbrowser.open(
            "https://github.com/aprixlabs/VidMuncher"
        )
        layout.addWidget(title_lbl)

        desc_widget = QWidget()
        desc_widget.setStyleSheet("background: transparent;")
        desc_layout = QVBoxLayout(desc_widget)
        desc_layout.setContentsMargins(20, 5, 20, 0)
        desc_layout.setSpacing(0)

        desc_lbl = QLabel(
            "Download videos and audio from YouTube, Instagram, "
            "TikTok, and many supported platforms."
        )
        desc_lbl.setFont(QFont("Poppins", 9))
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_layout.addWidget(desc_lbl)
        desc_layout.addSpacing(10)

        sites_lbl = QLabel("Supported sites:")
        sites_lbl.setFont(QFont("Poppins", 9))
        sites_lbl.setAlignment(Qt.AlignCenter)
        desc_layout.addWidget(sites_lbl)

        link_lbl = QLabel("yt-dlp Supported Sites")
        link_lbl.setFont(QFont("Poppins", 9))
        link_lbl.setAlignment(Qt.AlignCenter)
        link_lbl.setCursor(QCursor(Qt.PointingHandCursor))
        link_lbl.setStyleSheet("text-decoration: underline;")
        link_lbl.mousePressEvent = lambda _: webbrowser.open(
            "https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md"
        )
        desc_layout.addWidget(link_lbl)
        desc_layout.addSpacing(10)

        # Dependencies notice
        powered_row = QWidget()
        powered_row.setStyleSheet("background: transparent;")
        pr_layout = QHBoxLayout(powered_row)
        pr_layout.setContentsMargins(0, 10, 0, 0)
        pr_layout.setSpacing(0)
        pr_layout.setAlignment(Qt.AlignCenter)

        pw_lbl = QLabel("Powered by ")
        pw_lbl.setFont(QFont("Poppins", 9))
        pr_layout.addWidget(pw_lbl)

        ytdlp_link = QLabel("yt-dlp")
        ytdlp_link.setFont(QFont("Poppins", 9, QFont.Bold))
        ytdlp_link.setCursor(QCursor(Qt.PointingHandCursor))
        ytdlp_link.mousePressEvent = lambda _: webbrowser.open(
            "https://github.com/yt-dlp/yt-dlp"
        )
        pr_layout.addWidget(ytdlp_link)

        and_lbl = QLabel(" and ")
        and_lbl.setFont(QFont("Poppins", 9))
        pr_layout.addWidget(and_lbl)

        ffmpeg_link = QLabel("FFmpeg")
        ffmpeg_link.setFont(QFont("Poppins", 9, QFont.Bold))
        ffmpeg_link.setCursor(QCursor(Qt.PointingHandCursor))
        ffmpeg_link.mousePressEvent = lambda _: webbrowser.open("https://ffmpeg.org")
        pr_layout.addWidget(ffmpeg_link)

        desc_layout.addWidget(powered_row)
        desc_layout.addSpacing(15)

        # Copyright notice
        cr_row = QWidget()
        cr_row.setStyleSheet("background: transparent;")
        cr_layout = QHBoxLayout(cr_row)
        cr_layout.setContentsMargins(0, 0, 0, 0)
        cr_layout.setSpacing(0)
        cr_layout.setAlignment(Qt.AlignCenter)

        cr_lbl = QLabel("Copyright \u00a9 2026 ")
        cr_lbl.setFont(QFont("Poppins", 9))
        cr_layout.addWidget(cr_lbl)

        aprix_link = QLabel("Aprix Labs")
        aprix_link.setFont(QFont("Poppins", 9, QFont.Bold))
        aprix_link.setCursor(QCursor(Qt.PointingHandCursor))
        aprix_link.mousePressEvent = lambda _: webbrowser.open(
            "https://github.com/aprixlabs"
        )
        cr_layout.addWidget(aprix_link)

        desc_layout.addWidget(cr_row)
        layout.addWidget(desc_widget)

        # Support section
        support_title = QLabel("Support Me On")
        support_title.setFont(QFont("Poppins", 11, QFont.Bold))
        support_title.setAlignment(Qt.AlignCenter)
        support_title.setStyleSheet("background: transparent;")
        layout.addSpacing(20)
        layout.addWidget(support_title)
        layout.addSpacing(15)

        logos_row = QWidget()
        logos_row.setStyleSheet("background: transparent;")
        logos_layout = QHBoxLayout(logos_row)
        logos_layout.setContentsMargins(0, 0, 0, 0)
        logos_layout.setSpacing(20)
        logos_layout.setAlignment(Qt.AlignCenter)

        if KOFI_LOGO_PATH.exists():
            try:
                kofi_pm = QPixmap(KOFI_LOGO_PATH.as_posix())
                h = 25
                w = int(kofi_pm.width() * h / kofi_pm.height())
                kofi_pm = kofi_pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                kofi_lbl = QLabel()
                kofi_lbl.setPixmap(kofi_pm)
                kofi_lbl.setCursor(QCursor(Qt.PointingHandCursor))
                kofi_lbl.mousePressEvent = lambda _: webbrowser.open(
                    "https://ko-fi.com/aprixlabs"
                )
                logos_layout.addWidget(kofi_lbl)
            except Exception as e:
                debug_print(f"Failed to load Ko-fi logo: {e}")

        if SOCIABUZZ_LOGO_PATH.exists():
            try:
                socia_pm = QPixmap(SOCIABUZZ_LOGO_PATH.as_posix())
                h = 25
                w = int(socia_pm.width() * h / socia_pm.height())
                socia_pm = socia_pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                socia_lbl = QLabel()
                socia_lbl.setPixmap(socia_pm)
                socia_lbl.setCursor(QCursor(Qt.PointingHandCursor))
                socia_lbl.mousePressEvent = lambda _: webbrowser.open(
                    "https://sociabuzz.com/aprixlabs/support"
                )
                logos_layout.addWidget(socia_lbl)
            except Exception as e:
                debug_print(f"Failed to load Sociabuzz logo: {e}")

        layout.addWidget(logos_row)

        # Update button
        update_btn = QPushButton("Check for update")
        update_btn.setFixedSize(220, 35)
        update_btn.setCursor(QCursor(Qt.PointingHandCursor))
        update_btn.setFont(QFont("Poppins", 10, QFont.Bold))
        update_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
            QPushButton:disabled {{
                background-color: {BUTTON_DISABLED_COLOR};
            }}
        """)

        # Delegate update logic to updater
        update_ui = UpdateFlow(self.gui, update_btn)
        update_btn.clicked.connect(lambda: update_ui.start_check(dlg))

        layout.addSpacing(25)

        btn_wrapper = QWidget()
        btn_wrapper.setStyleSheet("background: transparent;")
        bw_layout = QHBoxLayout(btn_wrapper)
        bw_layout.setContentsMargins(0, 0, 0, 0)
        bw_layout.setAlignment(Qt.AlignCenter)
        bw_layout.addWidget(update_btn)
        layout.addWidget(btn_wrapper)

        layout.addStretch()
        layout.addSpacing(25)

        dlg.exec()

        # Remove overlay when dialog closes
        if hasattr(parent, 'central_widget'):
            overlay.hide()
            overlay.deleteLater()

