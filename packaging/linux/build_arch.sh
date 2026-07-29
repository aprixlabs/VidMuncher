#!/bin/bash
# Arch Linux Build Script for VidMuncher

set -e

# Change to project root
cd "$(dirname "$0")/../.."

APP_NAME="vidmuncher"
APP_NAME_FORMAL="VidMuncher"
VERSION="1.1.0"
PKGREL="1"
BUILD_TMP="/tmp/vidmuncher_arch_build"

if [ "$1" == "--clean" ]; then
    echo "Cleaning build artifacts..."
    rm -rf build dist VidMuncher.spec "$BUILD_TMP"
    echo "Clean complete."
    exit 0
fi

echo "VidMuncher Arch/Manjaro Packager"
echo "=================================================="

# Check requirements
if ! command -v pyinstaller &> /dev/null; then
    echo "Error: PyInstaller is not installed."
    exit 1
fi
if ! command -v makepkg &> /dev/null; then
    echo "Error: makepkg is not installed."
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

echo "Building Arch Package Structure in /tmp..."
mkdir -p "$BUILD_TMP"

# Copy files to build directory
cp "$EXE_PATH" "$BUILD_TMP/$APP_NAME"

# Desktop Entry
cat > "$BUILD_TMP/$APP_NAME.desktop" << EOF
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
    cp "src/app/assets/icons/icon.png" "$BUILD_TMP/$APP_NAME.png"
fi

# License
if [ -f "LICENSE" ]; then
    cp "LICENSE" "$BUILD_TMP/LICENSE"
fi

# Generate PKGBUILD file
cat > "$BUILD_TMP/PKGBUILD" << EOF
# Maintainer: VidMuncher Team <support@vidmuncher.app>
pkgname=$APP_NAME
pkgver=$VERSION
pkgrel=$PKGREL
pkgdesc="Ultimate Video Downloader & Converter"
arch=('x86_64')
url="https://github.com/aprixlabs/VidMuncher"
license=('GPL3')
depends=('glibc' 'libxkbcommon' 'libxcb' 'libglvnd' 'fontconfig')
options=('!strip')

package() {
    install -Dm755 "\$srcdir/../\$pkgname" "\$pkgdir/usr/bin/\$pkgname"
    install -Dm644 "\$srcdir/../\$pkgname.desktop" "\$pkgdir/usr/share/applications/\$pkgname.desktop"
    if [ -f "\$srcdir/../\$pkgname.png" ]; then
        install -Dm644 "\$srcdir/../\$pkgname.png" "\$pkgdir/usr/share/icons/hicolor/512x512/apps/\$pkgname.png"
    fi
    if [ -f "\$srcdir/../LICENSE" ]; then
        install -Dm644 "\$srcdir/../LICENSE" "\$pkgdir/usr/share/licenses/\$pkgname/LICENSE"
    fi
}
EOF

echo "Compiling Arch Package..."
cd "$BUILD_TMP"
# Run makepkg. Allow running as root if in container by checking environment
if [ "$(id -u)" -eq 0 ]; then
    # makepkg blocking root by default, using --allow-root or env CARCH if needed
    # Arch makepkg has different flag variants, -C -S -r etc. Standard is -d to ignore deps, -p PKGBUILD.
    # Note: --nobuild was telling makepkg NOT to build the package package, only prepare sources. Removed --nobuild.
    makepkg -d --asdeps --ignorearch || makepkg -d --asdeps
else
    makepkg -d
fi

PKG_FILE=$(find . -name "*.pkg.tar.zst" | head -n 1)

if [ -n "$PKG_FILE" ] && [ -f "$PKG_FILE" ]; then
    cp "$PKG_FILE" "$OLDPWD/dist/linux/"
    rm -rf "$BUILD_TMP"
    rm -f "$OLDPWD/$EXE_PATH"
    echo "Arch Package: dist/linux/\$(basename "\$PKG_FILE")"
    echo "Build successful!"
else
    echo "Failed to create Arch package."
    exit 1
fi
