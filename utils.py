import os
import time
import datetime
import glob
import gc
from config import (
    DEBUG_MODE, 
    INVALID_FILENAME_CHARS, 
    MAX_FILENAME_LENGTH, 
    MAX_UNIQUE_FILENAME_ATTEMPTS,
    VIDEO_EXTENSIONS
)

def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters and limiting length"""
    safe_filename = filename

    for char in INVALID_FILENAME_CHARS:
        safe_filename = safe_filename.replace(char, '_')

    if len(safe_filename) > MAX_FILENAME_LENGTH:
        safe_filename = safe_filename[:MAX_FILENAME_LENGTH]

    return safe_filename

def get_extension_from_preset(preset, encoding_enabled=True, encoder_selection="H.264 (CPU)"):
    """Get file extension based on selected preset and encoder"""
    if "Audio" in preset:
        return preset.replace("Audio (", "").replace(")", "").strip()
    else:
        if encoding_enabled and encoder_selection != "Keep Original":
            return "mp4"
        else:
            return "%(ext)s"

def get_unique_filename(filepath):
    """Return a unique filepath by appending (1), (2), etc. if the file already exists."""
    if not os.path.exists(filepath):
        return filepath

    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    counter = 1
    while True:
        new_name = f"{name} ({counter}){ext}"
        new_path = os.path.join(directory, new_name)

        if not os.path.exists(new_path):
            if DEBUG_MODE:
                print(f"Generated unique filename: {new_path}")
            return new_path

        counter += 1

        if counter > MAX_UNIQUE_FILENAME_ATTEMPTS:
            if DEBUG_MODE:
                print(f"Warning: Reached counter limit for {filepath}")
            break

    # Fallback to timestamp suffix when the counter limit is exhausted
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fallback_name = f"{name}_{timestamp}{ext}"
    fallback_path = os.path.join(directory, fallback_name)

    if DEBUG_MODE:
        print(f"Using timestamp fallback: {fallback_path}")

    return fallback_path

def get_unique_filename_without_ext(base_path):
    """Return a unique base path (no extension) by checking all known video extensions."""
    counter = 0
    while True:
        if counter == 0:
            test_base = base_path
        else:
            directory = os.path.dirname(base_path)
            filename = os.path.basename(base_path)
            test_base = os.path.join(directory, f"{filename} ({counter})")

        file_exists = False
        for ext in VIDEO_EXTENSIONS:
            if os.path.exists(f"{test_base}{ext}"):
                file_exists = True
                break

        if not file_exists:
            return test_base

        counter += 1

def find_downloaded_file(base_path, possible_extensions=None):
    """Locate a downloaded file by checking known extensions, then falling back to glob."""
    if possible_extensions is None:
        possible_extensions = VIDEO_EXTENSIONS

    for ext in possible_extensions:
        test_path = base_path + ext
        if os.path.exists(test_path):
            return test_path

    try:
        safe_base = base_path.replace('[', r'\[').replace(']', r'\]')  # escape glob metacharacters
        pattern = safe_base + ".*"
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    except Exception as e:
        if DEBUG_MODE:
            print(f"Glob search error: {e}")

    return None

def cleanup_file_with_timeout(filepath, max_attempts=3, total_timeout=2):
    """Attempt to delete a file within the given timeout, retrying on PermissionError."""
    start_time = time.time()
    for attempt in range(max_attempts):
        if time.time() - start_time > total_timeout:
            break
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except PermissionError:
            time.sleep(0.1)
        except Exception:
            break
    return False

def cleanup_temp_files(temp_files_list):
    """Delete files from the given list in-place, logging failures when in debug mode."""
    for temp_file in temp_files_list[:]:
        if cleanup_file_with_timeout(temp_file):
            temp_files_list.remove(temp_file)
            if DEBUG_MODE:
                print(f"Cleaned up temp file: {temp_file}")
        else:
            if DEBUG_MODE:
                print(f"Failed to clean up temp file: {temp_file}")

def force_garbage_collection():
    """Enhanced garbage collection to free memory"""
    collected = gc.collect()
    debug_print(f"Garbage collection freed {collected} objects")

    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        debug_print(f"Current memory usage: {memory_mb:.1f} MB")
    except ImportError:
        pass

def debug_print(message):
    """Print debug message if debug mode is enabled"""
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def format_file_size(size_bytes):
    """Convert a byte count to a human-readable string (e.g. 1.4 MB)."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_url(url):
    """Return True if the string looks like a supported video URL."""
    if not url or url.strip() == "":
        return False
    
    url = url.strip()

    if url.startswith(('http://', 'https://', 'www.')):
        return True

    video_platforms = ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com']
    for platform in video_platforms:
        if platform in url.lower():
            return True
    
    return False

def get_safe_path_preview(full_path, max_length=50):
    """Return a truncated path string suitable for display in the UI."""
    if len(full_path) <= max_length:
        return full_path
    
    filename = os.path.basename(full_path)
    if len(filename) < max_length - 10:
        directory = os.path.dirname(full_path)
        available_length = max_length - len(filename) - 4
        if available_length > 0:
            truncated_dir = directory[:available_length]
            return f"{truncated_dir}...//{filename}"
    
    return full_path[:max_length-3] + "..."
