@echo off
chcp 65001 >nul
echo ================================================
echo   Membangun ChordKu.exe (butuh internet)
echo ================================================
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name ChordKu --icon icon.ico chordku.py
echo.
echo Selesai! Jalankan: dist\ChordKu.exe
echo Opsional: salin ffmpeg.exe ke sebelah ChordKu.exe
pause
