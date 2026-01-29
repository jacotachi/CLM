@echo off
echo Lancement de CLM Reader...
python run_app.py
if errorlevel 1 (
    echo.
    echo ============================================================
    echo   ERREUR: Les dependances ne sont pas installees.
    echo   Executez d'abord INSTALL.bat
    echo ============================================================
    pause
)
