@echo off
:: Windows Build Script for VidMuncher
:: Uses PyInstaller to package the application

cd /d "%~dp0..\.."

echo VidMuncher Build Script
echo ==================================================
echo Working directory: %CD%

:: Check for clean argument
if "%~1"=="--clean" (
    echo Cleaning build artifacts...
    if exist build rmdir /s /q build
    if exist "dist\windows" rmdir /s /q "dist\windows"
    if exist VidMuncher.spec del /q VidMuncher.spec
    echo Clean complete.
    exit /b 0
)

:: Check requirements
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: PyInstaller is not installed or not in PATH.
    exit /b 1
)

if not exist src\vidmuncher.py (
    echo Error: src\vidmuncher.py not found.
    exit /b 1
)

if not exist src\app\assets (
    echo Error: src\app\assets folder not found.
    exit /b 1
)

:: Clean old build artifacts
echo Cleaning old build artifacts...
if exist build rmdir /s /q build
if exist "dist\windows" rmdir /s /q "dist\windows"
if exist VidMuncher.spec del /q VidMuncher.spec

echo Building VidMuncher.exe...

pyinstaller --onefile --windowed ^
  --name "VidMuncher" ^
  --distpath "dist/windows/VidMuncher" ^
  --workpath "build" ^
  --specpath "." ^
  --clean --noconfirm ^
  --version-file "packaging/windows/file_version_info.txt" ^
  --icon "src/app/assets/icons/icon.ico" ^
  --add-data "src/app/assets/icons/icon.ico;assets/icons" ^
  --add-data "src/app/assets/icons/icon.png;assets/icons" ^
  --add-data "src/app/assets/logos/kofi-logo.png;assets/logos" ^
  --add-data "src/app/assets/logos/sociabuzz-logo.png;assets/logos" ^
  --add-data "src/app/assets/ui/dropdown-arrow.svg;assets/ui" ^
  --add-data "src/app/assets/ui/up-arrow.svg;assets/ui" ^
  --add-data "src/app/assets/icons/about-icon.svg;assets/icons" ^
  --add-data "src/app/assets/icons/history-icon.svg;assets/icons" ^
  --add-data "src/app/assets/icons/settings-icon.svg;assets/icons" ^
  --add-data "src/app/assets/ui/checkmark.svg;assets/ui" ^
  --add-data "src/app/assets/fonts/Poppins-Regular.ttf;assets/fonts" ^
  --add-data "src/app/assets/fonts/Poppins-Medium.ttf;assets/fonts" ^
  --add-data "src/app/assets/fonts/Poppins-Bold.ttf;assets/fonts" ^
  --add-data "src/app/assets/fonts/Poppins-Black.ttf;assets/fonts" ^
  --add-data "src/app/languages/en.json;app/languages" ^
  --add-data "src/app/languages/id.json;app/languages" ^
  --hidden-import "PySide6" ^
  --hidden-import "requests" ^
  --exclude-module "yt_dlp" ^
  --exclude-module "ffmpeg" ^
  src/vidmuncher.py

if %errorlevel% neq 0 (
    echo Build failed with error code: %errorlevel%
    exit /b 1
)

if not exist "dist\windows\VidMuncher\VidMuncher.exe" (
    echo Build failed - executable not found.
    exit /b 1
)

echo Copying license files...
copy /y LICENSE dist\windows\VidMuncher\
copy /y LICENSE.txt dist\windows\VidMuncher\ 2>nul

echo Creating portable zip...
for /f "delims=" %%a in ('python -c "import sys; sys.path.insert(0, 'src'); from app.config.app_info import APP_VERSION; print(APP_VERSION)"') do set APP_VERSION=%%a
powershell -Command "Compress-Archive -Path 'dist\windows\VidMuncher\*' -DestinationPath 'dist\windows\VidMuncher-%APP_VERSION%-Windows-x64-Portable.zip' -Force"

echo.
echo Build successful!
echo Executable: dist\windows\VidMuncher\VidMuncher.exe
echo Portable Zip: dist\windows\VidMuncher-%APP_VERSION%-Windows-x64-Portable.zip
echo.
