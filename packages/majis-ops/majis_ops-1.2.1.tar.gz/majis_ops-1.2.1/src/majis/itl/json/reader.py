"""Majis ITL in JSON format sub-module."""

import json
from pathlib import Path

from planetary_coverage.events import EventWindow

from ...schema import MAJIS_SCHEMAS
from .mapping import JSON_MAPPING


def read_itl_json(fname: str | Path, fmt='ITL') -> list[EventWindow]:
    """Read ITL file in JSON format.

    ITL are validated against Juice SOC and Majis schema.

    """
    content = json.loads(Path(fname).read_text())

    for schema in MAJIS_SCHEMAS[fmt]:
        schema.validate(content)

    # Check filename match the one in the file
    filename = Path(content['header']['filename'])
    if not filename or filename.name != Path(fname).name:
        raise FileNotFoundError(filename)

    # Set default values
    defaults = {
        fmt: Path(filename),
    }

    return [
        EventWindow(
            obs['name'],
            parse_json(obs, defaults=defaults),
        )
        for obs in content['timeline']
        # Filter only Majis observations
        if obs['instrument'] == 'MAJIS'
    ]


def parse_json(obs: dict, defaults: dict | None = None) -> dict:
    """Map ITL JSON timeline keys to EPS event dictionary."""
    # Extract parameters if present
    params = obs.pop('parameters') if 'parameters' in obs else {}

    # Convert JSON keys to EPS keys
    content = {
        JSON_MAPPING.get(key, key.upper()): value for key, value in (obs | params).items()
    }

    # Add extra keys
    if 'OBSERVATION_TYPE' in content:
        content['PRIME'] = content['OBSERVATION_TYPE'] == 'PRIME'

    # Add default keys if not already present
    if defaults:
        for key, value in defaults.items():
            if key.upper() not in content:
                content[key.upper()] = value

    # Put comments last if present
    content['COMMENTS'] = content.pop('COMMENTS') if 'COMMENTS' in content else ''

    return content
