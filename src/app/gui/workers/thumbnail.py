from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable, Qt
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
import requests
from app.config import Layout, THUMBNAIL_TIMEOUT
from app.utils.debug import debug_print

class ThumbnailSignals(QObject):
    data_ready = Signal(bytes)
    error = Signal(str)

class ThumbnailWorker(QRunnable):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.signals = ThumbnailSignals()

    @Slot()
    def run(self):
        debug_print(f"ThumbnailWorker: fetching {self.url}")
        try:
            img_data = requests.get(self.url, timeout=THUMBNAIL_TIMEOUT).content
            debug_print(f"ThumbnailWorker: received {len(img_data)} bytes")
            self.signals.data_ready.emit(img_data)
        except Exception as e:
            debug_print(f"ThumbnailWorker: failed — {e}")
            self.signals.error.emit(str(e))

class ThumbnailController(QObject):
    """Manages downloading and processing video thumbnails"""
    
    thumbnail_ready = Signal(QPixmap)
    
    def __init__(self, threadpool=None):
        super().__init__()
        self.threadpool = threadpool or QThreadPool.globalInstance()
        
    def download_thumbnail(self, thumbnail_url):
        """Start async download of thumbnail"""
        if not thumbnail_url:
            return
            
        worker = ThumbnailWorker(thumbnail_url)
        worker.signals.data_ready.connect(self.on_thumbnail_ready)
        self.threadpool.start(worker)
        return worker
        
    @Slot(bytes)
    def on_thumbnail_ready(self, img_data):
        """Process downloaded thumbnail data, scale and round corners"""
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

            self.thumbnail_ready.emit(rounded)
