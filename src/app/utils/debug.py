import os
from datetime import datetime
from app.config.paths import ROOT

# Read env override (avoids circular imports)
_ENV_DEBUG = os.environ.get('VIDMUNCHER_DEBUG', '0') == '1'
LOG_FILE_PATH = ROOT / "vidmuncher.log"

def debug_print(message):
    """Print to console and write to log file if debug mode is enabled."""
    ui_debug = False
    try:
        # Avoid circular imports
        from app.config.settings import SettingsManager
        if SettingsManager._instance is not None:
            ui_debug = SettingsManager().get("advanced", "debug_mode")
    except ImportError:
        pass

    if _ENV_DEBUG or ui_debug:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [DEBUG] {message}"

        # Print to console
        print(log_line)

        # Append to log file
        try:
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
        except Exception:
            pass  # Silently ignore if lacking write permissions
