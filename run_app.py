#!/usr/bin/env python3
"""
Point d'entree principal pour l'application CLM Reader.

Lance l'interface graphique de gestion des contrats et factures.
"""

import sys
import os

# Ajouter le repertoire parent au path si necessaire
if getattr(sys, 'frozen', False):
    # Si execute depuis un executable PyInstaller
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from clm_reader.gui.main_window import main

if __name__ == '__main__':
    main()
