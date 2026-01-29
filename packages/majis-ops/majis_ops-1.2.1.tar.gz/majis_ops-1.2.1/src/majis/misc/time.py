"""Time miscellaneous module."""

import re

from numpy import datetime64, timedelta64

from planetary_coverage import datetime

from .evf import EVF_KEY, read_evf, ref_key

# Timedelta pattern: 'EVENT_NAME (COUNT = N) [-+][JJJ.]HH:MM:SS[.MS]'
EVF_TD = (
    r'^' + EVF_KEY + r'\s+'
    r'(?P<sign>[+-])?'
    r'(?:(?P<day>\d+)\.)?'
    r'(?P<h>\d{2})'
    r':'
    r'(?P<m>\d{2})'
    r':'
    r'(?P<s>\d{2})'
    r'(?:\.(?P<ms>\d+))?'
)


def get_datetime(time: str, refs: dict | str | list | None = None) -> datetime64:
    """Datetime getter."""
    if match := re.match(EVF_TD, time):
        ref, count, sign, d, h, m, s, ms = match.groups()

        # Extract reference absolute time
        if refs and not isinstance(refs, dict):
            refs = read_evf(refs)

        if not refs or (key := (ref.upper(), int(count))) not in refs:
            raise KeyError(f'Unknown time reference: `{ref} (COUNT = {count})`')

        # Compute time delta to reference
        t_delta = (-1 if sign == '-' else 1) * (
            timedelta64(int(d) if d else 0, 'D')
            + timedelta64(int(h), 'h')
            + timedelta64(int(m), 'm')
            + timedelta64(int(s), 's')
            + (timedelta64(int(1_000 * float(f'0.{ms}')), 'ms') if ms else 0)
        )
        return refs[key] + t_delta

    t, *_ = str(time).strip().split()
    return datetime(t)


def fmt_datetime(
    *times: str | datetime64, ref: str | dict | tuple | None = None
) -> str | list[str]:
    """Format relative datetime for a time or a list of times."""
    if ref is not None:
        key, t_ref = ref_key(ref)

        t = [f'{key}  {fmt_timedelta(datetime(t) - t_ref)}' for t in times]

    else:
        t = [
            (datetime(t).item().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z').replace(
                '.000Z', 'Z'
            )
            for t in times
        ]

    return t if len(times) > 1 else t[0]


def fmt_timedelta(dt: timedelta64) -> str:
    """Format time delta."""
    t = abs(dt.item())
    h, r = divmod(t.seconds, 3600)
    m, s = divmod(r, 60)

    out = '-' if dt < 0 else '+'
    out += f'{t.days:03d}.'
    out += f'{h:02d}:{m:02d}:{s:02d}'
    out += f'.{t.microseconds // 1_000:03d}'

    return out
