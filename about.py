import tkinter as tk
import webbrowser
from PIL import Image, ImageTk

from config import (
    APP_NAME, APP_VERSION, HEADER_BG_COLOR, WINDOW_BG_COLOR, TEXT_COLOR, 
    BUTTON_COLOR, BUTTON_ACTIVE_COLOR, BUTTON_DISABLED_COLOR, 
    ICON_PNG_PATH, KOFI_LOGO_PATH, SOCIABUZZ_LOGO_PATH, WINDOW_WIDTH, WINDOW_HEIGHT
)
from config import Fonts
from updater import updater
from utils import debug_print

class AboutDialogManager:
    """Manages the About dialog and its update check flow"""
    
    def __init__(self, main_gui):
        self.gui = main_gui
        self.window = main_gui.window
        
        # Keep references to images to prevent garbage collection
        self.about_icon = None
        self.kofi_icon = None
        self.socia_icon = None
        
    def show_about_dialog(self):
        """Show About dialog"""
        about_dialog = tk.Toplevel(self.window)
        about_dialog.title("About VidMuncher")
        about_dialog.geometry("400x570")
        about_dialog.configure(bg=HEADER_BG_COLOR)
        about_dialog.resizable(False, False)
        
        try:
            x = self.window.winfo_x() + (WINDOW_WIDTH // 2) - 200
            y = self.window.winfo_y() + (WINDOW_HEIGHT // 2) - 275
            about_dialog.geometry(f"+{x}+{y}")
        except:
            pass

        about_dialog.transient(self.window)
        about_dialog.grab_set()

        def on_about_close():
            if updater.is_updating:
                updater.cancel_update()
                self.gui.stop_indeterminate_progress(text="Update cancelled.", success=False)
            about_dialog.destroy()

        about_dialog.protocol("WM_DELETE_WINDOW", on_about_close)

        self.gui.apply_dark_title_bar(about_dialog)
        
        main_frame = tk.Frame(about_dialog, bg=HEADER_BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        if ICON_PNG_PATH.exists():
            try:
                icon_img = Image.open(ICON_PNG_PATH)
                icon_img = icon_img.resize((80, 80), Image.Resampling.LANCZOS)
                self.about_icon = ImageTk.PhotoImage(icon_img)
                tk.Label(main_frame, image=self.about_icon, bg=HEADER_BG_COLOR).pack(pady=(20, 10))
            except Exception as e:
                debug_print(f"Failed to load about icon: {e}")
                
        app_title_lbl = tk.Label(main_frame, text=f"VidMuncher {APP_VERSION}", font=("Poppins", 14, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR, cursor="hand2")
        app_title_lbl.pack()
        app_title_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/aprixlabs/VidMuncher"))

        desc_frame = tk.Frame(main_frame, bg=HEADER_BG_COLOR)
        desc_frame.pack(pady=20, padx=20, fill=tk.X)
        
        tk.Label(desc_frame, text="Download videos and audio from YouTube, Instagram, TikTok, and many supported platforms.", 
                 font=Fonts.SMALL, bg=HEADER_BG_COLOR, fg=TEXT_COLOR, wraplength=350, justify=tk.CENTER).pack(pady=(0, 10))
                 
        tk.Label(desc_frame, text="Supported sites:", font=Fonts.SMALL, bg=HEADER_BG_COLOR, fg=TEXT_COLOR).pack()
        
        link1 = tk.Label(desc_frame, text="yt-dlp Supported Sites", font=("Poppins", 9, "underline"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR, cursor="hand2")
        link1.pack(pady=(0, 10))
        link1.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md"))
        
        powered_frame = tk.Frame(desc_frame, bg=HEADER_BG_COLOR)
        powered_frame.pack(pady=10)
        
        tk.Label(powered_frame, text="Powered by ", font=Fonts.SMALL, bg=HEADER_BG_COLOR, fg=TEXT_COLOR, bd=0, padx=0, pady=0).pack(side=tk.LEFT)
        ytdlp_link = tk.Label(powered_frame, text="yt-dlp", font=("Poppins", 9, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR, cursor="hand2", bd=0, padx=0, pady=0)
        ytdlp_link.pack(side=tk.LEFT)
        ytdlp_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/yt-dlp/yt-dlp"))
        
        tk.Label(powered_frame, text=" and ", font=Fonts.SMALL, bg=HEADER_BG_COLOR, fg=TEXT_COLOR, bd=0, padx=0, pady=0).pack(side=tk.LEFT)
        ffmpeg_link = tk.Label(powered_frame, text="FFmpeg", font=("Poppins", 9, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR, cursor="hand2", bd=0, padx=0, pady=0)
        ffmpeg_link.pack(side=tk.LEFT)
        ffmpeg_link.bind("<Button-1>", lambda e: webbrowser.open("https://ffmpeg.org"))
        
        copyright_frame = tk.Frame(desc_frame, bg=HEADER_BG_COLOR)
        copyright_frame.pack()
        
        tk.Label(copyright_frame, text="Copyright \u00a9 2026 ", font=Fonts.SMALL, bg=HEADER_BG_COLOR, fg=TEXT_COLOR, bd=0, padx=0, pady=0).pack(side=tk.LEFT)
        aprix_link = tk.Label(copyright_frame, text="Aprix Labs", font=("Poppins", 9, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR, cursor="hand2", bd=0, padx=0, pady=0)
        aprix_link.pack(side=tk.LEFT)
        aprix_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/aprixlabs"))
        
        tk.Label(main_frame, text="Support Me On", font=("Poppins", 11, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR).pack(pady=(0, 5))
        
        support_frame = tk.Frame(main_frame, bg=HEADER_BG_COLOR)
        support_frame.pack(pady=5)
        
        if KOFI_LOGO_PATH.exists():
            try:
                kofi_img = Image.open(KOFI_LOGO_PATH)
                aspect = kofi_img.width / kofi_img.height
                kofi_img = kofi_img.resize((int(25 * aspect), 25), Image.Resampling.LANCZOS)
                self.kofi_icon = ImageTk.PhotoImage(kofi_img)
                kofi_btn = tk.Label(support_frame, image=self.kofi_icon, bg=HEADER_BG_COLOR, cursor="hand2")
                kofi_btn.pack(side=tk.LEFT, padx=10)
                kofi_btn.bind("<Button-1>", lambda e: webbrowser.open("https://ko-fi.com/aprixlabs"))
            except Exception as e:
                debug_print(f"Failed to load Ko-fi logo: {e}")
                
        if SOCIABUZZ_LOGO_PATH.exists():
            try:
                socia_img = Image.open(SOCIABUZZ_LOGO_PATH)
                aspect = socia_img.width / socia_img.height
                socia_img = socia_img.resize((int(25 * aspect), 25), Image.Resampling.LANCZOS)
                self.socia_icon = ImageTk.PhotoImage(socia_img)
                socia_btn = tk.Label(support_frame, image=self.socia_icon, bg=HEADER_BG_COLOR, cursor="hand2")
                socia_btn.pack(side=tk.LEFT, padx=10)
                socia_btn.bind("<Button-1>", lambda e: webbrowser.open("https://sociabuzz.com/aprixlabs/support"))
            except Exception as e:
                debug_print(f"Failed to load Sociabuzz logo: {e}")

        self.update_btn = tk.Button(
            main_frame,
            text="Check for update",
            bg=BUTTON_COLOR,
            fg=TEXT_COLOR,
            activebackground=BUTTON_ACTIVE_COLOR,
            activeforeground=TEXT_COLOR,
            disabledforeground=TEXT_COLOR,
            font=Fonts.BOLD,
            relief=tk.FLAT,
            borderwidth=0,
            cursor="hand2",
            command=lambda: self.start_update(self.update_btn, about_dialog)
        )
        self.update_btn.pack(pady=(25, 20), ipadx=10, ipady=2)

    def start_update(self, btn, dialog):
        """Start the dependency update process"""
        btn.config(state=tk.DISABLED, text="Checking for updates...", bg=BUTTON_DISABLED_COLOR)
        
        def check_result_cb(has_update, local_ver, remote_ver, error):
            self.window.after(0, lambda: self._handle_check_result(has_update, local_ver, remote_ver, error, btn, dialog))
            
        updater.check_updates(check_result_cb)

    def _handle_check_result(self, has_update, local_ver, remote_ver, error, btn, dialog):
        """Handle the result of update check"""
        if not dialog.winfo_exists():
            return
            
        if error:
            self.gui.show_custom_message(dialog, "Update Check Failed", f"The application could not check for updates.\nPlease verify your network connection and try again.\n\nDetails: {error}", "error")
            btn.config(state=tk.NORMAL, text="Check for update", bg=BUTTON_COLOR)
            return
            
        if has_update:
            btn.config(state=tk.NORMAL, text="Check for update", bg=BUTTON_COLOR)
            msg = (
                f"One or more components have updates available.\n\n"
                f"VidMuncher\tApp is up to date ({APP_VERSION}).\n"
                f"yt-dlp\t\tLatest: {remote_ver}\n"
                f"FFmpeg\t\tLatest build will be installed.\n\n"
                f"Download and install the latest yt-dlp and FFmpeg now?"
            )

            def on_yes():
                btn.config(state=tk.DISABLED, text="Downloading updates...", bg=BUTTON_DISABLED_COLOR)
                self._show_update_progress_dialog(dialog, btn)

            self.gui.show_custom_message(dialog, "Update Available", msg, "ask", on_yes)
        else:
            self.gui.show_custom_message(
                dialog,
                "All Components Up to Date",
                f"VidMuncher {APP_VERSION} — no app update available at this time.\n\nyt-dlp and FFmpeg are already on their latest versions.",
                "info"
            )
            btn.config(state=tk.NORMAL, text="Check for update", bg=BUTTON_COLOR)

    def _show_update_progress_dialog(self, about_dialog, btn):
        """Show a dedicated progress popup for the update download."""
        popup = tk.Toplevel(self.window)
        popup.title("Downloading Updates")
        popup.geometry("400x160")
        popup.configure(bg=HEADER_BG_COLOR)
        popup.resizable(False, False)
        popup.transient(self.window)
        popup.grab_set()

        try:
            x = self.window.winfo_x() + (WINDOW_WIDTH // 2) - 200
            y = self.window.winfo_y() + (WINDOW_HEIGHT // 2) - 80
            popup.geometry(f"+{x}+{y}")
        except:
            pass

        self.gui.apply_dark_title_bar(popup)

        tk.Label(popup, text="Downloading latest components...",
                 font=("Poppins", 11, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR).pack(pady=(22, 5))
        tk.Label(popup, text="Please wait while yt-dlp and FFmpeg are being updated.",
                 font=("Poppins", 9), bg=HEADER_BG_COLOR, fg="#cccccc").pack(pady=(0, 12))

        canvas_width = 340
        canvas_height = 18
        chunk_width = 120

        progress_canvas = tk.Canvas(popup, width=canvas_width, height=canvas_height, bg="#1a000e", highlightthickness=0)
        progress_canvas.pack(pady=(0, 8))
        progress_fill = progress_canvas.create_rectangle(0, 0, 0, canvas_height, fill=BUTTON_COLOR, outline="")

        status_lbl = tk.Label(popup, text="Preparing...", font=("Poppins", 9), bg=HEADER_BG_COLOR, fg=TEXT_COLOR)
        status_lbl.pack()

        anim_pos = [-chunk_width]
        anim_active = [True]

        def animate():
            if not anim_active[0]:
                return
            anim_pos[0] += 8
            if anim_pos[0] > canvas_width:
                anim_pos[0] = -chunk_width
            progress_canvas.coords(progress_fill, anim_pos[0], 0, anim_pos[0] + chunk_width, canvas_height)
            self.window.after(20, animate)

        animate()

        def on_popup_close():
            anim_active[0] = False
            if updater.is_updating:
                updater.cancel_update()
            btn.config(state=tk.NORMAL, text="Check for update", bg=BUTTON_COLOR)
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_popup_close)

        def progress_cb(msg, pct):
            self.window.after(0, lambda: status_lbl.config(text=msg))

        def complete_cb(success, msg):
            anim_active[0] = False
            self.window.after(0, lambda: btn.config(state=tk.NORMAL, text="Check for update", bg=BUTTON_COLOR))
            if success:
                self.window.after(0, lambda: progress_canvas.coords(progress_fill, 0, 0, canvas_width, canvas_height))
                self.window.after(200, popup.destroy)
                self.window.after(250, lambda: self.gui.show_custom_message(about_dialog, "Update Complete", msg, "info"))
            else:
                self.window.after(0, lambda: status_lbl.config(text=f"Failed: {msg}"))

        updater.download_updates(progress_cb, complete_cb)
