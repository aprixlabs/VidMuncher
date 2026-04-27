"""
VidMuncher Downloader Module
Contains yt-dlp download logic and progress tracking functionality
"""

import re
import json
import subprocess
import requests
from io import BytesIO
from PIL import Image, ImageTk

from config import (
    YTDLP_PATH,
    FFMPEG_PATH,
    USER_AGENT,
    REFERER,
    EXTRACTOR_RETRIES,
    FRAGMENT_RETRIES,
    RETRY_SLEEP,
    ANALYZE_TIMEOUT,
    THUMBNAIL_TIMEOUT,
    PROGRESS_UPDATE_THRESHOLD
)
from utils import debug_print, get_extension_from_preset, get_unique_filename, get_unique_filename_without_ext

class VideoAnalyzer:
    """Handles video analysis and information extraction"""

    def __init__(self):
        self.active_processes = []

    def analyze_video(self, url, progress_callback=None):
        """Analyze video URL and extract information"""
        try:
            if progress_callback:
                progress_callback("Getting information...", 0)
            
            # Build and run the analyze command
            analyze_cmd = self._build_analyze_command(url)
            
            debug_print(f"Analyze command: {' '.join(analyze_cmd)}")
            
            result = subprocess.run(
                analyze_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=ANALYZE_TIMEOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
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
            "--referer", REFERER,
            "--extractor-retries", str(EXTRACTOR_RETRIES),
            "--fragment-retries", str(FRAGMENT_RETRIES),
            "--retry-sleep", str(RETRY_SLEEP),
            "--no-check-certificate",
            "--no-playlist"
        ]
    
    def _parse_ytdlp_error(self, stderr):
        """Parse yt-dlp error messages and return user-friendly message"""
        if "This video is unavailable" in stderr:
            return "Video unavailable or private"
        elif "Video unavailable" in stderr:
            return "Video not found or restricted"
        elif "Sign in to confirm your age" in stderr:
            return "Age-restricted video"
        else:
            return "Failed to get video info"
    
    def download_thumbnail(self, thumbnail_url, size=(260, 130)):
        """
        Download and resize thumbnail image
        
        Args:
            thumbnail_url (str): URL of thumbnail image
            size (tuple): Target size (width, height)
            
        Returns:
            ImageTk.PhotoImage or None: Processed thumbnail image
        """
        try:
            debug_print(f"Downloading thumbnail from: {thumbnail_url}")
            
            img_data = requests.get(thumbnail_url, timeout=THUMBNAIL_TIMEOUT).content
            img = Image.open(BytesIO(img_data))
            img = img.resize(size, Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(img)
            
        except Exception as e:
            debug_print(f"Thumbnail download failed: {e}")
            return None

class VideoDownloader:
    """Handles video downloading with progress tracking"""
    
    def __init__(self):
        self.active_processes = []
        self.is_downloading = False
        self.current_process = None
        self.temp_files = []
    
    def download_video(self, url, output_path, preset, h264_enabled=True, progress_callback=None, cancel_check=None):
        """
        Download video with progress monitoring
        
        Args:
            url (str): Video URL
            output_path (str): Output file path (without extension)
            preset (str): Download quality preset
            h264_enabled (bool): Whether H264 encoding is enabled
            progress_callback (callable): Function to call with progress updates
            cancel_check (callable): Function to check if download should be cancelled
            
        Returns:
            tuple: (success: bool, final_path: str or None, error_message: str or None)
        """
        try:
            self.is_downloading = True
            self.temp_files.clear()
            
            # yt-dlp determines the final extension; strip any pre-existing one to avoid doubles (e.g. Video.mp4.webm)
            final_output = get_unique_filename_without_ext(output_path)
            
            debug_print(f"Download output base path: {final_output}")
            
            if progress_callback:
                progress_callback("Downloading...", 0)
            
            cmd = self._build_download_command(url, final_output, preset)
            
            debug_print(f"Download command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.active_processes.append(process)
            self.current_process = process
            
            self._monitor_download_progress(process, progress_callback, cancel_check)

            process.wait()

            if process in self.active_processes:
                self.active_processes.remove(process)

            debug_print(f"Download process finished with return code: {process.returncode}")

            if process.returncode == 0:
                debug_print("Download completed successfully")
                return True, final_output, None
            else:
                if process.returncode is None:
                    error_msg = "Download was interrupted"
                elif process.returncode == -15 or process.returncode == 1:
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
    
    def _build_download_command(self, url, output_path, preset):
        """Build yt-dlp download command"""
        cmd = [
            str(YTDLP_PATH), url, "-o", f"{output_path}.%(ext)s",
            "--no-playlist", "--progress",
            "--user-agent", USER_AGENT,
            "--referer", REFERER,
            "--extractor-retries", str(EXTRACTOR_RETRIES),
            "--fragment-retries", str(FRAGMENT_RETRIES),
            "--retry-sleep", str(RETRY_SLEEP),
            "--no-check-certificate",
            "--ffmpeg-location", str(FFMPEG_PATH)
        ]
        
        if "Audio" in preset:
            audio_format = preset.replace("Audio (", "").replace(")", "").strip()
            cmd.extend(["--extract-audio", "--audio-format", audio_format])
        elif preset != "Best Quality":
            height = preset.replace("p", "")
            cmd.extend(["-f", f"bestvideo[height={height}]+bestaudio/bestvideo[height<={height}]+bestaudio/best[height<={height}]"])
        else:
            cmd.extend(["-f", "bestvideo[height>=1080]+bestaudio/bestvideo[height>=720]+bestaudio/bestvideo+bestaudio/best"])
        
        return cmd
    
    def _monitor_download_progress(self, process, progress_callback, cancel_check):
        """Monitor download progress and handle cancellation"""
        stream_progress = {}
        current_stream = None
        total_streams = 0
        last_overall_progress = 0

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
    
    def _detect_stream(self, line):
        """Detect stream identifier from download line"""
        if ".f" in line and any(ext in line for ext in [".mp4", ".webm", ".m4a"]):
            stream_match = re.search(r'\.f(\d+)\.', line)
            if stream_match:
                return stream_match.group(1)
        else:
            return "single"
        return None
    
    def _parse_progress_line(self, line, stream_progress, current_stream, total_streams, last_progress, progress_callback):
        """Parse progress from yt-dlp output line"""
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
        """Cancel active download"""
        debug_print("Cancelling download...")
        self.is_downloading = False

        try:
            subprocess.run(['taskkill', '/F', '/IM', 'yt-dlp.exe'],
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            debug_print("Killed all yt-dlp processes system-wide")
        except Exception as e:
            debug_print(f"Error killing yt-dlp processes system-wide: {e}")

        if self.current_process:
            try:
                self.current_process.terminate()
                debug_print("Download process terminated")
                # Wait a bit for graceful termination
                try:
                    self.current_process.wait(timeout=2)
                except:
                    # Force kill if it doesn't terminate gracefully
                    try:
                        self.current_process.kill()
                        debug_print("Download process force killed")
                    except:
                        pass
            except Exception as e:
                debug_print(f"Error terminating download process: {e}")
    
    def cleanup_processes(self):
        """Clean up active download processes"""
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
