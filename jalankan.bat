@echo off
cd /d "%~dp0"
python chordku.py
if errorlevel 1 (
  echo.
  echo Ada kesalahan. Pastikan setup.bat sudah dijalankan.
  pause
)
