from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from app.config import APP_NAME, APP_VERSION

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("TitleBar")
        self.setStyleSheet("""
            QWidget#TitleBar {
                background-color: #2b2b2b;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border: none;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0)

        title_lbl = QLabel(f"{APP_NAME} {APP_VERSION}")
        title_lbl.setFont(QFont("Poppins", 9, QFont.Bold))
        title_lbl.setStyleSheet("color: #cccccc;")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(title_lbl, 1)

        btn_style = """
            QPushButton { border-radius: 7px; border: none; }
            QPushButton#closeBtn { background-color: #FF5F56; }
            QPushButton#closeBtn:hover { background-color: #E0443E; }
            QPushButton#minBtn { background-color: #FFBD2E; }
            QPushButton#minBtn:hover { background-color: #DEA125; }
        """
        self.min_btn = QPushButton("", self)
        self.min_btn.setObjectName("minBtn")
        self.min_btn.setFixedSize(14, 14)
        self.min_btn.setStyleSheet(btn_style)
        self.min_btn.setCursor(Qt.PointingHandCursor)

        self.close_btn = QPushButton("", self)
        self.close_btn.setObjectName("closeBtn")
        self.close_btn.setFixedSize(14, 14)
        self.close_btn.setStyleSheet(btn_style)
        self.close_btn.setCursor(Qt.PointingHandCursor)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.min_btn)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            win = self.window()
            if win and hasattr(win, "windowHandle") and win.windowHandle():
                win.windowHandle().startSystemMove()
            event.accept()
