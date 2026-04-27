"""
VidMuncher Configuration Module
Contains all constants, paths, and configuration settings
"""

import sys
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).parent

    return Path(base_path) / relative_path

APP_NAME = "VidMuncher"
APP_VERSION = "1.0.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

DEBUG_MODE = False
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 525
WINDOW_BG_COLOR = "#5B012A"
HEADER_BG_COLOR = "#2D0017"
TEXT_COLOR = "#EFEFEF"
PLACEHOLDER_COLOR = "#725B67"
BUTTON_COLOR = "#89003E"
BUTTON_ACTIVE_COLOR = "#6B0030"
BUTTON_DISABLED_COLOR = "#672845"

if getattr(sys, 'frozen', False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).parent

BIN_PATH = ROOT / "bin"
YTDLP_PATH = BIN_PATH / "yt-dlp.exe"
FFMPEG_PATH = BIN_PATH / "ffmpeg.exe"

ICON_PATH = get_resource_path("assets/icon.ico")
ICON_PNG_PATH = get_resource_path("assets/icon.png")
HEADER_PATH = get_resource_path("assets/header.png")
KOFI_LOGO_PATH = get_resource_path("assets/kofi-logo.png")
SOCIABUZZ_LOGO_PATH = get_resource_path("assets/sociabuzz-logo.png")

FONT_REGULAR = get_resource_path("assets/fonts/Poppins-Regular.ttf")
FONT_MEDIUM = get_resource_path("assets/fonts/Poppins-Medium.ttf")
FONT_BOLD = get_resource_path("assets/fonts/Poppins-Bold.ttf")
FONT_BLACK = get_resource_path("assets/fonts/Poppins-Black.ttf")

DEFAULT_DOWNLOAD_PATH = str(Path.home() / "Downloads")
DOWNLOAD_PRESETS = [
    "Best Quality",
    "2160p",
    "1440p",
    "1080p",
    "720p",
    "480p",
    "360p",
    "Audio (wav)",
    "Audio (mp3)",
    "Audio (m4a)",
    "Audio (flac)"
]

ENCODER_OPTIONS = [
    "Keep Original",
    "H.264 (Nvidia)",
    "H.265 (Nvidia)",
    "AV1 (Nvidia)",
    "H.264 (AMD)",
    "H.265 (AMD)",
    "AV1 (AMD)",
    "H.264 (Intel QuickSync)",
    "H.265 (Intel QuickSync)",
    "AV1 (Intel QuickSync)",
    "H.264 (CPU)",
    "AV1 (CPU)"
]

ENCODER_MAPPING = {
    "Keep Original": None,
    "H.264 (Nvidia)": {
        "encoder": "h264_nvenc",
        "name": "NVIDIA NVENC H.264",
        "hwaccel": "cuda",
        "codec": "h264",
        "settings": {
            "preset": "p4",
            "rc": "vbr",
            "cq": "23",
            "b:v": "0"
        }
    },
    "H.265 (Nvidia)": {
        "encoder": "hevc_nvenc",
        "name": "NVIDIA NVENC H.265",
        "hwaccel": "cuda",
        "codec": "h265",
        "settings": {
            "preset": "p4",
            "rc": "vbr",
            "cq": "25",
            "b:v": "0"
        }
    },
    "H.264 (AMD)": {
        "encoder": "h264_amf",
        "name": "AMD AMF H.264",
        "hwaccel": None,
        "codec": "h264",
        "settings": {
            "quality": "balanced",
            "rc": "vbr_peak",
            "qp_i": "22",
            "qp_p": "24"
        }
    },
    "H.265 (AMD)": {
        "encoder": "hevc_amf",
        "name": "AMD AMF H.265",
        "hwaccel": None,
        "codec": "h265",
        "settings": {
            "quality": "balanced",
            "rc": "vbr_peak",
            "qp_i": "24",
            "qp_p": "26"
        }
    },
    "H.264 (Intel QuickSync)": {
        "encoder": "h264_qsv",
        "name": "Intel QuickSync H.264",
        "hwaccel": None,
        "codec": "h264",
        "settings": {
            "preset": "medium",
            "global_quality": "23"
        }
    },
    "H.265 (Intel QuickSync)": {
        "encoder": "hevc_qsv",
        "name": "Intel QuickSync H.265",
        "hwaccel": None,
        "codec": "h265",
        "settings": {
            "preset": "medium",
            "global_quality": "25"
        }
    },
    "H.264 (CPU)": {
        "encoder": "libx264",
        "name": "CPU Software H.264",
        "hwaccel": None,
        "codec": "h264",
        "settings": {
            "preset": "medium",
            "crf": "23"
        }
    },
    "AV1 (Nvidia)": {
        "encoder": "av1_nvenc",
        "name": "NVIDIA NVENC AV1",
        "hwaccel": "cuda",
        "codec": "av1",
        "settings": {
            "preset": "p4",
            "cq": "35",
            "b:v": "0"
        }
    },
    "AV1 (AMD)": {
        "encoder": "av1_amf",
        "name": "AMD AMF AV1",
        "hwaccel": None,
        "codec": "av1",
        "settings": {
            "quality": "balanced",
            "rc": "cqp",
            "qp_i": "28",
            "qp_p": "28"
        }
    },
    "AV1 (Intel QuickSync)": {
        "encoder": "av1_qsv",
        "name": "Intel QuickSync AV1",
        "hwaccel": None,
        "codec": "av1",
        "settings": {
            "preset": "medium",
            "global_quality": "28"
        }
    },
    "AV1 (CPU)": {
        "encoder": "libsvtav1",
        "name": "SVT-AV1 (CPU)",
        "hwaccel": None,
        "codec": "av1",
        "settings": {
            "crf": "35",
            "preset": "8"
        }
    }
}

# Human-readable progress labels keyed by encoder selection
ENCODER_PROGRESS_MESSAGES = {
    "H.264 (Nvidia)": "Encoding to H.264 (NVIDIA NVENC H.264)",
    "H.265 (Nvidia)": "Encoding to H.265 (NVIDIA NVENC HEVC)",
    "AV1 (Nvidia)": "Encoding to AV1 (NVIDIA NVENC AV1)",
    "H.264 (AMD)": "Encoding to H.264 (AMD AMF H.264)",
    "H.265 (AMD)": "Encoding to H.265 (AMD AMF HEVC)",
    "AV1 (AMD)": "Encoding to AV1 (AMD AMF AV1)",
    "H.264 (Intel QuickSync)": "Encoding to H.264 (QuickSync H.264)",
    "H.265 (Intel QuickSync)": "Encoding to H.265 (QuickSync HEVC)",
    "AV1 (Intel QuickSync)": "Encoding to AV1 (QuickSync AV1)",
    "H.264 (CPU)": "Encoding to H.264 (CPU x264)",
    "AV1 (CPU)": "Encoding to AV1 (SVT-AV1)"
}

VIDEO_EXTENSIONS = [".mp4", ".webm", ".mkv", ".m4v", ".avi"]
AUDIO_EXTENSIONS = [".mp3", ".wav", ".m4a"]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
REFERER = "https://www.youtube.com/"
EXTRACTOR_RETRIES = 3
FRAGMENT_RETRIES = 3
RETRY_SLEEP = 1

ANALYZE_TIMEOUT = 30
THUMBNAIL_TIMEOUT = 10
ENCODER_TEST_TIMEOUT = 10

PROGRESS_UPDATE_THRESHOLD = 0.5  # Minimum delta (%) before a UI progress update is triggered

MAX_FILENAME_LENGTH = 100
INVALID_FILENAME_CHARS = ['<', '>', ':', '"', '|', '?', '*', '/', '\\']
MAX_UNIQUE_FILENAME_ATTEMPTS = 999

ENCODERS_CONFIG = [
    {
        "encoder": "h264_nvenc",
        "name": "NVIDIA NVENC",
        "hwaccel": "cuda",
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {
            "preset": "p4",
            "rc": "vbr",
            "cq": "23",
            "b:v": "0"
        }
    },
    {
        "encoder": "h264_amf",
        "name": "AMD AMF",
        "hwaccel": "d3d11va",
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {
            "quality": "balanced",
            "rc": "cqp",
            "qp_i": "23",
            "qp_p": "23",
            "qp_b": "23"
        }
    },
    {
        "encoder": "h264_qsv",
        "name": "Intel Quick Sync",
        "hwaccel": None,
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {
            "preset": "medium",
            "global_quality": "23"
        }
    },
    {
        "encoder": "libx264",
        "name": "CPU (Software)",
        "hwaccel": None,
        "test_args": ["-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-t", "1"],
        "settings": {
            "preset": "medium",
            "crf": "23"
        }
    }
]

AUDIO_CODEC = "aac"
AUDIO_BITRATE = "128k"

FFMPEG_COMMON_ARGS = [
    "-movflags", "+faststart",
    "-avoid_negative_ts", "make_zero"
]

class Layout:
    HEADER_HEIGHT = 80
    HEADER_IMAGE_X = 20
    HEADER_IMAGE_Y = 12
    
    ABOUT_BUTTON_X = 750
    ABOUT_BUTTON_Y = 25
    ABOUT_BUTTON_WIDTH = 30
    ABOUT_BUTTON_HEIGHT = 30

    # URL Entry
    URL_ENTRY_X = 20
    URL_ENTRY_Y = 100
    URL_ENTRY_WIDTH = 600
    URL_ENTRY_HEIGHT = 35
    URL_PLACEHOLDER = "  Input or Paste Video URL..."
    
    VIDEO_INFO_X = 20
    VIDEO_INFO_Y = 150
    VIDEO_INFO_WIDTH = 460
    VIDEO_INFO_HEIGHT = 130
    VIDEO_INFO_PLACEHOLDER = "Video Information"
    
    THUMBNAIL_X = 500
    THUMBNAIL_Y = 150
    THUMBNAIL_WIDTH = 260
    THUMBNAIL_HEIGHT = 130
    THUMBNAIL_PLACEHOLDER = "Thumbnail"
    
    PRESET_LABEL_X = 20
    PRESET_LABEL_Y = 300
    PRESET_COMBO_X = 150
    PRESET_COMBO_Y = 300
    PRESET_COMBO_WIDTH = 250
    PRESET_COMBO_HEIGHT = 30

    REENCODE_LABEL_X = 420
    REENCODE_LABEL_Y = 300
    REENCODE_COMBO_X = 520
    REENCODE_COMBO_Y = 300
    REENCODE_COMBO_WIDTH = 240
    REENCODE_COMBO_HEIGHT = 30
    
    SAVE_LABEL_X = 20
    SAVE_LABEL_Y = 340
    SAVE_ENTRY_X = 150
    SAVE_ENTRY_Y = 340
    SAVE_ENTRY_WIDTH = 400
    SAVE_ENTRY_HEIGHT = 30
    
    ANALYZE_BUTTON_X = 640
    ANALYZE_BUTTON_Y = 100
    ANALYZE_BUTTON_WIDTH = 120
    ANALYZE_BUTTON_HEIGHT = 35
    
    BROWSE_BUTTON_X = 570
    BROWSE_BUTTON_Y = 340
    BROWSE_BUTTON_WIDTH = 120
    BROWSE_BUTTON_HEIGHT = 30
    
    DOWNLOAD_BUTTON_X = 340
    DOWNLOAD_BUTTON_Y = 400
    DOWNLOAD_BUTTON_WIDTH = 120
    DOWNLOAD_BUTTON_HEIGHT = 35

    CANCEL_BUTTON_X = 340
    CANCEL_BUTTON_Y = 400
    CANCEL_BUTTON_WIDTH = 120
    CANCEL_BUTTON_HEIGHT = 35
    
    PROGRESS_X = 20
    PROGRESS_Y = 460
    PROGRESS_WIDTH = 760
    PROGRESS_HEIGHT = 25

    COPYRIGHT_X = 400
    COPYRIGHT_Y = 505

class Fonts:
    DEFAULT = ("Poppins", 10)
    SMALL = ("Poppins", 9)
    BOLD = ("Poppins", 10, "bold")
    COMBO = ("Poppins", 9)

class Messages:
    URL_EMPTY = "URL cannot be empty!"
    GETTING_INFO = "Getting information..."
    READY_DOWNLOAD = "Ready to download"
    DOWNLOADING = "Downloading..."
    DOWNLOAD_COMPLETE = "Download Complete!"
    DOWNLOAD_CANCELLED = "Download cancelled"
    DOWNLOAD_INTERRUPTED = "Download was interrupted"
    DOWNLOAD_FAILED = "Download failed"
    TIMEOUT_ANALYZE = "Timeout - URL took too long to analyze"
    VIDEO_UNAVAILABLE = "Video unavailable or private"
    VIDEO_NOT_FOUND = "Video not found or restricted"
    AGE_RESTRICTED = "Age-restricted video"
    FAILED_VIDEO_INFO = "Failed to get video info"
    INVALID_URL = "Invalid URL or network error"
    ENCODING_FAILED = "Encoding Failed!"
    FILE_NOT_FOUND = "Source file not found for encoding!"
    ENCODING_ERROR = "Encoding Error - Output file not found!"
    FILE_MOVE_ERROR = "File move error!"
