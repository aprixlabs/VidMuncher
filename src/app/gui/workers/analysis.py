from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable
import datetime
from app.core.downloader import video_analyzer
from app.utils.debug import debug_print
from app.utils.formatting import format_file_size

class WorkerSignals(QObject):
    finished = Signal(bool, object, str)
    progress = Signal(str, int)

class AnalyzeWorker(QRunnable):
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

class AnalysisWorker(QObject):
    """Manages video analysis logic and signals"""
    
    analysis_finished = Signal(bool, object, str)
    update_progress = Signal(str, int)
    
    def __init__(self, threadpool=None):
        super().__init__()
        self.threadpool = threadpool or QThreadPool.globalInstance()
        self.current_worker = None
        self.video_data = {}
        
    def cancel_current_task(self):
        """Cancel the active analysis worker if any"""
        if self.current_worker and hasattr(self.current_worker, 'is_cancelled'):
            self.current_worker.is_cancelled = True

    def analyze_video(self, url):
        """Start video analysis"""
        debug_print(f"analyze_video: starting — {url!r}")
        
        self.update_progress.emit("Getting information...", 0)
        
        worker = AnalyzeWorker(url)
        worker.signals.progress.connect(self.update_progress.emit)
        worker.signals.finished.connect(self.on_analyze_finished)
        
        self.current_worker = worker
        self.threadpool.start(worker)
        return worker
        
    @Slot(bool, object, str)
    def on_analyze_finished(self, success, data, err):
        """Handle analysis completion"""
        self.current_worker = None
        
        if success and data:
            self.video_data = data
            title = data.get("title", "N/A")
            debug_print(f"on_analyze_finished: success — title={title!r}")
        else:
            debug_print(f"on_analyze_finished: failed — {err!r}")
            self.video_data = {}
            
        self.analysis_finished.emit(success, data, err)
        
    def format_video_info(self):
        """Format video data into HTML for display"""
        if not self.video_data:
            return ""
            
        data = self.video_data
        title = data.get("title", "N/A")
        author = data.get("uploader") or data.get("creator") or "Unknown"
        platform = data.get("extractor_key", "Unknown")

        upload_date = data.get("upload_date", "")
        if upload_date and len(upload_date) == 8:
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        else:
            upload_date = "Unknown"

        duration = data.get("duration")
        if duration:
            duration_str = str(datetime.timedelta(seconds=int(duration)))
        else:
            duration_str = "Unknown"

        max_res = "Unknown"
        formats = data.get("formats", [])
        best_video = None
        max_pixels = 0
        for f in formats:
            if f.get("vcodec") != "none" and f.get("width") and f.get("height"):
                pixels = f["width"] * f["height"]
                if pixels > max_pixels:
                    max_pixels = pixels
                    best_video = f

        if best_video:
            res_str = f"{best_video['height']}p"
            if best_video.get("fps"):
                res_str += f"{int(best_video['fps'])}"

            size = best_video.get("filesize_approx") or best_video.get("filesize")
            if not size and best_video.get("tbr") and data.get("duration"):
                size = int(best_video["tbr"] * 1000 / 8 * data["duration"])
            size_str = f"(~{format_file_size(size)})" if size else "(Size unknown)"

            max_res = f"{res_str} {size_str}"

        return (
            "<table cellpadding='1' cellspacing='0' style='border: none;'>"
            f"<tr><td width='75'><b>Title</b></td><td width='10'><b>:</b></td><td>{title}</td></tr>"
            f"<tr><td><b>Author</b></td><td><b>:</b></td><td>{author} ({platform})</td></tr>"
            f"<tr><td><b>Uploaded</b></td><td><b>:</b></td><td>{upload_date}</td></tr>"
            f"<tr><td><b>Duration</b></td><td><b>:</b></td><td>{duration_str}</td></tr>"
            f"<tr><td><b>Max Res</b></td><td><b>:</b></td><td>{max_res}</td></tr>"
            "</table>"
        )
