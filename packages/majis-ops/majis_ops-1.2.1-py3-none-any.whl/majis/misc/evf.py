"""Event file miscellaneous module."""

import re
from pathlib import Path

from planetary_coverage import datetime

# EVF key pattern: REF_NAME (COUNT = N)
EVF_KEY = r'(?P<ref>\w+)\s*\(COUNT\s*=\s*(?P<count>\d+)\)'


def ref_count(key: str) -> tuple[str, int]:
    """Extract reference name and count from EVF key."""
    if match := re.match(EVF_KEY, key):
        return match.group('ref').upper(), int(match.group('count'))

    raise KeyError(f'Invalid EVF key pattern: `{key}`. Should be `REF_NAME (COUNT = N)`')


def read_evf(fname: Path | str | list | None, comment: str = '#') -> dict | None:
    """Read and extract EVF references and times."""
    if fname is None:
        return None

    if str(fname).endswith('.evf'):
        lines = Path(fname).read_text().splitlines()
    elif isinstance(fname, list):
        lines = fname
    else:
        lines = fname.splitlines()

    refs = {}
    for line in lines:
        if not line.startswith(comment) and (line_strip := line.strip()):
            dt, key = line_strip.split(maxsplit=1)
            refs[ref_count(key)] = datetime(dt)

    return refs


def ref_key(ref: str | dict | tuple) -> tuple[str, datetime]:
    """Format relative datetime reference key."""
    if isinstance(ref, tuple):
        key, t_ref = ref

    else:
        if not isinstance(ref, dict):
            ref = read_evf(ref)

        if len(ref) > 1:
            raise ValueError(f'Only 1 reference could be provided, not {len(ref)}')

        (ref, count), t_ref = list(ref.items())[0]
        key = f'{ref} (COUNT = {count})'

    return key, t_ref
