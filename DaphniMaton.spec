# -*- mode: python -*-
from kivy.deps import sdl2, glew

block_cipher = None


a = Analysis(['C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\kv\\ParametrageV2.py'],
             pathex=['C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code'],
             binaries=[],
             datas=[],
             hiddenimports=['win32file', 'win32timezone'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='DaphniMaton',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe, Tree('C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\kv'),
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               name='DaphniMaton')