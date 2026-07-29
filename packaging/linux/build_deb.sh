#!/bin/bash
# Debian Build Script for VidMuncher

set -e

# Change to project root
cd "$(dirname "$0")/../.."

APP_NAME="vidmuncher"
APP_NAME_FORMAL="VidMuncher"
VERSION="1.1.0"
ARCH="amd64"
DEB_DIR_NAME="${APP_NAME}_${VERSION}_${ARCH}"
BUILD_TMP="/tmp/vidmuncher_deb_build"

if [ "$1" == "--clean" ]; then
    echo "Cleaning build artifacts..."
    rm -rf build dist VidMuncher.spec "$BUILD_TMP"
    echo "Clean complete."
    exit 0
fi

echo "VidMuncher Debian Packager"
echo "=================================================="

# Check requirements
if ! command -v pyinstaller &> /dev/null; then
    echo "Error: PyInstaller is not installed."
    exit 1
fi
if ! command -v dpkg-deb &> /dev/null; then
    echo "Error: dpkg-deb is not installed."
    exit 1
fi

echo "Cleaning old build artifacts..."
rm -rf build VidMuncher.spec "$BUILD_TMP"
mkdir -p dist/linux

echo "Building PyInstaller binary..."
pyinstaller --onefile --windowed \
  --name "$APP_NAME_FORMAL" \
  --distpath "dist/linux" \
  --workpath "build" \
  --specpath "." \
  --clean --noconfirm \
  --add-data "src/app/assets/icons/icon.png:assets/icons" \
  --add-data "src/app/assets/logos/kofi-logo.png:assets/logos" \
  --add-data "src/app/assets/logos/sociabuzz-logo.png:assets/logos" \
  --add-data "src/app/assets/ui/dropdown-arrow.svg:assets/ui" \
  --add-data "src/app/assets/ui/up-arrow.svg:assets/ui" \
  --add-data "src/app/assets/icons/about-icon.svg:assets/icons" \
  --add-data "src/app/assets/icons/history-icon.svg:assets/icons" \
  --add-data "src/app/assets/icons/settings-icon.svg:assets/icons" \
  --add-data "src/app/assets/ui/checkmark.svg:assets/ui" \
  --add-data "src/app/assets/fonts/Poppins-Regular.ttf:assets/fonts" \
  --add-data "src/app/assets/fonts/Poppins-Medium.ttf:assets/fonts" \
  --add-data "src/app/assets/fonts/Poppins-Bold.ttf:assets/fonts" \
  --add-data "src/app/assets/fonts/Poppins-Black.ttf:assets/fonts" \
  --add-data "src/app/languages/en.json:app/languages" \
  --add-data "src/app/languages/id.json:app/languages" \
  --add-data "src/app/languages/zh.json:app/languages" \
  --add-data "src/app/languages/ru.json:app/languages" \
  --add-data "src/app/languages/ar.json:app/languages" \
  --add-data "src/app/languages/de.json:app/languages" \
  --add-data "src/app/languages/es.json:app/languages" \
  --add-data "src/app/languages/fr.json:app/languages" \
  --add-data "src/app/languages/hi.json:app/languages" \
  --add-data "src/app/languages/it.json:app/languages" \
  --add-data "src/app/languages/ja.json:app/languages" \
  --add-data "src/app/languages/pl.json:app/languages" \
  --add-data "src/app/languages/pt.json:app/languages" \
  --add-data "src/app/languages/tr.json:app/languages" \
  --hidden-import "PySide6" \
  --hidden-import "requests" \
  --exclude-module "yt_dlp" \
  --exclude-module "ffmpeg" \
  src/vidmuncher.py

EXE_PATH="dist/linux/$APP_NAME_FORMAL"
if [ ! -f "$EXE_PATH" ]; then
    echo "Build failed - executable not found"
    exit 1
fi

echo "Building Debian Package Structure in /tmp..."
DEB_DIR="$BUILD_TMP/$DEB_DIR_NAME"

mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$DEB_DIR/usr/share/doc/$APP_NAME"

chmod -R 755 "$DEB_DIR"

# Copy Binary
cp "$EXE_PATH" "$DEB_DIR/usr/bin/$APP_NAME"
chmod 755 "$DEB_DIR/usr/bin/$APP_NAME"

# Post-removal script to clean up user data
cat > "$DEB_DIR/DEBIAN/postrm" << EOF
#!/bin/sh
set -e

if [ "\$1" = "purge" ] || [ "\$1" = "remove" ]; then
    echo "Note: User configuration and downloaded binaries in ~/.local/share/VidMuncher are kept."
    echo "To remove them, users must manually delete ~/.local/share/VidMuncher"
fi

exit 0
EOF
chmod 755 "$DEB_DIR/DEBIAN/postrm"

# Control file
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $APP_NAME
Version: $VERSION
Architecture: $ARCH
Maintainer: VidMuncher Team <support@vidmuncher.app>
Description: Ultimate Video Downloader & Converter
 VidMuncher is a powerful, cross-platform video downloading and encoding
 tool powered by yt-dlp and FFmpeg.
Section: video
Priority: optional
Depends: libc6, libgl1, libegl1, libfontconfig1, libxkbcommon-x11-0, libxcb-cursor0
EOF
chmod 644 "$DEB_DIR/DEBIAN/control"

# Desktop Entry
cat > "$DEB_DIR/usr/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Name=$APP_NAME_FORMAL
Comment=Ultimate Video Downloader & Converter
Exec=/usr/bin/$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=AudioVideo;Video;
EOF

# Icon
if [ -f "src/app/assets/icons/icon.png" ]; then
    cp "src/app/assets/icons/icon.png" "$DEB_DIR/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png"
fi

# License
if [ -f "LICENSE" ]; then
    cp "LICENSE" "$DEB_DIR/usr/share/doc/$APP_NAME/copyright"
fi

echo "Compiling Debian Package..."
dpkg-deb --root-owner-group --build "$DEB_DIR"

if [ -f "$BUILD_TMP/$DEB_DIR_NAME.deb" ]; then
    cp "$BUILD_TMP/$DEB_DIR_NAME.deb" "dist/linux/"
    rm -rf "$BUILD_TMP"
    rm -f "$EXE_PATH" # Clean raw executable
    echo "Debian Package: dist/linux/\$(basename "\$BUILD_TMP/\$DEB_DIR_NAME.deb")"
    echo "Build successful!"
else
    echo "Failed to create Debian package."
    exit 1
fi
