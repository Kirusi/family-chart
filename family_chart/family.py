"""Family node in a family chart."""

from dataclasses import dataclass, field

from family_chart.text_line import TextLine


@dataclass
class Family:
    """Family node in a family chart."""

    id: str
    fillcolor: str | None = None
    text_lines: list[TextLine] = field(default_factory=list)
