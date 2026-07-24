"""Render graph settings, rows, and relationships back into GraphViz DOT notation."""

from family_chart.block import Block
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
        all_relationships = {}
        rendered_relationships = set()
        for rel in self.relationships:
            all_relationships[rel.lookup_key] = rel
        node_lines: list[str] = []
        for row in self.rows:
            for block in row.blocks:
                block_lines = self.render_block(block, all_relationships, rendered_relationships)
                node_lines.extend(block_lines)
        relationship_lines = []
        for relationship in self.relationships:
            if relationship.lookup_key not in rendered_relationships:
                relationship_lines.append(relationship.source)

        sections = [
            "\n".join(self.settings.sources),
            "\n".join(node_lines),
            "\n".join(relationship_lines),
            "}",
        ]
        return "\n\n".join(sections)

    def render_block(
        self, block: Block, all_relationships: dict[str, Relationship], rendered_relationships: set[str]
    ) -> list[str]:
        """Render cluster for one block."""
        cluster_lines: list[str] = []
        cluster_id = block.create_cluster_id()
        cluster_lines.append(f'subgraph cluster_{cluster_id}\n{{\nstyle="invis";\n')
        referenced_parents = set()
        for person_w in block.people:
            cluster_lines.append(person_w.person.source)
        for family_w in block.families:
            cluster_lines.append(family_w.family.source)
        for family_w in block.families:
            family_id = family_w.id
            for parent_id in family_w.parents:
                rel_id = f"{parent_id}_{family_id}"
                rel = all_relationships.get(rel_id)
                if rel is None:
                    raise ValueError(f"Cannot find relationship from '{parent_id}' to '{family_id}'")
                cluster_lines.append(rel.source)
                rendered_relationships.add(rel_id)
                referenced_parents.add(parent_id)
        for person_w in block.people:
            if len(block.families) > 0 and person_w.id not in referenced_parents:
                raise ValueError(f"Parent '{person_w.id}' is not referenced in cluster '{cluster_id}'")
        cluster_lines.append("}")
        return cluster_lines
