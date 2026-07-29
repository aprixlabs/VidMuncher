"""
App identity constants.
"""
import os

APP_NAME = "VidMuncher"
APP_VERSION = "1.1.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

# python vidmuncher.py --debug
DEBUG_MODE = os.environ.get('VIDMUNCHER_DEBUG', '0') == '1'
