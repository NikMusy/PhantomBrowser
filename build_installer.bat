@echo off
chcp 65001 >nul
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
echo === Building Phantom Browser installer ===
"%ISCC%" installer.iss
echo.
echo ============================================================
echo  ГОТОВО:  installer_out\PhantomBrowserSetup.exe
echo ============================================================
pause
