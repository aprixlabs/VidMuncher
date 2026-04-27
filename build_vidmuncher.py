
import os
import subprocess
import sys
import shutil
from pathlib import Path

def build_vidmuncher():

    print("VidMuncher Build Script")
    print("=" * 50)

    main_file = "vidmuncher.py"
    exe_name = "VidMuncher"

    if not os.path.exists(main_file):
        print(f"Error: {main_file} not found")
        return False

    if not os.path.exists("assets"):
        print("Error: assets folder not found")
        return False

    print(f"Working directory: {os.getcwd()}")
    print(f"Building {exe_name}.exe...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", exe_name,
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
        "--clean",
        "--noconfirm",
    ]

    if os.path.exists("version_info.py"):
        cmd.extend(["--version-file", "version_info.py"])
        print("Adding version metadata to executable")

    icon_files = ["assets/icon.ico", "assets/icon.png"]
    for icon_file in icon_files:
        if os.path.exists(icon_file):
            if icon_file.endswith('.ico'):
                cmd.extend(["--icon", icon_file])
                print(f"Using icon: {icon_file}")
            break

    # Bundle assets into executable
    print("Bundling assets into executable...")
    assets_to_bundle = [
        ("assets/icon.ico",                  "assets"),
        ("assets/icon.png",                  "assets"),
        ("assets/kofi-logo.png",             "assets"),
        ("assets/sociabuzz-logo.png",        "assets"),
        ("assets/fonts/Poppins-Regular.ttf", "assets/fonts"),
        ("assets/fonts/Poppins-Medium.ttf",  "assets/fonts"),
        ("assets/fonts/Poppins-Bold.ttf",    "assets/fonts"),
        ("assets/fonts/Poppins-Black.ttf",   "assets/fonts"),
    ]

    for asset_path, dest_dir in assets_to_bundle:
        if os.path.exists(asset_path):
            cmd.extend(["--add-data", f"{asset_path};{dest_dir}"])
            print(f"Bundling: {asset_path}")
        else:
            print(f"Warning: Asset not found: {asset_path}")

    # Hidden imports not auto-detected by PyInstaller
    hidden_imports = [
        "PIL._tkinter_finder",
        "PIL.Image",
        "PIL.ImageTk",
        "tkinter",
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "requests",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Exclude Python yt-dlp/ffmpeg packages — binaries are downloaded at runtime
    cmd.extend([
        "--exclude-module", "yt_dlp",
        "--exclude-module", "ffmpeg"
    ])
    
    cmd.append(main_file)

    print("Running PyInstaller...")
    print()

    try:
        subprocess.run(cmd, check=True)

        exe_path = f"dist/{exe_name}.exe"
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)

            print()
            print("Build successful!")
            print(f"Executable: {exe_path}")
            print(f"Size: {file_size:.1f} MB")

            copy_licenses()

            print()
            print("Build complete")
            
            return True
        else:
            print("Build failed - executable not found")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code: {e.returncode}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def copy_licenses():
    """Copy license files to dist/. Component licenses (FFmpeg, yt-dlp) go into dist/bin/."""
    print("Copying license files...")

    dist_bin = Path("dist/bin")
    dist_bin.mkdir(exist_ok=True)
    print("Created: dist/bin/")

    for f in ["LICENSE", "LICENSE.txt"]:
        if os.path.exists(f):
            shutil.copy2(f, Path("dist") / f)
            print(f"Copied: {f} → dist/")

    for f in ["FFMPEG_LICENSE.txt", "YT-DLP_LICENSE.txt"]:
        src_path = Path("bin") / f
        if src_path.exists():
            shutil.copy2(src_path, dist_bin / f)
            print(f"Copied: {src_path} → dist/bin/")

def clean_build():
    """Clean build artifacts"""
    print("Cleaning build artifacts...")

    dirs_to_clean = ["build", "dist", "__pycache__"]

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed: {dir_name}/")

    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"Removed: {spec_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_build()
    else:
        success = build_vidmuncher()

        if success:
            print("\nBuild completed successfully")
        else:
            print("\nBuild failed - check error messages above")
