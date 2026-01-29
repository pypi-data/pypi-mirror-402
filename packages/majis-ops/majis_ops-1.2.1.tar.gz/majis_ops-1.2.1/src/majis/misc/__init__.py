"""MAJIS miscellaneous submodule."""

from .depreciation import depreciated
from .evf import read_evf
from .time import fmt_datetime, get_datetime

__all__ = [
    'read_evf',
    'get_datetime',
    'fmt_datetime',
    'depreciated',
]
