"""OPL generic reader module."""

import csv
from pathlib import Path

from planetary_coverage.events import EventsDict, EventsList, EventWindow

from ..itl.reader import read_itl_json
from ..misc.events import flatten, group


def read_opl(fname: str | Path, flat: bool = False) -> EventsDict | EventsList:
    """Read OPL file.

    Both, CSV (``.csv``) and JSON (``.json``) format are supported.

    In the case of

    The result can be return as a nested dict of events (default) or
    as a flat list of events.

    """
    f = Path(fname)

    match f.suffix.lower():
        case '.csv':
            events = read_opl_csv(f)
        case '.json':
            events = read_opl_json(f)
        case _:
            raise ValueError(f'Invalid OPL file input: {fname}')

    return flatten(events) if flat else group(events)


def read_opl_csv(fname: str | Path) -> list[EventWindow]:
    """Read OPL file in CSV format."""
    with Path(fname).open(encoding='utf-8') as content:
        return [EventWindow(**parse_opl_csv(*params)) for params in csv.reader(content)]


def parse_opl_csv(key, start, end, obs_key, instrument) -> dict:
    """OPL CSV line parser.

    Warning
    -------
    Currently the OPL CSV don't have an explicit header.
    Here we assume that the header is as follow"

        # key, start, end, obs_key, instrument

    The initial ``key`` is composed of the following parameters:

        <instrument>_<observation_type>_<type>

    """
    _, observation_type, _type = key.split('_')

    return {
        'key': key,
        't_start': start,
        't_end': end,
        'OBS_KEY': obs_key,
        'INSTRUMENT': instrument,
        'OBSERVATION_TYPE': observation_type,
        'TYPE': _type,
    }


def read_opl_json(fname: str | Path) -> list[EventWindow]:
    """Read OPL file in JSON format.

    Note
    ----
    Re-use ITL JSON reader with OPL schema instead.

    """
    return read_itl_json(fname, fmt='OPL')
