import json
import threading
from pathlib import Path

class LocalizationManager:
    _lock = threading.RLock()
    _current_lang = "en"
    _translations = {}
    _lang_dir = Path(__file__).parent.parent / "languages"

    @classmethod
    def load_language(cls, lang_code: str):
        with cls._lock:
            code = lang_code.lower()
            if "indonesia" in code or code == "id":
                code = "id"
            else:
                code = "en"

            cls._current_lang = code
            file_path = cls._lang_dir / f"{code}.json"
            try:
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        cls._translations = json.load(f)
                else:
                    cls._translations = {}
            except Exception:
                cls._translations = {}

    @classmethod
    def get_text(cls, key: str, default: str = "") -> str:
        with cls._lock:
            parts = key.split(".")
            val = cls._translations
            for p in parts:
                if isinstance(val, dict) and p in val:
                    val = val[p]
                else:
                    # Fallback if key missing
                    return default or key
            return str(val)

def _(key: str, default: str = "") -> str:
    return LocalizationManager.get_text(key, default)
