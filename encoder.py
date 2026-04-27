

import re
import subprocess
import threading
from config import (
    DEBUG_MODE,
    FFMPEG_PATH,
    ENCODER_TEST_TIMEOUT,
    AUDIO_CODEC,
    AUDIO_BITRATE,
    FFMPEG_COMMON_ARGS,
    ENCODER_MAPPING,
    ENCODER_PROGRESS_MESSAGES
)
from utils import debug_print

class EncoderManager:
    """Manages FFmpeg encoding operations and encoder detection"""
    
    def __init__(self):
        self.active_processes = []

    def get_encoder_config(self, encoder_selection):
        """Get encoder configuration based on GUI selection"""
        return ENCODER_MAPPING.get(encoder_selection)

    def test_encoder_availability(self, encoder_config):
        """Test if specific encoder is available"""
        try:
            test_cmd = [str(FFMPEG_PATH)]

            if encoder_config.get("hwaccel"):
                test_cmd.extend(["-hwaccel", encoder_config["hwaccel"]])

            test_cmd.extend([
                "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1",
                "-c:v", encoder_config["encoder"],
                "-f", "null", "-"
            ])

            debug_print(f"Testing encoder: {encoder_config['name']}")

            result = subprocess.run(
                test_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=ENCODER_TEST_TIMEOUT,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                debug_print(f"Encoder available: {encoder_config['name']}")
                return True
            else:
                debug_print(f"Encoder not available: {encoder_config['name']}")
                return False

        except Exception as e:
            debug_print(f"Encoder test failed: {encoder_config['name']} - {str(e)}")
            return False
    

    def build_encoding_command_v2(self, input_file, output_file, encoder_config):
        """Construct the FFmpeg command list for the given encoder configuration."""
        cmd = [str(FFMPEG_PATH)]

        if encoder_config.get("hwaccel"):
            cmd.extend(["-hwaccel", encoder_config["hwaccel"]])

        cmd.extend(["-i", input_file])

        cmd.extend(["-c:v", encoder_config["encoder"]])

        settings = encoder_config.get("settings", {})
        for key, value in settings.items():
            if key.startswith("b:") or key.startswith("q"):
                cmd.extend([f"-{key}", str(value)])
            else:
                cmd.extend([f"-{key}", str(value)])

        cmd.extend(["-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE])

        cmd.extend(FFMPEG_COMMON_ARGS)

        cmd.extend(["-y", output_file])

        return cmd
    
    def encode_video(self, input_file, output_file, encoder_selection="H.264 (CPU)", progress_callback=None, cancel_check=None):
        """Encode a video file, reporting progress via callback. Falls back to CPU if the selected encoder is unavailable."""
        try:
            encoder_config = self.get_encoder_config(encoder_selection)

            if not encoder_config:
                return False, f"Invalid encoder selection: {encoder_selection}"

            if not self.test_encoder_availability(encoder_config):
                original_name = encoder_config['name']
                debug_print(f"Encoder {original_name} not available, falling back to CPU...")
                if progress_callback:
                    progress_callback(f"{original_name} unavailable, falling back to CPU encoder...", 0)
                encoder_selection = "H.264 (CPU)"
                encoder_config = self.get_encoder_config(encoder_selection)
                if not self.test_encoder_availability(encoder_config):
                    return False, "No suitable encoder available"

            encoder_name = encoder_config["name"]
            base_text = ENCODER_PROGRESS_MESSAGES.get(encoder_selection, f"Encoding {encoder_name}")

            cmd = self.build_encoding_command_v2(input_file, output_file, encoder_config)
            
            debug_print(f"FFmpeg command: {' '.join(cmd)}")
            
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
            
            duration_seconds = None
            encoding_progress = 0

            for line in process.stdout:
                if cancel_check and cancel_check():
                    debug_print("FFmpeg encoding cancelled by user")
                    break
                
                line = line.strip()
                debug_print(f"FFmpeg: {line}")
                
                if "Duration:" in line and not duration_seconds:
                    duration_seconds = self._extract_duration(line)
                    if duration_seconds:
                        debug_print(f"Video duration: {duration_seconds} seconds")
                
                elif "time=" in line and duration_seconds:
                    progress = self._extract_progress(line, duration_seconds)
                    if progress is not None and progress > encoding_progress:
                        encoding_progress = progress
                        if progress_callback:
                            progress_callback(f"{base_text} - {progress:.1f}%", progress)
                
                elif encoding_progress == 0 and any(keyword in line.lower() for keyword in ['frame=', 'fps=', 'bitrate=']):
                    encoding_progress = min(50, encoding_progress + 10)
                    if progress_callback:
                        progress_callback(f"{base_text} - {encoding_progress}%", encoding_progress)
            
            process.wait()

            if process in self.active_processes:
                self.active_processes.remove(process)

            debug_print(f"FFmpeg process finished with return code: {process.returncode}")

            is_cancelled = cancel_check and cancel_check()
            debug_print(f"Is cancelled check: {is_cancelled}")

            if process.returncode == 0:
                debug_print("FFmpeg encoding completed successfully")
                return True, None
            else:
                if cancel_check and cancel_check():
                    debug_print("H264 encoding was cancelled by user")
                    return False, "Encoding was cancelled by user"
                else:
                    if process.returncode == 4294967294:
                        error_msg = "H264 Encoding Failed! (Process terminated unexpectedly)"
                        debug_print(f"FFmpeg terminated unexpectedly with return code: {process.returncode}")
                    else:
                        error_msg = f"FFmpeg failed with return code: {process.returncode}"
                        debug_print(error_msg)
                    return False, error_msg
        
        except Exception as e:
            error_msg = f"Encoding error: {str(e)}"
            debug_print(error_msg)
            return False, error_msg
    
    def _extract_duration(self, line):
        """Extract video duration from FFmpeg output"""
        try:
            duration_match = re.search(r'Duration: (\d+):(\d+):(\d+)\.(\d+)', line)
            if duration_match:
                h, m, s, ms = map(int, duration_match.groups())
                return h * 3600 + m * 60 + s + ms / 100
        except:
            pass
        return None
    
    def _extract_progress(self, line, duration_seconds):
        """Extract encoding progress from FFmpeg output"""
        try:
            time_match = re.search(r'time=(\d+):(\d+):(\d+)\.(\d+)', line)
            if time_match:
                h, m, s, ms = map(int, time_match.groups())
                current_seconds = h * 3600 + m * 60 + s + ms / 100
                progress = min(99, (current_seconds / duration_seconds) * 100)
                return progress
        except:
            pass
        return None
    
    def cleanup_processes(self):
        """Clean up active encoding processes"""
        for process in self.active_processes[:]:
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
                self.active_processes.remove(process)
            except:
                pass
    
    def cancel_encoding(self):
        """Cancel all active encoding processes"""
        debug_print("Cancelling all encoding processes...")

        try:
            subprocess.run(['taskkill', '/F', '/IM', 'ffmpeg.exe'],
                         capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            debug_print("Killed all ffmpeg processes system-wide")
        except Exception as e:
            debug_print(f"Error killing ffmpeg processes system-wide: {e}")

        self.cleanup_processes()

encoder_manager = EncoderManager()
