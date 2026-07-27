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
        self.setWindowTitle("Settings")
        self.setFixedSize(650, 480)
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

        title_lbl = QLabel("Settings")
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
        self.btn_general = SidebarButton("General", 0, self.stacked)
        self.btn_network = SidebarButton("Network", 1, self.stacked)
        self.btn_advanced = SidebarButton("Advanced", 2, self.stacked)

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

        self.save_btn = QPushButton("Save")
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

        # We need to overlay the button container on top of the bottom edge of body
        # Since it's currently a VBox, it will just sit at the bottom.
        # But wait, QStackedWidget has no background color by default if not styled,
        # but we styled it. Let's just put the buttons at the bottom of the stacked widget area,
        # or globally at the bottom of main layout.

        # Actually, let's just make the btn_container sit across the bottom of the stacked widget,
        # or the whole window. The current code puts it in the main frame_layout.
        # But sidebar has bottom-left radius. If btn_container spans the whole width, it covers sidebar.
        # So we should put btn_container inside the right side (stacked side) only.

        # Let's adjust layout structure:
        # body_layout = HBox [ sidebar, right_side_vbox ]
        # right_side_vbox = VBox [ stacked, btn_container ]

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
                padding: 4px 12px;
                font-family: Poppins;
                font-size: 9pt;
                selection-background-color: {BUTTON_COLOR};
                selection-color: {TEXT_COLOR};
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
                padding: 6px 10px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
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
                font-family: Poppins;
                font-size: 9pt;
                background: transparent;
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

        header_lbl = QLabel("General Settings")
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

        browse_btn = QPushButton("Browse")
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

        form_layout.addRow(self._create_label("Download Location"), path_widget)
        form_layout.addRow(self._create_label("Default Preset"), self.preset_combo)
        form_layout.addRow(self._create_label("Default Encoder"), self.enc_combo)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.stacked.addWidget(page)

    def setup_network_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 10)

        header_lbl = QLabel("Network & Cookies")
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

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("e.g. socks5://127.0.0.1:1080")
        self.proxy_input.setStyleSheet(self._create_input_style())
        self.proxy_input.setFixedHeight(32)

        # Cookie row
        cookie_widget = QWidget()
        cookie_layout = QHBoxLayout(cookie_widget)
        cookie_layout.setContentsMargins(0, 0, 0, 0)
        cookie_layout.setSpacing(12)

        self.cookie_check = QCheckBox("Extract from:")
        self.cookie_check.setStyleSheet(self._create_checkbox_style())

        self.browser_combo = QComboBox()
        self.browser_combo.setItemDelegate(QStyledItemDelegate())
        self.browser_combo.addItems(["chrome", "firefox", "edge", "opera", "brave", "safari"])
        self.browser_combo.setStyleSheet(self._create_input_style())
        self.browser_combo.setFixedWidth(110)
        self.browser_combo.setFixedHeight(32)

        cookie_layout.addWidget(self.cookie_check)
        cookie_layout.addWidget(self.browser_combo)
        cookie_layout.addStretch()

        self.cookie_check.toggled.connect(self.browser_combo.setEnabled)

        form_layout.addRow(self._create_label("Max Retries"), self.retry_spin)
        form_layout.addRow(self._create_label("Rate Limit (MB/s)"), self.rate_spin)
        form_layout.addRow(self._create_label("Proxy Config"), self.proxy_input)
        form_layout.addRow(self._create_label("Cookies"), cookie_widget)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.stacked.addWidget(page)

    def setup_advanced_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 10)

        header_lbl = QLabel("Advanced Config")
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
        self.ff_input.setPlaceholderText("Leave empty to use bundled")
        self.ff_input.setStyleSheet(self._create_input_style())
        self.ff_input.setFixedHeight(32)

        ff_btn = QPushButton("Browse")
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
        self.yt_input.setPlaceholderText("Leave empty to use bundled")
        self.yt_input.setStyleSheet(self._create_input_style())
        self.yt_input.setFixedHeight(32)

        yt_btn = QPushButton("Browse")
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

        self.debug_check = QCheckBox("Enable Console Logs")
        self.debug_check.setStyleSheet(self._create_checkbox_style())

        form_layout.addRow(self._create_label("FFmpeg Path"), ff_widget)
        form_layout.addRow(self._create_label("yt-dlp Path"), yt_widget)
        form_layout.addRow(self._create_label("Debug Mode"), self.debug_check)

        layout.addLayout(form_layout)
        layout.addStretch()
        self.stacked.addWidget(page)

    def browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.dir_input.text())
        if path:
            self.dir_input.setText(path)

    def browse_exe(self, line_edit):
        path, _ = QFileDialog.getOpenFileName(self, "Select Executable", "", "Executables (*.exe);;All Files (*)")
        if path:
            line_edit.setText(path)

    def load_current_values(self):
        gen = self.current_settings["general"]
        self.dir_input.setText(gen["download_dir"])
        self.preset_combo.setCurrentText(gen["default_preset"])
        self.enc_combo.setCurrentText(gen["default_encoder"])

        net = self.current_settings["network"]
        self.retry_spin.setValue(net["extractor_retries"])
        self.rate_spin.setValue(net["rate_limit_mbps"])
        self.proxy_input.setText(net["proxy"])
        self.cookie_check.setChecked(net["use_cookies"])
        self.browser_combo.setCurrentText(net["browser_cookies"])
        self.browser_combo.setEnabled(net["use_cookies"])

        adv = self.current_settings["advanced"]
        self.ff_input.setText(adv["ffmpeg_path"])
        self.yt_input.setText(adv["ytdlp_path"])
        self.debug_check.setChecked(adv["debug_mode"])

    def save_and_close(self):
        new_settings = {
            "general": {
                "download_dir": self.dir_input.text(),
                "default_preset": self.preset_combo.currentText(),
                "default_encoder": self.enc_combo.currentText(),
                "theme": "Dark",
                "language": "English"
            },
            "network": {
                "extractor_retries": self.retry_spin.value(),
                "fragment_retries": self.retry_spin.value(),
                "concurrent_downloads": 1,
                "rate_limit_mbps": self.rate_spin.value(),
                "proxy": self.proxy_input.text(),
                "use_cookies": self.cookie_check.isChecked(),
                "browser_cookies": self.browser_combo.currentText()
            },
            "advanced": {
                "ffmpeg_path": self.ff_input.text(),
                "ytdlp_path": self.yt_input.text(),
                "debug_mode": self.debug_check.isChecked()
            }
        }

        self.settings_mgr.update_all(new_settings)
        self.settings_saved.emit(new_settings)
        self.accept()

class SettingsManagerDialog:
    """Wrapper to handle overlay and dialog execution"""
    def __init__(self, main_gui):
        self.gui = main_gui
        self.settings_mgr = SettingsManager()

    def show_dialog(self):
        if hasattr(self.gui, 'central_widget'):
            overlay = QWidget(self.gui.central_widget)
            overlay.setGeometry(self.gui.central_widget.rect())
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
            overlay.show()

        dlg = SettingsDialog(self.gui)

        # Center the dialog on top of the parent window
        parent_geo = self.gui.geometry()
        x = parent_geo.x() + (parent_geo.width() - dlg.width()) // 2
        y = parent_geo.y() + (parent_geo.height() - dlg.height()) // 2
        dlg.move(x, y)

        dlg.settings_saved.connect(self.gui.on_settings_saved)

        dlg.exec()

        if hasattr(self.gui, 'central_widget'):
            overlay.hide()
            overlay.deleteLater()
