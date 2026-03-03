# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['run_blindspot.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/blindspot/assets/splash.gif', 'assets')],
    hiddenimports=['PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BlindSpot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/blindspot/assets/lil_timmy.icns',
)

app = BUNDLE(
    exe,
    name='BlindSpot.app',
    icon='src/blindspot/assets/lil_timmy.icns',
    bundle_identifier='com.amymaddoxlab.blindspot',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'BlindSpot',
        'CFBundleDisplayName': 'BlindSpot',
        'NSHumanReadableCopyright': 'The Amy Maddox Lab, UNC Chapel Hill',
    },
)