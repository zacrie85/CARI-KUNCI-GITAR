@echo off
chcp 65001 >nul
echo Memasang dependensi CARI KUNCI GITAR...
python -m pip install --upgrade -r requirements.txt
echo.
echo Selesai! Jalankan aplikasi dengan: jalankan.bat
pause
