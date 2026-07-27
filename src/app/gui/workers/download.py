import os
from PySide6.QtCore import QObject, Signal, Slot, QThreadPool

from PySide6.QtCore import QRunnable, Signal, Slot, QObject
from app.core.downloader import video_downloader
from app.core.transcoder import transcoder

class WorkerSignals(QObject):
    finished = Signal(bool, object, str)
    progress = Signal(str, int)

class DownloadWorker(QRunnable):
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
    def __init__(self, input_file, encoder_selection):
        super().__init__()
        self.input_file = input_file
        self.encoder_selection = encoder_selection
        self.signals = WorkerSignals()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True
        transcoder.cancel_encoding()

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

        success, err = transcoder.encode_video(
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
from app.utils.debug import debug_print
from app.gui.dialogs.history import STATUS_COMPLETED, STATUS_ERROR, STATUS_CANCELLED

class DownloadController(QObject):
    """Manages video downloading and encoding logic"""
    
    download_finished = Signal(bool, str, str)
    encode_finished = Signal(bool, str, str)
    update_progress = Signal(str, int)
    task_completed = Signal(str, bool)
    add_history_entry = Signal(str, str, str, str, str)
    
    def __init__(self, threadpool=None):
        super().__init__()
        self.threadpool = threadpool or QThreadPool.globalInstance()
        self.current_worker = None
        self.is_downloading = False
        
    def download_video(self, url, out_path, preset, encoding_enabled, download_section=None, title="Unknown Title", encoder_selection="Auto"):
        """Start downloading video"""
        # Normalize out_path to be extension-less
        known_exts = {".mp4", ".mkv", ".webm", ".avi", ".m4v", ".wav", ".mp3", ".m4a"}
        while True:
            root_out, ext_out = os.path.splitext(out_path)
            if ext_out.lower() in known_exts:
                out_path = root_out
            else:
                break
                
        self.is_downloading = True
        
        worker = DownloadWorker(url, out_path, preset, encoding_enabled, download_section)
        worker.meta_title = title
        worker.meta_url = url
        worker.meta_preset = preset
        worker.meta_encoding_enabled = encoding_enabled
        worker.meta_encoder_selection = encoder_selection
        
        worker.signals.progress.connect(self.update_progress.emit)
        worker.signals.finished.connect(lambda s, f, e: self.on_download_finished(s, f, e, worker))
        
        self.current_worker = worker
        self.threadpool.start(worker)
        return worker
        
    @Slot(bool, object, str, object)
    def on_download_finished(self, success, final_path, err, worker):
        """Handle download completion"""
        title = getattr(worker, 'meta_title', 'Unknown Title')
        url = getattr(worker, 'meta_url', '')
        preset = getattr(worker, 'meta_preset', '')
        encoding_enabled = getattr(worker, 'meta_encoding_enabled', False)
        encoder_selection = getattr(worker, 'meta_encoder_selection', 'Auto')
        
        if success and final_path:
            if "Audio" not in preset and encoding_enabled and encoder_selection != "Auto":
                self.encode_video(final_path, encoder_selection, title, url, preset)
            else:
                self.add_history_entry.emit(title, url, final_path, preset, STATUS_COMPLETED)
                self.task_completed.emit("Download complete!", True)
        else:
            status = STATUS_CANCELLED if err and "cancelled" in err.lower() else STATUS_ERROR
            self.add_history_entry.emit(title, url, final_path or "", preset, status)
            self.task_completed.emit(err or "Download failed", False)
            
        self.download_finished.emit(success, final_path or "", err or "")
            
    def encode_video(self, input_path, encoder_selection, title, url, preset):
        """Start encoding video"""
        self.update_progress.emit("Preparing to encode...", 0)
        
        worker = EncodeWorker(input_path, encoder_selection)
        worker.meta_title = title
        worker.meta_url = url
        worker.meta_preset = preset
        
        worker.signals.progress.connect(self.update_progress.emit)
        worker.signals.finished.connect(lambda s, f, e: self.on_encode_finished(s, f, e, worker))
        
        self.current_worker = worker
        self.threadpool.start(worker)
        return worker
        
    @Slot(bool, object, str, object)
    def on_encode_finished(self, success, final_path, err, worker):
        """Handle encode completion"""
        title = getattr(worker, 'meta_title', 'Unknown Title')
        url = getattr(worker, 'meta_url', '')
        preset = getattr(worker, 'meta_preset', '')
        
        if success:
            self.add_history_entry.emit(title, url, final_path, preset, STATUS_COMPLETED)
            self.task_completed.emit("Encoding complete!", True)
        else:
            status = STATUS_CANCELLED if err and "cancelled" in err.lower() else STATUS_ERROR
            self.add_history_entry.emit(title, url, final_path or "", preset, status)
            self.task_completed.emit(err or "Encoding failed", False)
            
        self.encode_finished.emit(success, final_path or "", err or "")
        
    def cancel_current_task(self):
        """Cancel the currently running worker"""
        if self.current_worker:
            self.current_worker.cancel()
            self.current_worker = None
        self.is_downloading = False
