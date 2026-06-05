@echo off
REM ============================================================
REM  One-click build: monitor.py  ->  TrafficMonitor.exe  ->  Setup.exe
REM  Run this ON WINDOWS (double-click it, or run in a terminal).
REM  Requires Python here. (The finished .exe needs no Python to RUN.)
REM ============================================================

echo.
echo [1/4] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install psutil pystray pillow pyinstaller

echo.
echo [2/4] Making the app icon (icon.ico) ...
python make_icon.py

echo.
echo [3/4] Building TrafficMonitor.exe ...
REM  --onefile          : a single .exe (no folder of files)
REM  --noconsole        : no black command window pops up
REM  --noupx            : skip UPX compression (fewer antivirus false-positives)
REM  --icon             : give the .exe its own icon
REM  --hidden-import     : make sure pystray's Windows tray backend is bundled
python -m PyInstaller --onefile --noconsole --noupx --name TrafficMonitor ^
  --icon icon.ico --hidden-import pystray._win32 monitor.py

echo.
echo [4/4] Building the installer (if Inno Setup is installed)...
where ISCC >nul 2>nul
if %ERRORLEVEL%==0 (
  ISCC installer.iss
  echo   Installer ready:  installer\TrafficMonitor-Setup.exe
) else (
  echo   Inno Setup not found - skipping installer.
  echo   Get it free ^(no Python needed^): https://jrsoftware.org/isdl.php
)

echo.
echo Done!
echo   Portable app : dist\TrafficMonitor.exe
echo   Installer    : installer\TrafficMonitor-Setup.exe  ^(if built^)
echo.
pause
