from .. import *
from os import *
import contextlib as _contextlib
import os as _os
import shutil as _shutil

import subprocess as _subprocess

from .. import sys as _sys

def is_module(path:str):

    if _os.path.isfile(path) and path.endswith('.py'): return True

    if not _os.path.isdir(path): return False
    
    init_path = _os.path.join(path, '__init__.py')
    return _os.path.exists(init_path) and \
           _os.path.isfile(init_path)

TEMP_DIR = 'C:\\Temp' if _sys.is_this_windows() else \
           '/tmp'
class TempDir(_contextlib.AbstractContextManager):

    def __init__(self, path:str):
        self._path = _os.path.join(TEMP_DIR, path)
    def __enter__(self):
        makedirs(self._path, exist_ok=True)
        return self
    def __exit__(self, *aa, **kaa) -> bool | None:
        _shutil.rmtree(self._path)
    def relpath(self, *subpaths:str) -> str:
        return _os.path.join(self._path, *subpaths)

def getuserenv(name  :str,
               expand:bool=False):
    
    return (popen(f'powershell -NoProfile -Command "(Get-Item -Path HKCU:\\Environment).GetValue(\'{name}\')"')                                         if expand else \
            popen(f'powershell -NoProfile -Command "(Get-Item -Path HKCU:\\Environment).GetValue(\'{name}\', $null, \'DoNotExpandEnvironmentNames\')"')).read()

@warn_deprecated_redirect(getuserenv)
def get_user_env(name  :str,
                 expand:bool=False):
     
    return getuserenv(name, expand)


def pout(cmd:str|list[str]):
    completed = _subprocess.run(
        cmd,
        stdout=_subprocess.PIPE,
        stderr=_subprocess.STDOUT,
        shell=True,
        universal_newlines=True)
    return completed.stdout
