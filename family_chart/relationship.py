"""Directed edge between two nodes."""

import copy


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

    def clone(self) -> "Relationship":
        """Return a deep copy of this relationship."""
        return copy.deepcopy(self)

    def render(self) -> str:
        """Return this relationship as a GraphViz DOT edge line."""
        line = f'"{self.from_id}" -> "{self.to_id}"'
        if self.attrs:
            attr_str = " ".join(f"{key}={value}" for key, value in self.attrs.items())
            line += f" [ {attr_str} ]"
        return line + ";"
