"""Directed edge between two nodes."""

from dataclasses import dataclass


@dataclass
class Relationship:
    """Directed edge between two nodes."""

    from_id: str
    to_id: str
    attrs: dict[str, str] | None = None
