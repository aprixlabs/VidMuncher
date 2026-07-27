import os

# Circular import safe read of DEBUG_MODE
_DEBUG_MODE = os.environ.get('VIDMUNCHER_DEBUG', '0') == '1'

def debug_print(message):
    """Print to console if DEBUG_MODE true"""
    if _DEBUG_MODE:
        print(f"[DEBUG] {message}")
