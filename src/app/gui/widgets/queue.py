from PySide6.QtWidgets import (QWidget, QLabel, QLineEdit, QTextEdit, QComboBox,
                               QCheckBox, QTimeEdit, QStyledItemDelegate, QPushButton, QFrame)
from PySide6.QtGui import QFont, QCursor, QPixmap
from PySide6.QtCore import Qt, QTime

from app.config import (Layout, Fonts, HEADER_BG_COLOR, TEXT_COLOR, PLACEHOLDER_COLOR,
                        BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR,
                        DROPDOWN_ARROW_PATH, UP_ARROW_PATH, CHECKMARK_ICON_PATH,
                        DOWNLOAD_PRESETS, ENCODER_OPTIONS)

from app.utils.localization import _

class QueuePanel:
    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        self.setup_ui()

    def get_qfont(self, font_tuple):
        family = font_tuple[0]
        size = font_tuple[1]
        weight = QFont.Bold if len(font_tuple) > 2 and "bold" in font_tuple[2] else QFont.Normal
        return QFont(family, size, weight)

    def setup_ui(self):
        default_font = self.get_qfont(Fonts.DEFAULT)
        small_font = self.get_qfont(Fonts.SMALL)
        combo_font = self.get_qfont(Fonts.COMBO)
        bold_font = self.get_qfont(Fonts.BOLD)

        # URL Input
        self.url_entry = QLineEdit(self.parent_widget)
        self.url_entry.setFont(default_font)
        self.url_entry.setPlaceholderText(_("main_ui.url_placeholder"))
        self.url_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                padding-left: 10px;
                border-radius: 6px;
                selection-background-color: {BUTTON_COLOR};
                selection-color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{
                border: none;
                outline: none;
            }}
        """)
        self.url_entry.setGeometry(Layout.URL_ENTRY_X, Layout.URL_ENTRY_Y,
                                   Layout.URL_ENTRY_WIDTH, Layout.URL_ENTRY_HEIGHT)

        # Video Info
        self.video_info_frame = QWidget(self.parent_widget)
        self.video_info_frame.setAttribute(Qt.WA_StyledBackground, True)
        self.video_info_frame.setGeometry(Layout.VIDEO_INFO_X, Layout.VIDEO_INFO_Y,
                                          Layout.VIDEO_INFO_WIDTH, Layout.VIDEO_INFO_HEIGHT)
        self.video_info_frame.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; border-radius: 6px;")

        self.video_info_placeholder = QLabel(_("main_ui.video_info_placeholder"), self.video_info_frame)
        self.video_info_placeholder.setFont(small_font)
        self.video_info_placeholder.setStyleSheet(f"color: {PLACEHOLDER_COLOR}; background-color: transparent;")
        self.video_info_placeholder.setAlignment(Qt.AlignCenter)
        self.video_info_placeholder.setGeometry(0, 0, Layout.VIDEO_INFO_WIDTH, Layout.VIDEO_INFO_HEIGHT)

        self.video_info = QTextEdit(self.video_info_frame)
        self.video_info.setFont(small_font)
        self.video_info.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.video_info.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.video_info.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent; border: none; padding: 5px; selection-background-color: {BUTTON_COLOR}; selection-color: {TEXT_COLOR};")
        self.video_info.setReadOnly(True)
        self.video_info.setGeometry(0, 0, Layout.VIDEO_INFO_WIDTH, Layout.VIDEO_INFO_HEIGHT)
        self.video_info.hide()

        # Thumbnail
        self.thumbnail_frame = QWidget(self.parent_widget)
        self.thumbnail_frame.setAttribute(Qt.WA_StyledBackground, True)
        self.thumbnail_frame.setGeometry(Layout.THUMBNAIL_X, Layout.THUMBNAIL_Y,
                                         Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)
        self.thumbnail_frame.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; border-radius: 6px;")

        self.thumbnail_placeholder = QLabel(_("main_ui.thumbnail"), self.thumbnail_frame)
        self.thumbnail_placeholder.setFont(small_font)
        self.thumbnail_placeholder.setStyleSheet(f"color: {PLACEHOLDER_COLOR}; background-color: transparent;")
        self.thumbnail_placeholder.setAlignment(Qt.AlignCenter)
        self.thumbnail_placeholder.setGeometry(0, 0, Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)

        self.thumbnail_label = QLabel(self.thumbnail_frame)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setGeometry(0, 0, Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)
        self.thumbnail_label.hide()

        combo_style = f"""
            QComboBox {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                padding-left: 10px;
                padding-bottom: 2px;
                border-radius: 6px;
            }}
            QComboBox::drop-down {{
                background-color: {BUTTON_COLOR};
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                width: 30px;
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url("{DROPDOWN_ARROW_PATH.as_posix()}");
                width: 12px;
                height: 8px;
            }}
            QComboBox:focus {{
                outline: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                selection-background-color: {BUTTON_COLOR};
                selection-color: {TEXT_COLOR};
                border: 1px solid {BUTTON_COLOR};
                border-radius: 6px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                border: none;
                padding: 4px 10px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
                border: none;
                outline: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {HEADER_BG_COLOR};
                width: 6px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BUTTON_COLOR};
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px; background: none; border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """

        # Preset
        self.preset_label = QLabel(_("main_ui.select_preset"), self.parent_widget)
        self.preset_label.setFont(default_font)
        self.preset_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.preset_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.preset_label.setGeometry(Layout.PRESET_LABEL_X, Layout.PRESET_LABEL_Y, 100, Layout.PRESET_COMBO_HEIGHT)

        self.preset_combo = QComboBox(self.parent_widget)
        self.preset_combo.setItemDelegate(QStyledItemDelegate())
        self.preset_combo.addItems(DOWNLOAD_PRESETS)
        self.preset_combo.setFont(combo_font)
        self.preset_combo.setStyleSheet(combo_style)
        self.preset_combo.setGeometry(Layout.PRESET_COMBO_X, Layout.PRESET_COMBO_Y,
                                      Layout.PRESET_COMBO_WIDTH, Layout.PRESET_COMBO_HEIGHT)

        # Encoder
        self.reencode_label = QLabel(_("main_ui.codec"), self.parent_widget)
        self.reencode_label.setFont(default_font)
        self.reencode_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.reencode_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.reencode_label.setGeometry(Layout.REENCODE_LABEL_X, Layout.REENCODE_LABEL_Y, 50, Layout.REENCODE_COMBO_HEIGHT)

        self.encoder_combo = QComboBox(self.parent_widget)
        self.encoder_combo.setItemDelegate(QStyledItemDelegate())
        self.encoder_combo.addItems(ENCODER_OPTIONS)
        self.encoder_combo.setFont(combo_font)
        self.encoder_combo.setStyleSheet(combo_style)
        self.encoder_combo.setGeometry(Layout.REENCODE_COMBO_X, Layout.REENCODE_COMBO_Y,
                                       Layout.REENCODE_COMBO_WIDTH, Layout.REENCODE_COMBO_HEIGHT)

        # Section Download
        self.section_checkbox = QCheckBox(_("main_ui.download_section"), self.parent_widget)
        self.section_checkbox.setFont(default_font)
        self.section_checkbox.setStyleSheet(f"""
            QCheckBox {{ color: {TEXT_COLOR}; background-color: transparent; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px; border-radius: 4px; background-color: {HEADER_BG_COLOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {BUTTON_COLOR};
                image: url("{CHECKMARK_ICON_PATH.as_posix()}");
            }}
        """)
        self.section_checkbox.setGeometry(Layout.SECTION_CB_X, Layout.SECTION_CB_Y, 150, 30)

        time_style = f"""
            QTimeEdit {{
                background-color: {HEADER_BG_COLOR}; color: {TEXT_COLOR};
                border: none; border-radius: 6px; padding-left: 5px;
                selection-background-color: {BUTTON_COLOR}; selection-color: {TEXT_COLOR};
            }}
            QTimeEdit::up-button, QTimeEdit::down-button {{
                background-color: {BUTTON_COLOR}; width: 16px; border: none;
            }}
            QTimeEdit::up-button {{ border-top-right-radius: 6px; margin-bottom: 1px; }}
            QTimeEdit::down-button {{ border-bottom-right-radius: 6px; }}
            QTimeEdit::up-arrow {{ width: 6px; height: 6px; image: url("{UP_ARROW_PATH.as_posix()}"); }}
            QTimeEdit::down-arrow {{ width: 6px; height: 6px; image: url("{DROPDOWN_ARROW_PATH.as_posix()}"); }}
        """

        self.start_time_edit = QTimeEdit(self.parent_widget)
        self.start_time_edit.setDisplayFormat("HH:mm:ss")
        self.start_time_edit.setTime(QTime(0, 0, 0))
        self.start_time_edit.setSelectedSection(QTimeEdit.SecondSection)
        self.start_time_edit.setFont(combo_font)
        self.start_time_edit.setStyleSheet(time_style)
        self.start_time_edit.setGeometry(Layout.SECTION_START_X, Layout.SECTION_START_Y, 100, 30)
        self.start_time_edit.setEnabled(False)

        self.time_separator = QLabel("-", self.parent_widget)
        self.time_separator.setFont(default_font)
        self.time_separator.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.time_separator.setAlignment(Qt.AlignCenter)
        self.time_separator.setGeometry(Layout.SECTION_START_X + 100, Layout.SECTION_START_Y, 25, 30)

        self.end_time_edit = QTimeEdit(self.parent_widget)
        self.end_time_edit.setDisplayFormat("HH:mm:ss")
        self.end_time_edit.setTime(QTime(0, 0, 0))
        self.end_time_edit.setSelectedSection(QTimeEdit.SecondSection)
        self.end_time_edit.setFont(combo_font)
        self.end_time_edit.setStyleSheet(time_style)
        self.end_time_edit.setGeometry(Layout.SECTION_END_X, Layout.SECTION_END_Y, 100, 30)
        self.end_time_edit.setEnabled(False)

        # Save Location
        self.save_label = QLabel(_("main_ui.save_location"), self.parent_widget)
        self.save_label.setFont(default_font)
        self.save_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.save_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.save_label.setGeometry(Layout.SAVE_LABEL_X, Layout.SAVE_LABEL_Y, 100, Layout.SAVE_ENTRY_HEIGHT)

        self.save_entry = QLineEdit(self.parent_widget)
        self.save_entry.setFont(small_font)
        self.save_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HEADER_BG_COLOR}; color: {TEXT_COLOR};
                border: none; padding-left: 5px; border-radius: 6px;
                selection-background-color: {BUTTON_COLOR}; selection-color: {TEXT_COLOR};
            }}
        """)
        self.save_entry.setGeometry(Layout.SAVE_ENTRY_X, Layout.SAVE_ENTRY_Y,
                                    Layout.SAVE_ENTRY_WIDTH, Layout.SAVE_ENTRY_HEIGHT)

        self.browse_btn = QPushButton(_("buttons.browse"), self.parent_widget)
        self.browse_btn.setFont(bold_font)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {BUTTON_COLOR}; color: white; border: none; border-radius: 6px; }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """)
        self.browse_btn.setGeometry(Layout.BROWSE_BUTTON_X, Layout.BROWSE_BUTTON_Y,
                                    Layout.BROWSE_BUTTON_WIDTH, Layout.BROWSE_BUTTON_HEIGHT)

        # Connections
        self.section_checkbox.stateChanged.connect(self._on_section_toggled)
        self.preset_combo.currentTextChanged.connect(self._on_preset_change)

    def _on_section_toggled(self, state):
        is_checked = state == Qt.Checked.value
        self.start_time_edit.setEnabled(is_checked)
        self.end_time_edit.setEnabled(is_checked)

    def _on_preset_change(self, selected):
        if "Audio" in selected:
            self.encoder_combo.setCurrentText("Auto")
            self.encoder_combo.setEnabled(False)
        else:
            self.encoder_combo.setEnabled(True)

    def set_video_info(self, html_info):
        self.video_info_placeholder.hide()
        self.video_info.show()
        self.video_info.setHtml(html_info)

    def set_thumbnail(self, pixmap):
        self.thumbnail_placeholder.hide()
        self.thumbnail_label.show()
        self.thumbnail_label.setPixmap(pixmap)

    def reset_info(self):
        self.video_info.hide()
        self.video_info_placeholder.show()
        self.thumbnail_label.hide()
        self.thumbnail_label.setPixmap(QPixmap())
        self.thumbnail_placeholder.show()

    def get_url(self):
        return self.url_entry.text().strip()

    def get_preset(self):
        return self.preset_combo.currentText()

    def get_encoder(self):
        return self.encoder_combo.currentText()

    def get_save_path(self):
        return self.save_entry.text()

    def get_download_section(self):
        if self.section_checkbox.isChecked():
            start_time = self.start_time_edit.text()
            end_time = self.end_time_edit.text()
            return f"*{start_time}-{end_time}"
        return None
