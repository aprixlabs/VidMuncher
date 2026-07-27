import os
import subprocess
import sys
import shutil
from pathlib import Path

# Ensure working directory is always the project root, regardless of where
# this script is invoked from (e.g., python scripts/build-linux-deb.py).
_PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(_PROJECT_ROOT)

def build_vidmuncher_deb():
    print("VidMuncher Debian Packager")
    print("=" * 50)

    main_file = "vidmuncher.py"
    app_name = "vidmuncher"
    app_name_formal = "VidMuncher"
    version = "1.1.0"
    arch = "amd64"
    deb_dir_name = f"{app_name}_{version}_{arch}"
    deb_dir = Path("dist") / deb_dir_name

    if not os.path.exists(main_file):
        print(f"Error: {main_file} not found")
        return False

    print(f"Building PyInstaller binary for Linux...")
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", app_name_formal,
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", ".",
        "--clean",
        "--noconfirm",
    ]

    assets_to_bundle = [
        ("assets/icon.png",                  "assets"),
        ("assets/kofi-logo.png",             "assets"),
        ("assets/sociabuzz-logo.png",        "assets"),
        ("assets/dropdown-arrow.svg",        "assets"),
        ("assets/up-arrow.svg",              "assets"),
        ("assets/about-icon.svg",            "assets"),
        ("assets/history-icon.svg",          "assets"),
        ("assets/checkmark.svg",             "assets"),
        ("assets/fonts/Poppins-Regular.ttf", "assets/fonts"),
        ("assets/fonts/Poppins-Medium.ttf",  "assets/fonts"),
        ("assets/fonts/Poppins-Bold.ttf",    "assets/fonts"),
        ("assets/fonts/Poppins-Black.ttf",   "assets/fonts"),
    ]

    for asset_path, dest_dir in assets_to_bundle:
        if os.path.exists(asset_path):
            # PyInstaller on Linux uses ':' instead of ';' for --add-data
            cmd.extend(["--add-data", f"{asset_path}:{dest_dir}"])
        else:
            print(f"Warning: Asset not found: {asset_path}")

    hidden_imports = [
        "PySide6",
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

    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"PyInstaller build failed: {e}")
        return False

    exe_path = Path("dist") / app_name_formal
    if not exe_path.exists():
        print("Build failed - executable not found")
        return False

    print(f"\nBuilding Debian Package Structure in /tmp...")
    # Build in /tmp to avoid NTFS permission issues on mounted drives
    tmp_build_dir = Path("/tmp/vidmuncher_deb_build")
    if tmp_build_dir.exists():
        shutil.rmtree(tmp_build_dir)
        
    deb_dir = tmp_build_dir / deb_dir_name

    # Create Debian structure
    dirs = [
        deb_dir / "DEBIAN",
        deb_dir / "usr" / "bin",
        deb_dir / "usr" / "share" / "applications",
        deb_dir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps",
        deb_dir / "usr" / "share" / "doc" / app_name
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        os.chmod(d, 0o755)

    # 1. Copy Binary
    shutil.copy2(exe_path, deb_dir / "usr" / "bin" / app_name)
    os.chmod(deb_dir / "usr" / "bin" / app_name, 0o755)

    # 2. Control file
    control_content = f"""Package: {app_name}
Version: {version}
Architecture: {arch}
Maintainer: VidMuncher Team <support@vidmuncher.app>
Description: Ultimate Video Downloader & Converter
 VidMuncher is a powerful, cross-platform video downloading and encoding
 tool powered by yt-dlp and FFmpeg.
Section: video
Priority: optional
Depends: libc6, libgl1, libegl1, libfontconfig1, libxkbcommon-x11-0, libxcb-cursor0
"""
    control_file = deb_dir / "DEBIAN" / "control"
    with open(control_file, "w", encoding="utf-8") as f:
        f.write(control_content)
    os.chmod(control_file, 0o644)

    # 3. Desktop Entry
    desktop_content = f"""[Desktop Entry]
Name={app_name_formal}
Comment=Ultimate Video Downloader & Converter
Exec=/usr/bin/{app_name}
Icon={app_name}
Terminal=false
Type=Application
Categories=AudioVideo;Video;
"""
    with open(deb_dir / "usr" / "share" / "applications" / f"{app_name}.desktop", "w", encoding="utf-8") as f:
        f.write(desktop_content)
        
    # 4. Icon
    if Path("assets/icon.png").exists():
        shutil.copy2("assets/icon.png", deb_dir / "usr" / "share" / "icons" / "hicolor" / "512x512" / "apps" / f"{app_name}.png")

    # 5. Licenses
    if Path("LICENSE").exists():
        shutil.copy2("LICENSE", deb_dir / "usr" / "share" / "doc" / app_name / "copyright")

    print(f"\nCompiling Debian Package...")
    try:
        subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(deb_dir)], check=True)
        compiled_deb = tmp_build_dir / f"{deb_dir_name}.deb"
        final_deb = Path("dist") / f"{deb_dir_name}.deb"
        
        if compiled_deb.exists():
            shutil.copy2(compiled_deb, final_deb)
            file_size = os.path.getsize(final_deb) / (1024 * 1024)
            print(f"\nBuild successful!")
            print(f"Debian Package: {final_deb}")
            print(f"Size: {file_size:.1f} MB")
            
            # Cleanup intermediate artifacts
            shutil.rmtree(tmp_build_dir)
            if exe_path.exists():
                exe_path.unlink()
            return True
    except Exception as e:
        print(f"dpkg-deb failed: {e}")
        return False

def clean_build():
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
        success = build_vidmuncher_deb()
        if success:
            print("\nDebian Build completed successfully")
        else:
            print("\nDebian Build failed")
