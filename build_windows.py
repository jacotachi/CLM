#!/usr/bin/env python3
"""
Script pour construire l'executable Windows de CLM Reader.

Utilise PyInstaller pour creer un fichier .exe autonome.
Installe automatiquement toutes les dependances necessaires.

Usage:
    python build_windows.py
    python build_windows.py clean
"""

import os
import sys
import subprocess
import shutil


REQUIRED_PACKAGES = [
    'pydantic',
    'pdfplumber',
    'PyPDF2',
    'python-docx',
    'python-dateutil',
    'click',
    'rich',
    'pyinstaller',
]


def install_dependencies():
    """Installe toutes les dependances necessaires."""
    print("Installation des dependances...")
    print("-" * 40)

    for package in REQUIRED_PACKAGES:
        print(f"  Installation de {package}...")
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"    OK: {package}")
        except subprocess.CalledProcessError:
            print(f"    ERREUR: {package}")
            return False

    print("-" * 40)
    print("Toutes les dependances sont installees.\n")
    return True


def build():
    """Construit l'executable Windows."""
    print("=" * 60)
    print("  CLM Reader - Construction de l'executable Windows")
    print("=" * 60)
    print()

    # Installer les dependances
    if not install_dependencies():
        print("Erreur lors de l'installation des dependances")
        sys.exit(1)

    # Creer le fichier spec avec tous les imports necessaires
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Pydantic v2 imports
        'pydantic',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        'pydantic._internal',
        'pydantic._internal._config',
        'pydantic._internal._decorators',
        'pydantic._internal._fields',
        'pydantic._internal._generate_schema',
        'pydantic._internal._generics',
        'pydantic._internal._model_construction',
        'pydantic._internal._repr',
        'pydantic._internal._typing_extra',
        'pydantic._internal._utils',
        'pydantic._internal._validators',
        'pydantic.fields',
        'pydantic.main',
        'pydantic.types',
        'pydantic.json_schema',
        'pydantic_core',
        'annotated_types',

        # PDF processing
        'pdfplumber',
        'pdfplumber.page',
        'pdfplumber.pdf',
        'pdfplumber.table',
        'pdfplumber.utils',
        'pdfminer',
        'pdfminer.high_level',
        'pdfminer.layout',
        'pdfminer.pdfparser',
        'pdfminer.pdfdocument',
        'pdfminer.pdfpage',
        'pdfminer.pdfinterp',
        'pdfminer.converter',
        'pdfminer.cmapdb',
        'pdfminer.psparser',
        'pdfminer.pdftypes',
        'pdfminer.utils',
        'PyPDF2',

        # Word documents
        'docx',
        'docx.document',
        'docx.table',
        'docx.text',
        'docx.text.paragraph',
        'lxml',
        'lxml.etree',

        # Date parsing
        'dateutil',
        'dateutil.parser',
        'dateutil.tz',

        # CLI (not needed for GUI but included)
        'click',
        'rich',
        'rich.console',
        'rich.table',
        'rich.panel',

        # Standard library that might be missed
        'sqlite3',
        'decimal',
        'typing',
        'pathlib',
        'json',
        'datetime',
        're',
        'os',
        'sys',

        # Tkinter
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',

        # Our modules
        'clm_reader',
        'clm_reader.models',
        'clm_reader.models.contract',
        'clm_reader.models.invoice',
        'clm_reader.parsers',
        'clm_reader.parsers.contract_parser',
        'clm_reader.parsers.invoice_parser',
        'clm_reader.extractors',
        'clm_reader.extractors.document_extractor',
        'clm_reader.database',
        'clm_reader.database.db_manager',
        'clm_reader.utils',
        'clm_reader.utils.text_utils',
        'clm_reader.gui',
        'clm_reader.gui.main_window',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'pytest_cov',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CLMReader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''

    # Ecrire le fichier spec
    with open('CLMReader.spec', 'w') as f:
        f.write(spec_content)

    print("Fichier spec cree: CLMReader.spec")
    print()

    # Lancer PyInstaller
    print("Lancement de PyInstaller...")
    print("(Cela peut prendre quelques minutes)")
    print("-" * 40)

    try:
        subprocess.check_call([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'CLMReader.spec'
        ])
    except subprocess.CalledProcessError as e:
        print(f"\nErreur PyInstaller: {e}")
        sys.exit(1)

    # Verifier le resultat
    exe_path = os.path.join('dist', 'CLMReader.exe')
    if os.path.exists(exe_path):
        size = os.path.getsize(exe_path) / (1024 * 1024)
        print()
        print("=" * 60)
        print("  SUCCES!")
        print("=" * 60)
        print(f"  Executable: {os.path.abspath(exe_path)}")
        print(f"  Taille: {size:.1f} MB")
        print()
        print("  Vous pouvez maintenant copier CLMReader.exe")
        print("  sur n'importe quel PC Windows et l'executer")
        print("  sans avoir besoin d'installer Python.")
        print("=" * 60)
    else:
        print("\nErreur: L'executable n'a pas ete cree")
        sys.exit(1)


def clean():
    """Nettoie les fichiers de build."""
    print("Nettoyage des fichiers de build...")

    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['CLMReader.spec']

    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"  Suppression de {d}/")
            shutil.rmtree(d)

    for f in files_to_clean:
        if os.path.exists(f):
            print(f"  Suppression de {f}")
            os.remove(f)

    print("Nettoyage termine.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean()
    else:
        build()
