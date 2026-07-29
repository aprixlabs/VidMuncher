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
from app.utils.debug import debug_print
from app.utils.formatting import format_file_size
from app.utils.localization import _

STATUS_COMPLETED = "completed"
STATUS_ERROR     = "error"
STATUS_CANCELLED = "cancelled"

_ITEM_BG       = "#5B012A"
_ITEM_BG_SEL   = "#6b0038"

class HistoryDialog:

    def __init__(self, main_gui):
        self.gui = main_gui
        self.history = []

    # Persistence

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

    # Dialog entry point

    def show_history_dialog(self):
        # Load history lazily on first show to avoid blocking main startup
        if not hasattr(self, '_history_loaded'):
            self.history = self._load_history()
            self._history_loaded = True

        # Apply dark overlay to main window
        overlay = QWidget(self.gui.main_widget)
        overlay.setGeometry(self.gui.main_widget.rect())
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
        overlay.show()

        dlg = QDialog(self.gui)
        # Center the dialog on top of the parent window
        parent_geo = self.gui.geometry()
        x = parent_geo.x() + (parent_geo.width() - 620) // 2
        y = parent_geo.y() + (parent_geo.height() - 520) // 2
        dlg.move(x, y)
        dlg.setWindowTitle(_("history.title"))
        dlg.setFixedSize(620, 520)
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

        title_lbl_tb = QLabel(_("history.title"))
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

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", _("history.file_name"), _("history.date"), _("history.size"), _("history.status")])
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
                margin-bottom: -2px;
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
                background-color: #1e0010;
                width: 6px;
                padding-top: 34px;
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
                background-color: {WINDOW_BG_COLOR};
            }}
        """)

        # Add bottom margin padding by ensuring the table does not draw to the very edge
        # so the last item is not clipped off by the bottom border roundness or overlap
        self.table.setViewportMargins(0, 0, 0, 5)

        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setCascadingSectionResizes(True)
        header.setStretchLastSection(True)
        header.setMinimumSectionSize(17)

        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        header.sortIndicatorChanged.connect(self._on_sort_changed)
        header.sectionResized.connect(self._on_section_resized)

        self.table.setColumnWidth(0, 17)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 290)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 85)
        header.setSectionResizeMode(4, QHeaderView.Fixed)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

        bottom_widget = QFrame(content)
        bottom_widget.setObjectName("BottomWidget")
        bottom_widget.setFixedHeight(35)
        bottom_widget.setStyleSheet(f"""
            QFrame#BottomWidget {{
                background-color: {WINDOW_BG_COLOR};
                border-top: 1px solid {HEADER_BG_COLOR};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
        """)
        bottom_bar = QHBoxLayout(bottom_widget)
        bottom_bar.setContentsMargins(20, 0, 20, 0)

        self.count_lbl = QLabel(_("history.items_count").format(len(self.history)))
        self.count_lbl.setFont(QFont("Poppins", 9, QFont.Bold))
        self.count_lbl.setStyleSheet("background: transparent; color: #8C6A7B;")

        clear_btn = QPushButton(_("buttons.clear_all"))
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #8C6A7B;
                font-family: Poppins;
                font-size: 9pt;
                font-weight: bold;
                border: none;
                padding: 0px;
            }}
            QPushButton:hover {{
                color: #ffffff;
            }}
        """)
        clear_btn.clicked.connect(lambda: self._confirm_clear(dlg))

        bottom_bar.addWidget(self.count_lbl)
        bottom_bar.addStretch()
        bottom_bar.addWidget(clear_btn)

        layout.addWidget(bottom_widget)

        # Set Table spacing & content margins to align properly with the bottom bar
        layout.setContentsMargins(0, 0, 0, 0)
        self.table.setViewportMargins(0, 0, 0, 0)

        # Defer table population so dialog shows instantly
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._populate_table)

        dlg.exec()

        # Remove overlay when dialog closes
        overlay.hide()
        overlay.deleteLater()

    def _on_section_resized(self, logicalIndex, oldSize, newSize):
        if getattr(self, '_resizing_guard', False): return

        # Establish sensible limits to prevent vanishing columns or overlapping
        limits = {
            1: (150, 400), # File Name
            2: (100, 200), # Date
            3: (60, 150),  # Size
        }

        if logicalIndex in limits:
            min_w, max_w = limits[logicalIndex]
            if newSize > max_w:
                self._resizing_guard = True
                self.table.horizontalHeader().resizeSection(logicalIndex, max_w)
                self._resizing_guard = False
            elif newSize < min_w:
                self._resizing_guard = True
                self.table.horizontalHeader().resizeSection(logicalIndex, min_w)
                self._resizing_guard = False

    def _populate_table(self):
        self.table.setUpdatesEnabled(False)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        font_main = QFont("Poppins", 9)
        font_sub = QFont("Poppins", 8)
        font_bold = QFont("Poppins", 8, QFont.Bold)
        brush_gray = QBrush(QColor("#aaaaaa"))

        for entry in self.history:
            row = self.table.rowCount()
            self.table.insertRow(row)

            fp = entry.get("file_path", "")
            raw_name = os.path.basename(fp) if fp else (entry.get("title") or "Unknown")

            dummy_item = QTableWidgetItem("")
            dummy_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            name_item = QTableWidgetItem(raw_name)
            name_item.setFont(font_main)
            name_item.setData(Qt.UserRole, entry)

            date_item = QTableWidgetItem(entry.get("date", "—"))
            date_item.setFont(font_sub)
            date_item.setForeground(brush_gray)

            size_item = QTableWidgetItem(entry.get("size", "—"))
            size_item.setFont(font_sub)
            size_item.setForeground(brush_gray)

            size_item.setData(Qt.UserRole, entry.get("size_bytes", 0))

            status_key = entry.get("status", STATUS_COMPLETED)
            status_label = _(f"history.status_{status_key}", default=status_key.capitalize())
            s_color = TEXT_COLOR

            status_item = QTableWidgetItem(status_label)
            status_item.setFont(font_bold)
            status_item.setForeground(QBrush(QColor(s_color)))

            self.table.setItem(row, 0, dummy_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, date_item)
            self.table.setItem(row, 3, size_item)
            self.table.setItem(row, 4, status_item)

        self.table.setSortingEnabled(True)
        self.count_lbl.setText(f"{len(self.history)} item(s)")

        header = self.table.horizontalHeader()
        self._on_sort_changed(header.sortIndicatorSection(), header.sortIndicatorOrder())
        self.table.setUpdatesEnabled(True)

    def _on_sort_changed(self, index, order):
        if getattr(self, '_sorting_guard', False): return

        if index == 0:
            self._sorting_guard = True
            self.table.horizontalHeader().setSortIndicator(1, order)
            self._sorting_guard = False
            return
            
        labels = ["", _("history.file_name"), _("history.date"), _("history.size"), _("history.status")]
        for i in range(1, 5):
            item = self.table.horizontalHeaderItem(i)
            if item:
                if i == index:
                    arrow = " ▲" if order == Qt.AscendingOrder else " ▼"
                    item.setText(labels[i] + arrow)
                else:
                    item.setText(labels[i])

    # Context menu & Actions

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
        menu.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {HEADER_BG_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 6px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                font-family: Poppins;
                font-size: 9pt;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {BUTTON_COLOR};
                border-radius: 4px;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {WINDOW_BG_COLOR};
                margin: 4px 0px;
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

    # Remove / clear

    def _confirm_remove_selected(self):
        entries = self._get_selected_entries()
        if not entries:
            return

        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QWidget, QFrame
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont, QCursor

        dlg = QDialog(self.table)
        parent_geo = self.gui.geometry()
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

        title_lbl = QLabel(_("buttons.remove_files"))
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

        content = QWidget(main_frame)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        frame_layout.addWidget(content)

        lbl = QLabel(_("history.confirm_remove"))
        lbl.setFont(QFont("Poppins", 10))
        lbl.setWordWrap(True)
        lbl.setFixedWidth(300)
        layout.addWidget(lbl)

        from app.config import CHECKMARK_ICON_PATH
        chk = QCheckBox(_("buttons.remove_from_disk"))
        chk.setFont(QFont("Poppins", 9))
        chk.setStyleSheet(f"""
            QCheckBox {{
                color: {TEXT_COLOR};
                font-family: Poppins;
                font-size: 9pt;
                background: transparent;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                background-color: #1a000e;
            }}
            QCheckBox::indicator:checked {{
                background-color: {BUTTON_COLOR};
                image: url("{CHECKMARK_ICON_PATH.as_posix()}");
            }}
        """)
        layout.addWidget(chk)

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

        del_btn = QPushButton(_("buttons.delete"))
        del_btn.setFixedSize(90, 26)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(_ok_style)
        del_btn.clicked.connect(lambda: self._do_remove(entries, chk.isChecked(), dlg))

        cancel_btn = QPushButton(_("buttons.cancel"))
        cancel_btn.setFixedSize(90, 26)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(_cancel_style)
        cancel_btn.clicked.connect(dlg.reject)

        btn_row.addWidget(del_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        dlg.exec()

    def _do_remove(self, entries, delete_disk, dlg):
        for entry in entries:
            if delete_disk:
                fp = entry.get("file_path")
                if fp and os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception as e:
                        debug_print(f"Failed to delete {fp}: {e}")
            self.remove_entry_by_ref(entry)
            
        self._populate_table()
        dlg.accept()

    def _confirm_clear(self, parent):
        # Delegate message layout showing to modern update dialog helper style
        from app.gui.dialogs.update import UpdateFlow

        def on_yes():
            self.clear_history()
            self._populate_table()

        updater_ui = UpdateFlow(self.gui, parent)
        updater_ui._show_message(
            parent,
            _("history.clear_history_title"),
            _("history.confirm_clear_history"),
            msg_type="ask",
            on_yes=on_yes
        )
