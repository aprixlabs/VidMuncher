from PySide6.QtCore import QObject, QRunnable, Signal, Slot
import requests

from app.downloader import video_analyzer, video_downloader
from app.encoder import encoder_manager
from app.config import THUMBNAIL_TIMEOUT
from app.utils import debug_print


class WorkerSignals(QObject):
    """Signals for generic workers"""
    finished = Signal(bool, object, str)  # success, result_data, error_msg
    progress = Signal(str, int)           # status_text, percentage


class ThumbnailSignals(QObject):
    """Signals for thumbnail downloading"""
    data_ready = Signal(bytes)
    error = Signal(str)


class AnalyzeWorker(QRunnable):
    """Worker for analyzing video URLs"""
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.signals = WorkerSignals()
        self.is_cancelled = False

    def _progress_cb(self, status, val):
        if not self.is_cancelled:
            self.signals.progress.emit(status, int(val) if val is not None else 0)

    @Slot()
    def run(self):
        debug_print(f"AnalyzeWorker: start — {self.url}")
        success, data, err = video_analyzer.analyze_video(self.url, self._progress_cb)
        debug_print(f"AnalyzeWorker: done — success={success}, err={err!r}")
        if not self.is_cancelled:
            self.signals.finished.emit(success, data, err or "")


class ThumbnailWorker(QRunnable):
    """Worker for downloading thumbnails in the background"""
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


class DownloadWorker(QRunnable):
    """Worker for downloading videos"""
    def __init__(self, url, output_path, preset, h264_enabled, download_section=None):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.preset = preset
        self.h264_enabled = h264_enabled
        self.download_section = download_section
        self.signals = WorkerSignals()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True
        video_downloader.cancel_download()

    def _cancel_check(self):
        return self.is_cancelled

    def _progress_cb(self, status, val):
        self.signals.progress.emit(status, int(val) if val is not None else 0)

    @Slot()
    def run(self):
        debug_print(
            f"DownloadWorker: start — preset={self.preset}, "
            f"encode={self.h264_enabled}, section={self.download_section}"
        )
        success, final_path, err = video_downloader.download_video(
            self.url, self.output_path, self.preset, self.h264_enabled,
            self._progress_cb, self._cancel_check, self.download_section
        )
        debug_print(f"DownloadWorker: done — success={success}, path={final_path!r}, err={err!r}")
        self.signals.finished.emit(success, final_path, err or "")


class EncodeWorker(QRunnable):
    """Worker for encoding videos"""
    def __init__(self, input_file, encoder_selection):
        super().__init__()
        self.input_file = input_file
        self.encoder_selection = encoder_selection
        self.signals = WorkerSignals()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True
        encoder_manager.cancel_encoding()

    def _cancel_check(self):
        return self.is_cancelled

    def _progress_cb(self, status, val):
        self.signals.progress.emit(status, int(val) if val is not None else 0)

    @Slot()
    def run(self):
        import os
        base_path = os.path.splitext(self.input_file)[0]
        temp_path = base_path + "_temp.mp4"
        final_path = base_path + ".mp4"

        debug_print(f"EncodeWorker: start — encoder={self.encoder_selection}, input={self.input_file!r}")

        success, err = encoder_manager.encode_video(
            self.input_file, temp_path, self.encoder_selection,
            self._progress_cb, self._cancel_check
        )

        if success:
            try:
                if self.input_file != final_path and os.path.exists(self.input_file):
                    os.remove(self.input_file)

                if os.path.exists(temp_path):
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    os.rename(temp_path, final_path)

                debug_print(f"EncodeWorker: finalized — {final_path!r}")
            except Exception as e:
                success = False
                err = f"Failed to finalize file: {e}"
                final_path = None
                debug_print(f"EncodeWorker: finalize error — {e}")
        else:
            final_path = None
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            debug_print(f"EncodeWorker: encoding failed — {err!r}")

        self.signals.finished.emit(success, final_path, err or "")
