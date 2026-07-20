# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the standalone Microdrop launcher.
import os
import re
import sys

# CI passes the release tag (e.g. v0.2.0) so the .app bundle carries a real
# version; local/dispatch builds fall back to 0.0.0.
_tag = os.environ.get('MICRODROP_VERSION', '')
APP_VERSION = _tag[1:] if re.fullmatch(r'v\d+\.\d+\.\d+', _tag) else '0.0.0'
#
# One-file, console build (the --launch path streams git/pixi output and calls
# input() to pause). The launch shell scripts are bundled as data so they ship
# inside the exe; microdrop_setup.launcher_assets_dir() reads them from
# sys._MEIPASS at run time. No Qt/conda machinery is needed — the launcher is
# stdlib + tkinter only, unlike the main app's pyinstaller.spec.

a = Analysis(
    ['microdrop_setup.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('launch_microdrop.ps1', '.'),
        ('launch_microdrop.sh', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'pip', 'PyInstaller'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='microdrop_setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Windowed on macOS so the BUNDLE below yields a double-clickable .app;
    # everything user-facing streams through the GUI log callback, and a
    # windowed Mach-O still gets stdio when invoked from a terminal. Console
    # elsewhere: the --launch path streams git/pixi output and input()-pauses.
    console=(sys.platform != 'darwin'),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # .ico only embeds on Windows; the macOS icon lives on the BUNDLE below
    # (PyInstaller converts the .ico via Pillow), Linux ignores icons entirely.
    icon=['Microdrop_Icon.ico'] if sys.platform == 'win32' else None,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Microdrop Launcher.app',
        icon='Microdrop_Icon.ico',   # needs Pillow at build time (.ico -> .icns)
        bundle_identifier='ca.blueoceantechnologies.microdrop-launcher',
        info_plist={
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSHighResolutionCapable': True,
        },
    )
