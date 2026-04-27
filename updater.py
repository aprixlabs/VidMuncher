import os
import urllib.request
import zipfile
import tempfile
import threading
import shutil
from config import BIN_PATH, YTDLP_PATH, FFMPEG_PATH
from utils import debug_print

YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_ZIP_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

CHUNK_SIZE = 65536  # 64 KB per read chunk

def download_file(url, dest_path, cancel_event=None):
    """Download a file in chunks, respecting cancel_event if provided."""
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
        """Signal the update thread to stop and clean up partial files."""
        self._cancel_event.set()
        debug_print("Update cancellation requested.")

    def check_updates(self, result_callback):
        """
        Check for updates and return local and remote versions.
        result_callback: function(has_update, local_ver, remote_ver, error_msg)
        """
        def check_thread():
            try:
                import json
                import subprocess

                req = urllib.request.Request(
                    "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
                    headers={'User-Agent': 'VidMuncher-Updater/1.0'}
                )
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    remote_ver = data.get('tag_name', 'Unknown')

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

                has_update = (local_ver != remote_ver) or (not os.path.exists(FFMPEG_PATH))
                result_callback(has_update, local_ver, remote_ver, None)
            except Exception as e:
                result_callback(False, "Unknown", "Unknown", str(e))

        threading.Thread(target=check_thread, daemon=True).start()

    def download_updates(self, progress_callback, complete_callback):
        """Download and install yt-dlp and FFmpeg in a background thread."""
        if self.is_updating:
            return

        self.is_updating = True
        self._cancel_event.clear()
        self._partial_files.clear()

        def update_thread():
            try:
                os.makedirs(BIN_PATH, exist_ok=True)

                progress_callback("Downloading latest yt-dlp...", 10)
                self._partial_files.append(str(YTDLP_PATH))
                download_file(YTDLP_URL, str(YTDLP_PATH), self._cancel_event)
                self._partial_files.clear()
                progress_callback("yt-dlp updated successfully.", 40)

                progress_callback("Downloading latest FFmpeg...", 50)
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = os.path.join(temp_dir, "ffmpeg.zip")
                    self._partial_files.append(str(FFMPEG_PATH))
                    download_file(FFMPEG_ZIP_URL, zip_path, self._cancel_event)

                    progress_callback("Extracting FFmpeg...", 80)
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
                            raise Exception("ffmpeg.exe not found in the downloaded zip archive.")

                self._partial_files.clear()
                progress_callback("Update complete!", 100)
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
        """Remove any partially downloaded files to prevent corruption."""
        for path in self._partial_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    debug_print(f"Removed partial file: {path}")
            except Exception as e:
                debug_print(f"Failed to remove partial file {path}: {e}")
        self._partial_files.clear()

updater = DependencyUpdater()
