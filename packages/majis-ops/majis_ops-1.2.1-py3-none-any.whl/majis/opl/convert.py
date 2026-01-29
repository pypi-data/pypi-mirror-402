"""OPL convert module."""

from pathlib import Path

from .export import save_opl_csv, save_opl_json
from .reader import read_opl_csv, read_opl_json


def json2csv_opl(opl_json: str | Path | None, overlap: bool = False):
    """Export OPL from JSON to CSV format."""
    return save_opl_csv(
        Path(opl_json).with_suffix('.csv'),
        *read_opl_json(opl_json),
        overlap=overlap,
    )


def csv2json_opl(opl_csv: str | Path | None, overlap: bool = False):
    """Export OPL from CSV to JSON format."""
    return save_opl_json(
        Path(opl_csv).with_suffix('.json'),
        *read_opl_csv(opl_csv),
        overlap=overlap,
    )
