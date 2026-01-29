"""ITL JSON export module."""

import getpass
from datetime import datetime
from pathlib import Path

from planetary_coverage.events import Event, EventsDict, EventsList

from ...misc import fmt_datetime
from ...misc.events import flatten_events
from ...misc.export import save_file
from ...schema import MAJIS_SCHEMAS
from .mapping import EPS_MAPPING_OBS, EPS_MAPPING_OBS_EXTRA, EPS_MAPPING_PARAMS


@flatten_events
def save_itl_json(
    fout: str | Path | None,
    *events: EventsList | EventsDict,
    ref: str | None = None,
    overlap: bool = False,
    fmt='ITL',
) -> Path | dict:
    """Save ITL events to a new JSON ITL file.

    Notes
    -----
    By default, ITL blocks must not overlap each other.
    This can be disable with `overlap=True`.

    """
    if ref is not None:
        raise NotImplementedError

    content = {
        'header': get_header(fout, fmt=fmt),
        'timeline': [fmt_json(event) for event in events],
    }

    for schema in MAJIS_SCHEMAS[fmt]:
        schema.validate(content)

    return save_file(fout, content, suffix='.json')


def get_header(fout: str | Path | None = None, fmt='ITL') -> dict:
    """Get JSON header."""
    return {
        'filename': f'{fmt}_.json' if fout is None else Path(fout).name,
        'creation_date': fmt_datetime(datetime.now()),
        'author': getpass.getuser(),
    }


EXCLUDED_KEYS = [
    'ITL',
    'OPL',
    'PRIME',
]


def fmt_json(event: Event) -> dict:
    """Format an event into JSON timeline dictionary."""
    content, params = {'name': event.key}, {}
    for eps_key, value in event.items():
        if eps_key in EXCLUDED_KEYS:
            continue

        if eps_key in EPS_MAPPING_OBS:
            json_key, fmt = EPS_MAPPING_OBS[eps_key]
            content[json_key] = fmt(value)

        elif eps_key.upper() in EPS_MAPPING_OBS_EXTRA:
            json_key, fmt = EPS_MAPPING_OBS_EXTRA[eps_key.upper()]
            content[json_key] = fmt(value) if value is not None else None

        elif eps_key in EPS_MAPPING_PARAMS:
            json_key, fmt = EPS_MAPPING_PARAMS[eps_key]
            params[json_key] = fmt(value)

        else:
            params[eps_key.lower()] = value

    # Add observation type if missing
    if 'type' not in content:
        content['type'] = 'OBSERVATION'

    # Append parameters after the other obs parameters
    content['parameters'] = params

    # Put comment at the end of the block (if present)
    if 'comment' in content:
        content['comment'] = content.pop('comment')

    return content
