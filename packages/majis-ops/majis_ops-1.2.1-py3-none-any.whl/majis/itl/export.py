"""ITL export module."""

from pathlib import Path

from planetary_coverage.events import EventsDict, EventsList

from .csv import save_itl_csv
from .eps import save_itl_eps
from .json import save_itl_json
from .timeline import save_itl_xlsm


def save_itl(
    fout: str | Path | None,
    *events: EventsList | EventsDict,
    ref: str | dict | None = None,
    overlap: bool = False,
    **kwargs,
) -> Path:
    """Save ITL events to a new ITL file.

    Note
    ----
    By default, ITL blocks must not overlap each other.
    This can be disable with ``overlap=True``.

    """
    ext = Path(fout).suffix

    match ext:
        case '.itl':
            return save_itl_eps(
                fout,
                *events,
                ref=ref,
                overlap=overlap,
                **kwargs,
            )
        case '.json':
            return save_itl_json(
                fout,
                *events,
                ref=ref,
                overlap=overlap,
                **kwargs,
            )
        case '.csv':
            return save_itl_csv(
                fout,
                *events,
                ref=ref,
                overlap=overlap,
                **kwargs,
            )
        case '.xls' | '.xlsx' | '.xlsm':
            return save_itl_xlsm(
                fout,
                *events,
                ca_ref=ref,
                overlap=overlap,
                **kwargs,
            )
        case _:
            raise NotImplementedError
