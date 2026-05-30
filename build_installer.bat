@echo off
chcp 65001 >nul
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
echo === Building Phantom Browser installer ===

REM Иконка + баннеры мастера (app.ico, wizard_large.bmp, wizard_small.bmp)
if not exist wizard_large.bmp python make_icon.py

"%ISCC%" installer.iss
echo.
echo ============================================================
echo  ГОТОВО:  installer_out\PhantomBrowserSetup.exe
echo ============================================================
pause
