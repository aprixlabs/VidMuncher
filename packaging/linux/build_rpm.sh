#!/bin/bash
# RPM Build Script for VidMuncher

set -e

# Change to project root
cd "$(dirname "$0")/../.."

APP_NAME="vidmuncher"
APP_NAME_FORMAL="VidMuncher"
VERSION="1.1.0"
RELEASE="1"
ARCH="x86_64"
RPM_DIR_NAME="${APP_NAME}-${VERSION}-${RELEASE}.${ARCH}"
BUILD_TMP="/tmp/vidmuncher_rpm_build"

if [ "$1" == "--clean" ]; then
    echo "Cleaning build artifacts..."
    rm -rf build dist VidMuncher.spec "$BUILD_TMP"
    echo "Clean complete."
    exit 0
fi

echo "VidMuncher RPM Packager"
echo "=================================================="

# Check requirements
if ! command -v pyinstaller &> /dev/null; then
    echo "Error: PyInstaller is not installed."
    exit 1
fi
if ! command -v rpmbuild &> /dev/null; then
    echo "Error: rpmbuild is not installed."
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

echo "Building RPM Package Structure in /tmp..."
mkdir -p "$BUILD_TMP"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copy binary to build directory
mkdir -p "$BUILD_TMP/BUILD/usr/bin"
cp "$EXE_PATH" "$BUILD_TMP/BUILD/usr/bin/$APP_NAME"

# Copy Desktop Entry and Icons
mkdir -p "$BUILD_TMP/BUILD/usr/share/applications"
cat > "$BUILD_TMP/BUILD/usr/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Name=$APP_NAME_FORMAL
Comment=Ultimate Video Downloader & Converter
Exec=/usr/bin/$APP_NAME
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=AudioVideo;Video;
EOF

mkdir -p "$BUILD_TMP/BUILD/usr/share/icons/hicolor/512x512/apps"
if [ -f "src/app/assets/icons/icon.png" ]; then
    cp "src/app/assets/icons/icon.png" "$BUILD_TMP/BUILD/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png"
fi

mkdir -p "$BUILD_TMP/BUILD/usr/share/doc/$APP_NAME"
if [ -f "LICENSE" ]; then
    cp "LICENSE" "$BUILD_TMP/BUILD/usr/share/doc/$APP_NAME/LICENSE"
fi

# Generate SPEC file
cat > "$BUILD_TMP/SPECS/$APP_NAME.spec" << EOF
Name:           $APP_NAME
Version:        $VERSION
Release:        $RELEASE%{?dist}
Summary:        Ultimate Video Downloader & Converter
License:        MIT
URL:            https://github.com/aprixlabs/VidMuncher
BuildArch:      x86_64

Requires:       qt6-qtbase-gui, libxkbcommon-x11

%description
VidMuncher is a powerful, cross-platform video downloading and encoding
tool powered by yt-dlp and FFmpeg.

%prep
# Already prepared

%build
# Already built

%install
mkdir -p %{buildroot}/usr/bin
mkdir -p %{buildroot}/usr/share/applications
mkdir -p %{buildroot}/usr/share/icons/hicolor/512x512/apps
mkdir -p %{buildroot}/usr/share/doc/%{name}

cp -a $BUILD_TMP/BUILD/usr/bin/$APP_NAME %{buildroot}/usr/bin/
cp -a $BUILD_TMP/BUILD/usr/share/applications/$APP_NAME.desktop %{buildroot}/usr/share/applications/
cp -a $BUILD_TMP/BUILD/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png %{buildroot}/usr/share/icons/hicolor/512x512/apps/
cp -a $BUILD_TMP/BUILD/usr/share/doc/$APP_NAME/LICENSE %{buildroot}/usr/share/doc/%{name}/

%postun
if [ $1 -eq 0 ]; then
    echo "Note: User configuration and downloaded binaries in ~/.local/share/VidMuncher are kept."
    echo "To remove them, users must manually delete ~/.local/share/VidMuncher"
fi

%files
/usr/bin/$APP_NAME
/usr/share/applications/$APP_NAME.desktop
/usr/share/icons/hicolor/512x512/apps/$APP_NAME.png
/usr/share/doc/%{name}/LICENSE

%changelog
* Tue Jul 28 2026 Aprix <support@vidmuncher.app> - 1.1.0-1
- Initial RPM release.
EOF

echo "Compiling RPM Package..."
rpmbuild --define "_topdir $BUILD_TMP" -bb "$BUILD_TMP/SPECS/$APP_NAME.spec"

RPM_FILE=$(find "$BUILD_TMP/RPMS" -name "*.rpm" | head -n 1)

if [ -n "$RPM_FILE" ] && [ -f "$RPM_FILE" ]; then
    cp "$RPM_FILE" dist/linux/
    rm -rf "$BUILD_TMP"
    rm -f "$EXE_PATH" # Clean raw executable
    echo "RPM Package: dist/linux/\$(basename "\$RPM_FILE")"
    echo "Build successful!"
else
    echo "Failed to create RPM package."
    exit 1
fi
