"""
VidMuncher Configuration Paths.
Directories, binaries, and assets.
"""
import sys
import os
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute resource path for dev and PyInstaller."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        current_file = Path(__file__).resolve()
        base_path = current_file.parent.parent.parent.parent

    # Return Path object directly to ensure compatibility with methods like .exists()
    return base_path / relative_path

if sys.platform == "win32":
    if getattr(sys, 'frozen', False):
        ROOT = Path(sys.executable).parent
    else:
        ROOT = Path(__file__).resolve().parent.parent.parent.parent
else:
    if getattr(sys, 'frozen', False):
        ROOT = Path.home() / ".local" / "share" / "VidMuncher"
        ROOT.mkdir(parents=True, exist_ok=True)
    else:
        ROOT = Path(__file__).resolve().parent.parent.parent.parent

BIN_PATH = ROOT / "bin"
if sys.platform == "win32":
    YTDLP_PATH = BIN_PATH / "yt-dlp.exe"
    FFMPEG_PATH = BIN_PATH / "ffmpeg.exe"
else:
    YTDLP_PATH = BIN_PATH / "yt-dlp"
    FFMPEG_PATH = BIN_PATH / "ffmpeg"

if sys.platform == "win32":
    ICON_PATH = get_resource_path("assets/icon.ico")
else:
    ICON_PATH = get_resource_path("assets/icon.png")

ICON_PNG_PATH = get_resource_path("assets/icon.png")
DROPDOWN_ARROW_PATH = get_resource_path("assets/dropdown-arrow.svg")
UP_ARROW_PATH = get_resource_path("assets/up-arrow.svg")
ABOUT_ICON_PATH = get_resource_path("assets/about-icon.svg")
HISTORY_ICON_PATH = get_resource_path("assets/history-icon.svg")
CHECKMARK_ICON_PATH = get_resource_path("assets/checkmark.svg")
SETTINGS_ICON_PATH = get_resource_path("assets/settings-icon.svg")
KOFI_LOGO_PATH = get_resource_path("assets/kofi-logo.png")
SOCIABUZZ_LOGO_PATH = get_resource_path("assets/sociabuzz-logo.png")
HISTORY_FILE_PATH = ROOT / "history.vmunch"

FONT_REGULAR = get_resource_path("assets/fonts/Poppins-Regular.ttf")
FONT_MEDIUM = get_resource_path("assets/fonts/Poppins-Medium.ttf")
FONT_BOLD = get_resource_path("assets/fonts/Poppins-Bold.ttf")
FONT_BLACK = get_resource_path("assets/fonts/Poppins-Black.ttf")

DEFAULT_DOWNLOAD_PATH = str(Path.home() / "Downloads")
