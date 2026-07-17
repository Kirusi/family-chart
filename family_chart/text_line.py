"""One of the description lines in Person or Family classes."""

from dataclasses import dataclass


@dataclass
class TextLine:
    """One of the description lines in Person or Family classes."""

    text: str
    map_url: str | None = None
