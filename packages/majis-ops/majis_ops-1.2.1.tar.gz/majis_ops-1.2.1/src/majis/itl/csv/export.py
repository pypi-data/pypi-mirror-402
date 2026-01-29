"""ITL CSV export module."""

from pathlib import Path

from planetary_coverage.events import Event, EventsDict, EventsList, EventWindow

from ...misc.events import flatten_events
from ...misc.export import save_file
from ...misc.time import fmt_datetime


@flatten_events
def save_itl_csv(
    fout: str | Path | None,
    *events: EventsList | EventsDict,
    ref: str | None = None,
    overlap: bool = False,
    sep: str = ';',
) -> Path:
    """Save ITL events to CSV.

    Note
    ----
    By default, ITL blocks must not overlap each other.
    This can be disable with `overlap=True`.

    """
    content = fmt_csv(events, ref=ref, sep=sep)

    return save_file(fout, content, suffix='.csv')


CSV_TIME_REL_KEYS = {
    't_start': ['OBS_START', 'OBS_START_REL'],
    't_end': ['OBS_END', 'OBS_END_REL'],
}


def get_header(
    blocks: list[list | dict] | EventsList | EventsDict,
    ref: str | dict | None = None,
) -> list:
    """Get CSV header.

    The keys are unique and ordered with the following rules:

    - If `OBS_NAME` is present, it will be placed first.

    - `t_start` and `t_end` are required and replaced by `OBS_START`
        and `OBS_END` and placed after `OBS_NAME` (if present).

    - if `ref` time is provided `OBS_START_REL` and `OBS_END_REL`
        are appended after `OBS_START` and `OBS_END`.

    - `COMMENTS` is present, it will always put last.

    """
    keys = dict.fromkeys(key for block in blocks for key in block)

    first, last = [], []
    if 'OBS_NAME' in keys:
        keys.pop('OBS_NAME')
        first.append('OBS_NAME')

    if 't_start' in keys:
        keys.pop('t_start')
        first.append('OBS_START')
    else:
        raise KeyError('Missing `t_start` keyword.')

    if 't_end' in keys:
        keys.pop('t_end')
        first.append('OBS_END')
    else:
        raise KeyError('Missing `t_end` keyword.')

    if ref:
        first.append('OBS_START_REL')
        first.append('OBS_END_REL')

    if 'COMMENTS' in keys:
        keys.pop('COMMENTS')
        last.append('COMMENTS')

    return first + list(keys) + last


def get_value(
    block: dict | Event | EventWindow,
    key: str,
    ref: str | None = None,
) -> str:
    """Format block value.

    This method extract the block value for a given property
    and re-format the datetime if necessary.

    Comments values are escaped with double quotes (`"..."`).

    """
    if key == 'OBS_START':
        return fmt_datetime(block['t_start'])

    if key in ['OBS_START', 'OBS_END']:
        return fmt_datetime(block['t_end'])

    if key == 'OBS_START_REL' and ref:
        return fmt_datetime(block['t_start'], ref=ref)

    if key == 'OBS_END_REL' and ref:
        return fmt_datetime(block['t_end'], ref=ref)

    value = str(block.get(key, ''))

    if key == 'COMMENTS':
        return f'"{value}"'

    return value


def fmt_csv(
    blocks: dict | EventsList | EventsDict,
    ref: str | None = None,
    sep: str = ';',
) -> str:
    """Format CSV format."""
    # Get unique header keys (ordered)
    header = get_header(blocks, ref=ref)

    # Create rows values with separator
    rows = [
        sep.join(get_value(block, key, ref=ref) for key in header) for block in blocks
    ]

    # Merge header and rows
    return ['#' + sep.join(header)] + rows
