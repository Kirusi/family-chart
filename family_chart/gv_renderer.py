"""Render graph settings, rows, and relationships back into GraphViz DOT notation."""

from family_chart.graph_settings import GraphSettings
from family_chart.relationship import Relationship
from family_chart.row import Row


class GvRenderer:
    """Render a family chart back into GraphViz DOT notation."""

    settings: GraphSettings
    rows: list[Row]
    relationships: list[Relationship]

    def __init__(self, settings: GraphSettings, rows: list[Row], relationships: list[Relationship]):
        """Default constructor."""
        self.settings = settings
        self.rows = rows
        self.relationships = relationships

    def render(self) -> str:
        """Return a multiline GraphViz DOT string with people and families ordered as they appear in rows."""
        node_lines: list[str] = []
        for row in self.rows:
            people = [person_w for people_list in row.get_people() for person_w in people_list]
            for person_w in people:
                node_lines.append(person_w.person.source)
            families = [family_w for family_list in row.get_families() for family_w in family_list]
            for family_w in families:
                node_lines.append(family_w.family.source)
        relationship_lines = [relationship.source for relationship in self.relationships]

        sections = [
            "\n".join(self.settings.sources),
            "\n".join(node_lines),
            "\n".join(relationship_lines),
            "}",
        ]
        return "\n\n".join(sections)
