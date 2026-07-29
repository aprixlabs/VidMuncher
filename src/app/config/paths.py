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
        # In development: Base is src/app/ (which contains assets/)
        current_file = Path(__file__).resolve()
        base_path = current_file.parent.parent

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
    DENO_PATH = BIN_PATH / "deno.exe"
else:
    YTDLP_PATH = BIN_PATH / "yt-dlp"
    FFMPEG_PATH = BIN_PATH / "ffmpeg"
    DENO_PATH = BIN_PATH / "deno"

if sys.platform == "win32":
    ICON_PATH = get_resource_path("assets/icons/icon.ico")
else:
    ICON_PATH = get_resource_path("assets/icons/icon.png")

ICON_PNG_PATH = get_resource_path("assets/icons/icon.png")
DROPDOWN_ARROW_PATH = get_resource_path("assets/ui/dropdown-arrow.svg")
UP_ARROW_PATH = get_resource_path("assets/ui/up-arrow.svg")
ABOUT_ICON_PATH = get_resource_path("assets/icons/about-icon.svg")
HISTORY_ICON_PATH = get_resource_path("assets/icons/history-icon.svg")
CHECKMARK_ICON_PATH = get_resource_path("assets/ui/checkmark.svg")
SETTINGS_ICON_PATH = get_resource_path("assets/icons/settings-icon.svg")
KOFI_LOGO_PATH = get_resource_path("assets/logos/kofi-logo.png")
SOCIABUZZ_LOGO_PATH = get_resource_path("assets/logos/sociabuzz-logo.png")
HISTORY_FILE_PATH = ROOT / "history.vmunch"

FONT_REGULAR = get_resource_path("assets/fonts/Poppins-Regular.ttf")
FONT_MEDIUM = get_resource_path("assets/fonts/Poppins-Medium.ttf")
FONT_BOLD = get_resource_path("assets/fonts/Poppins-Bold.ttf")
FONT_BLACK = get_resource_path("assets/fonts/Poppins-Black.ttf")

DEFAULT_DOWNLOAD_PATH = str(Path.home() / "Downloads")
