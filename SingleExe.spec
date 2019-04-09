# -*- mode: python -*-
from kivy.deps import sdl2, glew

block_cipher = None

a = Analysis(['C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\app\\ParametrageV2.py'],
             pathex=['C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code'],
             binaries=[],
             datas=[],
             hiddenimports=['win32file', 'win32timezone'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

a.datas += [('main.kv', 'C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\app\\main.kv', 'DATA')]

exe = EXE(pyz, Tree('C:\\Users\\Administrateur\\Desktop\\DaphnieMaton\\Code\\app\\assets'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
          name='DaphniMaton',
          debug=False,
          strip=False,
          upx=True,
          console=False )