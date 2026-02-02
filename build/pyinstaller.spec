# PyInstaller spec for EmailSorter (windowed, onefile)

import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

datas = [
    ('config/config_default.json', 'config'),
]

hiddenimports = collect_submodules('extract_msg')

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='EmailSorter',
    debug=False,
    strip=False,
    upx=False,
    console=False
)
