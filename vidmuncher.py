#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEBUG_MODE, APP_NAME, APP_VERSION, FONT_REGULAR, FONT_MEDIUM, FONT_BOLD, FONT_BLACK
from utils import debug_print
from gui import gui

def load_fonts():
    """Load bundled Poppins font files into the Windows GDI font registry."""
    if os.name != 'nt':
        return

    try:
        import ctypes
        gdi32 = ctypes.windll.gdi32
        FR_PRIVATE = 0x10

        font_files = [FONT_REGULAR, FONT_MEDIUM, FONT_BOLD, FONT_BLACK]
        for font_path in font_files:
            if font_path.exists():
                result = gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, 0)
                if result:
                    debug_print(f"Loaded font: {font_path.name}")
                else:
                    debug_print(f"Failed to load font: {font_path.name}")
            else:
                debug_print(f"Font file not found: {font_path}")
    except Exception as e:
        debug_print(f"Font loading error: {e}")

def main():
    """Main entry point for VidMuncher application"""
    try:
        debug_print(f"Starting {APP_NAME} {APP_VERSION}")
        debug_print(f"Debug mode: {DEBUG_MODE}")

        load_fonts()
        check_dependencies()

        debug_print("Launching GUI...")
        gui.run()
        
    except KeyboardInterrupt:
        debug_print("Application interrupted by user")
        gui.cleanup_and_exit()
    except Exception as e:
        debug_print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def check_dependencies():
    """Check if required files and dependencies exist, download if missing"""
    from config import YTDLP_PATH, FFMPEG_PATH, BIN_PATH, HEADER_BG_COLOR, TEXT_COLOR, BUTTON_COLOR, HEADER_PATH, APP_NAME, APP_VERSION
    import tkinter as tk
    from updater import updater
    
    if not BIN_PATH.exists():
        BIN_PATH.mkdir(parents=True, exist_ok=True)
        
    missing = []
    if not YTDLP_PATH.exists(): missing.append("yt-dlp")
    if not FFMPEG_PATH.exists(): missing.append("FFmpeg")

    if not HEADER_PATH.exists():
        debug_print(f"Warning: Header asset not found: {HEADER_PATH}")
    
    if missing:
        debug_print(f"Missing dependencies: {missing}. Starting setup...")
        
        dialog = tk.Toplevel(gui.window)
        dialog.title(f"{APP_NAME} {APP_VERSION}")
        dialog.geometry("400x180")
        dialog.configure(bg=HEADER_BG_COLOR)
        dialog.resizable(False, False)
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 90
        dialog.geometry(f"+{x}+{y}")
        
        gui.apply_dark_title_bar(dialog)
        
        tk.Label(dialog, text="Setting up components for the first time...", 
                 font=("Poppins", 11, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR).pack(pady=(25, 5))
                 
        tk.Label(dialog, text="Please be patient, this background setup will only happen once.", 
                 font=("Poppins", 9), bg=HEADER_BG_COLOR, fg="#cccccc").pack(pady=(0, 15))
        
        canvas_width = 340
        canvas_height = 20
        chunk_width = 120

        progress_canvas = tk.Canvas(dialog, width=canvas_width, height=canvas_height, bg="#1a000e", highlightthickness=0)
        progress_canvas.pack(pady=(0, 10))

        progress_fill = progress_canvas.create_rectangle(0, 0, 0, canvas_height, fill=BUTTON_COLOR, outline="")

        status_lbl = tk.Label(dialog, text="Preparing to download...", font=("Poppins", 9), bg=HEADER_BG_COLOR, fg=TEXT_COLOR)
        status_lbl.pack()

        anim_pos = [-chunk_width]
        anim_active = [True]

        def animate():
            if not anim_active[0]:
                return
            anim_pos[0] += 8
            if anim_pos[0] > canvas_width:
                anim_pos[0] = -chunk_width
            x1 = anim_pos[0]
            x2 = x1 + chunk_width
            progress_canvas.coords(progress_fill, x1, 0, x2, canvas_height)
            gui.window.after(20, animate)

        animate()

        def on_setup_close():
            anim_active[0] = False
            if updater.is_updating:
                updater.cancel_update()
            gui.window.destroy()
            sys.exit(0)

        dialog.protocol("WM_DELETE_WINDOW", on_setup_close)

        def progress_cb(msg, pct):
            gui.window.after(0, lambda: status_lbl.config(text=msg))

        def complete_cb(success, msg):
            anim_active[0] = False
            if success:
                gui.window.after(0, lambda: progress_canvas.coords(progress_fill, 0, 0, canvas_width, canvas_height))
                gui.window.after(200, dialog.destroy)
                gui.window.after(200, gui.window.deiconify)
            else:
                gui.window.after(0, lambda: status_lbl.config(text=f"Failed: {msg}"))

        updater.download_updates(progress_cb, complete_cb)
    else:
        gui.window.deiconify()



if __name__ == "__main__":
    main()
