"""Majis ITL in EPS format sub-module."""

import re
from pathlib import Path

from numpy import datetime64

from planetary_coverage.events import EventWindow

from ...misc import get_datetime

# ITL prefix pattern: # INST - KEY=VALUE ... or # INST - COMMENTS : VALUE
ATTRIBUTES = re.compile(r'^#\s*\w+\s+-\s+(?P<values>.*)')
COMMENTS = re.compile(r'^#\s*\w+\s+-\s+COMMENTS?\s*:\s*(?P<value>.*)')
OBS_INST = re.compile(r'(?P<inst>[a-zA-Z]\w*)\s+OBS_(?:START|END)\s')
OBS_KEY = re.compile(r'OBS_(?:START|END)\s+(?P<key>\w*[a-zA-Z])(?:_\d+)?')


def read_itl_eps(
    fname: str | Path,
    refs: dict | str | list | None = None,
) -> list[EventWindow]:
    """Read ITL file in EPS (text) format.

    Note
    ----
    - The blocks can be prefixed with additional instrument parameters.

    - Blocks must be continuous, ie. consecutive OBS_START and OBS_END lines
      should have the same instrument observation name.
      If not an ValueError will be raised

    """
    lines = Path(fname).read_text().splitlines()

    return _parse_itl_eps(lines, refs=refs, filename=fname)


def _parse_itl_eps(
    lines: list[str],
    refs: dict | str | list | None = None,
    filename: str | Path | None = None,
) -> list[EventWindow]:
    """Parse ITL EPS content as EventWindows list."""
    events, attrs, comments, inst, key = [], {}, [], None, None

    for line in lines:
        if line.startswith('#'):
            comments, attrs = _parse_itl_eps_comment(line, comments, attrs)
            continue

        if ' OBS_START ' in line:
            start, inst, key = _parse_itl_eps_obs(line, refs)

            attrs['PRIME'] = '(PRIME=TRUE)' in line
            continue

        if ' OBS_END ' in line:
            end, _inst, _key = _parse_itl_eps_obs(line, refs)

            _check_obs_block(inst, key, _inst, _key)

            attrs['COMMENTS'] = ' / '.join(comments) if comments else None
            attrs['ITL'] = Path(filename) if filename else None

            # Compile the observation in an EventWindow object
            event = EventWindow(key, t_start=start, t_end=end, INSTRUMENT=inst, **attrs)
            events.append(event)

        attrs, comments, inst, key = {}, [], None, None

    return events


def _parse_itl_eps_comment(line: str, comments: list, attrs: dict) -> (list, dict):
    """Parse ITL EPS comment line.

    Extract new comments or attributes if present.

    """
    if match := COMMENTS.match(line):
        comments.append(match.group('value').strip())

    elif match := ATTRIBUTES.match(line):
        kv = [field.split('=', 1) for field in match.group('values').split(' ')]
        attrs |= dict(kv)

    return comments, attrs


def _parse_itl_eps_obs(
    line: str, refs: dict | str | list | None
) -> (datetime64, str, str):
    """Parse ITL EPS observation line."""
    dt = get_datetime(line, refs=refs)

    if not (match := OBS_INST.search(line)):
        raise ValueError(f'Missing instrument in: `{line}`')

    inst = match.group('inst')

    if not (match := OBS_KEY.search(line)):
        raise ValueError(f'Missing obs name in: `{line}`')

    key = match.group('key')

    return dt, inst, key


def _check_obs_block(inst: str, key: str, _inst: str, _key: str) -> bool:
    """Check observation block consistency.

    Raise a ValueError if the instrument or key mismatch in an observation block.

    """
    if _inst != inst:
        raise ValueError(f'Instrument block mismatch: `{inst}` / `{_inst}`')

    if _key != key:
        raise ValueError(f'Obs name block mismatch: `{key}` / `{_key}`')
