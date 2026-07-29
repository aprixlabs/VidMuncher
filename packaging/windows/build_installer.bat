@echo off
:: Windows Installer Build Script for VidMuncher
:: Uses Inno Setup to create the setup executable

cd /d "%~dp0"

echo VidMuncher Installer Build Script
echo ==================================================
echo Working directory: %CD%

:: Check if the executable exists
if exist "..\..\dist\windows\VidMuncher\VidMuncher.exe" goto CheckISCC
echo Warning: dist\windows\VidMuncher\VidMuncher.exe not found!
echo Automatically running build_windows.bat...
call build_windows.bat
if %errorlevel% neq 0 (
    echo Error: Auto-build failed.
    exit /b 1
)
:: Restore working directory
cd /d "%~dp0"
if not exist "..\..\dist\windows\VidMuncher\VidMuncher.exe" (
    echo Error: Executable still not found after auto-build.
    exit /b 1
)

:CheckISCC
:: Find Inno Setup Compiler
set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if exist "%ISCC%" goto BuildInstaller
echo Error: Inno Setup 6 compiler (ISCC.exe) not found.
echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
exit /b 1

:BuildInstaller
echo Found Inno Setup Compiler: %ISCC%
echo Building Installer...

"%ISCC%" "resources\setup.iss"

if %errorlevel% equ 0 goto Success
echo Installer build failed with error code: %errorlevel%
exit /b 1

:Success
echo.
echo Installer build successful!
echo Output directory: ..\..\dist\windows
echo.
exit /b 0