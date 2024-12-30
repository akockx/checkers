# ------------------------------------------------------------------------------
#  Copyright (c) 2024 A.C. Kockx, All Rights Reserved.
# ------------------------------------------------------------------------------

""" This module contains a decorator for performance measurement. """
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import Any, Final


def print_time[_T](name: str | None = None) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    """ Return a print_time_decorator that uses the passed name (optional). If name is not passed, then the name of the wrapped function will be used. """

    if name:
        name = name.strip()

    def print_time_decorator(function: Callable[..., _T]) -> Callable[..., _T]:
        """ Return a closure that wraps the passed function and prints the time the function takes to execute (only in debug mode). """

        @wraps(function)
        def print_time_wrapper(*args: Any, **kwargs: Any) -> _T:
            """ Call the wrapped function using the passed arguments and print the time the function takes to execute (only in debug mode).
            Return the result of the wrapped function.
            """

            start_time: Final[float] = perf_counter()
            result: Final[_T] = function(*args, **kwargs)
            end_time: Final[float] = perf_counter()
            if __debug__:
                print(f"{name if name else function.__name__}: {end_time - start_time:.3f} s")

            return result

        return print_time_wrapper

    return print_time_decorator
