import os
import urllib.request
import zipfile
import tempfile
import threading
import shutil
from app.config import BIN_PATH, YTDLP_PATH, FFMPEG_PATH
from app.utils.debug import debug_print

import sys
import tarfile

if sys.platform == "win32":
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    FFMPEG_EXT = ".zip"
else:
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"
    FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    FFMPEG_EXT = ".tar.xz"

CHUNK_SIZE = 65536  # 64 KB per read chunk

def download_file(url, dest_path, cancel_event=None):
    """Download file in chunks; abort on cancel_event."""
    req = urllib.request.Request(url, headers={'User-Agent': 'VidMuncher-Updater/1.0'})
    with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
        while True:
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Download cancelled by user.")
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            out_file.write(chunk)

class DependencyUpdater:
    def __init__(self):
        self.is_updating = False
        self._cancel_event = threading.Event()
        self._partial_files = []

    def cancel_update(self):
        """Signal update thread to stop; clean partials."""
        self._cancel_event.set()
        debug_print("Update cancellation requested.")

    def check_updates(self, result_callback):
        """
        Check versions async.
        result_callback: function(has_update, local_ver, remote_ver, error_msg)
        """
        def check_thread():
            try:
                import json
                import subprocess

                debug_print("Updater: checking yt-dlp version from GitHub...")
                req = urllib.request.Request(
                    "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
                    headers={'User-Agent': 'VidMuncher-Updater/1.0'}
                )
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    remote_ver = data.get('tag_name', 'Unknown')

                req_ff = urllib.request.Request(
                    "https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/latest",
                    headers={'User-Agent': 'VidMuncher-Updater/1.0'}
                )
                ffmpeg_needs_update = False
                remote_ff_ver = "Unknown"
                local_ff_ver = "Not installed"
                with urllib.request.urlopen(req_ff) as response:
                    ff_data = json.loads(response.read().decode('utf-8'))
                    ff_published = ff_data.get('published_at', '')
                    if ff_published:
                        remote_ff_ver = ff_published[:10]
                    
                if os.path.exists(FFMPEG_PATH):
                    if ff_published:
                        from datetime import datetime, timezone
                        try:
                            dt = datetime.strptime(ff_published, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            remote_time = dt.timestamp()
                            local_time = os.path.getmtime(FFMPEG_PATH)
                            local_ff_ver = datetime.fromtimestamp(local_time).strftime("%Y-%m-%d")
                            if remote_time > local_time + 3600:
                                ffmpeg_needs_update = True
                        except Exception:
                            pass
                else:
                    ffmpeg_needs_update = True

                local_ver = "Not installed"
                if os.path.exists(YTDLP_PATH):
                    try:
                        creationflags = 0x08000000 if os.name == 'nt' else 0
                        result = subprocess.run(
                            [str(YTDLP_PATH), '--version'],
                            capture_output=True, text=True, creationflags=creationflags
                        )
                        local_ver = result.stdout.strip()
                    except:
                        pass

                has_update = (local_ver != remote_ver) or ffmpeg_needs_update
                debug_print(f"Updater: check done — yt-dlp local={local_ver!r} remote={remote_ver!r}, ffmpeg needs_update={ffmpeg_needs_update}")
                result_callback(has_update, local_ver, remote_ver, local_ff_ver, remote_ff_ver, None)
            except Exception as e:
                debug_print(f"Updater: check failed — {e}")
                result_callback(False, "Unknown", "Unknown", "Unknown", "Unknown", str(e))

        threading.Thread(target=check_thread, daemon=True).start()

    def download_updates(self, progress_callback, complete_callback):
        """Async yt-dlp & FFmpeg update."""
        if self.is_updating:
            return

        self.is_updating = True
        self._cancel_event.clear()
        self._partial_files.clear()

        def update_thread():
            try:
                debug_print(f"Updater: starting download — yt-dlp from {YTDLP_URL}")
                os.makedirs(BIN_PATH, exist_ok=True)

                progress_callback("Downloading latest yt-dlp...", 10)
                self._partial_files.append(str(YTDLP_PATH))
                download_file(YTDLP_URL, str(YTDLP_PATH), self._cancel_event)
                self._partial_files.clear()
                progress_callback("yt-dlp updated successfully.", 40)

                progress_callback("Downloading latest FFmpeg...", 50)
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = os.path.join(temp_dir, f"ffmpeg{FFMPEG_EXT}")
                    self._partial_files.append(str(FFMPEG_PATH))
                    download_file(FFMPEG_URL, zip_path, self._cancel_event)

                    progress_callback("Extracting FFmpeg...", 80)
                    
                    if FFMPEG_EXT == ".zip":
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            ffmpeg_exe_path = None
                            for file_info in zip_ref.infolist():
                                if file_info.filename.endswith("bin/ffmpeg.exe"):
                                    ffmpeg_exe_path = file_info.filename
                                    break

                            if ffmpeg_exe_path:
                                with zip_ref.open(ffmpeg_exe_path) as source:
                                    with open(FFMPEG_PATH, "wb") as target:
                                        shutil.copyfileobj(source, target)
                            else:
                                raise Exception("FFmpeg binary not found in the downloaded zip archive.")
                    elif FFMPEG_EXT == ".tar.xz":
                        with tarfile.open(zip_path, "r:xz") as tar_ref:
                            ffmpeg_bin_path = None
                            for member in tar_ref.getmembers():
                                if member.name.endswith("bin/ffmpeg"):
                                    ffmpeg_bin_path = member
                                    break
                            
                            if ffmpeg_bin_path:
                                source = tar_ref.extractfile(ffmpeg_bin_path)
                                with open(FFMPEG_PATH, "wb") as target:
                                    shutil.copyfileobj(source, target)
                            else:
                                raise Exception("ffmpeg not found in the downloaded tar archive.")
                                
                    if sys.platform != "win32":
                        os.chmod(YTDLP_PATH, 0o755)
                        os.chmod(FFMPEG_PATH, 0o755)

                self._partial_files.clear()
                progress_callback("Update complete!", 100)
                debug_print("Updater: all dependencies updated successfully.")
                complete_callback(True, "All dependencies updated successfully!")

            except InterruptedError:
                debug_print("Update cancelled — cleaning up partial files.")
                self._cleanup_partial_files()
                complete_callback(False, "Update cancelled.")
            except Exception as e:
                debug_print(f"Update failed: {str(e)}")
                self._cleanup_partial_files()
                complete_callback(False, f"Update failed: {str(e)}")
            finally:
                self.is_updating = False
                self._partial_files.clear()

        threading.Thread(target=update_thread, daemon=True).start()

    def _cleanup_partial_files(self):
        """Remove partially downloaded files."""
        for path in self._partial_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    debug_print(f"Removed partial file: {path}")
            except Exception as e:
                debug_print(f"Failed to remove partial file {path}: {e}")
        self._partial_files.clear()

updater = DependencyUpdater()

