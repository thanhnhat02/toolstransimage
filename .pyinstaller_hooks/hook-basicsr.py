"""
Custom PyInstaller hook for basicsr.
Ensures all model architectures and utility modules are bundled.
"""
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hiddenimports = collect_all('basicsr')
hiddenimports += collect_submodules('basicsr')
hiddenimports += [
    'basicsr.archs.rrdbnet_arch',
    'basicsr.archs.swinir_arch',
    'basicsr.archs.arch_util',
    'basicsr.utils.img_util',
    'basicsr.utils.download_util',
]
