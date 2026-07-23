"""Directed edge between two nodes."""

from dataclasses import dataclass


@dataclass
class Relationship:
    """Directed edge between two nodes."""

    from_id: str
    to_id: str
    attrs: dict[str, str] | None
    source: str
    lookup_key: str

    def __init__(self, from_id: str, to_id: str, attrs: dict[str, str] | None = None, source: str = ""):
        """Default constructor."""
        self.from_id = from_id
        self.to_id = to_id
        self.attrs = attrs
        self.source = source
        self.lookup_key = f"{from_id}_{to_id}"
