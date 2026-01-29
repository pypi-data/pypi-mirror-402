"""Depreciation miscellaneous sub-module."""

from functools import wraps
from warnings import warn


def depreciated(func, *, old, new):
    """Depreciation warning decorator."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Depreciation wrapper."""
        warn(
            f'`{old}` is depreciated in favor of `{new}`.',
            DeprecationWarning,
            stacklevel=2,
        )
        return func(*args, **kwargs)

    return wrapper
