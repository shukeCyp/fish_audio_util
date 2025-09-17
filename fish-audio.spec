# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 收集 fish-audio-sdk 相关文件
fish_audio_datas = collect_data_files('fish_audio_sdk')
fish_audio_hiddenimports = collect_submodules('fish_audio_sdk')

# 收集 PyQt5 相关文件
pyqt5_datas = collect_data_files('PyQt5')
pyqt5_hiddenimports = collect_submodules('PyQt5')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 添加资源文件
        ('resources', 'resources'),
        # 添加 fish-audio-sdk 数据文件
        *fish_audio_datas,
        # 添加 PyQt5 数据文件
        *pyqt5_datas,
    ],
    hiddenimports=[
        # PyQt5 相关模块
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.QtNetwork',
        # fish-audio-sdk 相关模块
        'fish_audio_sdk',
        *fish_audio_hiddenimports,
        *pyqt5_hiddenimports,
        # 其他必要模块
        'requests',
        'numpy',
        'scipy',
        'loguru',
        'pathlib',
        'json',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'tkinter',
        'matplotlib',
        'pandas',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
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
    a.zipfiles,
    a.datas,
    [],
    name='fish-audio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为 False 以隐藏控制台窗口
    disable_windowed_traceback=False,
    target_arch='x86' if os.environ.get('PROCESSOR_ARCHITECTURE') == 'x86' or os.environ.get('PROCESSOR_ARCHITEW6432') is None else None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icons/app.ico' if os.path.exists('resources/icons/app.ico') else None,
    version_file=None,
) 