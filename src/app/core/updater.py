import os
import urllib.request
import zipfile
import tempfile
import threading
import shutil
from app.config import BIN_PATH, YTDLP_PATH, FFMPEG_PATH, DENO_PATH
from app.utils.debug import debug_print

import sys
import tarfile

if sys.platform == "win32":
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    FFMPEG_EXT = ".zip"
    DENO_URL = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip"
else:
    YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"
    FFMPEG_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
    FFMPEG_EXT = ".tar.xz"
    DENO_URL = "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip"

CHUNK_SIZE = 65536  # 64 KB per read chunk

def download_file(url, dest_path, cancel_event=None, progress_cb=None, base_pct=0, total_pct_range=30):
    """Download file in chunks; abort on cancel_event. Report progress if callback given."""
    req = urllib.request.Request(url, headers={'User-Agent': 'VidMuncher-Updater/1.0'})
    with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, 'wb') as out_file:
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        while True:
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Download cancelled by user.")
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if progress_cb and total_size > 0:
                # Calculate chunk percentage within the overall allowed range
                pct = base_pct + int((downloaded / total_size) * total_pct_range)
                progress_cb(None, pct)

class DependencyUpdater:
    def __init__(self):
        self.is_updating = False
        self._cancel_event = threading.Event()
        self._partial_files = []
        self._pending_updates = {'ytdlp': True, 'ffmpeg': True, 'deno': True}

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
                from app.config.app_info import APP_VERSION

                debug_print("Updater: checking component versions from GitHub...")

                # 1. Check App version
                remote_app_ver = "Unknown"
                local_app_ver = APP_VERSION
                try:
                    req_app = urllib.request.Request(
                        "https://api.github.com/repos/aprixlabs/VidMuncher/releases/latest",
                        headers={'User-Agent': 'VidMuncher-Updater/1.0'}
                    )
                    with urllib.request.urlopen(req_app) as response:
                        app_data = json.loads(response.read().decode('utf-8'))
                        tag = app_data.get('tag_name', 'Unknown')
                        if tag.startswith('v'):
                            remote_app_ver = tag[1:]
                        else:
                            remote_app_ver = tag
                except Exception as e:
                    debug_print(f"Updater: App version check failed — {e}")

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
                            # If our local extraction time is newer or the same day as remote, don't trigger downgrade
                            elif local_ff_ver >= remote_ff_ver:
                                local_ff_ver = remote_ff_ver
                        except Exception:
                            pass
                else:
                    ffmpeg_needs_update = True

                req_deno = urllib.request.Request(
                    "https://api.github.com/repos/denoland/deno/releases/latest",
                    headers={'User-Agent': 'VidMuncher-Updater/1.0'}
                )
                deno_needs_update = False
                remote_deno_ver = "Unknown"
                local_deno_ver = "Not installed"
                with urllib.request.urlopen(req_deno) as response:
                    deno_data = json.loads(response.read().decode('utf-8'))
                    remote_deno_ver = deno_data.get('tag_name', 'Unknown')

                if os.path.exists(DENO_PATH):
                    try:
                        creationflags = 0x08000000 if os.name == 'nt' else 0
                        result = subprocess.run(
                            [str(DENO_PATH), '--version'],
                            capture_output=True, text=True, creationflags=creationflags
                        )
                        # deno --version outputs multiple lines, first line is like "deno 1.40.3 (release, x86_64-pc-windows-msvc)"
                        first_line = result.stdout.split('\n')[0]
                        local_deno_ver = 'v' + first_line.split(' ')[1]
                        if local_deno_ver != remote_deno_ver:
                            deno_needs_update = True
                    except:
                        pass
                else:
                    deno_needs_update = True

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

                def is_newer(remote, local):
                    if local == "Not installed" or remote == "Unknown": return True
                    import re
                    def parse(v): return [int(x) if x.isdigit() else x for x in re.split(r'[.-]', re.sub(r'^[vV]', '', str(v)))]
                    try: return parse(remote) > parse(local)
                    except: return remote != local

                app_needs_update = is_newer(remote_app_ver, local_app_ver)
                ytdlp_needs_update = is_newer(remote_ver, local_ver)
                deno_needs_update = is_newer(remote_deno_ver, local_deno_ver)
                
                # FFmpeg has special handling already via ffmpeg_needs_update flag, 
                # but we'll also apply the fallback logic just in case
                ff_is_newer = ffmpeg_needs_update if "ffmpeg_needs_update" in locals() else is_newer(remote_ff_ver, local_ff_ver)

                has_update = app_needs_update or ytdlp_needs_update or ff_is_newer or deno_needs_update
                self._pending_updates['app'] = app_needs_update
                self._pending_updates['ytdlp'] = ytdlp_needs_update
                self._pending_updates['ffmpeg'] = ff_is_newer
                self._pending_updates['deno'] = deno_needs_update
                debug_print(f"Updater: check done — App local={local_app_ver!r} remote={remote_app_ver!r}, yt-dlp local={local_ver!r} remote={remote_ver!r}, ffmpeg local={local_ff_ver!r} remote={remote_ff_ver!r}, deno local={local_deno_ver!r} remote={remote_deno_ver!r}")
                result_callback(has_update, local_app_ver, remote_app_ver, local_ver, remote_ver, local_ff_ver, remote_ff_ver, local_deno_ver, remote_deno_ver, None)
            except Exception as e:
                debug_print(f"Updater: check failed — {e}")
                result_callback(False, "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", str(e))

        threading.Thread(target=check_thread, daemon=True).start()

    def download_updates(self, progress_callback, complete_callback):
        """Async yt-dlp & FFmpeg update."""
        if self.is_updating:
            return

        self.is_updating = True
        self._cancel_event.clear()
        self._partial_files.clear()

        def update_thread():
            from app.utils.localization import _
            try:
                os.makedirs(BIN_PATH, exist_ok=True)

                if self._pending_updates.get('ytdlp', True) or not os.path.exists(YTDLP_PATH):
                    debug_print(f"Updater: starting download — yt-dlp from {YTDLP_URL}")
                    progress_callback(_("setup.download_ytdlp"), 10)
                    self._partial_files.append(str(YTDLP_PATH))
                    download_file(YTDLP_URL, str(YTDLP_PATH), self._cancel_event, progress_callback, 10, 30)
                    self._partial_files.clear()
                    progress_callback(_("setup.ytdlp_success"), 40)
                else:
                    debug_print("Updater: skipping yt-dlp download (up to date)")

                if self._pending_updates.get('ffmpeg', True) or not os.path.exists(FFMPEG_PATH):
                    debug_print(f"Updater: starting download — ffmpeg from {FFMPEG_URL}")
                    progress_callback(_("setup.download_ffmpeg"), 50)
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_path = os.path.join(temp_dir, f"ffmpeg{FFMPEG_EXT}")
                        self._partial_files.append(str(FFMPEG_PATH))
                        download_file(FFMPEG_URL, zip_path, self._cancel_event, progress_callback, 50, 30)

                        progress_callback(_("setup.extract_ffmpeg"), 80)

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
                else:
                    debug_print("Updater: skipping ffmpeg download (up to date)")

                if self._pending_updates.get('deno', True) or not os.path.exists(DENO_PATH):
                    debug_print(f"Updater: starting download — deno from {DENO_URL}")
                    progress_callback(_("setup.download_deno"), 85)
                    with tempfile.TemporaryDirectory() as temp_dir:
                        deno_zip = os.path.join(temp_dir, "deno.zip")
                        self._partial_files.append(str(DENO_PATH))
                        download_file(DENO_URL, deno_zip, self._cancel_event, progress_callback, 85, 10)

                        progress_callback(_("setup.extract_deno"), 95)
                        with zipfile.ZipFile(deno_zip, 'r') as zip_ref:
                            deno_exe_path = None
                            for file_info in zip_ref.infolist():
                                if file_info.filename.endswith("deno.exe") or file_info.filename.endswith("deno"):
                                    deno_exe_path = file_info.filename
                                    break

                            if deno_exe_path:
                                with zip_ref.open(deno_exe_path) as source:
                                    with open(DENO_PATH, "wb") as target:
                                        shutil.copyfileobj(source, target)
                            else:
                                raise Exception("Deno binary not found in the downloaded zip archive.")
                else:
                    debug_print("Updater: skipping deno download (up to date)")

                if sys.platform != "win32":
                    if os.path.exists(YTDLP_PATH): os.chmod(YTDLP_PATH, 0o755)
                    if os.path.exists(FFMPEG_PATH): os.chmod(FFMPEG_PATH, 0o755)
                    if os.path.exists(DENO_PATH): os.chmod(DENO_PATH, 0o755)

                self._partial_files.clear()
                progress_callback(_("setup.update_complete"), 100)
                debug_print("Updater: all components updated successfully.")
                complete_callback(True, _("setup.update_success"))

            except InterruptedError:
                debug_print("Update cancelled — cleaning up partial files.")
                self._cleanup_partial_files()
                complete_callback(False, _("setup.update_cancelled"))
            except Exception as e:
                debug_print(f"Update failed: {str(e)}")
                self._cleanup_partial_files()
                complete_callback(False, str(e))
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

