import os

spec = "..\\DaphniMaton.spec"

os.system("python -m PyInstaller --name DaphniMaton kv\\ParametrageV2.py")
os.system("xcopy /Y "+spec+" .\\")
os.system("python -m PyInstaller DaphniMaton.spec")