# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['./__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('./analysis_files/template_files', 'template_files/'),('./analysis_files/handler_files', 'handler_files/'),('./analysis_files/tools_files', 'tools_files/'), ('./.venv/Lib/site-packages/customtkinter', 'customtkinter/'),('./.venv/Lib/site-packages/darkdetect', 'darkdetect/'), ('./image_files', 'image_files/'),('./NikonLogHandler.XML','.'),('./languages.json','.'),('./.venv/Lib/site-packages/office365', 'office365/')],
    hiddenimports=['main_app_files.core_script_files.custom_graphs', 'main_app_files.core_script_files.utilities', 'PIL', 'customtkinter', 'matplotlib', 'msoffcrypto', 'numpy', 'openpyxl', 'pandas','pymatreader', 'scipy', 'xmltodict',],
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
    [],
    exclude_binaries=True,
    name='NikonLogHandler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='./image_files/app_images/NikonLogHandler_app_icon.png',
    version="version.rc"
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NikonLogHandler',
)
