"""
VidMuncher Qt GUI Module
PySide6 Implementation Skeleton
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                               QLineEdit, QPushButton, QTextEdit, QComboBox, 
                               QProgressBar, QHBoxLayout, QVBoxLayout, QFileDialog, QDialog,
                               QCheckBox, QTimeEdit, QStyledItemDelegate, QFrame)
from PySide6.QtGui import QFontDatabase, QIcon, QFont, QPalette, QColor, QPixmap, QCursor, QPainter, QPainterPath, QBrush
from PySide6.QtWidgets import QGraphicsColorizeEffect
from PySide6.QtCore import Qt, QSize, QRect, QThreadPool, Slot, Signal, QObject, QTimer, QTime
import os

from app.gui.setup_dialog import SetupDialog

from app.utils import sanitize_filename, get_extension_from_preset, get_unique_filename, validate_url, debug_print
from app.config import (
    APP_NAME, APP_VERSION, APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_BG_COLOR,
    HEADER_BG_COLOR, TEXT_COLOR, PLACEHOLDER_COLOR, BUTTON_COLOR, BUTTON_ACTIVE_COLOR,
    BUTTON_DISABLED_COLOR, ICON_PNG_PATH, ICON_PATH, DROPDOWN_ARROW_PATH, UP_ARROW_PATH, ABOUT_ICON_PATH, HISTORY_ICON_PATH, CHECKMARK_ICON_PATH,
    FONT_REGULAR, FONT_MEDIUM, FONT_BOLD, FONT_BLACK, DEBUG_MODE, Layout, Fonts, DOWNLOAD_PRESETS, ENCODER_OPTIONS, DEFAULT_DOWNLOAD_PATH
)
from app.gui.download_history import DownloadHistoryManager, STATUS_COMPLETED, STATUS_ERROR, STATUS_CANCELLED
from app.gui.about import AboutDialogManager
from app.tasks import AnalyzeWorker, ThumbnailWorker, DownloadWorker, EncodeWorker

class VidMuncherQtGUI(QMainWindow):
    """Main Qt GUI class for VidMuncher application"""
    
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool.globalInstance()
        self.video_data = {}
        self.is_downloading = False
        self.current_worker = None
        self.history_manager = DownloadHistoryManager(self)
        self.about_manager = AboutDialogManager(self)
        self.init_ui()
        
    def init_ui(self):
        # Set app title
        self.setWindowTitle(APP_TITLE)
        
        # Increase window height by 30px for the custom title bar
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT + 30)
        self.setMaximumSize(WINDOW_WIDTH, WINDOW_HEIGHT + 30)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Apply base dark theme, color constants, and global scrollbar styles
        self.setStyleSheet(f"""
            QMainWindow {{ border: 1px solid #1a000e; background-color: {WINDOW_BG_COLOR}; }}
            QWidget {{
                color: {TEXT_COLOR};
                font-family: 'Poppins';
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {HEADER_BG_COLOR};
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {BUTTON_COLOR};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
                background: none;
                border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        
        # Load bundled fonts
        self.setup_fonts()
        
        # Set application icon
        self.setup_window_icon()
        
        # Main widget
        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainWidget")
        self.main_widget.setStyleSheet(f"""
            QWidget#MainWidget {{ 
                background-color: {WINDOW_BG_COLOR}; 
                border-radius: 10px;
                border: 1px solid #1a000e;
            }}
        """)
        self.setCentralWidget(self.main_widget)
        
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom Title Bar
        self.title_bar = QWidget(self.main_widget)
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        # App Name
        title_lbl = QLabel(f"{APP_NAME} {APP_VERSION}")
        title_lbl.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl.setStyleSheet("color: #cccccc;")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        title_layout.addWidget(title_lbl, 1)  # stretch=1 to center it
        
        # macOS style buttons on the right side
        btn_style = """
            QPushButton { border-radius: 6px; border: none; }
            QPushButton#closeBtn { background-color: #FF5F56; }
            QPushButton#closeBtn:hover { background-color: #E0443E; }
            QPushButton#minBtn { background-color: #FFBD2E; }
            QPushButton#minBtn:hover { background-color: #DEA125; }
        """
        self.min_btn = QPushButton("", self.title_bar)
        self.min_btn.setObjectName("minBtn")
        self.min_btn.setFixedSize(12, 12)
        self.min_btn.setStyleSheet(btn_style)
        self.min_btn.setCursor(Qt.PointingHandCursor)
        self.min_btn.clicked.connect(self.showMinimized)
        
        self.close_btn = QPushButton("", self.title_bar)
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(12, 12)
        self.close_btn.setStyleSheet(btn_style)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.min_btn)
        btn_layout.addWidget(self.close_btn)
        
        title_layout.addLayout(btn_layout)
        main_layout.addWidget(self.title_bar)
        
        # Attach dragging to title bar explicitly via Wayland-compatible startSystemMove
        def mp(event):
            if event.button() == Qt.LeftButton:
                window = self.windowHandle()
                if window:
                    window.startSystemMove()
                event.accept()
        self.title_bar.mousePressEvent = mp
        
        self.central_widget = QWidget(self.main_widget)
        self.central_widget.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        main_layout.addWidget(self.central_widget)
        
        self.setup_gui_components()
        
    def setup_fonts(self):
        """Load bundled fonts"""
        for font_path in [FONT_REGULAR, FONT_MEDIUM, FONT_BOLD, FONT_BLACK]:
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))
                
    def get_qfont(self, font_tuple):
        """Convert config Fonts tuple to QFont"""
        family = font_tuple[0]
        size = font_tuple[1]
        weight = QFont.Bold if len(font_tuple) > 2 and "bold" in font_tuple[2] else QFont.Normal
        return QFont(family, size, weight)
                
    def setup_window_icon(self):
        """Set window icon from assets"""
        icon_path = str(ICON_PNG_PATH) if ICON_PNG_PATH.exists() else str(ICON_PATH)
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))
            
    def setup_gui_components(self):
        """Setup all GUI components using absolute positioning"""
        self.setup_header()
        self.setup_url_input()
        self.setup_video_info()
        self.setup_thumbnail()
        self.setup_preset_selection()
        self.setup_download_section()
        self.setup_save_location()
        self.setup_buttons()
        self.setup_progress_bar()
        self.setup_copyright()
        
    def setup_header(self):
        """Setup header section"""
        self.header_bg = QWidget(self.central_widget)
        self.header_bg.setGeometry(0, 0, WINDOW_WIDTH, Layout.HEADER_HEIGHT)
        self.header_bg.setStyleSheet(f"background-color: {HEADER_BG_COLOR};")
        
        # Icon
        if ICON_PNG_PATH.exists():
            self.header_icon_label = QLabel(self.header_bg)
            pixmap = QPixmap(str(ICON_PNG_PATH)).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.header_icon_label.setPixmap(pixmap)
            self.header_icon_label.setGeometry(Layout.HEADER_IMAGE_X, 15, 50, 50)
            self.header_icon_label.setStyleSheet("background: transparent;")
            
        # Title Container
        self.title_container = QWidget(self.header_bg)
        self.title_container.setGeometry(Layout.HEADER_IMAGE_X + 64, 18, 300, 35)
        self.title_container.setStyleSheet("background: transparent;")
        
        title_layout = QHBoxLayout(self.title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        title_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        
        self.title_label = QLabel(APP_NAME)
        self.title_label.setFont(QFont("Poppins", 24, QFont.Black))
        self.title_label.setStyleSheet("color: #ffdcee;")
        self.title_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        
        self.version_label = QLabel(APP_VERSION)
        self.version_label.setFont(QFont("Poppins", 8, QFont.Bold))
        self.version_label.setStyleSheet("color: #ffdcee;")
        self.version_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        self.version_label.setContentsMargins(2, 0, 0, 7)
        
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(self.version_label)
        
        # Subtitle
        self.subtitle_label = QLabel("Video Downloader", self.header_bg)
        self.subtitle_label.setFont(QFont("Poppins", 12, QFont.Medium))
        self.subtitle_label.setStyleSheet("color: #ffdcee; background-color: transparent;")
        self.subtitle_label.setGeometry(Layout.HEADER_IMAGE_X + 66, 46, 150, 20)
        
        # About Button
        self.about_btn = QPushButton("", self.header_bg)
        self.about_btn.setIcon(QIcon(str(ABOUT_ICON_PATH)))
        self.about_btn.setIconSize(QSize(20, 20))
        self.about_btn.setCursor(Qt.PointingHandCursor)
        self.about_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        self.about_btn.setGeometry(Layout.ABOUT_BUTTON_X, Layout.ABOUT_BUTTON_Y,
                                   Layout.ABOUT_BUTTON_WIDTH, Layout.ABOUT_BUTTON_HEIGHT)
        self.about_btn.clicked.connect(self.show_about_dialog)
        
        # History Button
        self.history_btn = QPushButton("", self.header_bg)
        self.history_btn.setIcon(QIcon(str(HISTORY_ICON_PATH)))
        self.history_btn.setIconSize(QSize(20, 20))
        self.history_btn.setCursor(Qt.PointingHandCursor)
        self.history_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        self.history_btn.setGeometry(Layout.HISTORY_BUTTON_X, Layout.HISTORY_BUTTON_Y,
                                     Layout.HISTORY_BUTTON_WIDTH, Layout.HISTORY_BUTTON_HEIGHT)
        self.history_btn.clicked.connect(self.show_history_dialog)

    def setup_url_input(self):
        """Setup URL input field"""
        self.url_entry = QLineEdit(self.central_widget)
        self.url_entry.setFont(self.get_qfont(Fonts.DEFAULT))
        self.url_entry.setPlaceholderText(Layout.URL_PLACEHOLDER.strip())
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
                border: 1px solid {BUTTON_COLOR};
                outline: none;
            }}
        """)
        self.url_entry.setGeometry(Layout.URL_ENTRY_X, Layout.URL_ENTRY_Y,
                                   Layout.URL_ENTRY_WIDTH, Layout.URL_ENTRY_HEIGHT)
        
    def setup_video_info(self):
        """Setup video information display"""
        self.video_info_frame = QWidget(self.central_widget)
        self.video_info_frame.setGeometry(Layout.VIDEO_INFO_X, Layout.VIDEO_INFO_Y,
                                          Layout.VIDEO_INFO_WIDTH, Layout.VIDEO_INFO_HEIGHT)
        self.video_info_frame.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; border-radius: 6px;")
        
        self.video_info_placeholder = QLabel(Layout.VIDEO_INFO_PLACEHOLDER, self.video_info_frame)
        self.video_info_placeholder.setFont(self.get_qfont(Fonts.SMALL))
        self.video_info_placeholder.setStyleSheet(f"color: {PLACEHOLDER_COLOR}; background-color: transparent;")
        self.video_info_placeholder.setAlignment(Qt.AlignCenter)
        self.video_info_placeholder.setGeometry(0, 0, Layout.VIDEO_INFO_WIDTH, Layout.VIDEO_INFO_HEIGHT)
        
        self.video_info = QTextEdit(self.video_info_frame)
        self.video_info.setFont(self.get_qfont(Fonts.SMALL))
        self.video_info.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent; border: none; padding: 5px; selection-background-color: {BUTTON_COLOR}; selection-color: {TEXT_COLOR};")
        self.video_info.setReadOnly(True)
        self.video_info.setGeometry(0, 0, Layout.VIDEO_INFO_WIDTH, Layout.VIDEO_INFO_HEIGHT)
        self.video_info.hide() # Hidden initially
        
    def setup_thumbnail(self):
        """Setup thumbnail display"""
        self.thumbnail_frame = QWidget(self.central_widget)
        self.thumbnail_frame.setGeometry(Layout.THUMBNAIL_X, Layout.THUMBNAIL_Y,
                                         Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)
        self.thumbnail_frame.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; border-radius: 6px;")
        
        self.thumbnail_placeholder = QLabel(Layout.THUMBNAIL_PLACEHOLDER, self.thumbnail_frame)
        self.thumbnail_placeholder.setFont(self.get_qfont(Fonts.SMALL))
        self.thumbnail_placeholder.setStyleSheet(f"color: {PLACEHOLDER_COLOR}; background-color: transparent;")
        self.thumbnail_placeholder.setAlignment(Qt.AlignCenter)
        self.thumbnail_placeholder.setGeometry(0, 0, Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)
        
        self.thumbnail_label = QLabel(self.thumbnail_frame)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setGeometry(0, 0, Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)
        self.thumbnail_label.hide() # Hidden initially
        
    def setup_preset_selection(self):
        """Setup preset selection components"""
        self.preset_label = QLabel("Select Preset", self.central_widget)
        self.preset_label.setFont(self.get_qfont(Fonts.DEFAULT))
        self.preset_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.preset_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.preset_label.setGeometry(Layout.PRESET_LABEL_X, Layout.PRESET_LABEL_Y, 100, Layout.PRESET_COMBO_HEIGHT)
        
        self.preset_combo = QComboBox(self.central_widget)
        self.preset_combo.setItemDelegate(QStyledItemDelegate())
        self.preset_combo.addItems(DOWNLOAD_PRESETS)
        self.preset_combo.setFont(self.get_qfont(Fonts.COMBO))
        self.preset_combo.setStyleSheet(f"""
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
                image: url("{str(DROPDOWN_ARROW_PATH).replace('\\', '/')}");
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
                border: none;
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
                height: 0px;
                background: none;
                border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        self.preset_combo.setGeometry(Layout.PRESET_COMBO_X, Layout.PRESET_COMBO_Y,
                                      Layout.PRESET_COMBO_WIDTH, Layout.PRESET_COMBO_HEIGHT)
        self.preset_combo.currentTextChanged.connect(self.on_preset_change)
                                      
        self.reencode_label = QLabel("Codec", self.central_widget)
        self.reencode_label.setFont(self.get_qfont(Fonts.DEFAULT))
        self.reencode_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.reencode_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.reencode_label.setGeometry(Layout.REENCODE_LABEL_X, Layout.REENCODE_LABEL_Y, 50, Layout.REENCODE_COMBO_HEIGHT)
        
        self.encoder_combo = QComboBox(self.central_widget)
        self.encoder_combo.setItemDelegate(QStyledItemDelegate())
        self.encoder_combo.addItems(ENCODER_OPTIONS)
        self.encoder_combo.setFont(self.get_qfont(Fonts.COMBO))
        self.encoder_combo.setStyleSheet(self.preset_combo.styleSheet())
        self.encoder_combo.setGeometry(Layout.REENCODE_COMBO_X, Layout.REENCODE_COMBO_Y,
                                       Layout.REENCODE_COMBO_WIDTH, Layout.REENCODE_COMBO_HEIGHT)
        self.encoder_combo.currentTextChanged.connect(self.on_encoder_change)
        
    def setup_download_section(self):
        """Setup download section checkbox and time inputs"""
        self.section_checkbox = QCheckBox("Download Section", self.central_widget)
        self.section_checkbox.setFont(self.get_qfont(Fonts.DEFAULT))
        self.section_checkbox.setStyleSheet(f"""
            QCheckBox {{ color: {TEXT_COLOR}; background-color: transparent; }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border-radius: 4px;
                background-color: {HEADER_BG_COLOR};
            }}
            QCheckBox::indicator:checked {{
                background-color: {BUTTON_COLOR};
                image: url("{str(CHECKMARK_ICON_PATH).replace('\\', '/')}"); 
            }}
        """)
        self.section_checkbox.setGeometry(Layout.SECTION_CB_X, Layout.SECTION_CB_Y, 150, 30)
        self.section_checkbox.stateChanged.connect(self.on_section_checkbox_toggled)
        
        time_style = f"""
            QTimeEdit {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 6px;
                padding-left: 5px;
                selection-background-color: {BUTTON_COLOR};
                selection-color: {TEXT_COLOR};
            }}
            QTimeEdit::up-button, QTimeEdit::down-button {{
                background-color: {BUTTON_COLOR};
                width: 16px;
                border: none;
            }}
            QTimeEdit::up-button {{
                border-top-right-radius: 6px;
                margin-bottom: 1px;
            }}
            QTimeEdit::down-button {{
                border-bottom-right-radius: 6px;
            }}
            QTimeEdit::up-arrow {{
                width: 6px; height: 6px;
                image: url("{str(UP_ARROW_PATH).replace('\\', '/')}");
            }}
            QTimeEdit::down-arrow {{
                width: 6px; height: 6px;
                image: url("{str(DROPDOWN_ARROW_PATH).replace('\\', '/')}");
            }}
        """
        
        self.start_time_edit = QTimeEdit(self.central_widget)
        self.start_time_edit.setDisplayFormat("HH:mm:ss")
        self.start_time_edit.setTime(QTime(0, 0, 0))
        self.start_time_edit.setFont(self.get_qfont(Fonts.COMBO))
        self.start_time_edit.setStyleSheet(time_style)
        self.start_time_edit.setGeometry(Layout.SECTION_START_X, Layout.SECTION_START_Y, 100, 30)
        self.start_time_edit.setEnabled(False)
        
        self.time_separator = QLabel("-", self.central_widget)
        self.time_separator.setFont(self.get_qfont(Fonts.DEFAULT))
        self.time_separator.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.time_separator.setAlignment(Qt.AlignCenter)
        self.time_separator.setGeometry(Layout.SECTION_START_X + 100, Layout.SECTION_START_Y, 25, 30)
        
        self.end_time_edit = QTimeEdit(self.central_widget)
        self.end_time_edit.setDisplayFormat("HH:mm:ss")
        self.end_time_edit.setTime(QTime(0, 0, 0))
        self.end_time_edit.setFont(self.get_qfont(Fonts.COMBO))
        self.end_time_edit.setStyleSheet(time_style)
        self.end_time_edit.setGeometry(Layout.SECTION_END_X, Layout.SECTION_END_Y, 100, 30)
        self.end_time_edit.setEnabled(False)
        
    def on_section_checkbox_toggled(self, state):
        is_checked = state == Qt.Checked.value
        self.start_time_edit.setEnabled(is_checked)
        self.end_time_edit.setEnabled(is_checked)
        
    def setup_save_location(self):
        """Setup save location components"""
        self.save_label = QLabel("Save Location", self.central_widget)
        self.save_label.setFont(self.get_qfont(Fonts.DEFAULT))
        self.save_label.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.save_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.save_label.setGeometry(Layout.SAVE_LABEL_X, Layout.SAVE_LABEL_Y, 100, Layout.SAVE_ENTRY_HEIGHT)
        
        self.save_entry = QLineEdit(self.central_widget)
        self.save_entry.setFont(self.get_qfont(Fonts.SMALL))
        self.save_entry.setStyleSheet(f"""
            QLineEdit {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                padding-left: 5px;
                border-radius: 6px;
                selection-background-color: {BUTTON_COLOR};
                selection-color: {TEXT_COLOR};
            }}
        """)
        self.save_entry.setGeometry(Layout.SAVE_ENTRY_X, Layout.SAVE_ENTRY_Y,
                                    Layout.SAVE_ENTRY_WIDTH, Layout.SAVE_ENTRY_HEIGHT)
                                    
        self.browse_btn = QPushButton("Browse", self.central_widget)
        self.browse_btn.setFont(self.get_qfont(Fonts.BOLD))
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        self.browse_btn.setGeometry(Layout.BROWSE_BUTTON_X, Layout.BROWSE_BUTTON_Y,
                                    Layout.BROWSE_BUTTON_WIDTH, Layout.BROWSE_BUTTON_HEIGHT)
        self.browse_btn.clicked.connect(self.browse_save_path)
        
    def setup_buttons(self):
        """Setup action buttons"""
        self.analyze_button = QPushButton("Analyze", self.central_widget)
        self.analyze_button.setFont(self.get_qfont(Fonts.BOLD))
        self.analyze_button.setCursor(Qt.PointingHandCursor)
        self.analyze_button.setStyleSheet(f"""
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
        """)
        self.analyze_button.setGeometry(Layout.ANALYZE_BUTTON_X, Layout.ANALYZE_BUTTON_Y,
                                        Layout.ANALYZE_BUTTON_WIDTH, Layout.ANALYZE_BUTTON_HEIGHT)
        self.analyze_button.clicked.connect(self.analyze_video)
                                        
        self.download_button = QPushButton("Download", self.central_widget)
        self.download_button.setFont(self.get_qfont(Fonts.BOLD))
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.setStyleSheet(self.analyze_button.styleSheet())
        self.download_button.setGeometry(Layout.DOWNLOAD_BUTTON_X, Layout.DOWNLOAD_BUTTON_Y,
                                         Layout.DOWNLOAD_BUTTON_WIDTH, Layout.DOWNLOAD_BUTTON_HEIGHT)
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.download_video)
        
        self.cancel_button = QPushButton("Cancel", self.central_widget)
        self.cancel_button.setFont(self.get_qfont(Fonts.BOLD))
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet(self.analyze_button.styleSheet())
        self.cancel_button.setGeometry(Layout.CANCEL_BUTTON_X, Layout.CANCEL_BUTTON_Y,
                                       Layout.CANCEL_BUTTON_WIDTH, Layout.CANCEL_BUTTON_HEIGHT)
        self.cancel_button.clicked.connect(self.cancel_task)
        self.cancel_button.hide()
        
    def setup_progress_bar(self):
        """Setup progress bar"""
        self.progress_frame = QWidget(self.central_widget)
        self.progress_frame.setGeometry(Layout.PROGRESS_X, Layout.PROGRESS_Y,
                                        Layout.PROGRESS_WIDTH, Layout.PROGRESS_HEIGHT)
        self.progress_frame.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; border-radius: 6px;")
        
        # Use a simple QWidget for the fill to avoid cross-platform QProgressBar stylesheet bugs
        self.progress_fill = QWidget(self.progress_frame)
        self.progress_fill.setGeometry(0, 0, 0, Layout.PROGRESS_HEIGHT)
        self.progress_fill.setStyleSheet(f"background-color: {BUTTON_COLOR}; border-radius: 6px;")
        
        self.progress_text = QLabel("", self.progress_frame)
        self.progress_text.setFont(self.get_qfont(Fonts.SMALL))
        self.progress_text.setStyleSheet(f"color: {TEXT_COLOR}; background-color: transparent;")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setGeometry(0, 0, Layout.PROGRESS_WIDTH, Layout.PROGRESS_HEIGHT)
        
    def setup_copyright(self):
        """Setup copyright text"""
        self.copyright_label = QLabel("Copyright © 2026 - VidMuncher by Aprix Labs", self.central_widget)
        self.copyright_label.setFont(self.get_qfont(Fonts.SMALL))
        self.copyright_label.setStyleSheet(f"color: #76485D; background-color: transparent;")
        self.copyright_label.setAlignment(Qt.AlignCenter)
        self.copyright_label.setGeometry(Layout.COPYRIGHT_X - 150, Layout.COPYRIGHT_Y - 10, 300, 20)

    def show_about_dialog(self):
        """Show About dialog via AboutDialogManager"""
        self.about_manager.show_about_dialog()
        
    def show_history_dialog(self):
        """Port History dialog entry point"""
        if hasattr(self, 'history_manager'):
            self.history_manager.show_history_dialog()

    def update_progress(self, text, progress=None):
        """Update progress bar and text"""
        self.progress_text.setText(text)
        
        # Prevent expensive style recalculation on every tick
        current_style = self.progress_text.styleSheet()
        expected_style = f"color: {TEXT_COLOR}; background-color: transparent;"
        if current_style != expected_style:
            self.progress_text.setStyleSheet(expected_style)
            
        if progress is not None:
            # Clamp progress between 0 and 100
            progress = max(0, min(100, progress))
            fill_width = int(Layout.PROGRESS_WIDTH * (progress / 100.0))
            self.progress_fill.setGeometry(0, 0, fill_width, Layout.PROGRESS_HEIGHT)

    def set_button_states(self, analyze_enabled=True, download_enabled=False):
        """Set state of Analyze and Download buttons"""
        self.analyze_button.setEnabled(analyze_enabled)
        self.download_button.setEnabled(download_enabled)

    def is_encoding_enabled(self):
        return self.encoder_combo.currentText() != "Auto"

    @Slot(str)
    def on_preset_change(self, selected):
        if "Audio" in selected:
            self.encoder_combo.setCurrentText("Auto")
            self.encoder_combo.setEnabled(False)
        else:
            self.encoder_combo.setEnabled(True)
            
        self.update_preview_path()

    @Slot(str)
    def on_encoder_change(self, selected):
        self.update_preview_path()

    def update_preview_path(self):
        """Update preview path based on preset and H.264 status"""
        if 'title' not in self.video_data:
            return

        title = self.video_data['title']
        safe_title = sanitize_filename(title)

        known_exts = {".mp4", ".mkv", ".webm", ".avi", ".m4v", ".wav", ".mp3", ".m4a"}
        while True:
            root, ext_part = os.path.splitext(safe_title)
            if ext_part.lower() in known_exts:
                safe_title = root
            else:
                break

        encoding_enabled = self.is_encoding_enabled()
        encoder_selection = self.encoder_combo.currentText()
        ext = get_extension_from_preset(self.preset_combo.currentText(), encoding_enabled, encoder_selection)

        filename_with_ext = f"{safe_title}.{ext}"
        full_path_with_ext = os.path.join(DEFAULT_DOWNLOAD_PATH, filename_with_ext)
        unique_full_path = get_unique_filename(full_path_with_ext)

        self.save_entry.setText(unique_full_path)

    def browse_save_path(self):
        """Browse for save location"""
        encoding_enabled = self.is_encoding_enabled()
        encoder_selection = self.encoder_combo.currentText()
        extension = get_extension_from_preset(self.preset_combo.currentText(), encoding_enabled, encoder_selection)

        current_path = self.save_entry.text()
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
            self.save_entry.setText(path)

    def reset_video_data(self):
        """Reset video data and clear thumbnail"""
        self.video_data.clear()
        
        self.video_info.hide()
        self.video_info_placeholder.show()
        
        self.thumbnail_label.hide()
        self.thumbnail_label.setPixmap(QPixmap())
        self.thumbnail_placeholder.show()

    def analyze_video(self):
        """Analyze video URL using Qt Worker"""
        url = self.url_entry.text().strip()
        if not url or url == Layout.URL_PLACEHOLDER.strip():
            debug_print("analyze_video: rejected — URL is empty")
            self.progress_text.setText("Please enter a valid URL")
            self.progress_text.setStyleSheet("color: #FF5050;")
            return

        if not validate_url(url):
            debug_print(f"analyze_video: rejected — invalid URL format: {url!r}")
            self.progress_text.setText("Invalid URL format")
            self.progress_text.setStyleSheet("color: #FF5050;")
            return

        debug_print(f"analyze_video: starting — {url!r}")

        self.set_button_states(analyze_enabled=False, download_enabled=False)
        self.update_progress("Getting information...", 0)

        worker = AnalyzeWorker(url)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.on_analyze_finished)
        
        self.current_worker = worker
        self.threadpool.start(worker)

    @Slot(bool, object, str)
    def on_analyze_finished(self, success, data, err):
        self.current_worker = None
        if success and data:
            self.video_data = data
            title = data.get("title", "N/A")
            debug_print(f"on_analyze_finished: success — title={title!r}")
            desc = data.get("description", "")
            thumbnail_url = data.get("thumbnail", "")
            
            self.video_info_placeholder.hide()
            self.video_info.show()
            self.video_info.setPlainText(f"{title}\n\n{desc}")
            
            if thumbnail_url:
                self.download_thumbnail_async(thumbnail_url)
                
            self.update_preview_path()
            self.update_progress("Ready to download", 0)
            self.set_button_states(analyze_enabled=True, download_enabled=True)
        else:
            debug_print(f"on_analyze_finished: failed — {err!r}")
            self.progress_text.setText(err or "Failed to get video info")
            self.progress_text.setStyleSheet("color: #FF5050;")
            self.reset_video_data()
            self.set_button_states(analyze_enabled=True, download_enabled=False)

    def download_thumbnail_async(self, thumbnail_url):
        worker = ThumbnailWorker(thumbnail_url)
        worker.signals.data_ready.connect(self.on_thumbnail_ready)
        # error ignored silently for thumbnail as in original
        self.threadpool.start(worker)

    @Slot(bytes)
    def on_thumbnail_ready(self, img_data):
        pixmap = QPixmap()
        if pixmap.loadFromData(img_data):
            scaled_pixmap = pixmap.scaled(Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            x_offset = (scaled_pixmap.width() - Layout.THUMBNAIL_WIDTH) // 2
            y_offset = (scaled_pixmap.height() - Layout.THUMBNAIL_HEIGHT) // 2
            cropped_pixmap = scaled_pixmap.copy(x_offset, y_offset, Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)
            
            rounded = QPixmap(cropped_pixmap.size())
            rounded.fill(Qt.transparent)
            
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, cropped_pixmap.width(), cropped_pixmap.height(), 6, 6)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, cropped_pixmap)
            painter.end()

            self.thumbnail_placeholder.hide()
            self.thumbnail_label.show()
            self.thumbnail_label.setPixmap(rounded)

    def download_video(self):
        """Start the download process"""
        url = self.url_entry.text().strip()
        out_path = self.save_entry.text()
        preset = self.preset_combo.currentText()

        # Normalize out_path to be extension-less
        known_exts = {".mp4", ".mkv", ".webm", ".avi", ".m4v", ".wav", ".mp3", ".m4a"}
        while True:
            root_out, ext_out = os.path.splitext(out_path)
            if ext_out.lower() in known_exts:
                out_path = root_out
            else:
                break

        if not url or url == Layout.URL_PLACEHOLDER.strip():
            self.progress_text.setText("Please enter a valid URL")
            self.progress_text.setStyleSheet("color: #FF5050;")
            return

        self.set_button_states(analyze_enabled=False, download_enabled=False)
        self.download_button.hide()
        self.cancel_button.show()
        
        self.is_downloading = True
        encoding_enabled = self.is_encoding_enabled()
        
        download_section = None
        if hasattr(self, 'section_checkbox') and self.section_checkbox.isChecked():
            start_time = self.start_time_edit.text()
            end_time = self.end_time_edit.text()
            download_section = f"*{start_time}-{end_time}"

        worker = DownloadWorker(url, out_path, preset, encoding_enabled, download_section)
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(self.on_download_finished)
        
        self.current_worker = worker
        self.threadpool.start(worker)

    @Slot(bool, object, str)
    def on_download_finished(self, success, final_path, err):
        url = self.url_entry.text().strip()
        title = self.video_data.get("title", "Unknown Title")
        preset = self.preset_combo.currentText()
        encoding_enabled = self.is_encoding_enabled()
        encoder_selection = self.encoder_combo.currentText()
        
        if success and final_path:
            if "Audio" not in preset and encoding_enabled and encoder_selection != "Auto":
                self.encode_video(final_path, encoder_selection, title, url, preset)
            else:
                self.history_manager.add_entry(title, url, final_path, preset, STATUS_COMPLETED)
                self.complete_task("Download complete!", True)
        else:
            status = STATUS_CANCELLED if err and "cancelled" in err.lower() else STATUS_ERROR
            self.history_manager.add_entry(title, url, final_path or "", preset, status)
            self.complete_task(err or "Download failed", False)

    def encode_video(self, input_path, encoder_selection, title, url, preset):
        """Start the encoding process"""
        self.update_progress("Preparing to encode...", 0)
        
        # We'll attach the metadata to the worker so we can retrieve it in on_encode_finished
        worker = EncodeWorker(input_path, encoder_selection)
        worker.meta_title = title
        worker.meta_url = url
        worker.meta_preset = preset
        worker.meta_final_path = input_path
        
        worker.signals.progress.connect(self.update_progress)
        worker.signals.finished.connect(lambda s, f, e: self.on_encode_finished(s, f, e, worker))
        
        self.current_worker = worker
        self.threadpool.start(worker)

    @Slot(bool, object, str, object)
    def on_encode_finished(self, success, final_path, err, worker):
        title = getattr(worker, 'meta_title', 'Unknown Title')
        url = getattr(worker, 'meta_url', '')
        preset = getattr(worker, 'meta_preset', '')
        
        if success:
            self.history_manager.add_entry(title, url, final_path or "", preset, STATUS_COMPLETED)
            self.complete_task("Encoding complete!", True)
        else:
            status = STATUS_CANCELLED if err and "cancelled" in err.lower() else STATUS_ERROR
            self.history_manager.add_entry(title, url, final_path or "", preset, status)
            self.complete_task(err or "Encoding failed", False)

    def complete_task(self, msg, success):
        """Cleanup after process finishes"""
        self.current_worker = None
        self.is_downloading = False
        self.cancel_button.setEnabled(True)
        self.cancel_button.hide()
        self.download_button.show()
        self.set_button_states(analyze_enabled=True, download_enabled=True)
        self.progress_text.setText(msg)
        self.progress_text.setStyleSheet(f"color: {TEXT_COLOR if success else '#FF5050'}; background-color: transparent;")
        self.progress_fill.setGeometry(0, 0, Layout.PROGRESS_WIDTH if success else 0, Layout.PROGRESS_HEIGHT)

    def cancel_task(self):
        """Cancel the currently running worker process"""
        if self.current_worker and hasattr(self.current_worker, 'cancel'):
            self.current_worker.cancel()
            self.update_progress("Cancelling...")
        self.cancel_button.setEnabled(False)

    # Drag support is now attached directly to title_bar


def run():
    """Bootstrap Qt application without replacing Tkinter entrypoint yet"""
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
