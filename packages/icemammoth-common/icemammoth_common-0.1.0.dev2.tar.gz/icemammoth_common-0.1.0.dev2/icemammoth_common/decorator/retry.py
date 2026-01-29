# -*- coding: utf-8 -*-

import random
import time
import traceback
from icemammoth_common.util.log_util import logger as Logger
from functools import partial

from decorator import decorator


def __retry_internal(
    f,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=10,
    backoff=1,
    jitter=0,
    logger=Logger,
    log_traceback=False,
    on_exception=None,
):
    """
    Executes a function and retries it if it failed.

    :param f: the function to execute.
    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts. default: 0.
    :param max_delay: the maximum value of delay. default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param on_exception: handler called when exception occurs. will be passed the captured
                         exception as an argument. further retries are stopped when handler
                         returns True. default: None
    :returns: the result of the f function.
    """
    _tries, _delay = tries, delay
    while _tries:
        try:
            return f()
        except exceptions as e:
            if on_exception is not None and on_exception(e):
                raise e

            _tries -= 1
            if _tries <= 0:
                raise e

            try:
                func_qualname = f.func.__qualname__
            except AttributeError:
                func_qualname = str(f.func)
            logger.warning(
                f'method {f.func.__module__}.{func_qualname} execute failed, ' + \
                f'will do {tries-_tries}th retry in {_delay} seconds. ' + \
                f'error_type:{e.__class__.__qualname__}, error_message:{e}'
            )

            if log_traceback:
                logger.warning(traceback.format_exc())

            time.sleep(_delay)
            _delay *= backoff

            _delay += random.uniform(*jitter) if isinstance(jitter, tuple) else jitter
            if max_delay is not None:
                _delay = min(_delay, max_delay)


def retry(
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=10,
    backoff=1,
    jitter=0,
    logger=Logger,
    log_traceback=False,
    on_exception=None,
):
    """Returns a retry decorator.

    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts. default: 0.
    :param max_delay: the maximum value of delay. default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param on_exception: handler called when exception occurs. will be passed the captured
                         exception as an argument. further retries are stopped when handler
                         returns True. default: None
    :returns: a retry decorator.
    """

    @decorator
    def retry_decorator(f, *fargs, **fkwargs):
        args = fargs or []
        kwargs = fkwargs or {}
        return __retry_internal(
            partial(f, *args, **kwargs),
            exceptions,
            tries,
            delay,
            max_delay,
            backoff,
            jitter,
            logger,
            log_traceback,
            on_exception,
        )

    return retry_decorator


def retry_call(
    f,
    fargs=None,
    fkwargs=None,
    exceptions=Exception,
    tries=-1,
    delay=0,
    max_delay=10,
    backoff=1,
    jitter=0,
    logger=Logger,
    log_traceback=False,
    on_exception=None,
):
    """
    Calls a function and re-executes it if it failed.

    :param f: the function to execute.
    :param fargs: the positional arguments of the function to execute.
    :param fkwargs: the named arguments of the function to execute.
    :param exceptions: an exception or a tuple of exceptions to catch. default: Exception.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts. default: 0.
    :param max_delay: the maximum value of delay. default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :param on_exception: handler called when exception occurs. will be passed the captured
                         exception as an argument. further retries are stopped when handler
                         returns True. default: None
    :returns: the result of the f function.
    """
    args = fargs or []
    kwargs = fkwargs or {}
    return __retry_internal(
        partial(f, *args, **kwargs),
        exceptions,
        tries,
        delay,
        max_delay,
        backoff,
        jitter,
        logger,
        log_traceback,
        on_exception,
    )
