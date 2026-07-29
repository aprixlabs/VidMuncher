from PySide6.QtWidgets import QLabel, QPushButton, QWidget
from PySide6.QtGui import QFont, QCursor
from PySide6.QtCore import Qt

from app.config.ui_layout import Layout, BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR, HEADER_BG_COLOR, TEXT_COLOR

from app.utils.localization import _

class ProgressPanel:
    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.setup_ui()

    def get_qfont(self, font_tuple):
        family = font_tuple[0]
        size = font_tuple[1]
        weight = QFont.Bold if len(font_tuple) > 2 and "bold" in font_tuple[2] else QFont.Normal
        return QFont(family, size, weight)

    def setup_ui(self):
        bold_font = self.get_qfont(("Poppins", 10, "bold"))
        small_font = self.get_qfont(("Poppins", 9))

        btn_style = f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
            QPushButton:disabled {{
                background-color: {BUTTON_DISABLED_COLOR};
                color: rgba(239, 239, 239, 100);
            }}
        """

        self.analyze_button = QPushButton(_("buttons.analyze"), self.parent_widget)
        self.analyze_button.setFont(bold_font)
        self.analyze_button.setCursor(Qt.PointingHandCursor)
        self.analyze_button.setStyleSheet(btn_style)
        self.analyze_button.setGeometry(Layout.ANALYZE_BUTTON_X, Layout.ANALYZE_BUTTON_Y,
                                        Layout.ANALYZE_BUTTON_WIDTH, Layout.ANALYZE_BUTTON_HEIGHT)

        self.download_button = QPushButton(_("buttons.download"), self.parent_widget)
        self.download_button.setFont(bold_font)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.setStyleSheet(btn_style)
        self.download_button.setGeometry(Layout.DOWNLOAD_BUTTON_X, Layout.DOWNLOAD_BUTTON_Y,
                                         Layout.DOWNLOAD_BUTTON_WIDTH, Layout.DOWNLOAD_BUTTON_HEIGHT)
        self.download_button.setEnabled(False)

        self.cancel_button = QPushButton(_("buttons.cancel"), self.parent_widget)
        self.cancel_button.setFont(bold_font)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet(btn_style)
        self.cancel_button.setGeometry(Layout.CANCEL_BUTTON_X, Layout.CANCEL_BUTTON_Y,
                                       Layout.CANCEL_BUTTON_WIDTH, Layout.CANCEL_BUTTON_HEIGHT)
        self.cancel_button.hide()

        self.progress_frame = QWidget(self.parent_widget)
        self.progress_frame.setAttribute(Qt.WA_StyledBackground, True)
        self.progress_frame.setGeometry(Layout.PROGRESS_X, Layout.PROGRESS_Y,
                                        Layout.PROGRESS_WIDTH, Layout.PROGRESS_HEIGHT)
        self.progress_frame.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; border-radius: 6px;")

        self.progress_fill = QWidget(self.progress_frame)
        self.progress_fill.setAttribute(Qt.WA_StyledBackground, True)
        self.progress_fill.setGeometry(0, 0, 0, Layout.PROGRESS_HEIGHT)
        self.progress_fill.setStyleSheet(f"background-color: {BUTTON_COLOR}; border-radius: 6px;")

        self.progress_text = QLabel("", self.progress_frame)
        self.progress_text.setFont(small_font)
        self.progress_text.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setGeometry(0, 0, Layout.PROGRESS_WIDTH, Layout.PROGRESS_HEIGHT)

    def set_progress(self, text, progress_percent=None):
        self.progress_text.setText(text)
        current_style = self.progress_text.styleSheet()
        expected_style = f"color: {TEXT_COLOR}; background-color: transparent;"
        if current_style != expected_style:
            self.progress_text.setStyleSheet(expected_style)

        if progress_percent is not None:
            progress_percent = max(0, min(100, progress_percent))
            fill_width = int(Layout.PROGRESS_WIDTH * (progress_percent / 100.0))
            self.progress_fill.setGeometry(0, 0, fill_width, Layout.PROGRESS_HEIGHT)

    def set_error_message(self, text):
        self.progress_text.setText(text)
        self.progress_text.setStyleSheet("color: #FF5050; background-color: transparent;")
        self.progress_fill.setGeometry(0, 0, 0, Layout.PROGRESS_HEIGHT)

    def set_button_states(self, analyze_enabled=True, download_enabled=False):
        self.analyze_button.setEnabled(analyze_enabled)
        self.download_button.setEnabled(download_enabled)
