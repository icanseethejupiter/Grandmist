@echo off
rem Build Grandmist.exe into the dist folder
cd /d "%~dp0"
python -m pip install --disable-pip-version-check -q pywebview pyinstaller
if errorlevel 1 goto fail
rem The private core is bundled only as a compiled module (built by grandmist-core\build_core.bat)
set CORE_ARGS=--exclude-module grandmist_core
if exist "..\grandmist-core\build\core\grandmist_core*.pyd" set CORE_ARGS=--paths "..\grandmist-core\build\core" --hidden-import grandmist_core
rem Extra modules the compiled core needs at run time, listed by the core build
set CORE_EXTRA=
if exist "..\grandmist-core\build\core\pyinstaller_args.txt" set /p CORE_EXTRA=<"..\grandmist-core\build\core\pyinstaller_args.txt"
echo Core: %CORE_ARGS% %CORE_EXTRA%
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Grandmist --icon assets/grandmist.ico --add-data "app;app" %CORE_ARGS% %CORE_EXTRA% main.py
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
