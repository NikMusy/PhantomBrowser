@echo off
chcp 65001 >nul
echo === Building Phantom Browser .exe (PyInstaller) ===

REM Иконка + баннеры мастера (если нужно — пересоздать: python make_icon.py)
if not exist app.ico python make_icon.py
if not exist wizard_large.bmp python make_icon.py

python -m pip install --upgrade pyinstaller >nul 2>&1
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist PhantomBrowser.spec del /q PhantomBrowser.spec

python -m PyInstaller --noconfirm --windowed --name PhantomBrowser --icon app.ico --collect-all PyQt6 main.py

echo.
echo ============================================================
echo  ГОТОВО:  dist\PhantomBrowser\PhantomBrowser.exe
echo ============================================================
pause
