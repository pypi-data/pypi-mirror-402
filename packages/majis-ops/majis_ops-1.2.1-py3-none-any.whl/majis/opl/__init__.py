"""MAJIS OPL submodule."""

from .convert import csv2json_opl, json2csv_opl
from .export import save_opl
from .reader import read_opl

__all__ = [
    'read_opl',
    'save_opl',
    'json2csv_opl',
    'csv2json_opl',
]
