"""MAJIS ITL submodule."""

from ..misc import depreciated
from .csv import save_itl_csv
from .export import save_itl
from .reader import read_itl
from .timeline import Timeline, save_itl_xlsm

# Depreciated methods
save_csv = depreciated(save_itl_csv, old='save_csv', new='save_itl')
save_xlsm = depreciated(save_itl_xlsm, old='save_xlsm', new='save_itl')

__all__ = [
    'read_itl',
    'save_itl',
    'Timeline',
    'save_csv',  # Depreciated
    'save_xlsm',  # Depreciated
]
