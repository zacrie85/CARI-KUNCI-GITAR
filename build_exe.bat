@echo off
chcp 65001 >nul
echo ================================================
echo   Membangun ChordKu.exe (butuh internet)
echo ================================================
python -m pip install --upgrade pyinstaller
if not exist ffmpeg.exe (
  echo Mengunduh ffmpeg untuk di-bundle ke dalam exe...
  curl.exe -L -o ffmpeg.zip https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip
  powershell -NoProfile -Command "Expand-Archive ffmpeg.zip -DestinationPath ffbin -Force; Copy-Item ^ffbinfmpeg-master-latest-win64-gplinfmpeg.exe^ -Destination ffmpeg.exe -Force"
  del ffmpeg.zip 2>nul
  rd /s /q ffbin 2>nul
)
set PYIARGS=--noconfirm --onefile --windowed --name ChordKu --icon icon.ico
if exist ffmpeg.exe set PYIARGS=%PYIARGS% --add-binary "ffmpeg.exe;."
rem browser tersemat (pywebview/WebView2) + pythonnet harus ikut terkumpul
set PYIARGS=%PYIARGS% --collect-all webview --collect-all clr_loader --collect-all pythonnet --hidden-import bottle
python -m PyInstaller %PYIARGS% chordku.py
echo.
echo Selesai! Jalankan: dist\ChordKu.exe  (ffmpeg sudah di dalam exe)
pause
