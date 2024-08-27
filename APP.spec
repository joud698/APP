# APP.spec

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['APP.py'],  
    pathex=['C:\\Users\\joudy\\Desktop\\python_joud'],  # Ajouter le chemin où se trouvent vos fichiers Python
    binaries=[
        ('C:\\Users\\joudy\\anaconda3\\envs\\joud\\Library\\bin\\hdf5.dll', '.'),
        # Ajoutez d'autres DLLs nécessaires ici si nécessaire
    ],
    datas=[
        ('C:\\Users\\joudy\\anaconda3\\envs\\joud\\Lib\\site-packages\\xyzservices\\data\\providers.json', 'xyzservices/data'),('MAP.py', '.'),  
    ],
    hiddenimports=[
        'pandas',
        'shapely.geometry',
        'geopandas',
        'numpy',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'fastkml',
        'subprocess',
        'PyQt5.QtWebEngineWidgets',
        'matplotlib',
        'folium',
	'PyQt5.sip',
    	'PyQt5.QtWebEngineWidgets',
        'h5py',
 	'requests',
        'chardet',
        'charset_normalizer'

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
    [],
    exclude_binaries=True,
    name='APP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    icon=['icone.ico'],
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='APP',
)
