#!/usr/bin/env python3
"""
Script pour construire l'executable Windows de CLM Reader.

Utilise PyInstaller pour creer un fichier .exe autonome.

Usage:
    python build_windows.py
"""

import os
import sys
import subprocess
import shutil


def build():
    """Construit l'executable Windows."""
    print("=" * 60)
    print("Construction de l'executable CLM Reader")
    print("=" * 60)

    # Verifier que PyInstaller est installe
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Installation de PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # Creer le fichier spec
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pdfplumber',
        'PyPDF2',
        'docx',
        'pydantic',
        'dateutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=False,  # False = pas de console, True = avec console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Ajouter un fichier .ico ici si souhaite
)
'''

    # Ecrire le fichier spec
    with open('CLMReader.spec', 'w') as f:
        f.write(spec_content)

    print("\nFichier spec cree: CLMReader.spec")

    # Lancer PyInstaller
    print("\nLancement de PyInstaller...")
    subprocess.check_call([
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        'CLMReader.spec'
    ])

    # Verifier le resultat
    exe_path = os.path.join('dist', 'CLMReader.exe')
    if os.path.exists(exe_path):
        size = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n{'=' * 60}")
        print(f"Executable cree avec succes!")
        print(f"Chemin: {os.path.abspath(exe_path)}")
        print(f"Taille: {size:.1f} MB")
        print(f"{'=' * 60}")
    else:
        print("\nErreur: L'executable n'a pas ete cree")
        sys.exit(1)


def clean():
    """Nettoie les fichiers de build."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['CLMReader.spec']

    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"Suppression de {d}/")
            shutil.rmtree(d)

    for f in files_to_clean:
        if os.path.exists(f):
            print(f"Suppression de {f}")
            os.remove(f)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean()
    else:
        build()
