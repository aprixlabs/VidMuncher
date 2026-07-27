import os
import glob
import datetime
from app.config.filenames import INVALID_FILENAME_CHARS, MAX_FILENAME_LENGTH, MAX_UNIQUE_FILENAME_ATTEMPTS, VIDEO_EXTENSIONS
from app.utils.debug import debug_print

def sanitize_filename(filename):
    """Remove invalid chars, truncate to max length"""
    safe_filename = filename

    for char in INVALID_FILENAME_CHARS:
        safe_filename = safe_filename.replace(char, '_')

    if len(safe_filename) > MAX_FILENAME_LENGTH:
        safe_filename = safe_filename[:MAX_FILENAME_LENGTH]

    return safe_filename

def get_extension_from_preset(preset, encoding_enabled=True, encoder_selection="H.264 (CPU)"):
    """Get extension based on preset/encoder selection"""
    if "Audio" in preset:
        return preset.replace("Audio (", "").replace(")", "").strip()
    else:
        if encoding_enabled and encoder_selection != "Auto":
            return "mp4"
        else:
            return "%(ext)s"

def get_unique_filename(filepath):
    """Return unique path by appending (1), (2), etc. if file exists"""
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
            debug_print(f"Generated unique filename: {new_path}")
            return new_path

        counter += 1

        if counter > MAX_UNIQUE_FILENAME_ATTEMPTS:
            debug_print(f"Warning: Reached counter limit for {filepath}")
            break

    # Fallback to timestamp when counter exhausted
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fallback_name = f"{name}_{timestamp}{ext}"
    fallback_path = os.path.join(directory, fallback_name)

    debug_print(f"Using timestamp fallback: {fallback_path}")
    return fallback_path

def get_unique_filename_without_ext(base_path):
    """Return unique base path across all known video extensions"""
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
    """Locate downloaded file by checking extensions, fallback to glob"""
    if possible_extensions is None:
        possible_extensions = VIDEO_EXTENSIONS

    for ext in possible_extensions:
        test_path = base_path + ext
        if os.path.exists(test_path):
            return test_path

    try:
        # Escape glob metacharacters
        safe_base = base_path.replace('[', r'\[').replace(']', r'\]')
        pattern = safe_base + ".*"
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    except Exception as e:
        debug_print(f"Glob search error: {e}")

    return None
