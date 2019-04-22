import os

spec = "..\\DaphnieMaton.spec"

os.system("python -m PyInstaller --name DaphnieMaton --icon ..\\Images\\icon.ico .\\app\\ParametrageV2.py")
os.system("xcopy /Y "+spec+" .\\")
os.system("python -m PyInstaller DaphnieMaton.spec")