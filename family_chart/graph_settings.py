"""Settings assigned to GraphViz dot graph."""

from dataclasses import dataclass, field


@dataclass
class GraphSettings:
    """Settings assigned to GraphViz dot graph."""

    attrs: dict[str, str] = field(default_factory=dict)  # top-level key=value pairs
    graph_attrs: dict[str, str] = field(default_factory=dict)  # graph [...] block
    edge_defaults: dict[str, str] = field(default_factory=dict)  # edge [...] block
    node_defaults: dict[str, str] = field(default_factory=dict)  # node [...] block
    metadata: dict[str, int] = field(default_factory=dict)  # "# Key: N" comment lines
    people_of_interest: list[tuple[str, str]] = field(default_factory=list)  # [(id, name)]
