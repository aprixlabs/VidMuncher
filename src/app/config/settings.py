"""
VidMuncher Settings Manager.
Handles loading, saving, and providing default application settings.
"""
import json
import os
from pathlib import Path

from app.config.paths import ROOT, DEFAULT_DOWNLOAD_PATH
from app.utils.debug import debug_print

SETTINGS_FILE_PATH = ROOT / "settings.vmunch"

DEFAULT_SETTINGS = {
    "general": {
        "download_dir": DEFAULT_DOWNLOAD_PATH,
        "default_preset": "Best Quality",
        "default_encoder": "Auto",
        "theme": "Dark",
        "language": "English"
    },
    "network": {
        "extractor_retries": 3,
        "fragment_retries": 3,
        "concurrent_downloads": 1,
        "rate_limit_mbps": 0,
        "proxy": "",
        "cookie_mode": "none",        # "none", "browser", "file"
        "browser_cookies": "chrome",
        "cookie_file": ""
    },
    "advanced": {
        "ffmpeg_path": "",
        "ytdlp_path": "",
        "deno_path": "",
        "debug_mode": False,
        "detected_gpus": []
    }
}

class SettingsManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()
        
    def load(self):
        if not os.path.exists(SETTINGS_FILE_PATH):
            self.save()
            return
            
        try:
            with open(SETTINGS_FILE_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                
            for section, values in DEFAULT_SETTINGS.items():
                if section not in loaded:
                    loaded[section] = values
                else:
                    for k, v in values.items():
                        if k not in loaded[section]:
                            loaded[section][k] = v
                            
            self.settings = loaded
        except Exception as e:
            debug_print(f"Failed to load settings: {e}")
            self.settings = DEFAULT_SETTINGS.copy()
            
    def save(self):
        try:
            with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            debug_print(f"Failed to save settings: {e}")
            
    def get(self, section, key):
        return self.settings.get(section, {}).get(key, DEFAULT_SETTINGS[section][key])
        
    def set(self, section, key, value):
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
        
    def get_all(self):
        return self.settings
        
    def update_all(self, new_settings):
        self.settings = new_settings
        self.save()
