@echo off
echo ============================================================
echo   CLM Reader - Creation de l'executable Windows
echo ============================================================
echo.
echo Ce script va:
echo   1. Installer toutes les dependances necessaires
echo   2. Creer un fichier CLMReader.exe autonome
echo.
echo L'executable pourra etre copie sur n'importe quel PC Windows
echo sans avoir besoin d'installer Python.
echo.
echo Cela peut prendre plusieurs minutes...
echo.
pause

python build_windows.py

echo.
pause
