@echo off
rem Build Grandmist.exe into the dist folder
cd /d "%~dp0"
python -m pip install --disable-pip-version-check -q pywebview pyinstaller
if errorlevel 1 goto fail
rem The private core is bundled only as a compiled module (built by grandmist-core\build_core.bat)
set CORE_ARGS=--exclude-module grandmist_core
if exist "..\grandmist-core\build\core\grandmist_core*.pyd" set CORE_ARGS=--paths "..\grandmist-core\build\core" --hidden-import grandmist_core
echo Core: %CORE_ARGS%
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Grandmist --icon assets/grandmist.ico --add-data "app;app" %CORE_ARGS% main.py
if errorlevel 1 goto fail
echo.
echo Build OK: dist\Grandmist.exe
pause
exit /b 0
:fail
echo.
echo Build FAILED. Please send the error messages above to Claude.
pause
exit /b 1
