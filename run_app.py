#!/usr/bin/env python3
"""
Point d'entree principal pour l'application CLM Reader.
Lance l'interface graphique de gestion des contrats et factures.
"""

import sys
import os

# Ajouter le repertoire courant au path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def show_error(title, message):
    """Affiche une erreur avec tkinter."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except:
        print(f"ERREUR: {title}")
        print(message)
        input("Appuyez sur Entree pour quitter...")

def run():
    """Lance l'application."""
    # Verifier les dependances
    missing = []
    
    try:
        import pydantic
    except ImportError:
        missing.append("pydantic")
    
    try:
        import pdfplumber
    except ImportError:
        missing.append("pdfplumber")
    
    try:
        import dateutil
    except ImportError:
        missing.append("python-dateutil")
    
    try:
        import docx
    except ImportError:
        missing.append("python-docx")
    
    if missing:
        show_error(
            "Dependances manquantes",
            f"Modules manquants: {', '.join(missing)}\n\n"
            f"Executez INSTALL.bat ou:\n"
            f"pip install {' '.join(missing)}"
        )
        sys.exit(1)

    # Lancer l'interface
    try:
        from clm_reader.gui.main_window import MainWindow
        app = MainWindow()
        app.run()
    except Exception as e:
        show_error("Erreur", f"Erreur au lancement:\n{e}")
        sys.exit(1)


if __name__ == '__main__':
    run()
