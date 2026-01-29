"""File export miscellaneous module."""

import json
from pathlib import Path


def save_file(
    fout: str | Path | None,
    content: list | dict,
    suffix: str | None = None,
) -> Path | list | dict:
    """Save content to file.

    Raises
    ------
    ValueError
        If the provided extension suffix don't match the one in the filename.

    """
    if fout is None:
        return content

    fout = Path(fout)

    if suffix and fout.suffix != suffix:
        raise ValueError(
            f'Output file name should ends with `{suffix}`: `{fout.name}` provided.'
        )

    if isinstance(content, list):
        _content = '\n'.join(content)
    elif isinstance(content, dict):
        _content = json.dumps(content, indent=2)
    else:
        raise TypeError(
            'Content type must be a `list` or a `dict`, '
            f'not a `{content.__class__.__name__}`'
        )

    fout.write_text(_content, encoding='utf-8')

    return fout
