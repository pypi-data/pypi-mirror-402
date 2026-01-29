"""Timing decorators and utilities for measuring comparison performance."""

import time
from functools import wraps
from typing import Callable, Any


def timed(func: Callable) -> Callable:
    """
    Decorator to measure the execution time of a function.

    Usage:
        @timed
        def my_func(...):
            ...

    Returns:
        function: wrapped function
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> tuple[Any, float]:
        start = time.perf_counter()
        end = time.perf_counter()
        elapsed = end - start
        result = func(*args, **kwargs)
        return elapsed, result

    return wrapper
