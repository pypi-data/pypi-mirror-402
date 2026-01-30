from sys import *

_SYS_ARGV_ITER = iter(argv[1:])

def a():

    next(_SYS_ARGV_ITER)

def is_this_windows():

    return platform == 'win32'
