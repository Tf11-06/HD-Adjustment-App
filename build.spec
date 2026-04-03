# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter
import tkinterdnd2

# Include customtkinter assets
ctk_path = os.path.dirname(customtkinter.__file__)

# Include tkinterdnd2 package (contains platform-specific tkdnd DLL)
tkdnd_path = os.path.dirname(tkinterdnd2.__file__)

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        (ctk_path, 'customtkinter'),
        (tkdnd_path, 'tkinterdnd2'),
        # config.json and service_account.json are NOT bundled.
        # They live next to HDProcessor.exe and are set up by the client.
    ],
    hiddenimports=[
        'tkinterdnd2',
        'pdfplumber',
        'gspread',
        'google.auth',
        'google.oauth2.service_account',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='HDProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
