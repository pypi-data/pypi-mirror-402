import logging
import inspect
from time import perf_counter
from typing import Any, Callable
from functools import wraps, partial


logger = logging.getLogger(__name__)


def process_status(err: BaseException | None) -> None:
    """Log process completion status.
    
    Args:
        err: Exception object if process failed, None if successful
    """
    if err is not None:
        logger.error(f"Process failed: {err}")
    else:
        logger.info("Process completed successfully")


def logtimer(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        start = perf_counter()
        result = func(*args, **kwargs)
        logger.info(f"Execution of {func.__name__} took: {(perf_counter() - start):.6f} sec")
        return result
    return wrapper


def funcLifeLog(func: Callable[..., Any], logger: logging.Logger) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        logger.info(f"Calling for execution of {func.__name__}")
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
        logger.info(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        value = func(*args, **kwargs)
        logger.info(f"Finished execution of {func.__name__}")
        return value
    return wrapper

inOutLog = partial(funcLifeLog, logger=logger)