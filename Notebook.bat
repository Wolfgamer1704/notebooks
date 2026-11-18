@echo off
setlocal EnableDelayedExpansion
rem In den Ordner wechseln, in dem diese Datei liegt (auch bei Doppelklick)
cd /d "%~dp0"

echo [1/4] git pull ...
git pull
if errorlevel 1 (
    echo.
    echo FEHLER: git pull ist fehlgeschlagen. Jupyter wird nicht gestartet.
    pause
    exit /b 1
)

echo.
echo [2/4] Starte Jupyter Notebook ...
echo       Beenden im Browser ueber "Datei - Herunterfahren" (File - Shut Down).
".venv\Scripts\python.exe" -m notebook

echo.
echo [3/4] Pruefe auf Aenderungen ...
git add -A
git diff --cached --quiet
if not errorlevel 1 (
    echo Keine Aenderungen - nichts zu synchronisieren.
    pause
    exit /b 0
)

echo Folgende Aenderungen werden committet:
git status --short
echo.

set "msg="
set /p "msg=Commit-Text (leer lassen = abbrechen): "
if not defined msg (
    echo.
    echo Abgebrochen. Die Aenderungen sind vorgemerkt, aber nicht committet.
    pause
    exit /b 0
)

git commit -m "!msg!"
if errorlevel 1 (
    echo.
    echo FEHLER: git commit ist fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo [4/4] git push ...
git push
if errorlevel 1 (
    echo.
    echo FEHLER: git push ist fehlgeschlagen. Der Commit liegt nur lokal vor.
    pause
    exit /b 1
)

echo.
echo Fertig - Aenderungen sind auf GitHub.
pause
