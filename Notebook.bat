@echo off
rem In den Ordner wechseln, in dem diese Datei liegt (auch bei Doppelklick)
cd /d "%~dp0"

echo [1/2] git pull ...
git pull
if errorlevel 1 (
    echo.
    echo FEHLER: git pull ist fehlgeschlagen. Jupyter wird nicht gestartet.
    pause
    exit /b 1
)

echo.
echo [2/2] Starte Jupyter Notebook ...
".venv\Scripts\python.exe" -m notebook