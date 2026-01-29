"""JSON schema sub-module."""

import re
from collections import UserDict
from json import loads
from pathlib import Path

from jsonschema import validate

SCHEMA_FOLDER = Path(__file__).parent


class JsonSchema(UserDict):
    """JSON schema object."""

    def __init__(self, fname: str | Path):
        self.fname = Path(fname)
        self.data = loads(self.fname.read_text(encoding='utf-8'))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}> {self}'

    @property
    def name(self) -> str:
        """Schema file name."""
        return self.fname.stem

    @property
    def title(self) -> str:
        """Schema title description."""
        return self.data.get('title', '(undefined)')

    @property
    def version(self) -> int:
        """Schema version.

        At the moment this value is extracted from the title property.

        """
        if 'version' in self.data:
            return int(self.data['version'])

        for version in re.findall(r'v(\d+)', self.title):
            return int(version)

        return 0

    def validate(self, content: dict) -> None:
        """Validate content against the JSON schema."""
        validate(instance=content, schema=self.data)


MAJIS_SCHEMAS = {
    'ITL': [
        JsonSchema(SCHEMA_FOLDER / 'jsoc-itl-schema.json'),
        JsonSchema(SCHEMA_FOLDER / 'majis-itl-schema.json'),
    ],
    'OPL': [
        JsonSchema(SCHEMA_FOLDER / 'jsoc-opl-schema.json'),
    ],
}
