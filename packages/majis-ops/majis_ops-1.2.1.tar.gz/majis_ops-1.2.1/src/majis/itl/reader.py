"""ITL generic reader module."""

from pathlib import Path

from planetary_coverage.events import EventsDict, EventsList

from ..misc.events import flatten, group
from .eps import read_itl_eps
from .json import read_itl_json


def read_itl(
    fname: str | Path,
    refs: dict | str | list | None = None,
    flat: bool = False,
) -> EventsDict | EventsList:
    """Read any ITL file.

    Both, EPS/text (``.itl`` or ``.txt``) or JSON (``.json``)
    format are supported.

    In the case of EPS format, relative datetime input is supported
    with references value(s) or file (``.evf``).

    The result can be return as a nested dict of events (default) or
    as a flat list of events.

    """
    f = Path(fname)

    match f.suffix.lower():
        case '.itl' | '.txt':
            events = read_itl_eps(f, refs=refs)
        case '.json':
            if refs:
                raise NotImplementedError('Relative time ITL is not yet supported.')
            events = read_itl_json(f)
        case _:
            raise ValueError(f'Invalid ITL file input: {fname}')

    return flatten(events) if flat else group(events)
