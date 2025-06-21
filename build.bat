@echo off
echo ================================
echo  Menarik update dari GitHub...
echo ================================
git pull
if %errorlevel% neq 0 (
    echo Gagal menarik update dari GitHub.
    pause
    exit /b
)

echo.
echo ================================
echo  Membuat file .exe dengan PyInstaller...
echo ================================

:: Hapus folder build dan dist sebelumnya jika ada
rmdir /s /q build
rmdir /s /q dist
del /q airdrop_manager.spec

:: Bangun ulang
pyinstaller --noconfirm --onefile --windowed airdrop_manager.py

echo.
echo ================================
echo  Selesai! File .exe berada di folder dist\
echo ================================
pause
