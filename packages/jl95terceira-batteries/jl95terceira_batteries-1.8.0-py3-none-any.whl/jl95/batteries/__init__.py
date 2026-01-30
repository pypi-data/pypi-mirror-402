import abc as _abc
import functools as _functools
import threading as _threading
import time as _time
import typing as _typing

def warn_deprecated(arg:str|None|_typing.Callable=None):

    if callable(arg):

        return warn_deprecated()(arg)

    def decorator(funcdepr:_typing.Callable):

        @_functools.wraps(funcdepr)
        def wrapper(*aa, **kaa):

            print(f'[DEPRECATED] {funcdepr.__module__}.{funcdepr.__qualname__}{f': {arg}' if arg else ''}')
            return funcdepr(*aa, **kaa)
        
        return wrapper
    
    return decorator

def warn_deprecated_redirect(funcnew:_typing.Callable):

    return warn_deprecated(arg=f'Please, use {funcnew.__module__}.{funcnew.__qualname__} instead')

from . import os as _os

@warn_deprecated_redirect(_os.is_module)
def is_module(path:str):

    if _os.path.isfile(path) and path.endswith('.py'): return True

    if not _os.path.isdir(path): return False
    
    init_path = _os.path.join(path, '__init__.py')
    return _os.path.exists(init_path) and \
           _os.path.isfile(init_path)
class Enumerator[T]:

    def __init__(self):

        self._managed:list[T] = list()
    
    def __call__(self, x):

        self._managed.append(x)
        return x

    @warn_deprecated_redirect(__call__)
    def E(self, x):

        return self(x)
    
    def __iter__(self):

        return self._managed.__iter__()

class _CallablesRef:

    def __init__(self, *ff:_typing.Callable):

        self._ff = ff

class _JoinedCallables(_CallablesRef):

    def __call__(self, *aa, **kaa):

        for f in self._ff: 
            
            f(*aa, **kaa)

def joincallables(*ff:_typing.Callable): return _JoinedCallables(*ff).__call__

class _JoinedFunctions(_CallablesRef):

    def __call__(self, *aa, **kaa): 
        
        for f in self._ff: 
            
            yield f(*aa, **kaa)

def joinfunctions(*ff:_typing.Callable): return _JoinedFunctions(*ff).__call__

class _Raiser:

    def __init__(self, ex:Exception):       self._ex = ex
    def __call__(self)              : raise self._ex

def raiser(ex:Exception): return _Raiser(ex).__call__

def selfie[T](v:T): return v # instead of "self" since the latter is widely used for the instance reference in methods

class _Constant[T]:

    def __init__(self, v:T): self._v = v
    def __call__(self, *aa, **kaa): return self._v

def constant[T](v:T): return _Constant(v).__call__

def waitkbi(poll_time_s:float=60):

    while True:
        try: _time.sleep(poll_time_s)
        except KeyboardInterrupt: break

class Future[T](_typing.Protocol):

    @_abc.abstractmethod
    def is_completed(self) -> bool: ...

    @_abc.abstractmethod
    def get(self, timeout:float|None=None) -> T: ...

    def map[U](self, f:_typing.Callable[[T], U]) -> 'Future[U]':

        parent = self
        class MappedFuture(Future[U]):

            @_typing.override
            def is_completed(self) -> bool:

                return parent.is_completed()
            
            @_typing.override
            def get(self, timeout:float|None=None) -> U:

                return f(parent.get(timeout))
        
        return MappedFuture()

class _NotCompleted: pass
_NOT_COMPLETED = _NotCompleted()
class CompletableFuture[T](Future[T]):

    def __init__(self): 

        self._result:T|_NotCompleted = _NOT_COMPLETED
        self._lock = _threading.Lock()
        self._lock.acquire()

    def complete(self, result:T):
        
        self._result = result
        self._lock.release()

    def reset(self):

        if not self.is_completed():
            return
        self._result = _NOT_COMPLETED
        self._lock.acquire()

    @_typing.override
    def is_completed(self):

        return not self._lock.locked()
    
    @_typing.override
    def get(self, timeout:float|None=None) -> T:

        acquired = self._lock.acquire(timeout=timeout) if timeout is not None else \
                   self._lock.acquire()
        if not acquired:
            raise TimeoutError('Timeout expired before future was completed')
        self._lock.release()
        self._result
        assert not isinstance(self._result, _NotCompleted)
        return self._result  # type: ignore
