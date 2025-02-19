# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['wallpaper_app.py'],
    binaries=[],
    # datas=[
    #     ('icon.ico', '.'),  # 如果有图标文件需要包含
    # ],
    hiddenimports=[
        'win32timezone',    # 解决 pywin32 的隐藏依赖
        'PIL._tkinter_finder',  # 解决 Pillow 的隐藏依赖
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
    name='WallpaperMaster',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩（需单独安装）
    console=False,  # 不显示控制台窗口
    # icon='icon.ico',  # 设置程序图标
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)