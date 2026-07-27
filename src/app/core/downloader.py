"""
VidMuncher Downloader Module
yt-dlp download logic and progress tracking.
"""

import re
import json
import subprocess
import time
import requests

from app.config import (
    YTDLP_PATH,
    FFMPEG_PATH,
    USER_AGENT,
    EXTRACTOR_RETRIES,
    FRAGMENT_RETRIES,
    RETRY_SLEEP,
    ANALYZE_TIMEOUT,
    THUMBNAIL_TIMEOUT,
    PROGRESS_UPDATE_THRESHOLD
)
from app.utils.debug import debug_print
from app.utils.filesystem import get_extension_from_preset, get_unique_filename, get_unique_filename_without_ext, find_downloaded_file

class VideoAnalyzer:
    """Handles video analysis and information extraction."""

    def __init__(self):
        self.active_processes = []

    def analyze_video(self, url, progress_callback=None):
        """Extract video information via yt-dlp analyze."""
        try:
            if progress_callback:
                progress_callback("Getting information...", 0)

            analyze_cmd = self._build_analyze_command(url)
            
            debug_print(f"Analyze command: {' '.join(analyze_cmd)}")
            
            result = subprocess.run(
                analyze_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=ANALYZE_TIMEOUT,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )
            
            video_data = json.loads(result.stdout)
            
            debug_print(f"Successfully analyzed video: {video_data.get('title', 'Unknown')}")
            
            return True, video_data, None
            
        except subprocess.TimeoutExpired:
            error_msg = "Timeout - URL took too long to analyze"
            debug_print(f"Analyze timeout after {ANALYZE_TIMEOUT} seconds")
            return False, None, error_msg
            
        except subprocess.CalledProcessError as e:
            error_msg = self._parse_ytdlp_error(e.stderr)
            debug_print(f"yt-dlp error: {e.stderr}")
            return False, None, error_msg
            
        except json.JSONDecodeError as e:
            error_msg = "Failed to parse video information"
            debug_print(f"JSON decode error: {str(e)}")
            return False, None, error_msg
            
        except Exception as e:
            error_msg = "Invalid URL or network error"
            debug_print(f"Analyze error: {str(e)}")
            return False, None, error_msg
    
    def _build_analyze_command(self, url):
        """Build yt-dlp analyze command"""
        return [
            str(YTDLP_PATH), "--dump-json", url,
            "--user-agent", USER_AGENT,
            "--extractor-retries", str(EXTRACTOR_RETRIES),
            "--fragment-retries", str(FRAGMENT_RETRIES),
            "--retry-sleep", str(RETRY_SLEEP),
            "--no-check-certificate",
            "--no-playlist"
        ]
    
    def _parse_ytdlp_error(self, stderr):
        """Parse yt-dlp stderr to user-friendly messages."""
        if "This video is unavailable" in stderr:
            return "Video unavailable or private"
        elif "Video unavailable" in stderr:
            return "Video not found or restricted"
        elif "Sign in to confirm your age" in stderr:
            return "Age-restricted video"
        else:
            return "Failed to get video info"

class VideoDownloader:
    """Handles video downloading with progress tracking."""
    
    def __init__(self):
        self.active_processes = []
        self.is_downloading = False
        self.current_process = None
        self.temp_files = []
    
    def download_video(self, url, output_path, preset, h264_enabled=True, progress_callback=None, cancel_check=None, download_section=None):
        """Download video with progress monitoring."""
        try:
            self.is_downloading = True
            self.temp_files.clear()
            
            # Strip %(ext)s placeholder if save_path_var already has it
            if output_path.endswith(".%(ext)s"):
                output_path = output_path[: -len(".%(ext)s")]

            # yt-dlp determines final extension; strip any pre-existing one to avoid double extensions (e.g. Video.mp4.webm)
            final_output = get_unique_filename_without_ext(output_path)
            
            debug_print(f"Download output base path: {final_output}")
            
            if progress_callback:
                progress_callback("Downloading...", 0)
            
            cmd = self._build_download_command(url, final_output, preset, download_section)
            
            debug_print(f"Download command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )
            
            self.active_processes.append(process)
            self.current_process = process
            
            self._monitor_download_progress(process, progress_callback, cancel_check, download_section)

            process.wait()

            if process in self.active_processes:
                self.active_processes.remove(process)

            debug_print(f"Download process finished with return code: {process.returncode}")

            if process.returncode == 0:
                debug_print("Download completed successfully")
                actual_path = find_downloaded_file(final_output) or final_output
                debug_print(f"Resolved actual file path: {actual_path}")
                return True, actual_path, None
            else:
                if cancel_check and cancel_check():
                    error_msg = "Download was cancelled by user"
                else:
                    error_msg = f"Download failed with return code: {process.returncode}"

                debug_print(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            debug_print(error_msg)
            return False, None, error_msg
        finally:
            self.is_downloading = False
            self.current_process = None
    
    def _build_download_command(self, url, output_path, preset, download_section=None):
        """Build yt-dlp download command."""
        cmd = [
            str(YTDLP_PATH), url, "-o", f"{output_path}.%(ext)s",
            "--no-playlist", "--progress",
            "--user-agent", USER_AGENT,
            "--extractor-retries", str(EXTRACTOR_RETRIES),
            "--fragment-retries", str(FRAGMENT_RETRIES),
            "--retry-sleep", str(RETRY_SLEEP),
            "--no-check-certificate",
            "--force-overwrites",
            "--downloader-args", "ffmpeg:-nostdin -y",
            "--ffmpeg-location", str(FFMPEG_PATH)
        ]
        
        if download_section:
            cmd.extend(["--download-sections", download_section])
        
        if "Audio" in preset:
            audio_format = preset.replace("Audio (", "").replace(")", "").strip()
            cmd.extend(["--extract-audio", "--audio-format", audio_format])
        elif preset != "Best Quality":
            height = preset.replace("p", "")
            cmd.extend(["-f", f"bestvideo[height={height}]+bestaudio/bestvideo[height<={height}]+bestaudio/best[height<={height}]"])
        else:
            cmd.extend(["-f", "bestvideo[height>=1080]+bestaudio/bestvideo[height>=720]+bestvideo/bestvideo+bestaudio/best"])
        
        return cmd
    
    def _monitor_download_progress(self, process, progress_callback, cancel_check, download_section=None):
        """Monitor download progress and handle cancellation."""
        stream_progress = {}
        current_stream = None
        total_streams = 0
        last_overall_progress = 0
        last_ffmpeg_update = 0
        
        section_duration = 0
        if download_section:
            try:
                times = download_section.replace('*', '').split('-')
                if len(times) == 2:
                    h1, m1, s1 = map(int, times[0].split(':'))
                    h2, m2, s2 = map(int, times[1].split(':'))
                    start_sec = h1 * 3600 + m1 * 60 + s1
                    end_sec = h2 * 3600 + m2 * 60 + s2
                    section_duration = max(1, end_sec - start_sec)
            except Exception as e:
                debug_print(f"Failed to parse section duration: {e}")

        for line in process.stdout:
            if cancel_check and cancel_check():
                debug_print("Download cancelled by user")
                break

            line = line.strip()
            debug_print(f"yt-dlp: {line}")

            if "[download] Destination:" in line:
                current_stream = self._detect_stream(line)
                if current_stream:
                    stream_progress[current_stream] = 0
                    total_streams = len(stream_progress)
                    debug_print(f"Detected stream: {current_stream}, Total streams: {total_streams}")

            elif line and "%" in line and "[download]" in line:
                progress = self._parse_progress_line(line, stream_progress, current_stream, total_streams, last_overall_progress, progress_callback)
                if progress is not None:
                    last_overall_progress = progress

            elif line and any(keyword in line.lower() for keyword in ['merger', 'merging']):
                if progress_callback:
                    progress_callback("Merging video and audio...", 95)
            elif line and any(keyword in line.lower() for keyword in ['extracting', 'converting']):
                if "webpage" not in line.lower() and progress_callback:
                    status = line[:50] + "..." if len(line) > 50 else line
                    progress_callback(status, None)
                    
            elif "[info]" in line and "Downloading" in line and "time ranges" in line:
                if progress_callback:
                    progress_callback("Preparing to download section...", 0)
                    
            elif "time=" in line and "bitrate=" in line:
                current_time = time.time()
                if current_time - last_ffmpeg_update > 0.2:
                    time_match = re.search(r'time=([\-\d:.]+)', line)
                    speed_match = re.search(r'speed=\s*([\d.x]+)', line)

                    if time_match and progress_callback:
                        time_str = time_match.group(1)
                        speed_str = speed_match.group(1) if speed_match else "Unknown"

                        if time_str.startswith('-'):
                            progress_callback("Seeking to section start... (This may take a while)", 0)
                        else:
                            progress_val = None
                            if section_duration > 0:
                                try:
                                    parts = time_str.split(':')
                                    if len(parts) == 3:
                                        h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                                        curr_sec = h * 3600 + m * 60 + s
                                        progress_val = min(100.0, (curr_sec / section_duration) * 100.0)
                                except:
                                    pass

                            if progress_val is not None:
                                progress_callback(f"Downloading section - {speed_str} - {progress_val:.1f}%", progress_val)
                            else:
                                progress_callback(f"Downloading section - {speed_str} - {time_str}", 0)

                    last_ffmpeg_update = current_time
    
    def _detect_stream(self, line):
        """Detect stream identifier from download line."""
        if ".f" in line and any(ext in line for ext in [".mp4", ".webm", ".m4a"]):
            stream_match = re.search(r'\.f(\d+)\.', line)
            if stream_match:
                return stream_match.group(1)
        else:
            return "single"
        return None
    
    def _parse_progress_line(self, line, stream_progress, current_stream, total_streams, last_progress, progress_callback):
        """Parse progress from yt-dlp output line."""
        try:
            percent_match = re.search(r'(\d+(?:\.\d+)?)%', line)
            if not percent_match:
                return None
            
            progress = float(percent_match.group(1))
            
            if current_stream:
                stream_progress[current_stream] = progress
            
            if total_streams > 0:
                if total_streams > 1:
                    overall_progress = sum(stream_progress.values()) / total_streams
                    completed_count = sum(1 for p in stream_progress.values() if p >= 100)
                    
                    if completed_count == 0:
                        phase = "Video stream"
                    elif completed_count == 1:
                        phase = "Audio stream"
                    else:
                        phase = "Finalizing"
                else:
                    overall_progress = progress
                    phase = "Downloading"
                
                speed_match = re.search(r'(\d+(?:\.\d+)?[KMGT]?i?B/s)', line)
                speed = speed_match.group(1) if speed_match else "Unknown"
                
                if abs(overall_progress - last_progress) >= PROGRESS_UPDATE_THRESHOLD or overall_progress == 100:
                    if progress_callback:
                        if total_streams > 1:
                            progress_callback(f"{phase} - {speed} - {overall_progress:.1f}%", overall_progress)
                        else:
                            progress_callback(f"{speed} - {overall_progress:.1f}%", overall_progress)
                    return overall_progress
            
        except Exception as e:
            debug_print(f"Progress parsing error: {e}")
        
        return None
    
    def cancel_download(self):
        """Cancel active download."""
        debug_print("Cancelling download...")
        self.is_downloading = False

        try:
            import sys
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/F', '/IM', 'yt-dlp.exe'],
                             capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                subprocess.run(['taskkill', '/F', '/IM', 'ffmpeg.exe'],
                             capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            else:
                subprocess.run(['killall', '-9', 'yt-dlp'], capture_output=True)
                subprocess.run(['killall', '-9', 'ffmpeg'], capture_output=True)
            debug_print("Killed all yt-dlp and ffmpeg processes system-wide")
        except Exception as e:
            debug_print(f"Error killing processes system-wide: {e}")

        if self.current_process:
            try:
                self.current_process.terminate()
                debug_print("Download process terminated")
                try:
                    self.current_process.wait(timeout=2)
                except:
                    try:
                        self.current_process.kill()
                        debug_print("Download process force killed")
                    except:
                        pass
            except Exception as e:
                debug_print(f"Error terminating download process: {e}")
    
    def cleanup_processes(self):
        """Clean up active download processes."""
        for process in self.active_processes[:]:
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
                self.active_processes.remove(process)
            except:
                pass

video_analyzer = VideoAnalyzer()
video_downloader = VideoDownloader()
