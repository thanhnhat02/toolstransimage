# PyInstaller spec file for AI Image Enhancer
# Usage: pyinstaller ai_enhancer.spec

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# ── Collect all data and hidden imports ────────────────────────────── #
datas = []
hiddenimports = []
binaries = []

# PySide6
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')
datas     += pyside6_datas
binaries  += pyside6_binaries
hiddenimports += pyside6_hiddenimports

# OpenCV
cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')
datas     += cv2_datas
binaries  += cv2_binaries
hiddenimports += cv2_hiddenimports

# numpy / PIL
datas += collect_data_files('numpy')
datas += collect_data_files('PIL')

# basicsr / facexlib / realesrgan / gfpgan
for pkg in ['basicsr', 'facexlib', 'realesrgan', 'gfpgan']:
    try:
        pkg_datas, pkg_bins, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_bins
        hiddenimports += pkg_hidden
    except Exception:
        pass

# transformers / diffusers / accelerate
for pkg in ['transformers', 'diffusers', 'accelerate', 'safetensors', 'huggingface_hub']:
    try:
        pkg_datas, pkg_bins, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_bins
        hiddenimports += pkg_hidden
    except Exception:
        pass

# timm / einops
for pkg in ['timm', 'einops']:
    try:
        datas += collect_data_files(pkg)
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# Project source
datas += [('src', 'src')]
datas += [('assets', 'assets')]

# Extra hidden imports
hiddenimports += [
    # PySide6 core
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    'PySide6.QtXml', 'PySide6.QtNetwork',
    # ML
    'torch', 'torchvision', 'torchaudio',
    'torch.nn', 'torch.nn.functional',
    'torch.cuda', 'torch.backends.cudnn',
    # Image
    'PIL', 'PIL.Image', 'PIL.ImageOps', 'PIL.ImageEnhance',
    'cv2', 'numpy', 'scipy', 'scipy.ndimage',
    # basicsr archs
    'basicsr.archs', 'basicsr.archs.rrdbnet_arch',
    'basicsr.archs.swinir_arch',
    'basicsr.utils', 'basicsr.data.transforms',
    # realesrgan
    'realesrgan', 'realesrgan.archs',
    # gfpgan
    'gfpgan', 'gfpgan.archs',
    # facexlib
    'facexlib', 'facexlib.detection', 'facexlib.parsing',
    # packaging
    'packaging', 'packaging.version',
    # misc
    'einops', 'timm', 'requests', 'tqdm',
    'urllib', 'urllib.request', 'urllib.parse',
    'logging', 'logging.handlers',
    'pathlib', 'dataclasses', 'abc',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.pyinstaller_hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'tkinter', 'IPython',
        'jupyter', 'notebook', 'PyQt5', 'PyQt6',
        'wx', 'gtk', 'gi',
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
    [],
    exclude_binaries=True,
    name='AIImageEnhancer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,        # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon='assets/icons/app_icon.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AIImageEnhancer',
)
