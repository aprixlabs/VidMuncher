from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QStackedWidget, QLineEdit, QComboBox,
    QSpinBox, QCheckBox, QFileDialog, QFormLayout, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor, QColor

from app.config import (
    HEADER_BG_COLOR, WINDOW_BG_COLOR, TEXT_COLOR,
    BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR,
    DOWNLOAD_PRESETS, ENCODER_OPTIONS, DROPDOWN_ARROW_PATH, UP_ARROW_PATH, CHECKMARK_ICON_PATH
)
from app.config.settings import SettingsManager
from app.utils.cookies import get_installed_browsers
from app.utils.debug import debug_print

from app.utils.localization import _

class SidebarButton(QPushButton):
    def __init__(self, text, index, stacked_widget):
        super().__init__(text)
        self.index = index
        self.stacked = stacked_widget
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self.setFont(QFont("Poppins", 10, QFont.Bold))
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left;
                padding-left: 20px;
                color: #8C6A7B;
                background-color: transparent;
                border: none;
                border-radius: 6px;
                margin: 2px 10px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                color: {TEXT_COLOR};
            }}
            QPushButton:checked {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
            }}
        """)
        self.clicked.connect(self.activate)

    def activate(self):
        self.stacked.setCurrentIndex(self.index)

class SettingsDialog(QDialog):
    settings_saved = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_mgr = SettingsManager()
        self.current_settings = self.settings_mgr.get_all()
        self.setup_ui()
        self.load_current_values()

    def setup_ui(self):
        self.setWindowTitle(_("settings.title"))
        self.setFixedSize(650, 480)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(f"""
            QDialog {{ background: transparent; }}
            QMenu {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {BUTTON_COLOR};
                border-radius: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 6px 20px 6px 20px;
                margin: 2px 4px;
                border-radius: 4px;
            }}
            QMenu::icon {{
                padding-left: 10px;
            }}
            QMenu::item:selected {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
            }}
            QMenu::item:disabled {{
                color: #555555;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_frame = QFrame(self)
        main_frame.setObjectName("MainFrame")
        main_frame.setStyleSheet(f"""
            QFrame#MainFrame {{
                background-color: {WINDOW_BG_COLOR};
                border-radius: 10px;
                border: none;
            }}
        """)
        main_layout.addWidget(main_frame)

        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Title Bar
        title_bar = QWidget(main_frame)
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet(f"""
            QWidget {{
                background-color: #2b2b2b;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }}
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel(_("settings.title"))
        title_lbl.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl.setStyleSheet("color: #cccccc;")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_bar_layout.addWidget(title_lbl, 1)

        close_btn = QPushButton("", title_bar)
        close_btn.setFixedSize(14, 14)
        close_btn.setStyleSheet("QPushButton { border-radius: 7px; background-color: #FF5F56; border: none; } QPushButton:hover { background-color: #E0443E; }")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        title_bar_layout.addWidget(close_btn)

        def mp(event):
            if event.button() == Qt.LeftButton:
                window = self.windowHandle()
                if window: window.startSystemMove()
                event.accept()
        title_bar.mousePressEvent = mp
        frame_layout.addWidget(title_bar)

        # Body Layout (Sidebar + Stacked Content)
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(160)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {HEADER_BG_COLOR};
                border-bottom-left-radius: 10px;
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 15, 0, 15)
        sidebar_layout.setSpacing(5)

        # Stacked Widget for Pages
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {WINDOW_BG_COLOR};
                border-bottom-right-radius: 10px;
            }}
        """)

        # Setup Pages
        self.setup_general_tab()
        self.setup_network_tab()
        self.setup_advanced_tab()

        # Sidebar Buttons
        self.btn_general = SidebarButton(_("settings.general_settings").split()[0], 0, self.stacked)
        self.btn_network = SidebarButton(_("settings.network_cookies").split()[0], 1, self.stacked)
        self.btn_advanced = SidebarButton(_("settings.advanced_config").split()[0], 2, self.stacked)

        sidebar_layout.addWidget(self.btn_general)
        sidebar_layout.addWidget(self.btn_network)
        sidebar_layout.addWidget(self.btn_advanced)
        sidebar_layout.addStretch()

        # Button Group Logic
        self.nav_btns = [self.btn_general, self.btn_network, self.btn_advanced]
        for btn in self.nav_btns:
            btn.clicked.connect(lambda checked=False, b=btn: self._update_nav_selection(b))

        self.btn_general.setChecked(True)

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.stacked)
        frame_layout.addWidget(body_widget)

        # Action Buttons Area
        btn_container = QWidget(main_frame)
        btn_container.setFixedHeight(60)
        btn_container.setStyleSheet(f"""
            QWidget {{
                background-color: {WINDOW_BG_COLOR};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
        """)
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(20, 10, 20, 15)
        btn_layout.addStretch()

        self.save_btn = QPushButton(_("buttons.save"))
        self.save_btn.setFixedSize(110, 35)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: Poppins;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        self.save_btn.clicked.connect(self.save_and_close)

        btn_layout.addWidget(self.save_btn)

        # Build stacked content and buttons
        right_side = QWidget()
        right_side.setStyleSheet(f"background-color: {WINDOW_BG_COLOR}; border-bottom-right-radius: 10px;")
        rs_layout = QVBoxLayout(right_side)
        rs_layout.setContentsMargins(0, 0, 0, 0)
        rs_layout.setSpacing(0)
        rs_layout.addWidget(self.stacked)
        rs_layout.addWidget(btn_container)

        body_layout.addWidget(right_side)

    def _update_nav_selection(self, selected_btn):
        for btn in self.nav_btns:
            if btn != selected_btn:
                btn.setChecked(False)
            else:
                btn.setChecked(True)

    def _create_label(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Poppins", 9, QFont.Medium))
        lbl.setStyleSheet(f"color: #D3B9C6; background: transparent;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        return lbl

    def _create_input_style(self):
        return f"""
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 6px;
                padding: 4px 30px 4px 12px;
                font-family: Poppins;
                font-size: 9pt;
                selection-background-color: {BUTTON_COLOR};
                selection-color: {TEXT_COLOR};
            }}
            QLineEdit {{
                padding: 4px 12px;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: none;
                outline: none;
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
            QComboBox QAbstractItemView {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                selection-background-color: {BUTTON_COLOR};
                selection-color: {TEXT_COLOR};
                border: none;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
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
            /* Style scrollbar inside QComboBox dropdown */
            QComboBox QScrollBar:vertical {{
                border: none;
                background-color: {HEADER_BG_COLOR};
                width: 6px;
                margin: 0px 0px 0px 0px;
            }}
            QComboBox QScrollBar::handle:vertical {{
                background-color: {BUTTON_COLOR};
                min-height: 20px;
                border-radius: 3px;
            }}
            QComboBox QScrollBar::add-line:vertical, QComboBox QScrollBar::sub-line:vertical {{
                height: 0px; background: none; border: none;
            }}
            QComboBox QScrollBar::add-page:vertical, QComboBox QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                background-color: {BUTTON_COLOR};
                border-top-right-radius: 6px;
                border: none;
            }}
            QSpinBox::up-arrow {{
                image: url("{UP_ARROW_PATH.as_posix()}");
                width: 10px;
                height: 6px;
            }}
            QSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                background-color: {BUTTON_COLOR};
                border-bottom-right-radius: 6px;
                border: none;
            }}
            QSpinBox::down-arrow {{
                image: url("{DROPDOWN_ARROW_PATH.as_posix()}");
                width: 10px;
                height: 6px;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {HEADER_BG_COLOR};
                width: 6px;
                margin: 0px;
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

    def _create_checkbox_style(self):
        return f"""
            QCheckBox {{
                color: {TEXT_COLOR};
                font-family: 'Poppins';
                font-size: 9pt;
                background: transparent;
                spacing: 12px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                background-color: {HEADER_BG_COLOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {BUTTON_COLOR};
                image: url("{CHECKMARK_ICON_PATH.as_posix()}");
            }}
        """

    def setup_general_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 10)

        header_lbl = QLabel(_("settings.general_settings"))
        header_lbl.setFont(QFont("Poppins", 14, QFont.Bold))
        header_lbl.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(header_lbl)

        layout.addSpacing(20)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form_layout.setVerticalSpacing(25)
        form_layout.setHorizontalSpacing(20)

        # Path input row with browse button
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        path_layout.setSpacing(8)

        self.dir_input = QLineEdit()
        self.dir_input.setStyleSheet(self._create_input_style())
        self.dir_input.setFixedHeight(32)

        browse_btn = QPushButton(_("buttons.browse"))
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setFixedSize(85, 32)
        browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: Poppins;
                font-weight: bold;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        browse_btn.clicked.connect(self.browse_dir)

        path_layout.addWidget(self.dir_input)
        path_layout.addWidget(browse_btn)

        self.preset_combo = QComboBox()
        self.preset_combo.setItemDelegate(QStyledItemDelegate())
        self.preset_combo.addItems(DOWNLOAD_PRESETS)
        self.preset_combo.setStyleSheet(self._create_input_style())
        self.preset_combo.setFixedHeight(32)

        self.enc_combo = QComboBox()
        self.enc_combo.setItemDelegate(QStyledItemDelegate())
        self.enc_combo.addItems(ENCODER_OPTIONS)
        self.enc_combo.setStyleSheet(self._create_input_style())
        self.enc_combo.setFixedHeight(32)

        self.lang_combo = QComboBox()
        self.lang_combo.setItemDelegate(QStyledItemDelegate())

        available_langs = ["English", "Indonesian", "Chinese", "Russian", "Arabic", "German", "Spanish", "French", "Hindi", "Italian", "Japanese", "Polish", "Portuguese", "Turkish"]
        self.lang_combo.addItems(sorted(available_langs))

        self.lang_combo.setStyleSheet(self._create_input_style())
        self.lang_combo.setFixedHeight(32)

        form_layout.addRow(self._create_label(_("app.language")), self.lang_combo)
        form_layout.addRow(self._create_label(_("settings.default_save_path")), path_widget)
        form_layout.addRow(self._create_label(_("settings.default_preset")), self.preset_combo)
        form_layout.addRow(self._create_label(_("settings.default_encoder")), self.enc_combo)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.stacked.addWidget(page)

    def setup_network_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 10)

        header_lbl = QLabel(_("settings.network_cookies"))
        header_lbl.setFont(QFont("Poppins", 14, QFont.Bold))
        header_lbl.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(header_lbl)

        layout.addSpacing(20)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form_layout.setVerticalSpacing(25)
        form_layout.setHorizontalSpacing(20)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setFixedWidth(80)
        self.retry_spin.setFixedHeight(32)
        self.retry_spin.setStyleSheet(self._create_input_style())

        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(0, 1000)
        self.rate_spin.setFixedWidth(80)
        self.rate_spin.setFixedHeight(32)
        self.rate_spin.setStyleSheet(self._create_input_style())

        rate_hint = QLabel(_("settings.unlimited_hint"))
        rate_hint.setFont(QFont("Poppins", 9))
        rate_hint.setStyleSheet("color: #8C6A7B; background: transparent;")

        rate_widget = QWidget()
        rate_layout = QHBoxLayout(rate_widget)
        rate_layout.setContentsMargins(0, 0, 0, 0)
        rate_layout.setSpacing(10)
        rate_layout.addWidget(self.rate_spin)
        rate_layout.addWidget(rate_hint)
        rate_layout.addStretch()

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText(_("settings.proxy_placeholder"))
        self.proxy_input.setStyleSheet(self._create_input_style())
        self.proxy_input.setFixedHeight(32)

        # Cookie Mode Dropdown
        self.cookie_mode_combo = QComboBox()
        self.cookie_mode_combo.setItemDelegate(QStyledItemDelegate())
        self.cookie_mode_combo.addItems([
            _("settings.cookie_mode_none"),
            _("settings.cookie_mode_browser"),
            _("settings.cookie_mode_file")
        ])
        self.cookie_mode_combo.setStyleSheet(self._create_input_style())
        self.cookie_mode_combo.setFixedHeight(32)

        # Stacked widget for cookie settings (Browser vs File)
        self.cookie_stack = QStackedWidget()
        self.cookie_stack.setFixedHeight(32)

        # 1. Empty Page (None)
        empty_page = QWidget()
        self.cookie_stack.addWidget(empty_page)

        # 2. Browser Page
        browser_page = QWidget()
        browser_layout = QHBoxLayout(browser_page)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(12)

        self.browser_combo = QComboBox()
        self.browser_combo.setItemDelegate(QStyledItemDelegate())
        detected_browsers = get_installed_browsers()
        if not detected_browsers:
            detected_browsers = ["chrome"]
        self.browser_combo.addItems(detected_browsers)
        self.browser_combo.setMaxVisibleItems(4)
        self.browser_combo.setStyleSheet(self._create_input_style())
        self.browser_combo.setFixedWidth(130)
        self.browser_combo.setFixedHeight(32)

        browser_layout.addWidget(self.browser_combo)
        browser_layout.addStretch()
        self.cookie_stack.addWidget(browser_page)

        # 3. File Page
        file_page = QWidget()
        file_layout = QHBoxLayout(file_page)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_layout.setSpacing(8)

        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setPlaceholderText(_("settings.cookies_file_placeholder"))
        self.cookie_file_input.setStyleSheet(self._create_input_style())
        self.cookie_file_input.setFixedHeight(32)

        cookie_browse_btn = QPushButton(_("buttons.browse"))
        cookie_browse_btn.setFixedSize(85, 32)
        cookie_browse_btn.setCursor(Qt.PointingHandCursor)
        cookie_browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white; border: none; border-radius: 6px;
                font-family: Poppins; font-weight: bold; font-size: 9pt;
            }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """)
        cookie_browse_btn.clicked.connect(self.browse_cookie_txt)

        cookie_help_btn = QPushButton("?")
        cookie_help_btn.setFixedSize(24, 24)
        cookie_help_btn.setCursor(Qt.PointingHandCursor)
        cookie_help_btn.setToolTip(_("settings.cookie_help_tooltip"))
        cookie_help_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white; border: none; border-radius: 12px;
                font-family: Poppins; font-weight: bold; font-size: 10pt;
            }}
            QPushButton:hover {{ background-color: {BUTTON_ACTIVE_COLOR}; }}
        """)
        def open_cookie_help():
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            QDesktopServices.openUrl(QUrl("https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"))
        cookie_help_btn.clicked.connect(open_cookie_help)

        file_layout.addWidget(self.cookie_file_input)
        file_layout.addWidget(cookie_browse_btn)
        file_layout.addWidget(cookie_help_btn)
        self.cookie_stack.addWidget(file_page)

        self.cookie_mode_combo.currentIndexChanged.connect(self.cookie_stack.setCurrentIndex)

        self.cookie_source_label = self._create_label(_("settings.cookies_source"))

        form_layout.addRow(self._create_label(_("settings.max_retries")), self.retry_spin)
        form_layout.addRow(self._create_label(_("settings.rate_limit")), rate_widget)
        form_layout.addRow(self._create_label(_("settings.proxy_config")), self.proxy_input)
        form_layout.addRow(self._create_label(_("settings.cookies_mode")), self.cookie_mode_combo)
        form_layout.addRow(self.cookie_source_label, self.cookie_stack)

        def toggle_cookie_source_row(index):
            show_source = (index != 0)
            self.cookie_source_label.setVisible(show_source)
            self.cookie_stack.setVisible(show_source)

        self.cookie_mode_combo.currentIndexChanged.connect(toggle_cookie_source_row)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.stacked.addWidget(page)

    def setup_advanced_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 10)

        header_lbl = QLabel(_("settings.advanced_config"))
        header_lbl.setFont(QFont("Poppins", 14, QFont.Bold))
        header_lbl.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(header_lbl)

        layout.addSpacing(20)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form_layout.setVerticalSpacing(25)
        form_layout.setHorizontalSpacing(20)

        # FFmpeg override
        ff_widget = QWidget()
        ff_layout = QHBoxLayout(ff_widget)
        ff_layout.setContentsMargins(0, 0, 0, 0)
        ff_layout.setSpacing(8)

        self.ff_input = QLineEdit()
        self.ff_input.setPlaceholderText(_("settings.leave_empty"))
        self.ff_input.setStyleSheet(self._create_input_style())
        self.ff_input.setFixedHeight(32)

        ff_btn = QPushButton(_("buttons.browse"))
        ff_btn.setFixedSize(85, 32)
        ff_btn.setCursor(Qt.PointingHandCursor)
        ff_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: Poppins;
                font-weight: bold;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        ff_btn.clicked.connect(lambda: self.browse_exe(self.ff_input))

        ff_layout.addWidget(self.ff_input)
        ff_layout.addWidget(ff_btn)

        # yt-dlp override
        yt_widget = QWidget()
        yt_layout = QHBoxLayout(yt_widget)
        yt_layout.setContentsMargins(0, 0, 0, 0)
        yt_layout.setSpacing(8)

        self.yt_input = QLineEdit()
        self.yt_input.setPlaceholderText(_("settings.leave_empty"))
        self.yt_input.setStyleSheet(self._create_input_style())
        self.yt_input.setFixedHeight(32)

        yt_btn = QPushButton(_("buttons.browse"))
        yt_btn.setFixedSize(85, 32)
        yt_btn.setCursor(Qt.PointingHandCursor)
        yt_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: Poppins;
                font-weight: bold;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        yt_btn.clicked.connect(lambda: self.browse_exe(self.yt_input))

        yt_layout.addWidget(self.yt_input)
        yt_layout.addWidget(yt_btn)

        # Deno override
        deno_widget = QWidget()
        deno_layout = QHBoxLayout(deno_widget)
        deno_layout.setContentsMargins(0, 0, 0, 0)
        deno_layout.setSpacing(8)

        self.deno_input = QLineEdit()
        self.deno_input.setPlaceholderText(_("settings.leave_empty"))
        self.deno_input.setStyleSheet(self._create_input_style())
        self.deno_input.setFixedHeight(32)

        deno_btn = QPushButton(_("buttons.browse"))
        deno_btn.setFixedSize(85, 32)
        deno_btn.setCursor(Qt.PointingHandCursor)
        deno_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
                font-family: Poppins;
                font-weight: bold;
                font-size: 9pt;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        deno_btn.clicked.connect(lambda: self.browse_exe(self.deno_input))

        deno_layout.addWidget(self.deno_input)
        deno_layout.addWidget(deno_btn)

        self.debug_check = QCheckBox(_("settings.enable_logs"))
        self.debug_check.setStyleSheet(self._create_checkbox_style())

        form_layout.addRow(self._create_label(_("settings.ytdlp_path")), yt_widget)
        form_layout.addRow(self._create_label(_("settings.ffmpeg_path")), ff_widget)
        form_layout.addRow(self._create_label(_("settings.deno_path")), deno_widget)
        form_layout.addRow(self._create_label(_("settings.debug_mode")), self.debug_check)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.stacked.addWidget(page)

    def browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.dir_input.text())
        if path:
            self.dir_input.setText(path)

    def browse_exe(self, line_edit):
        import sys
        if sys.platform == "win32":
            filter_str = "Executables (*.exe);;All Files (*)"
        else:
            filter_str = "All Files (*)"

        path, _ = QFileDialog.getOpenFileName(self, "Select Executable", "", filter_str)
        if path:
            line_edit.setText(path)

    def browse_cookie_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Cookie File", "", "Text Files (*.txt);;All Files (*)")
        if path:
            self.cookie_file_input.setText(path)

    def load_current_values(self):
        gen = self.current_settings["general"]
        self.dir_input.setText(gen["download_dir"])
        self.preset_combo.setCurrentText(gen["default_preset"])
        self.enc_combo.setCurrentText(gen["default_encoder"])

        lang_map = {
            "en": "English", "id": "Indonesian", "zh": "Chinese", "ru": "Russian",
            "ar": "Arabic", "de": "German", "es": "Spanish", "fr": "French",
            "hi": "Hindi", "it": "Italian", "ja": "Japanese", "pl": "Polish",
            "pt": "Portuguese", "tr": "Turkish"
        }
        current_lang = gen.get("language", "en")
        self.lang_combo.setCurrentText(lang_map.get(current_lang, "English"))

        # Sync labels to language selection
        labels = self.preset_combo.parentWidget().findChildren(QLabel)
        if len(labels) > 3:
            labels[1].setText(_("app.language"))
            labels[2].setText(_("settings.default_save_path"))
            labels[3].setText(_("settings.default_preset"))
            labels[4].setText(_("settings.default_encoder"))

        net = self.current_settings["network"]
        self.retry_spin.setValue(net["extractor_retries"])
        self.rate_spin.setValue(net["rate_limit_mbps"])
        self.proxy_input.setText(net["proxy"])

        mode = net.get("cookie_mode", "none")
        mode_index = 0
        if mode == "browser":
            mode_index = 1
        elif mode == "file":
            mode_index = 2

        self.cookie_mode_combo.setCurrentIndex(mode_index)
        self.cookie_stack.setCurrentIndex(mode_index)

        # Explicitly hide/show on load
        show_source = (mode_index != 0)
        self.cookie_source_label.setVisible(show_source)
        self.cookie_stack.setVisible(show_source)

        self.browser_combo.setCurrentText(net["browser_cookies"])
        self.cookie_file_input.setText(net.get("cookie_file", ""))

        adv = self.current_settings["advanced"]
        self.ff_input.setText(adv["ffmpeg_path"])
        self.yt_input.setText(adv["ytdlp_path"])
        self.deno_input.setText(adv.get("deno_path", ""))
        self.debug_check.setChecked(adv["debug_mode"])

    def save_and_close(self):
        mode_text = "none"
        idx = self.cookie_mode_combo.currentIndex()
        if idx == 1:
            mode_text = "browser"
        elif idx == 2:
            mode_text = "file"

        lang_reverse_map = {
            "English": "en", "Indonesian": "id", "Chinese": "zh", "Russian": "ru",
            "Arabic": "ar", "German": "de", "Spanish": "es", "French": "fr",
            "Hindi": "hi", "Italian": "it", "Japanese": "ja", "Polish": "pl",
            "Portuguese": "pt", "Turkish": "tr"
        }
        selected_lang = lang_reverse_map.get(self.lang_combo.currentText(), "en")

        new_settings = {
            "general": {
                "download_dir": self.dir_input.text(),
                "default_preset": self.preset_combo.currentText(),
                "default_encoder": self.enc_combo.currentText(),
                "theme": "Dark",
                "language": selected_lang
            },
            "network": {
                "extractor_retries": self.retry_spin.value(),
                "fragment_retries": self.retry_spin.value(),
                "concurrent_downloads": 1,
                "rate_limit_mbps": self.rate_spin.value(),
                "proxy": self.proxy_input.text(),
                "cookie_mode": mode_text,
                "browser_cookies": self.browser_combo.currentText(),
                "cookie_file": self.cookie_file_input.text()
            },
            "advanced": {
                "ffmpeg_path": self.ff_input.text(),
                "ytdlp_path": self.yt_input.text(),
                "deno_path": self.deno_input.text(),
                "debug_mode": self.debug_check.isChecked()
            }
        }

        debug_print(f"Settings saved: {new_settings}")

        self.settings_mgr.update_all(new_settings)
        from app.utils.localization import LocalizationManager
        LocalizationManager.load_language(selected_lang)
        self.settings_saved.emit(new_settings)
        self.accept()

class SettingsManagerDialog:
    """Wrapper to handle overlay and dialog execution"""
    def __init__(self, main_gui):
        self.gui = main_gui
        self.settings_mgr = SettingsManager()

    def show_dialog(self):
        overlay = QWidget(self.gui.main_widget)
        overlay.setGeometry(self.gui.main_widget.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
        overlay.show()

        dlg = SettingsDialog(self.gui)

        parent_geo = self.gui.geometry()
        x = parent_geo.x() + (parent_geo.width() - dlg.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - dlg.height()) // 2
        dlg.move(x, y)

        dlg.settings_saved.connect(self.gui.on_settings_saved)

        dlg.exec()

        overlay.hide()
        overlay.deleteLater()
