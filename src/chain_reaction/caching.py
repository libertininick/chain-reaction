"""Tools for caching function and tool calls."""

from collections.abc import Callable
from functools import wraps
from hashlib import md5
from typing import Final, cast

from diskcache import Cache
from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic_core import to_json

# Define a custom logging level for cache operations
CACHE_LOG_LEVEL_NAME: Final[str] = "CACHE"
CACHE_LOG_LEVEL = logger.level(name=CACHE_LOG_LEVEL_NAME, no=10, color="<yellow>", icon="💾")


def cache_calls[**P, R](cache: Cache | None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to cache function calls using diskcache.

    NOTE: Decorated function must have a `__name__` attribute and its arguments must be JSON serializable.

    Args:
        cache (Cache | None): An instance of diskcache.Cache to store cached results. If None, caching is disabled.

    Returns:
        Callable[[Callable[P, R]], Callable[P, R]]: A decorator that can be applied to functions to enable caching.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Check if cache is provided
            if cache is None:
                # Cache not provided, execute function directly
                return func(*args, **kwargs)

            # Get function name
            func_name = _get_function_name(func)

            # Generate cache key for the function call
            cache_key = _get_cache_key(func_name, args, kwargs)

            # Try to get cached value
            value = cache.get(cache_key)

            # If cached value exists, return it
            if value is not None:
                logger.log(CACHE_LOG_LEVEL_NAME, f"[CACHE HIT] function: {func_name} key: {cache_key}")
                return cast(R, value)

            # otherwise, execute function
            result = func(*args, **kwargs)

            # and store result in cache tagged with function name
            cache.set(key=cache_key, value=result, tag=func_name)
            logger.log(CACHE_LOG_LEVEL_NAME, f"[CACHED] function: {func_name} key: {cache_key}")
            return result

        return wrapper

    return decorator


def evict_calls(cache: Cache, func: StructuredTool | Callable | str) -> int:
    """Clear all cached calls for a specific function.

    Args:
        cache (Cache): An instance of diskcache.Cache to clear cached results from.
        func (StructuredTool | Callable | str): The function or function name whose cached calls should be cleared.

    Returns:
        int: The number of cache entries that were cleared.
    """
    # Invalidate all cache entries tagged with the function name
    func_name = _get_function_name(func)
    num_cleared = cache.evict(tag=func_name)

    # Log the cache eviction
    logger.log(
        CACHE_LOG_LEVEL_NAME,
        f"[CACHE CLEARED] function: {func_name} cleared_entries: {num_cleared}",
    )

    # Return the number of cleared entries
    return num_cleared


# Helpers
def _get_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Create cache key from function name and arguments.

    Args:
        func_name (str): The name of the function.
        args (tuple): The positional arguments passed to the function.
        kwargs (dict): The keyword arguments passed to the function.

    Returns:
        str: A unique cache key as an MD5 hash.
    """
    # Serialize function name and arguments to JSON bytes
    key_data = to_json({
        "func": func_name,
        "args": args,
        "kwargs": kwargs,
    })

    # Hash the serialized data to create a fixed-size cache key
    return md5(key_data, usedforsecurity=False).hexdigest()


def _get_function_name(func: StructuredTool | Callable | str) -> str:
    """Get the name of a function or StructuredTool.

    Args:
        func (StructuredTool | Callable | str): The function or function name.

    Returns:
        str: The name of the function.

    Raises:
        AttributeError: If the Callable does not have a __name__ attribute or __name__ is not a string.
        TypeError: If the input is not a StructuredTool, Callable, or str.
    """
    if isinstance(func, StructuredTool):
        return func.get_name()
    elif callable(func):
        name = getattr(func, "__name__", None)
        if isinstance(name, str):
            return name
        raise AttributeError(f"{func!r} has no __name__ attribute or __name__ is not a string")
    elif isinstance(func, str):
        return func
    else:
        raise TypeError("function must be a StructuredTool, Callable, or str")
