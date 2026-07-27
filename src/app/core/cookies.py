import os
import sys
from app.utils import debug_print

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
    """Return default profile paths for a given browser by OS."""
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
    """Check if the browser's data directory exists."""
    paths = get_browser_cookie_paths(browser_name)
    for path in paths:
        if os.path.exists(path):
            return True
    return False

def get_installed_browsers():
    """Return a list of installed supported browsers, ordered by preference."""
    installed = []
    for browser in SUPPORTED_BROWSERS:
        if is_browser_likely_installed(browser):
            installed.append(browser)
    
    # Fallback if path detection fails
    if not installed:
        return ["chrome", "edge", "firefox"]
        
    return installed

def test_browser_cookies(browser_name):
    """
    Test yt-dlp cookie extraction from a browser.
    Returns True on success, False otherwise.
    """
    opts = {
        'cookiesfrombrowser': (browser_name,),
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        # Trigger yt-dlp cookie extraction without downloading.
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl._setup_opener()
            return True
    except Exception as e:
        debug_print(f"Failed to extract cookies from {browser_name}: {e}")
        return False

def auto_detect_best_browser():
    """
    Find first browser with working cookie extraction.
    Returns browser name or None.
    """
    installed_browsers = get_installed_browsers()
    debug_print(f"Detected installed browsers: {installed_browsers}")
    
    for browser in installed_browsers:
        debug_print(f"Testing cookies from: {browser}")
        if test_browser_cookies(browser):
            debug_print(f"Successfully loaded cookies from {browser}")
            return browser
            
    debug_print("Failed to auto-detect any working browser cookies.")
    return None
