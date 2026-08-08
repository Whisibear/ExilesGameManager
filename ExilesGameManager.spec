# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('web/dist', 'web/dist'), ('LICENSE', '.'), ('CREDITS.md', '.'), ('THIRD_PARTY_NOTICES.md', '.'), ('GETTING_STARTED.md', '.'), ('ExilesGameManager.ico', '.')],
    hiddenimports=['app.routes.app_update', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on', 'uvicorn.logging', 'ooz', 'pystray', 'pystray._win32', 'PIL', 'PIL.Image', 'PIL.IcoImagePlugin'],
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
    [],
    exclude_binaries=True,
    name='ExilesGameManager',
    icon='ExilesGameManager.ico',
    version='version_info.txt',
    manifest='ExilesGameManager.manifest',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ExilesGameManager',
)
