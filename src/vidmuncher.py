#!/usr/bin/env python3

import sys
import os

# Must be set before any app module is imported so config.py reads it correctly.
if '--debug' in sys.argv:
    os.environ['VIDMUNCHER_DEBUG'] = '1'
    sys.argv.remove('--debug')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import DEBUG_MODE, APP_NAME, APP_VERSION
from app.utils import debug_print
from app.gui import run


def main():
    """Main entry point for VidMuncher application"""
    try:
        # Patch for Qt plugin path in venv
        from PySide6.QtCore import QCoreApplication
        site_packages = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Lib', 'site-packages')
        qt_plugins_path = os.path.join(site_packages, 'PySide6', 'plugins')
        if os.path.exists(qt_plugins_path):
            QCoreApplication.addLibraryPath(qt_plugins_path)

        debug_print(f"Starting {APP_NAME} {APP_VERSION}")
        debug_print(f"Debug mode: {DEBUG_MODE}")
        debug_print(f"Python: {sys.version}")
        debug_print(f"Platform: {sys.platform}")
        debug_print("Launching GUI...")
        run()

    except KeyboardInterrupt:
        debug_print("Application interrupted by user")
    except Exception as e:
        debug_print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
