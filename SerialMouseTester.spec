# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Serial Mouse Tester
Build: pyinstaller SerialMouseTester.spec
"""

import os
import sys

block_cipher = None

# Project root
ROOT = os.path.abspath(SPECPATH)

a = Analysis(
    [os.path.join(ROOT, 'run.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'VERSION'), '.'),
    ],
    hiddenimports=[
        'serial_mouse_tester',
        'serial_mouse_tester.core.protocols',
        'serial_mouse_tester.core.serial_worker',
        'serial_mouse_tester.core.logger',
        'serial_mouse_tester.ui.main_window',
        'serial_mouse_tester.ui.hex_monitor',
        'serial_mouse_tester.ui.mouse_canvas',
        'serial_mouse_tester.ui.log_panel',
        'serial_mouse_tester.ui.settings_dialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
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
    a.datas,
    [],
    name='SerialMouseTester',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=None,
)
