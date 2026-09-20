@echo off
REM Builds the nawat-cli .deb package via WSL (dpkg-buildpackage is Linux-only).
setlocal

where wsl >nul 2>nul
if errorlevel 1 (
    echo WSL is required to build the .deb package. Install it with: wsl --install
    exit /b 1
)

set "WIN_DIR=%~dp0"

echo Building nawat-cli .deb package inside WSL...
wsl bash -lc "cd '$(wslpath '%WIN_DIR%')' && chmod +x build_deb.sh && ./build_deb.sh"
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo Done. Check the cli\..\ folder for the generated .deb file.
endlocal
