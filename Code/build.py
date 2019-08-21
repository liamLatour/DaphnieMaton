import os
import sys


os.system("xcopy /Y "+sys.argv[1]+" .\\")
os.system("python -m PyInstaller DaphnieMaton.spec")
