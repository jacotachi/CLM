@echo off
echo ============================================================
echo   CLM Reader - Installation des dependances
echo ============================================================
echo.

echo Installation de pydantic...
pip install pydantic

echo Installation de pdfplumber...
pip install pdfplumber

echo Installation de PyPDF2...
pip install PyPDF2

echo Installation de python-docx...
pip install python-docx

echo Installation de python-dateutil...
pip install python-dateutil

echo Installation de click...
pip install click

echo Installation de rich...
pip install rich

echo.
echo ============================================================
echo   Installation terminee!
echo ============================================================
echo.
echo Pour lancer l'application:
echo   python run_app.py
echo.
echo Pour creer un executable:
echo   python build_windows.py
echo.
pause
