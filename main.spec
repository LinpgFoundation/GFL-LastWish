# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex = ['D:\\GitHub\\GirlsFrontLine-LastWish'],
    binaries = [],
    datas = [
        ('Assets','Assets'),
        ('Data','Data'),
        ('Lang','Lang'),
        ('Source_pyd','Source_pyd'),
        ('icon.ico','.')
    ],
    hiddenimports = [
        "numpy",
        "PIL.Image",
        "tkinter",
        "cv2",
        "yaml",
        "linpg",
        "linpgtoolkit",
        "pygame",
        "pygame.locals",
        "pygame.colordict",
        "pygame._sdl2",
        "pypresence",
    ],
    hookspath = [],
    runtime_hooks = [],
    excludes = [],
    win_no_prefer_redirects = False,
    win_private_assemblies = False,
    cipher = block_cipher,
    noarchive = False
    )
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher = block_cipher
    )
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries = True,
    name = 'main',
    debug = False,
    bootloader_ignore_signals = False,
    strip = False,
    upx = True,
    console = True,
    icon = "icon.ico"
    )
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip = False,
    upx = True,
    upx_exclude = [],
    name = 'main'
    )
