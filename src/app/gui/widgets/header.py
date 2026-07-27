from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtGui import QFont, QPixmap, QIcon, Qt
from PySide6.QtCore import Signal

from app.config import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, HEADER_BG_COLOR,
    TEXT_COLOR, BUTTON_COLOR, BUTTON_ACTIVE_COLOR,
    ICON_PNG_PATH, ABOUT_ICON_PATH, HISTORY_ICON_PATH, SETTINGS_ICON_PATH, Layout
)

class HeaderWidget(QWidget):
    """Header widget containing app title, logo, and top buttons."""

    about_clicked = Signal()
    history_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(0, 0, WINDOW_WIDTH, Layout.HEADER_HEIGHT)
        self.setStyleSheet(f"background-color: {HEADER_BG_COLOR};")
        self.setup_ui()

    def setup_ui(self):
        # QWidget doesn't support direct background-color via stylesheet without this flag
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {HEADER_BG_COLOR};")

        if ICON_PNG_PATH.exists():
            self.header_icon_label = QLabel(self)
            pixmap = QPixmap(ICON_PNG_PATH.as_posix()).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.header_icon_label.setPixmap(pixmap)
            self.header_icon_label.setGeometry(Layout.HEADER_IMAGE_X, 15, 50, 50)
            self.header_icon_label.setStyleSheet("background-color: transparent; border: none;")

        self.title_container = QWidget(self)
        self.title_container.setGeometry(Layout.HEADER_IMAGE_X + 64, 18, 500, 35)
        self.title_container.setStyleSheet("background: transparent;")

        title_layout = QHBoxLayout(self.title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        self.title_label = QLabel(APP_NAME)
        self.title_label.setFont(QFont("Poppins", 24, QFont.Black))
        self.title_label.setStyleSheet("color: #ffdcee;")
        self.title_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        # Avoid title_label expanding and pushing everything else
        self.title_label.setSizePolicy(self.title_label.sizePolicy().Policy.Maximum, self.title_label.sizePolicy().Policy.Preferred)

        self.version_label = QLabel(APP_VERSION)
        self.version_label.setFont(QFont("Poppins", 8, QFont.Bold))
        self.version_label.setStyleSheet("color: #ffdcee;")
        self.version_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        self.version_label.setContentsMargins(2, 0, 0, 7)
        self.version_label.setSizePolicy(self.version_label.sizePolicy().Policy.Maximum, self.version_label.sizePolicy().Policy.Preferred)

        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.version_label)
        title_layout.addStretch()

        self.subtitle_label = QLabel("Video Downloader", self)
        self.subtitle_label.setFont(QFont("Poppins", 12, QFont.Medium))
        self.subtitle_label.setStyleSheet("color: #ffdcee; background-color: transparent;")
        self.subtitle_label.setGeometry(Layout.HEADER_IMAGE_X + 66, 46, 150, 20)

        btn_style = f"""
            QPushButton {{ background-color: {BUTTON_COLOR}; color: {TEXT_COLOR}; border: none; border-radius: 6px; padding: 5px; }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """

        self.about_btn = QPushButton("", self)
        self.about_btn.setIcon(QIcon(ABOUT_ICON_PATH.as_posix()))
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.setStyleSheet(btn_style)
        self.about_btn.setGeometry(Layout.ABOUT_BUTTON_X, Layout.ABOUT_BUTTON_Y,
                                   Layout.ABOUT_BUTTON_WIDTH, Layout.ABOUT_BUTTON_HEIGHT)
        self.about_btn.clicked.connect(self.about_clicked.emit)

        self.history_btn = QPushButton("", self)
        self.history_btn.setIcon(QIcon(HISTORY_ICON_PATH.as_posix()))
        self.history_btn.setCursor(Qt.PointingHandCursor)
        self.history_btn.setStyleSheet(btn_style)
        self.history_btn.setGeometry(Layout.HISTORY_BUTTON_X, Layout.HISTORY_BUTTON_Y,
                                     Layout.HISTORY_BUTTON_WIDTH, Layout.HISTORY_BUTTON_HEIGHT)
        self.history_btn.clicked.connect(self.history_clicked.emit)

        self.settings_btn = QPushButton("", self)
        self.settings_btn.setIcon(QIcon(SETTINGS_ICON_PATH.as_posix()))
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.setStyleSheet(btn_style)
        self.settings_btn.setGeometry(Layout.SETTINGS_BUTTON_X, Layout.SETTINGS_BUTTON_Y,
                                     Layout.SETTINGS_BUTTON_WIDTH, Layout.SETTINGS_BUTTON_HEIGHT)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
