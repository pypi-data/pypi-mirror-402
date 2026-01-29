"""ITL EPS export module."""

from pathlib import Path

from planetary_coverage.events import EventsDict, EventsList, EventWindow

from ...misc import fmt_datetime
from ...misc.events import flatten_events
from ...misc.evf import ref_key
from ...misc.export import save_file


@flatten_events
def save_itl_eps(
    fout: str | Path | None,
    *events: EventsList | EventsDict,
    ref: str | None = None,
    overlap: bool = False,
    header: str = None,
) -> Path:
    """Save ITL events to a new EPS ITL file.

    Notes
    -----
    By default, ITL blocks must not overlap each other.
    This can be disable with `overlap=True`.

    Any custom header can be added.

    Reference datetime, if provided, will be reported after
    the header (if any provided).

    All the bocks will be commented if additional parameters
    are present in the Event objects.

    """
    content = [header, ''] if header else []

    if ref:
        ref = ref_key(ref)

        content += [
            '# Relative time reference:',
            f'# {ref[1]}  {ref[0]}',
            '',
        ]

    for event in events:
        content.extend(fmt_eps_comments(event))

        start, end = fmt_datetime(event.start, event.stop, ref=ref)

        inst = event['INSTRUMENT']
        prime = ' (PRIME=TRUE)' if event['PRIME'] else ''

        content.append(f'{start}  {inst}  OBS_START  {event.key}{prime}')
        content.append(f'{end}  {inst}  OBS_END    {event.key}')
        content.append('')  # empty line

    return save_file(fout, content, suffix='.itl')


EXCLUDED_KEYS = [
    'INSTRUMENT',
    'PRIME',
    'T_START',
    'T_END',
    'COMMENTS',
    'ITL',
]


def fmt_eps_comments(event: dict | EventWindow, max_length: int = 90) -> list[str]:
    """Format EPS comments."""
    if instrument := event.get('INSTRUMENT'):
        prefix = f'# {instrument.upper()} -'
    else:
        prefix = '#'

    comments, current = [], prefix
    for key, value in event.items():
        if key.upper() in EXCLUDED_KEYS:
            continue

        param = f'{key.upper()}={value}'

        # Append only if length is shorter than `max_length`
        if current == prefix or len(current) + len(param) <= max_length:
            current += f' {param}'
        else:
            comments.append(current)
            current = f'{prefix} {param}'

    # Add last parameter key-value is not empty
    if current != prefix:
        comments.append(current)

    # Add multi-lines comments (separated with a `/`)
    if 'COMMENTS' in event and event['COMMENTS']:
        for comment in event['COMMENTS'].split('/'):
            comments.append(f'{prefix} COMMENT: {comment.strip()}')

    return comments
