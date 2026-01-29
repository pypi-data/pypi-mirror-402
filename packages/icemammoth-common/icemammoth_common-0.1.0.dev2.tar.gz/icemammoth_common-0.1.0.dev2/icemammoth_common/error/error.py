# -*- coding: utf-8 -*-

from icemammoth_common.util.log_util import logger

from decorator import decorator

class NotExistError(Exception): ...
class ParamError(Exception): ...
class InvalidTypeError(Exception): ...
class OperationError(Exception): ...
class OverLimitError(Exception): ...
class ExecuteError(Exception): ...
class ConcurrentError(Exception): ...

def catch_exception( msg:str = None):

    @decorator
    def catch_exception_decorator(f, *fargs, **fkwargs):
        args = fargs or []
        kwargs = fkwargs or {}
        return __process_exception(
            f,
            msg,
            *args,
            **kwargs
        )
        

    return catch_exception_decorator

def __process_exception(f,msg:str = None , *args, **kwargs):# -> Any:
    try:
        return f(*args,**kwargs)
    except Exception as e:
        if not msg:
            msg = f'execute func {f.__qualname__} in module {f.__module__} failed!'
        logger.exception(f'{msg}')
        raise e