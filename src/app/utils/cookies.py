import os
import sys
import subprocess
from app.config import YTDLP_PATH
from app.config.settings import SettingsManager
from app.utils.debug import debug_print

SUPPORTED_BROWSERS = [
    "chrome",
    "edge",
    "firefox",
    "brave",
    "opera",
    "vivaldi",
    "chromium",
    "safari"
]

def get_browser_cookie_paths(browser_name):
    paths = []

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        roaming_app_data = os.environ.get("APPDATA", "")
        
        if browser_name == "chrome" and local_app_data:
            paths.append(os.path.join(local_app_data, "Google", "Chrome", "User Data"))
        elif browser_name == "edge" and local_app_data:
            paths.append(os.path.join(local_app_data, "Microsoft", "Edge", "User Data"))
        elif browser_name == "firefox" and roaming_app_data:
            paths.append(os.path.join(roaming_app_data, "Mozilla", "Firefox", "Profiles"))
        elif browser_name == "brave" and local_app_data:
            paths.append(os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "User Data"))
        elif browser_name == "opera" and roaming_app_data:
            paths.append(os.path.join(roaming_app_data, "Opera Software", "Opera Stable"))
        elif browser_name == "vivaldi" and local_app_data:
            paths.append(os.path.join(local_app_data, "Vivaldi", "User Data"))
            
    elif sys.platform.startswith("linux"):
        home = os.path.expanduser("~")
        if browser_name == "chrome":
            paths.append(os.path.join(home, ".config", "google-chrome"))
        elif browser_name == "firefox":
            paths.append(os.path.join(home, ".mozilla", "firefox"))
            
    return paths

def is_browser_likely_installed(browser_name):
    paths = get_browser_cookie_paths(browser_name)
    for path in paths:
        if os.path.exists(path):
            return True
    return False

def get_installed_browsers():
    installed = []
    for browser in SUPPORTED_BROWSERS:
        if is_browser_likely_installed(browser):
            installed.append(browser)

    # Fallback if path detection fails
    if not installed:
        return ["chrome", "edge", "firefox"]

    return installed

def test_browser_cookies(browser_name):
    """Test yt-dlp cookie extraction from a browser."""
    try:
        settings = SettingsManager()
        ytdlp_path = str(YTDLP_PATH)
        custom_ytdlp = settings.get("advanced", "ytdlp_path")
        if custom_ytdlp and os.path.exists(custom_ytdlp):
            ytdlp_path = custom_ytdlp

        creationflags = 0x08000000 if os.name == 'nt' else 0
        cmd = [
            ytdlp_path,
            "--cookies-from-browser", browser_name,
            "--simulate",
            "--quiet",
            "https://example.com"
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=creationflags
        )
        stderr = result.stderr.lower()
        if "could not copy cookies" in stderr or "browser" in stderr and "not found" in stderr or "does not look like" in stderr:
            return False
        return result.returncode == 0
    except Exception as e:
        debug_print(f"Failed to extract cookies from {browser_name}: {e}")
        return False

def auto_detect_best_browser():
    """Find first browser with working cookie extraction."""
    installed_browsers = get_installed_browsers()
    debug_print(f"Detected installed browsers: {installed_browsers}")
    
    for browser in installed_browsers:
        debug_print(f"Testing cookies from: {browser}")
        if test_browser_cookies(browser):
            debug_print(f"Successfully loaded cookies from {browser}")
            return browser
            
    debug_print("Failed to auto-detect any working browser cookies.")
    return None
