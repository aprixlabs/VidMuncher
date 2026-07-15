import json
import os
import sys
import subprocess
import webbrowser
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QAbstractItemView,
    QCheckBox, QMessageBox, QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QCursor, QColor, QBrush, QAction, QPixmap, QIcon

from app.config import (
    HISTORY_FILE_PATH, HEADER_BG_COLOR, WINDOW_BG_COLOR, TEXT_COLOR,
    BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR, HISTORY_ICON_PATH
)
from app.utils import debug_print, format_file_size

STATUS_COMPLETED = "completed"
STATUS_ERROR     = "error"
STATUS_CANCELLED = "cancelled"

_STATUS_STYLE = {
    STATUS_COMPLETED: ("Complete",  TEXT_COLOR),
    STATUS_ERROR:     ("Failed",    TEXT_COLOR),
    STATUS_CANCELLED: ("Canceled",  TEXT_COLOR),
}

# Same color palette as Tkinter version for consistency
_ITEM_BG       = "#5B012A"   
_ITEM_BG_SEL   = "#6b0038"

class DownloadHistoryManager:
    """Manages download history persistence and the Qt history dialog."""

    def __init__(self, main_gui):
        self.gui = main_gui
        self.history = self._load_history()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #

    def _load_history(self) -> list:
        if os.path.exists(HISTORY_FILE_PATH):
            try:
                with open(HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                debug_print(f"Failed to load history: {e}")
        return []

    def _save_history(self):
        try:
            with open(HISTORY_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            debug_print(f"Failed to save history: {e}")

    def add_entry(self, title: str, url: str, file_path: str,
                  format_name: str, status: str = STATUS_COMPLETED):
        size_bytes = 0
        size_str   = "—"
        try:
            if file_path and os.path.exists(file_path):
                size_bytes = os.path.getsize(file_path)
                size_str   = format_file_size(size_bytes)
        except Exception:
            pass

        entry = {
            "title":      title,
            "url":        url,
            "file_path":  file_path,
            "format":     format_name,
            "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
            "size":       size_str,
            "size_bytes": size_bytes,
            "status":     status,
        }
        self.history.insert(0, entry)
        if len(self.history) > 100:
            self.history = self.history[:100]
        self._save_history()

    def remove_entry_by_ref(self, entry: dict):
        try:
            self.history.remove(entry)
            self._save_history()
        except ValueError:
            pass

    def clear_history(self):
        self.history = []
        self._save_history()

    # ------------------------------------------------------------------ #
    # Dialog entry point
    # ------------------------------------------------------------------ #

    def show_history_dialog(self):
        dlg = QDialog(self.gui)
        dlg.setWindowTitle("Download History")
        dlg.setFixedSize(620, 520 + 30)
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
                border: 1px solid #1a000e;
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

        title_lbl_tb = QLabel("Download History")
        title_lbl_tb.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl_tb.setStyleSheet("color: #cccccc;")
        title_lbl_tb.setAlignment(Qt.AlignCenter)
        title_lbl_tb.setAttribute(Qt.WA_TransparentForMouseEvents)
        title_layout.addWidget(title_lbl_tb, 1)

        close_btn_tb = QPushButton("", title_bar)
        close_btn_tb.setFixedSize(12, 12)
        close_btn_tb.setStyleSheet("QPushButton { border-radius: 6px; background-color: #FF5F56; border: none; } QPushButton:hover { background-color: #E0443E; }")
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

        # Top Bar Container
        top_widget = QWidget(content)
        top_widget.setStyleSheet(f"background-color: {HEADER_BG_COLOR};")
        top_bar = QHBoxLayout(top_widget)
        top_bar.setContentsMargins(20, 18, 20, 18)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(QIcon(str(HISTORY_ICON_PATH)).pixmap(24, 24))
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        
        title_lbl = QLabel("Download History")
        title_lbl.setFont(QFont("Poppins", 14, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {TEXT_COLOR};")
        
        self.count_lbl = QLabel(f"{len(self.history)} item(s)")
        self.count_lbl.setFont(QFont("Poppins", 9))
        self.count_lbl.setStyleSheet("color: #888888;")
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedSize(90, 35)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_COLOR};
                color: {TEXT_COLOR};
                font-family: Poppins;
                font-size: 10pt;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_ACTIVE_COLOR};
            }}
        """)
        clear_btn.clicked.connect(lambda: self._confirm_clear(dlg))

        top_bar.addWidget(icon_lbl)
        top_bar.addWidget(title_lbl)
        top_bar.addWidget(self.count_lbl)
        top_bar.addStretch()
        top_bar.addWidget(clear_btn)
        
        layout.addWidget(top_widget)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "File Name", "Date", "Size", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(True)
        
        self.table.setStyleSheet(f"""
            QTableWidget, QTableView {{
                background-color: {WINDOW_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 5px 0px;
                border-bottom: 2px solid {WINDOW_BG_COLOR};
                background-color: {_ITEM_BG};
            }}
            QTableWidget::item:selected {{
                background-color: {_ITEM_BG_SEL};
                color: {TEXT_COLOR};
            }}
            QHeaderView {{
                background-color: transparent;
            }}
            QHeaderView::section {{
                background-color: #1e0010;
                color: #888888;
                padding: 0px 10px 0px 3px;
                height: 34px;
                border: none;
                font-family: Poppins;
                font-weight: bold;
                font-size: 8pt;
            }}
            QHeaderView::up-arrow, QHeaderView::down-arrow {{
                width: 0px; height: 0px; border: none; background: none; image: none;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: #1e0010; /* Fills the header gap exactly */
                width: 6px;
                padding-top: 34px; /* Restricts the handle and track from climbing into the header */
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
                background-color: {WINDOW_BG_COLOR}; /* The track below the header */
            }}
        """)

        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setCascadingSectionResizes(True)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(17) # Allow the dummy column to be 17px
        
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Setup manual sort arrow rendering
        header.sortIndicatorChanged.connect(self._on_sort_changed)
        header.sectionResized.connect(self._on_section_resized)
        
        # Set initial widths using the dummy column (17px) as left padding
        self.table.setColumnWidth(0, 17)
        header.setSectionResizeMode(0, QHeaderView.Fixed) # Prevent resizing the margin
        self.table.setColumnWidth(1, 248) # 265 - 17
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 85)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)
        
        self._populate_table()
        
        dlg.exec()

    def _on_section_resized(self, logicalIndex, oldSize, newSize):
        if getattr(self, '_resizing_guard', False): return
        
        # Enforce maximum widths on all resizable columns to prevent crushing columns on their right
        max_widths = {1: 350, 2: 250, 3: 150}
        
        if logicalIndex in max_widths and newSize > max_widths[logicalIndex]:
            self._resizing_guard = True
            self.table.horizontalHeader().resizeSection(logicalIndex, max_widths[logicalIndex])
            self._resizing_guard = False

    def _populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for entry in self.history:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            fp = entry.get("file_path", "")
            raw_name = os.path.basename(fp) if fp else (entry.get("title") or "Unknown")
            
            # Dummy item for left padding column
            dummy_item = QTableWidgetItem("")
            dummy_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            
            name_item = QTableWidgetItem(raw_name)
            name_item.setFont(QFont("Poppins", 9))
            name_item.setData(Qt.UserRole, entry) # Store entry data
            
            date_item = QTableWidgetItem(entry.get("date", "—"))
            date_item.setFont(QFont("Poppins", 8))
            date_item.setForeground(QBrush(QColor("#aaaaaa")))
            
            size_item = QTableWidgetItem(entry.get("size", "—"))
            size_item.setFont(QFont("Poppins", 8))
            size_item.setForeground(QBrush(QColor("#aaaaaa")))
            
            # For correct sorting of size, set numeric data
            size_item.setData(Qt.UserRole, entry.get("size_bytes", 0))
            
            status_key = entry.get("status", STATUS_COMPLETED)
            status_label, s_color = _STATUS_STYLE.get(status_key, ("Unknown", "#888888"))
            
            status_item = QTableWidgetItem(status_label)
            status_item.setFont(QFont("Poppins", 8, QFont.Bold))
            status_item.setForeground(QBrush(QColor(s_color)))

            self.table.setItem(row, 0, dummy_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, date_item)
            self.table.setItem(row, 3, size_item)
            self.table.setItem(row, 4, status_item)

        self.table.setSortingEnabled(True)
        self.count_lbl.setText(f"{len(self.history)} item(s)")
        
        # Trigger header update to show the arrow on the currently sorted column
        header = self.table.horizontalHeader()
        self._on_sort_changed(header.sortIndicatorSection(), header.sortIndicatorOrder())

    def _on_sort_changed(self, index, order):
        if getattr(self, '_sorting_guard', False): return
        
        # Disable sorting on the dummy padding column
        if index == 0:
            self._sorting_guard = True
            self.table.horizontalHeader().setSortIndicator(1, order)
            self._sorting_guard = False
            return
            
        labels = ["", "File Name", "Date", "Size", "Status"]
        for i in range(1, 5):
            item = self.table.horizontalHeaderItem(i)
            if item:
                if i == index:
                    arrow = " ▲" if order == Qt.AscendingOrder else " ▼"
                    item.setText(labels[i] + arrow)
                else:
                    item.setText(labels[i])

    # ------------------------------------------------------------------ #
    # Context menu & Actions
    # ------------------------------------------------------------------ #

    def _get_selected_entries(self):
        entries = []
        for item in self.table.selectedItems():
            if item.column() == 1:
                entries.append(item.data(Qt.UserRole))
        return entries

    def _show_context_menu(self, position):
        entries = self._get_selected_entries()
        if not entries:
            return
            
        entry = entries[0]
        file_path = entry.get("file_path")
        url = entry.get("url")

        menu = QMenu(self.table)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: 1px solid {WINDOW_BG_COLOR};
            }}
            QMenu::item {{
                padding: 6px 20px;
                font-family: Poppins;
            }}
            QMenu::item:selected {{
                background-color: {BUTTON_COLOR};
            }}
        """)

        open_act = QAction("Open", menu)
        open_act.triggered.connect(lambda: self._open_file(file_path))
        menu.addAction(open_act)

        open_folder_act = QAction("Open Folder", menu)
        open_folder_act.triggered.connect(lambda: self._open_folder(file_path))
        menu.addAction(open_folder_act)

        open_url_act = QAction("Open URL", menu)
        open_url_act.triggered.connect(lambda: webbrowser.open(url) if url else None)
        menu.addAction(open_url_act)

        menu.addSeparator()

        remove_act = QAction("Remove", menu)
        remove_act.triggered.connect(self._confirm_remove_selected)
        menu.addAction(remove_act)

        menu.exec(self.table.mapToGlobal(position))

    def _on_double_click(self, item):
        entry = self.table.item(item.row(), 1).data(Qt.UserRole)
        if entry:
            self._open_file(entry.get("file_path"))

    def _open_file(self, file_path: str):
        if file_path and os.path.exists(file_path):
            abs_path = os.path.abspath(file_path)
            if sys.platform == "win32":
                os.startfile(abs_path)
            else:
                subprocess.run(["xdg-open", abs_path], check=False)

    def _open_folder(self, file_path: str):
        if not file_path:
            return
            
        abs_path = os.path.abspath(file_path)
        folder = os.path.dirname(abs_path)
        
        if os.path.exists(abs_path):
            if sys.platform == "win32":
                subprocess.run(["explorer", "/select,", abs_path], check=False)
            else:
                try:
                    import urllib.parse
                    file_uri = "file://" + urllib.parse.quote(abs_path)
                    subprocess.run([
                        "dbus-send", "--session", "--dest=org.freedesktop.FileManager1",
                        "--type=method_call", "/org/freedesktop/FileManager1",
                        "org.freedesktop.FileManager1.ShowItems",
                        f"array:string:{file_uri}", "string:"
                    ], check=True, capture_output=True)
                except Exception:
                    subprocess.run(["xdg-open", folder], check=False)
        elif os.path.exists(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            else:
                subprocess.run(["xdg-open", folder], check=False)

    # ------------------------------------------------------------------ #
    # Remove / clear
    # ------------------------------------------------------------------ #

    def _confirm_remove_selected(self):
        entries = self._get_selected_entries()
        if not entries:
            return

        dlg = QDialog(self.table)
        dlg.setWindowTitle("Remove Files")
        dlg.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; color: {TEXT_COLOR};")
        layout = QVBoxLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        
        lbl = QLabel("Are you sure you want to remove selected files?")
        lbl.setFont(QFont("Poppins", 10))
        layout.addWidget(lbl)
        
        layout.addSpacing(5)
        
        chk = QCheckBox("Remove files from disk")
        chk.setFont(QFont("Poppins", 9))
        chk.setStyleSheet(f"QCheckBox::indicator {{ width: 16px; height: 16px; }}")
        layout.addWidget(chk)
        
        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        del_btn = QPushButton("Delete")
        del_btn.setFixedSize(90, 35)
        del_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}; border-radius: 6px; font-family: Poppins; font-weight: bold;")
        del_btn.clicked.connect(lambda: self._do_remove(entries, chk.isChecked(), dlg))
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(90, 35)
        cancel_btn.setStyleSheet(f"background-color: {BUTTON_DISABLED_COLOR}; border-radius: 6px; font-family: Poppins; font-weight: bold;")
        cancel_btn.clicked.connect(dlg.reject)
        
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        dlg.exec()

    def _do_remove(self, entries, delete_disk, dlg):
        for entry in entries:
            if delete_disk:
                fp = entry.get("file_path")
                if fp and os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception as e:
                        debug_print(f"Failed to delete {{fp}}: {{e}}")
            self.remove_entry_by_ref(entry)
            
        self._populate_table()
        dlg.accept()

    def _confirm_clear(self, parent):
        dlg = QDialog(parent)
        dlg.setWindowTitle("Clear History")
        dlg.setStyleSheet(f"background-color: {HEADER_BG_COLOR}; color: {TEXT_COLOR};")
        
        layout = QVBoxLayout(dlg)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        
        lbl = QLabel("Are you sure you want to clear all download history?")
        lbl.setFont(QFont("Poppins", 10))
        layout.addWidget(lbl)
        
        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        yes_btn = QPushButton("Yes")
        yes_btn.setFixedSize(90, 35)
        yes_btn.setStyleSheet(f"background-color: {BUTTON_COLOR}; border-radius: 6px; font-family: Poppins; font-weight: bold;")
        
        def on_yes():
            self.clear_history()
            self._populate_table()
            dlg.accept()
            
        yes_btn.clicked.connect(on_yes)
        
        no_btn = QPushButton("No")
        no_btn.setFixedSize(90, 35)
        no_btn.setStyleSheet(f"background-color: {BUTTON_DISABLED_COLOR}; border-radius: 6px; font-family: Poppins; font-weight: bold;")
        no_btn.clicked.connect(dlg.reject)
        
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        
        layout.addLayout(btn_layout)
        dlg.exec()
