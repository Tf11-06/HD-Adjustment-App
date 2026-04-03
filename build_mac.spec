# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter
import tkinterdnd2

ctk_path = os.path.dirname(customtkinter.__file__)
tkdnd_path = os.path.dirname(tkinterdnd2.__file__)

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        (ctk_path, 'customtkinter'),
        (tkdnd_path, 'tkinterdnd2'),
        # config.json and service_account.json are NOT bundled.
        # They must live in the same folder as HDProcessor.app at runtime.
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
    [],
    exclude_binaries=True,
    name='HDProcessor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HDProcessor',
)

app = BUNDLE(
    coll,
    name='HDProcessor.app',
    icon=None,
    bundle_identifier='com.klearconcepts.hdprocessor',
)
