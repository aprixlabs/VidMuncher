"""
VidMuncher GUI Module
Contains GUI components and event handlers
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import webbrowser
from PIL import Image, ImageTk

from config import *
from utils import (
    sanitize_filename, get_extension_from_preset, get_unique_filename,
    debug_print, validate_url, force_garbage_collection, find_downloaded_file
)
from downloader import video_analyzer, video_downloader
from encoder import encoder_manager
from updater import updater
from about import AboutDialogManager

class VidMuncherGUI:
    """Main GUI class for VidMuncher application"""
    
    def __init__(self):
        self.window = None
        self.video_data = {}
        self.thumbnail_imgtk = None
        self.current_pil_image = None
        self.is_downloading = False
        self.current_temp_files = []
        self.active_threads = []
        self.last_completed_path = None
        # Guard against double-call to complete_download() from race condition
        self._download_complete_lock = threading.Lock()
        self._complete_download_called = False

        self.url_var = None
        self.url_entry = None
        self.video_info = None
        self.thumbnail_label = None
        self.preset_combo = None
        self.encoder_combo = None
        self.save_path_var = None
        self.save_entry = None
        self.analyze_button = None
        self.download_button = None
        self.cancel_button = None
        self.progress_canvas = None
        self.progress_fill = None
        self.progress_text_item = None
        self._indeterminate_active = False
        self._indeterminate_pos = 0
        
        self.setup_window()
        
        self.about_manager = AboutDialogManager(self)
        self.setup_gui_components()
        self.setup_styles()

        self.window.after(300000, self.periodic_cleanup)
    
    def setup_window(self):
        """Initialize main window"""
        self.window = tk.Tk()
        self.window.withdraw()
        self.window.title(APP_TITLE)

        self.window.update_idletasks()
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = (screen_w - WINDOW_WIDTH) // 2
        y = (screen_h - WINDOW_HEIGHT) // 2
        self.window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.window.configure(bg=WINDOW_BG_COLOR)
        
        self.window.resizable(False, False)
        self.window.maxsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.window.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.apply_dark_title_bar()

        self.setup_window_icon()

    def apply_dark_title_bar(self, target_window=None):
        """
        Applies a dark mode theme to the window title bar on Windows.
        This function only works on Windows operating systems.
        """
        if target_window is None:
            target_window = self.window
            
        try:
            import ctypes

            if ctypes.windll.kernel32.GetVersion() >= 0x0A000000:
                target_window.update()
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
                get_parent = ctypes.windll.user32.GetParent

                hwnd = get_parent(target_window.winfo_id())
                rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
                value = 2
                value = ctypes.c_int(value)
                set_window_attribute(hwnd, rendering_policy, ctypes.byref(value), ctypes.sizeof(value))
        except Exception as e:
            debug_print(f"Could not set dark title bar: {e}")

    def setup_window_icon(self):
        """Setup window icon"""
        icon_set = False
        
        if ICON_PNG_PATH.exists():
            try:
                icon_image = Image.open(ICON_PNG_PATH)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.window.iconphoto(True, icon_photo)
                icon_set = True
                debug_print("Icon set from PNG")
            except Exception as e:
                debug_print(f"Failed to set PNG icon: {e}")
        
        if not icon_set and ICON_PATH.exists():
            try:
                self.window.iconbitmap(ICON_PATH)
                icon_set = True
                debug_print("Icon set from ICO")
            except Exception as e:
                debug_print(f"Failed to set ICO icon: {e}")
        
        if icon_set:
            try:
                import ctypes
                myappid = f'{APP_NAME.lower()}.app.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                debug_print("App ID set for taskbar")
            except:
                pass
    
    def setup_gui_components(self):
        """Setup all GUI components"""
        self.setup_header()
        self.setup_url_input()
        self.setup_video_info()
        self.setup_thumbnail()
        self.setup_preset_selection()
        self.setup_save_location()
        self.setup_buttons()
        self.setup_progress_bar()
        self.setup_copyright()
    
    def setup_header(self):
        """Setup header section"""
        header_bg = tk.Frame(self.window, bg=HEADER_BG_COLOR, height=Layout.HEADER_HEIGHT)
        header_bg.place(x=0, y=0, width=WINDOW_WIDTH, height=Layout.HEADER_HEIGHT)
        
        logo_frame = tk.Frame(header_bg, bg=HEADER_BG_COLOR)
        logo_frame.place(x=Layout.HEADER_IMAGE_X, y=6, width=400, height=65)
        
        # Icon
        if ICON_PNG_PATH.exists():
            try:
                icon_img = Image.open(ICON_PNG_PATH)
                icon_img = icon_img.resize((50, 50), Image.Resampling.LANCZOS)
                self.header_icon = ImageTk.PhotoImage(icon_img)
                tk.Label(logo_frame, image=self.header_icon, bg=HEADER_BG_COLOR, bd=0).place(x=0, y=5)
            except Exception as e:
                debug_print(f"Failed to load header icon: {e}")
                
        title_frame = tk.Frame(logo_frame, bg=HEADER_BG_COLOR)
        title_frame.place(x=64, y=0)
        
        tk.Label(title_frame, text=APP_NAME, font=("Poppins Black", 22), bg=HEADER_BG_COLOR, fg="#ffdcee", bd=0, padx=0, pady=0).pack(side=tk.LEFT, anchor="s")
        tk.Label(title_frame, text=APP_VERSION, font=("Poppins", 8, "bold"), bg=HEADER_BG_COLOR, fg="#ffdcee", bd=0, padx=0, pady=0).pack(side=tk.LEFT, anchor="s", padx=(2, 0), pady=(0, 8))
        
        tk.Label(logo_frame, text="Video Downloader", font=("Poppins Medium", 11), bg=HEADER_BG_COLOR, fg="#ffdcee", bd=0, padx=0, pady=0).place(x=66, y=36)
                
        # About Button
        self.about_btn = tk.Button(
            self.window,
            text="ⓘ",
            bg=BUTTON_COLOR,
            fg=TEXT_COLOR,
            activebackground=BUTTON_ACTIVE_COLOR,
            activeforeground=TEXT_COLOR,
            font=("Segoe UI", 12),
            relief=tk.FLAT,
            borderwidth=0,
            cursor="hand2",
            command=self.about_manager.show_about_dialog
        )
        self.about_btn.place(
            x=Layout.ABOUT_BUTTON_X, y=Layout.ABOUT_BUTTON_Y,
            width=Layout.ABOUT_BUTTON_WIDTH, height=Layout.ABOUT_BUTTON_HEIGHT
        )
    
    def setup_url_input(self):
        """Setup URL input field"""
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            self.window,
            textvariable=self.url_var,
            font=Fonts.DEFAULT,
            bg=HEADER_BG_COLOR,
            fg=PLACEHOLDER_COLOR,
            insertbackground=TEXT_COLOR,
            selectbackground=BUTTON_COLOR,
            selectforeground=TEXT_COLOR,
            relief=tk.FLAT
        )
        self.url_entry.place(
            x=Layout.URL_ENTRY_X, y=Layout.URL_ENTRY_Y,
            width=Layout.URL_ENTRY_WIDTH, height=Layout.URL_ENTRY_HEIGHT
        )
        self.url_entry.insert(0, Layout.URL_PLACEHOLDER)
        
        self.url_entry.bind("<FocusIn>", self.clear_url_placeholder)
        self.url_entry.bind("<FocusOut>", self.restore_url_placeholder)
        self.url_entry.bind("<Button-3>", self.show_url_context_menu)
    
    def setup_video_info(self):
        """Setup video information display"""
        self.video_info_frame = tk.Frame(self.window, bg=HEADER_BG_COLOR)
        self.video_info_frame.place(
            x=Layout.VIDEO_INFO_X, y=Layout.VIDEO_INFO_Y,
            width=Layout.VIDEO_INFO_WIDTH, height=Layout.VIDEO_INFO_HEIGHT
        )

        self.video_info_placeholder = tk.Label(
            self.video_info_frame,
            text=Layout.VIDEO_INFO_PLACEHOLDER,
            bg=HEADER_BG_COLOR,
            fg=PLACEHOLDER_COLOR,
            font=Fonts.SMALL,
            anchor='center'
        )
        self.video_info_placeholder.place(
            x=Layout.VIDEO_INFO_WIDTH // 2,
            y=Layout.VIDEO_INFO_HEIGHT // 2,
            anchor='center'
        )

        self.video_info = tk.Text(
            self.video_info_frame,
            wrap=tk.WORD,
            bg=HEADER_BG_COLOR,
            fg=TEXT_COLOR,
            font=Fonts.SMALL,
            relief=tk.FLAT,
            state=tk.DISABLED,
            cursor="arrow"
        )

        self.video_info.bind("<MouseWheel>", self.on_video_info_mousewheel)
        self.window.bind("<MouseWheel>", self.on_window_mousewheel)
    
    def setup_thumbnail(self):
        """Setup thumbnail display"""
        self.thumbnail_frame = tk.Frame(self.window, bg=HEADER_BG_COLOR)
        self.thumbnail_frame.place(
            x=Layout.THUMBNAIL_X, y=Layout.THUMBNAIL_Y,
            width=Layout.THUMBNAIL_WIDTH, height=Layout.THUMBNAIL_HEIGHT
        )

        self.thumbnail_placeholder = tk.Label(
            self.thumbnail_frame,
            text=Layout.THUMBNAIL_PLACEHOLDER,
            bg=HEADER_BG_COLOR,
            fg=PLACEHOLDER_COLOR,
            font=Fonts.SMALL,
            anchor='center'
        )
        self.thumbnail_placeholder.place(
            x=Layout.THUMBNAIL_WIDTH // 2,
            y=Layout.THUMBNAIL_HEIGHT // 2,
            anchor='center'
        )

        self.thumbnail_label = tk.Label(self.thumbnail_frame, bg=HEADER_BG_COLOR)
    
    def setup_preset_selection(self):
        """Setup preset selection components"""
        tk.Label(
            self.window,
            text="Select Preset",
            font=Fonts.DEFAULT,
            bg=WINDOW_BG_COLOR,
            fg=TEXT_COLOR
        ).place(x=Layout.PRESET_LABEL_X, y=Layout.PRESET_LABEL_Y)
        
        self.preset_combo = ttk.Combobox(
            self.window,
            state="readonly",
            font=Fonts.COMBO,
            style='Custom.TCombobox',
            values=DOWNLOAD_PRESETS
        )
        self.preset_combo.place(
            x=Layout.PRESET_COMBO_X, y=Layout.PRESET_COMBO_Y,
            width=Layout.PRESET_COMBO_WIDTH, height=Layout.PRESET_COMBO_HEIGHT
        )
        self.preset_combo.current(0)
        self.preset_combo.bind('<<ComboboxSelected>>', self.on_preset_change)

        tk.Label(
            self.window,
            text="Transcode",
            font=Fonts.DEFAULT,
            bg=WINDOW_BG_COLOR,
            fg=TEXT_COLOR
        ).place(x=Layout.REENCODE_LABEL_X, y=Layout.REENCODE_LABEL_Y)

        self.encoder_combo = ttk.Combobox(
            self.window,
            state="readonly",
            font=Fonts.COMBO,
            style='Custom.TCombobox',
            values=ENCODER_OPTIONS
        )
        self.encoder_combo.place(
            x=Layout.REENCODE_COMBO_X, y=Layout.REENCODE_COMBO_Y,
            width=Layout.REENCODE_COMBO_WIDTH, height=Layout.REENCODE_COMBO_HEIGHT
        )
        self.encoder_combo.current(0)
        self.encoder_combo.bind('<<ComboboxSelected>>', self.on_encoder_change)
    
    def setup_save_location(self):
        """Setup save location components"""
        tk.Label(
            self.window,
            text="Save Location",
            font=Fonts.DEFAULT,
            bg=WINDOW_BG_COLOR,
            fg=TEXT_COLOR
        ).place(x=Layout.SAVE_LABEL_X, y=Layout.SAVE_LABEL_Y)
        
        self.save_path_var = tk.StringVar()
        self.save_entry = tk.Entry(
            self.window,
            textvariable=self.save_path_var,
            font=Fonts.SMALL,
            bg=HEADER_BG_COLOR,
            fg=TEXT_COLOR,
            relief=tk.FLAT,
            insertbackground=TEXT_COLOR
        )
        self.save_entry.place(
            x=Layout.SAVE_ENTRY_X, y=Layout.SAVE_ENTRY_Y,
            width=Layout.SAVE_ENTRY_WIDTH, height=Layout.SAVE_ENTRY_HEIGHT
        )
        
        tk.Button(
            self.window,
            text="Browse",
            font=Fonts.BOLD,
            bg=BUTTON_COLOR,
            fg="white",
            activebackground=BUTTON_ACTIVE_COLOR,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.browse_save_path
        ).place(
            x=Layout.BROWSE_BUTTON_X, y=Layout.BROWSE_BUTTON_Y,
            width=Layout.BROWSE_BUTTON_WIDTH, height=Layout.BROWSE_BUTTON_HEIGHT
        )
    
    def setup_buttons(self):
        """Setup action buttons"""
        self.analyze_button = tk.Button(
            self.window,
            text="Analyze",
            font=Fonts.BOLD,
            bg=BUTTON_COLOR,
            fg="white",
            activebackground=BUTTON_ACTIVE_COLOR,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.analyze_video
        )
        self.analyze_button.place(
            x=Layout.ANALYZE_BUTTON_X, y=Layout.ANALYZE_BUTTON_Y,
            width=Layout.ANALYZE_BUTTON_WIDTH, height=Layout.ANALYZE_BUTTON_HEIGHT
        )
        
        self.download_button = tk.Button(
            self.window,
            text="Download",
            font=Fonts.BOLD,
            bg=BUTTON_DISABLED_COLOR,
            fg="white",
            activebackground=BUTTON_ACTIVE_COLOR,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.download_video,
            state=tk.DISABLED
        )
        self.download_button.place(
            x=Layout.DOWNLOAD_BUTTON_X, y=Layout.DOWNLOAD_BUTTON_Y,
            width=Layout.DOWNLOAD_BUTTON_WIDTH, height=Layout.DOWNLOAD_BUTTON_HEIGHT
        )
        
        self.cancel_button = tk.Button(
            self.window,
            text="Cancel",
            font=Fonts.BOLD,
            bg=BUTTON_COLOR,
            fg="white",
            activebackground=BUTTON_ACTIVE_COLOR,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.cancel_download
        )
        self.cancel_button.place_forget()

        self.open_folder_button = tk.Button(
            self.window,
            text="Open Folder",
            font=Fonts.BOLD,
            bg=BUTTON_COLOR,
            fg="white",
            activebackground=BUTTON_ACTIVE_COLOR,
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_download_folder
        )
    
    def setup_progress_bar(self):
        """Setup progress bar"""
        progress_frame = tk.Frame(self.window, bg=HEADER_BG_COLOR)
        progress_frame.place(
            x=Layout.PROGRESS_X, y=Layout.PROGRESS_Y,
            width=Layout.PROGRESS_WIDTH, height=Layout.PROGRESS_HEIGHT
        )
        
        self.progress_canvas = tk.Canvas(
            progress_frame,
            bg=HEADER_BG_COLOR,
            highlightthickness=0,
            height=Layout.PROGRESS_HEIGHT
        )
        self.progress_canvas.place(relwidth=1, relheight=1)

        progress_bg = self.progress_canvas.create_rectangle(
            0, 0, Layout.PROGRESS_WIDTH, Layout.PROGRESS_HEIGHT,
            fill=HEADER_BG_COLOR, outline=HEADER_BG_COLOR
        )
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, Layout.PROGRESS_HEIGHT,
            fill=BUTTON_COLOR, outline=BUTTON_COLOR
        )
        
        # Progress text
        self.progress_text_item = self.progress_canvas.create_text(
            Layout.PROGRESS_WIDTH // 2, Layout.PROGRESS_HEIGHT // 2,
            text="", font=Fonts.SMALL, fill=TEXT_COLOR, anchor=tk.CENTER
        )

    def setup_copyright(self):
        """Setup copyright text"""
        copyright_label = tk.Label(
            self.window,
            text="Copyright © 2026 - VidMuncher by Aprix Labs",
            font=Fonts.SMALL,
            bg=WINDOW_BG_COLOR,
            fg="#76485D"
        )
        copyright_label.place(x=Layout.COPYRIGHT_X, y=Layout.COPYRIGHT_Y, anchor=tk.CENTER)

    def cleanup_thumbnail(self):
        """Proper thumbnail cleanup to prevent memory leaks"""
        if hasattr(self, 'thumbnail_imgtk') and self.thumbnail_imgtk:
            self.thumbnail_imgtk = None

        if hasattr(self, 'current_pil_image') and self.current_pil_image:
            try:
                self.current_pil_image.close()
            except:
                pass
            self.current_pil_image = None

        force_garbage_collection()

    def clear_video_data(self):
        """Clear video data and associated resources"""
        if 'formats' in self.video_data:
            del self.video_data['formats']

        if 'thumbnails' in self.video_data:
            del self.video_data['thumbnails']

        self.video_data.clear()

        self.video_info.delete(1.0, tk.END)

        force_garbage_collection()

    def cleanup_temp_files(self):
        """Clean up temporary files and references"""
        for temp_file in self.current_temp_files[:]:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    debug_print(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                debug_print(f"Failed to cleanup {temp_file}: {e}")
            finally:
                if temp_file in self.current_temp_files:
                    self.current_temp_files.remove(temp_file)

        self.current_temp_files.clear()

    def add_temp_file(self, filepath):
        """Add temp file with automatic cleanup on limit"""
        self.current_temp_files.append(filepath)

        if len(self.current_temp_files) > 10:
            old_files = self.current_temp_files[:5]
            for old_file in old_files:
                try:
                    if os.path.exists(old_file):
                        os.remove(old_file)
                except:
                    pass
            self.current_temp_files = self.current_temp_files[5:]

    def cleanup_finished_threads(self):
        """Remove finished threads from active list"""
        initial_count = len(self.active_threads)
        self.active_threads = [t for t in self.active_threads if t.is_alive()]

        if len(self.active_threads) < initial_count * 0.5:
            force_garbage_collection()

    def start_thread_with_cleanup(self, target, *args, **kwargs):
        """Start thread with automatic cleanup"""
        self.cleanup_finished_threads()

        thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
        self.active_threads.append(thread)
        thread.start()

        return thread

    def comprehensive_cleanup(self):
        """Comprehensive cleanup of all resources"""
        self.cleanup_thumbnail()

        self.cleanup_temp_files()

        self.cleanup_finished_threads()

        if not self.is_downloading:
            self.clear_video_data()

        force_garbage_collection()

    def periodic_cleanup(self):
        """Periodic cleanup every 5 minutes"""
        self.comprehensive_cleanup()

        self.window.after(300000, self.periodic_cleanup)

    def setup_styles(self):
        """Setup TTK styles"""
        combo_style = ttk.Style()
        combo_style.theme_use('clam')

        combo_style.configure('Custom.TCombobox',
                             fieldbackground=HEADER_BG_COLOR,
                             background=BUTTON_COLOR,
                             foreground=TEXT_COLOR,
                             arrowcolor=TEXT_COLOR,
                             bordercolor=HEADER_BG_COLOR,
                             lightcolor=HEADER_BG_COLOR,
                             darkcolor=HEADER_BG_COLOR,
                             focuscolor=HEADER_BG_COLOR,
                             borderwidth=1,
                             relief='flat')

        combo_style.map('Custom.TCombobox',
                       fieldbackground=[('readonly', HEADER_BG_COLOR)],
                       selectbackground=[('readonly', HEADER_BG_COLOR)],
                       selectforeground=[('readonly', TEXT_COLOR)],
                       background=[('active', BUTTON_ACTIVE_COLOR), ('pressed', BUTTON_ACTIVE_COLOR)],
                       bordercolor=[('focus', HEADER_BG_COLOR)],
                       lightcolor=[('focus', HEADER_BG_COLOR)],
                       darkcolor=[('focus', HEADER_BG_COLOR)])

        combo_style.configure('Custom.TCombobox.Listbox',
                             background=HEADER_BG_COLOR,
                             foreground=TEXT_COLOR,
                             selectbackground=BUTTON_COLOR,
                             selectforeground=TEXT_COLOR,
                             borderwidth=0,
                             relief='flat')
                             
        combo_style.configure('TComboboxPopdownFrame', 
                             background=HEADER_BG_COLOR,
                             borderwidth=0,
                             relief='flat')

        try:
            self.window.option_add('*TCombobox*Listbox.Background', HEADER_BG_COLOR)
            self.window.option_add('*TCombobox*Listbox.Foreground', TEXT_COLOR)
            self.window.option_add('*TCombobox*Listbox.selectBackground', BUTTON_COLOR)
            self.window.option_add('*TCombobox*Listbox.selectForeground', TEXT_COLOR)
            self.window.option_add('*TCombobox*Listbox.font', 'Poppins 9')
            self.window.option_add('*TCombobox*Listbox.borderWidth', '0')
            self.window.option_add('*TCombobox*Listbox.relief', 'flat')
            self.window.option_add('*TCombobox*Listbox.highlightThickness', '0')
            self.window.option_add('*TCombobox*Listbox.highlightBackground', HEADER_BG_COLOR)
            self.window.option_add('*TCombobox*Listbox.highlightColor', HEADER_BG_COLOR)
            self.window.option_add('*Listbox.borderWidth', '0')
            self.window.option_add('*Listbox.highlightThickness', '0')
            self.window.option_add('*Scrollbar.width', '6')
            self.window.option_add('*Scrollbar.background', BUTTON_COLOR)
            self.window.option_add('*Scrollbar.troughColor', HEADER_BG_COLOR)
            self.window.option_add('*Scrollbar.activeBackground', BUTTON_ACTIVE_COLOR)
            self.window.option_add('*Scrollbar.borderWidth', '0')
            self.window.option_add('*Scrollbar.highlightThickness', '0')
            self.window.option_add('*Scrollbar.relief', 'flat')
            self.window.option_add('*Scrollbar.elementBorderWidth', '0')
        except:
            pass

        combo_style.configure('Vertical.TScrollbar',
                             background=BUTTON_COLOR,
                             troughcolor=HEADER_BG_COLOR,
                             arrowcolor=TEXT_COLOR,
                             bordercolor=HEADER_BG_COLOR,
                             lightcolor=BUTTON_COLOR,
                             darkcolor=BUTTON_COLOR,
                             borderwidth=0,
                             width=6)

        combo_style.map('Vertical.TScrollbar',
                       background=[('active', BUTTON_ACTIVE_COLOR), ('pressed', BUTTON_ACTIVE_COLOR)],
                       arrowcolor=[('disabled', PLACEHOLDER_COLOR)])

    def clear_url_placeholder(self, event):
        """Clear URL placeholder on focus"""
        if self.url_entry.get() == Layout.URL_PLACEHOLDER:
            self.url_var.set("")
            self.url_entry.config(fg=TEXT_COLOR)

    def restore_url_placeholder(self, event):
        """Restore URL placeholder when empty"""
        if self.url_entry.get() == "":
            self.url_entry.insert(0, Layout.URL_PLACEHOLDER)
            self.url_entry.config(fg=PLACEHOLDER_COLOR)

    def show_url_context_menu(self, event):
        """Show custom borderless context menu on right click"""
        self.url_entry.focus()
        
        if hasattr(self, 'custom_menu') and self.custom_menu.winfo_exists():
            self.custom_menu.destroy()

        self.custom_menu = tk.Toplevel(self.window)
        self.custom_menu.wm_overrideredirect(True)
        self.custom_menu.configure(bg=HEADER_BG_COLOR)
        
        paste_btn = tk.Label(
            self.custom_menu,
            text="Paste",
            bg=HEADER_BG_COLOR,
            fg=TEXT_COLOR,
            font=Fonts.DEFAULT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        paste_btn.pack(fill=tk.BOTH, expand=True)
        
        paste_btn.bind("<Enter>", lambda e: paste_btn.config(bg=BUTTON_COLOR))
        paste_btn.bind("<Leave>", lambda e: paste_btn.config(bg=HEADER_BG_COLOR))
        
        def on_paste(e):
            self.paste_to_url_entry()
            self.custom_menu.destroy()
            
        paste_btn.bind("<Button-1>", on_paste)
        
        self.custom_menu.geometry(f"+{event.x_root}+{event.y_root}")
        self.custom_menu.bind("<FocusOut>", lambda e: self.custom_menu.destroy())
        self.custom_menu.focus_set()

    def paste_to_url_entry(self):
        """Paste clipboard content to URL entry"""
        try:
            self.clear_url_placeholder(None)
            text = self.window.clipboard_get()
            
            try:
                # If there's a selection, replace it
                sel_start = self.url_entry.index(tk.SEL_FIRST)
                sel_end = self.url_entry.index(tk.SEL_LAST)
                self.url_entry.delete(sel_start, sel_end)
            except tk.TclError:
                pass
                
            self.url_entry.insert(tk.INSERT, text)
        except tk.TclError:
            pass # No text in clipboard

    def on_video_info_mousewheel(self, event):
        """Handle mousewheel in video info area"""
        self.video_info.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_window_mousewheel(self, event):
        """Handle mousewheel on window (for video info area)"""
        x, y = (self.window.winfo_pointerx() - self.window.winfo_rootx(),
                self.window.winfo_pointery() - self.window.winfo_rooty())
        if (Layout.VIDEO_INFO_X <= x <= Layout.VIDEO_INFO_X + Layout.VIDEO_INFO_WIDTH and
            Layout.VIDEO_INFO_Y <= y <= Layout.VIDEO_INFO_Y + Layout.VIDEO_INFO_HEIGHT):
            self.video_info.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_preset_change(self, event):
        """Handle preset selection change"""
        selected = self.preset_combo.get()
        debug_print(f"Preset changed to: {selected}")

        # Disable encoder for audio presets
        if "Audio" in selected:
            self.encoder_combo.current(0)  # Set to "Keep Original"
            self.encoder_combo.config(state="disabled")
        else:
            self.encoder_combo.config(state="readonly")

        if 'title' in self.video_data:
            self.update_preview_path()

    def on_encoder_change(self, event):
        """Handle encoder selection change"""
        selected = self.encoder_combo.get()
        debug_print(f"Encoder changed to: {selected}")

        if 'title' in self.video_data:
            self.update_preview_path()

    def is_encoding_enabled(self):
        """Check if encoding is enabled based on encoder selection"""
        return self.encoder_combo.get() != "Keep Original"

    def clear_thumbnail(self):
        """Clear previous thumbnail to prevent memory leaks"""
        self.cleanup_thumbnail()

    def reset_video_data(self):
        """Reset video data and clear thumbnail"""
        self.clear_video_data()
        self.cleanup_thumbnail()

        self.video_info.place_forget()
        self.video_info_placeholder.place(
            x=Layout.VIDEO_INFO_WIDTH // 2,
            y=Layout.VIDEO_INFO_HEIGHT // 2,
            anchor='center'
        )

        self.thumbnail_label.place_forget()
        self.thumbnail_placeholder.place(
            x=Layout.THUMBNAIL_WIDTH // 2,
            y=Layout.THUMBNAIL_HEIGHT // 2,
            anchor='center'
        )
        self.thumbnail_label.config(image="")
        self.thumbnail_label.config(bg=HEADER_BG_COLOR)

    def update_preview_path(self):
        """Update preview path based on preset and H.264 status"""
        if 'title' not in self.video_data:
            return

        title = self.video_data['title']
        safe_title = sanitize_filename(title)

        # Strip known extensions from title to prevent double extensions (e.g. Video.mp4.mp4)
        known_exts = {".mp4", ".mkv", ".webm", ".avi", ".m4v", ".wav", ".mp3", ".m4a"}
        while True:
            root, ext_part = os.path.splitext(safe_title)
            if ext_part.lower() in known_exts:
                safe_title = root
            else:
                break

        encoding_enabled = self.is_encoding_enabled()
        encoder_selection = self.encoder_combo.get()
        ext = get_extension_from_preset(self.preset_combo.get(), encoding_enabled, encoder_selection)

        # We allow %(ext)s to show in the GUI for "Keep Original" as requested
        filename_with_ext = f"{safe_title}.{ext}"
        full_path_with_ext = os.path.join(DEFAULT_DOWNLOAD_PATH, filename_with_ext)
        unique_full_path = get_unique_filename(full_path_with_ext)

        self.save_path_var.set(unique_full_path)
        debug_print(f"Updated preview path: {unique_full_path}")

    def set_button_states(self, analyze_enabled=True, download_enabled=False):
        """Set state of Analyze and Download buttons"""
        if analyze_enabled:
            self.analyze_button.config(state=tk.NORMAL, bg=BUTTON_COLOR)
        else:
            self.analyze_button.config(state=tk.DISABLED, bg=BUTTON_DISABLED_COLOR)

        if download_enabled:
            self.download_button.config(state=tk.NORMAL, bg=BUTTON_COLOR)
        else:
            self.download_button.config(state=tk.DISABLED, bg=BUTTON_DISABLED_COLOR)

    def show_cancel_button(self, show=True):
        """Show or hide cancel button"""
        if show:
            self.cancel_button.place(
                x=Layout.CANCEL_BUTTON_X, y=Layout.CANCEL_BUTTON_Y,
                width=Layout.CANCEL_BUTTON_WIDTH, height=Layout.CANCEL_BUTTON_HEIGHT
            )
        else:
            self.cancel_button.place_forget()

    def show_open_folder_button(self, show=True):
        """Show or hide the Open Folder button"""
        if show and self.last_completed_path:
            self.open_folder_button.place(
                x=Layout.DOWNLOAD_BUTTON_X, y=Layout.DOWNLOAD_BUTTON_Y,
                width=Layout.DOWNLOAD_BUTTON_WIDTH, height=Layout.DOWNLOAD_BUTTON_HEIGHT
            )
        else:
            self.open_folder_button.place_forget()

    def update_progress(self, text, progress=None, error=False):
        """Update progress bar and text"""
        color = "#FF5050" if error else TEXT_COLOR
        self.progress_canvas.itemconfig(self.progress_text_item, text=text, fill=color)

        if progress is not None:
            width = int((progress / 100) * Layout.PROGRESS_WIDTH)
            self.progress_canvas.coords(self.progress_fill, 0, 0, width, Layout.PROGRESS_HEIGHT)

        self.window.update_idletasks()

    def start_indeterminate_progress(self, text=""):
        """Start a looping indeterminate progress animation."""
        self._indeterminate_active = True
        self._indeterminate_pos = -180
        if text:
            self.progress_canvas.itemconfig(self.progress_text_item, text=text, fill=TEXT_COLOR)
        self._animate_indeterminate()

    def _animate_indeterminate(self):
        """Advance one frame of the indeterminate animation."""
        if not self._indeterminate_active:
            return
        chunk = 180
        self._indeterminate_pos += 10
        if self._indeterminate_pos > Layout.PROGRESS_WIDTH:
            self._indeterminate_pos = -chunk
        x1 = self._indeterminate_pos
        x2 = x1 + chunk
        self.progress_canvas.coords(self.progress_fill, x1, 0, x2, Layout.PROGRESS_HEIGHT)
        self.window.after(20, self._animate_indeterminate)

    def stop_indeterminate_progress(self, text="", success=True):
        """Stop the indeterminate animation and reset the progress bar."""
        self._indeterminate_active = False
        self.progress_canvas.coords(self.progress_fill, 0, 0, 0, Layout.PROGRESS_HEIGHT)
        if text:
            color = TEXT_COLOR if success else "#FF5050"
            self.progress_canvas.itemconfig(self.progress_text_item, text=text, fill=color)

    def browse_save_path(self):
        """Browse for save location"""
        encoding_enabled = self.is_encoding_enabled()
        encoder_selection = self.encoder_combo.get()
        extension = get_extension_from_preset(self.preset_combo.get(), encoding_enabled, encoder_selection)

        current_path = self.save_path_var.get()
        default_name = os.path.splitext(os.path.basename(current_path))[0] if current_path else "video"

        path = filedialog.asksaveasfilename(
            defaultextension=f".{extension}",
            initialfile=f"{default_name}.{extension}",
            filetypes=[("Media Files", f"*.{extension}")]
        )
        if path:
            # Ensure path has extension (asksaveasfilename should supply it)
            if not os.path.splitext(path)[1]:
                path = f"{path}.{extension}"
            self.save_path_var.set(path)

    def analyze_video(self):
        """Analyze video URL"""
        self.show_open_folder_button(False)

        url = self.url_var.get().strip()
        if not url or url == Layout.URL_PLACEHOLDER:
            self.update_progress(Messages.URL_EMPTY, error=True)
            return

        if not validate_url(url):
            self.update_progress(Messages.INVALID_URL, error=True)
            return

        self.set_button_states(analyze_enabled=False, download_enabled=False)

        def safe_progress(text, progress=None):
            """Thread-safe progress callback: schedules update on main thread"""
            self.window.after(0, self.update_progress, text, progress)

        def analyze_task():
            success, video_data, error_msg = video_analyzer.analyze_video(
                url, progress_callback=safe_progress
            )

            if success and video_data:
                # Capture data in local vars before scheduling UI update
                captured_data = dict(video_data)
                title = captured_data.get("title", "N/A")
                desc = captured_data.get("description", "")
                thumbnail_url = captured_data.get("thumbnail", "")

                def update_ui_success():
                    """All widget operations run on main thread via after()"""
                    self.video_data.clear()
                    self.video_data.update(captured_data)

                    self.video_info_placeholder.place_forget()
                    self.video_info.place(
                        x=0, y=0,
                        width=Layout.VIDEO_INFO_WIDTH,
                        height=Layout.VIDEO_INFO_HEIGHT
                    )
                    self.video_info.config(state=tk.NORMAL)
                    self.video_info.delete("1.0", tk.END)
                    self.video_info.insert(tk.END, f"{title}\n\n{desc}")
                    self.video_info.config(fg=TEXT_COLOR)
                    self.video_info.config(state=tk.DISABLED)

                    if thumbnail_url:
                        self.download_thumbnail_async(thumbnail_url)

                    self.update_preview_path()

                    self.update_progress(Messages.READY_DOWNLOAD, progress=0)
                    self.set_button_states(analyze_enabled=True, download_enabled=True)

                self.window.after(0, update_ui_success)
            else:
                captured_error = error_msg

                def update_ui_failure():
                    """All widget operations run on main thread via after()"""
                    self.update_progress(captured_error or Messages.FAILED_VIDEO_INFO, error=True)
                    self.reset_video_data()
                    self.set_button_states(analyze_enabled=True, download_enabled=False)

                self.window.after(0, update_ui_failure)

        thread = threading.Thread(target=analyze_task, daemon=True, name="AnalyzeThread")
        self.active_threads.append(thread)
        thread.start()

    def download_thumbnail_async(self, thumbnail_url):
        """Download thumbnail asynchronously"""
        def download_task():
            thumbnail_img = video_analyzer.download_thumbnail(
                thumbnail_url,
                size=(Layout.THUMBNAIL_WIDTH, Layout.THUMBNAIL_HEIGHT)
            )

            def update_thumbnail():
                if thumbnail_img:
                    self.clear_thumbnail()
                    self.thumbnail_imgtk = thumbnail_img

                    self.thumbnail_placeholder.place_forget()
                    self.thumbnail_label.place(x=0, y=0, width=Layout.THUMBNAIL_WIDTH, height=Layout.THUMBNAIL_HEIGHT)
                    self.thumbnail_label.config(image=self.thumbnail_imgtk)
                else:
                    self.thumbnail_label.place_forget()
                    self.thumbnail_placeholder.place(
                        x=Layout.THUMBNAIL_WIDTH // 2,
                        y=Layout.THUMBNAIL_HEIGHT // 2,
                        anchor='center'
                    )
                    self.thumbnail_label.config(image="")

            self.window.after(0, update_thumbnail)

        threading.Thread(target=download_task, daemon=True, name="ThumbnailThread").start()

    def download_video(self):
        """Download video"""
        self.show_open_folder_button(False)
        self.last_completed_path = None

        url = self.url_var.get().strip()
        out_path = self.save_path_var.get()
        preset = self.preset_combo.get()

        # Normalize out_path to be extension-less to avoid double extensions
        known_exts = {".mp4", ".mkv", ".webm", ".avi", ".m4v", ".wav", ".mp3", ".m4a"}
        while True:
            root_out, ext_out = os.path.splitext(out_path)
            if ext_out.lower() in known_exts:
                out_path = root_out
            else:
                break

        if not url or url == Layout.URL_PLACEHOLDER:
            self.update_progress(Messages.URL_EMPTY, error=True)
            return

        self.set_button_states(analyze_enabled=False, download_enabled=False)
        self.show_cancel_button(True)

        self.is_downloading = True
        self.current_temp_files.clear()
        # Reset completion guard for this new download session
        with self._download_complete_lock:
            self._complete_download_called = False

        def download_task():
            encoding_enabled = self.is_encoding_enabled()

            success, final_path, error_msg = video_downloader.download_video(
                url, out_path, preset, encoding_enabled,
                progress_callback=self.update_progress,
                cancel_check=lambda: not self.is_downloading
            )

            if success and final_path:
                debug_print("Download success check:")
                debug_print(f"  - Preset: {preset}")
                debug_print(f"  - Audio in preset: {'Audio' in preset}")
                debug_print(f"  - Encoding enabled: {encoding_enabled}")
                debug_print(f"  - Selected encoder: {self.encoder_combo.get()}")
                debug_print(f"  - Not Keep Original: {self.encoder_combo.get() != 'Keep Original'}")

                if "Audio" not in preset and encoding_enabled and self.encoder_combo.get() != "Keep Original":
                    debug_print("Starting encoding process...")
                    self.encode_video_h264(final_path)
                else:
                    debug_print("Skipping encoding, completing download...")
                    self.update_file_timestamp(final_path, preset)
                    self.last_completed_path = final_path
                    self.complete_download(success=True, message=Messages.DOWNLOAD_COMPLETE)
            else:
                if self.is_downloading:
                    if error_msg and "cancelled" in error_msg.lower():
                        self.update_progress(Messages.DOWNLOAD_CANCELLED, error=True)
                    elif error_msg and "interrupted" in error_msg.lower():
                        self.update_progress(Messages.DOWNLOAD_INTERRUPTED, error=True)
                    else:
                        self.update_progress(error_msg or Messages.DOWNLOAD_FAILED, error=True)
                    self.complete_download(success=False)

        thread = threading.Thread(target=download_task, daemon=True, name="DownloadThread")
        self.active_threads.append(thread)
        thread.start()

    def update_file_timestamp(self, file_path, preset):
        """Update file timestamp for visibility in Explorer after download."""
        try:
            if "Audio" in preset:
                extensions = [".mp3", ".wav", ".m4a", ".aac", ".ogg"]
            else:
                extensions = [".webm", ".mp4", ".mkv", ".m4v", ".avi"]

            self._apply_file_timestamp(file_path, extensions)
        except Exception as e:
            debug_print(f"Error updating file timestamp: {str(e)}")

    def _apply_file_timestamp(self, base_path, extensions):
        """
        Locate a downloaded file by trying multiple extensions, then touch its
        modification timestamp so it appears at the top in Explorer.

        Args:
            base_path (str): Path as returned by the downloader (may include
                             an extension already, or may be bare).
            extensions (list): Ordered list of extensions to probe.
        """
        import time
        import glob

        # Normalise: strip any known extension so we always search from a bare base
        bare_base = os.path.splitext(base_path)[0] if os.path.splitext(base_path)[1] else base_path

        target_file = None

        # Method 1: direct extension probe
        for ext in extensions:
            candidate = bare_base + ext
            if os.path.exists(candidate):
                target_file = candidate
                debug_print(f"Timestamp target found (direct): {target_file}")
                break

        # Method 2: glob wildcard search
        if not target_file:
            safe_base = bare_base.replace('[', r'\[').replace(']', r'\]')
            matches = glob.glob(safe_base + ".*")
            debug_print(f"Glob matches for timestamp: {matches}")
            for match in matches:
                if any(match.lower().endswith(ext) for ext in extensions):
                    target_file = match
                    debug_print(f"Timestamp target found (glob): {target_file}")
                    break

        # Method 3: directory scan by base name substring
        if not target_file:
            directory = os.path.dirname(bare_base)
            base_name = os.path.basename(bare_base)
            try:
                if os.path.exists(directory):
                    for fname in os.listdir(directory):
                        if base_name.lower() in fname.lower():
                            if any(fname.lower().endswith(ext) for ext in extensions):
                                target_file = os.path.join(directory, fname)
                                debug_print(f"Timestamp target found (dir scan): {target_file}")
                                break
            except Exception as scan_err:
                debug_print(f"Directory scan error during timestamp update: {scan_err}")

        if target_file and os.path.exists(target_file):
            current_time = time.time()
            os.utime(target_file, (current_time, current_time))
            debug_print(f"Timestamp updated: {target_file}")
        else:
            debug_print(f"File not found for timestamp update. Base: {bare_base}, Extensions: {extensions}")



    def encode_video_h264(self, input_file):
        """Encode video to H.264"""
        try:
            # Ensure source file exists; fall back to locating by base name
            if not os.path.exists(input_file):
                base_probe = os.path.splitext(input_file)[0]
                probed_file = find_downloaded_file(base_probe)
                if probed_file and os.path.exists(probed_file):
                    debug_print(f"Resolved missing source to: {probed_file}")
                    input_file = probed_file
                else:
                    if self.is_downloading:
                        self.update_progress(Messages.FILE_NOT_FOUND, error=True)
                        self.complete_download(success=False)
                    return

            base_path = os.path.splitext(input_file)[0]
            temp_path = base_path + "_temp.mp4"
            final_path = base_path + ".mp4"

            self.current_temp_files.append(temp_path)

            selected_encoder = self.encoder_combo.get()

            progress_message = ENCODER_PROGRESS_MESSAGES.get(
                selected_encoder,
                f"Encoding to {selected_encoder}"
            )
            self.update_progress(f"{progress_message} - 0%", progress=0)

            success, error_msg = encoder_manager.encode_video(
                input_file, temp_path,
                encoder_selection=selected_encoder,
                progress_callback=self.update_progress,
                cancel_check=lambda: not self.is_downloading
            )

            if success:
                self.update_progress(f"Finalizing {selected_encoder}...", progress=99)

                try:
                    # Remove original file if different from final output
                    if input_file != final_path and os.path.exists(input_file):
                        os.remove(input_file)
                        debug_print(f"Removed source file: {input_file}")

                    if os.path.exists(temp_path):
                        try:
                            if os.path.exists(final_path):
                                os.remove(final_path)
                        except Exception as remove_err:
                            debug_print(f"Pre-remove failed before replace: {remove_err}")

                        import shutil
                        shutil.move(temp_path, final_path)
                        debug_print(f"Moved encoded file to: {final_path}")

                        self.last_completed_path = final_path
                        self.complete_download(success=True, message=Messages.DOWNLOAD_COMPLETE)
                    else:
                        if self.is_downloading:
                            self.update_progress(Messages.ENCODING_ERROR, error=True)
                            self.complete_download(success=False)

                except Exception as e:
                    if self.is_downloading:
                        self.update_progress(Messages.FILE_MOVE_ERROR, error=True)
                        debug_print(f"Move error: {str(e)}")
                        self.complete_download(success=False)
            else:
                if not self.is_downloading:
                    # This was a cancellation, not an encoding failure
                    debug_print("H264 encoding was cancelled by user")
                    return
                else:
                    self.update_progress(Messages.ENCODING_FAILED, error=True)
                    debug_print(f"FFmpeg failed: {error_msg}")
                    self.complete_download(success=False)

            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

        except Exception as e:
            if not self.is_downloading:
                debug_print("Encoding exception due to cancellation")
                return
            else:
                self.update_progress("Encoding Error!", error=True)
                debug_print(f"Encoding exception: {str(e)}")
                self.complete_download(success=False)

    def cancel_download(self):
        """Cancel current download/encoding"""
        self.is_downloading = False
        video_downloader.cancel_download()
        encoder_manager.cancel_encoding()
        from utils import cleanup_temp_files
        cleanup_temp_files(self.current_temp_files)

        self.update_progress(Messages.DOWNLOAD_CANCELLED, error=True)
        self.complete_download(success=False)

    def complete_download(self, success=True, message=None):
        """Complete download process and reset UI.

        Protected by a lock+flag to prevent double execution when
        cancel_download() and download_task both call this near-simultaneously.
        """
        # Ensure this runs only once per download session
        with self._download_complete_lock:
            if self._complete_download_called:
                debug_print("complete_download() skipped — already called this session")
                return
            self._complete_download_called = True

        self.is_downloading = False

        if message:
            self.update_progress(message, progress=100 if success else None, error=not success)

        self.show_cancel_button(False)
        self.set_button_states(analyze_enabled=True, download_enabled=True)

        if success:
            self.show_open_folder_button(True)
        else:
            self.show_open_folder_button(False)

        self.cleanup_finished_processes()

    def open_download_folder(self):
        """Open folder containing the last completed download"""
        try:
            if not self.last_completed_path:
                self.update_progress("No completed download to open.", error=True)
                return

            target_path = self.last_completed_path
            folder = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)

            if not folder or not os.path.exists(folder):
                self.update_progress("Folder not found.", error=True)
                return

            # Prefer selecting the completed file in Explorer
            if os.path.isfile(target_path):
                try:
                    import subprocess
                    subprocess.run(
                        ["explorer", "/select,", os.path.abspath(target_path)],
                        check=False
                    )
                    debug_print(f"Opened folder with selection: {target_path}")
                except Exception as e:
                    self.update_progress("Failed to open folder.", error=True)
                    debug_print(f"Open folder error: {str(e)}")
            else:
                try:
                    os.startfile(folder)
                    debug_print(f"Opened folder: {folder}")
                except Exception as e:
                    self.update_progress("Failed to open folder.", error=True)
                    debug_print(f"Open folder error: {str(e)}")
        finally:
            # Keep button visible; no state change here
            pass

    def show_custom_message(self, parent, title, message, msg_type="info", on_yes=None):
        """Show a custom themed message box."""
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.configure(bg=HEADER_BG_COLOR)
        dialog.resizable(False, False)
        
        dialog.transient(parent)
        dialog.grab_set()
        self.apply_dark_title_bar(dialog)
        
        main_frame = tk.Frame(dialog, bg=HEADER_BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        top_frame = tk.Frame(main_frame, bg=HEADER_BG_COLOR)
        top_frame.pack(fill=tk.X, pady=(0, 25))

        text_frame = tk.Frame(top_frame, bg=HEADER_BG_COLOR)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(text_frame, text=title, font=("Poppins", 11, "bold"), bg=HEADER_BG_COLOR, fg=TEXT_COLOR, anchor="w").pack(fill=tk.X, pady=(0, 5))
        tk.Label(text_frame, text=message, font=Fonts.DEFAULT, bg=HEADER_BG_COLOR, fg=TEXT_COLOR, anchor="w", justify=tk.LEFT).pack(fill=tk.X)
        
        btn_frame = tk.Frame(main_frame, bg=HEADER_BG_COLOR)
        btn_frame.pack(anchor="e")
        
        def close_dialog(call_yes=False):
            dialog.destroy()
            if call_yes and on_yes:
                on_yes()

        if msg_type == "ask":
            btn_yes = tk.Button(btn_frame, text="Yes", bg=BUTTON_COLOR, fg=TEXT_COLOR, 
                               activebackground=BUTTON_ACTIVE_COLOR, activeforeground=TEXT_COLOR,
                               font=Fonts.DEFAULT, relief=tk.FLAT, borderwidth=0, cursor="hand2",
                               command=lambda: close_dialog(True))
            btn_yes.pack(side=tk.LEFT, padx=10, ipadx=15, ipady=3)
            
            btn_no = tk.Button(btn_frame, text="No", bg=BUTTON_DISABLED_COLOR, fg=TEXT_COLOR, 
                              activebackground=BUTTON_COLOR, activeforeground=TEXT_COLOR,
                              font=Fonts.DEFAULT, relief=tk.FLAT, borderwidth=0, cursor="hand2",
                              command=lambda: close_dialog(False))
            btn_no.pack(side=tk.LEFT, padx=10, ipadx=15, ipady=3)
        else:
            btn_ok = tk.Button(btn_frame, text="OK", bg=BUTTON_COLOR, fg=TEXT_COLOR, 
                              activebackground=BUTTON_ACTIVE_COLOR, activeforeground=TEXT_COLOR,
                              font=Fonts.DEFAULT, relief=tk.FLAT, borderwidth=0, cursor="hand2",
                              command=lambda: close_dialog(False))
            btn_ok.pack(ipadx=20, ipady=3)
            
        dialog.update_idletasks()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
        except:
            pass

    def cleanup_finished_processes(self):
        """Remove finished processes and dead threads from tracking lists"""
        self.active_threads[:] = [t for t in self.active_threads if t.is_alive()]
        video_downloader.cleanup_processes()
        encoder_manager.cleanup_processes()

    def run(self):
        """Start the GUI main loop"""
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            self.cleanup_and_exit()

    def cleanup_and_exit(self):
        """Clean up resources and exit"""
        self.is_downloading = False

        video_downloader.cancel_download()
        encoder_manager.cancel_encoding()

        self.comprehensive_cleanup()

        self.cleanup_finished_processes()

        if self.window:
            self.window.destroy()

# Create global GUI instance
gui = VidMuncherGUI()
