# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the standalone Microdrop launcher.
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Microdrop_Icon.ico'],
)
