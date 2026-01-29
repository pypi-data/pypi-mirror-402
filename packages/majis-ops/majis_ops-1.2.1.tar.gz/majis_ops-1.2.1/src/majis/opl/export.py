"""OPL generic export module."""

from pathlib import Path

from planetary_coverage.events import EventsDict, EventsList, EventWindow

from ..itl.export import save_itl_json
from ..misc import fmt_datetime
from ..misc.events import flatten_events
from ..misc.export import save_file


def save_opl(
    fout: str | Path | None,
    *events: EventsList | EventsDict,
    overlap: bool = False,
    **kwargs,
) -> Path:
    """Save OPL events to a new OPL file.

    Note
    ----
    By default, OPL blocks must not overlap each other.
    This can be disable with ``overlap=True``.

    """
    ext = Path(fout).suffix

    match ext:
        case '.csv':
            return save_opl_csv(
                fout,
                *events,
                overlap=overlap,
                **kwargs,
            )
        case '.json':
            return save_opl_json(
                fout,
                *events,
                overlap=overlap,
                **kwargs,
            )
        case _:
            raise NotImplementedError


@flatten_events
def save_opl_csv(
    fout: str | Path | None,
    *events: EventsList | EventsDict,
    overlap: bool = False,
    sep: str = ',',
):
    """Export OPL file in CSV format."""
    content = [sep.join(fmt_opl_csv(event)) for event in events]

    return save_file(fout, content, suffix='.csv')


def fmt_opl_csv(obs: EventWindow) -> list[str]:
    """OPL CSV line formatter.

    Warning
    -------
    Currently the OPL CSV don't have an explicit header.
    Here we assume that the header is as follow"

        # key, start, end, obs_key, instrument

    The initial ``key`` is composed of the following parameters:

        <instrument>_<observation_type>_<type>

    """
    return [
        '_'.join(
            [
                obs['INSTRUMENT'],
                obs['OBSERVATION_TYPE'],
                obs['TYPE'],
            ]
        ),
        fmt_datetime(obs.start),
        fmt_datetime(obs.stop),
        obs['OBS_KEY'],
        obs['INSTRUMENT'],
    ]


def save_opl_json(
    fout: str | Path | None,
    *events: EventsList | EventsDict,
    overlap: bool = False,
):
    """Export OPL file in JSON format.

    Note
    ----
    Re-use ITL JSON export with OPL schema instead.

    """
    return save_itl_json(fout, *events, overlap=overlap, fmt='OPL')
