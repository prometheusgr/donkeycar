import importlib
import traceback
import os
import sys
repo_root = r'c:\Users\Beat\source\donkeycar'
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
print('sys.path[0]=', sys.path[0])
try:
    importlib.import_module('donkeycar.vehicle')
    print('imported donkeycar.vehicle OK')
except Exception:
    traceback.print_exc()
