"""Render graph settings, rows, and relationships back into GraphViz DOT notation."""

from collections import deque

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

    def render2(self) -> str:
        """Return a multiline GraphViz DOT string with people and families ordered as they appear in rows."""
        node_lines: deque[str] = deque()
        for row in self.rows:
            lines = self.render_row(row)
            node_lines.extend(lines)
        relationship_lines: deque[str] = deque()
        for relationship in self.relationships:
            clone = relationship.clone()
            clone.attrs["weight"] = "5"
            relationship_lines.append(relationship.source)

        sections = [
            "\n".join(self.settings.sources),
            "\n".join(node_lines),
            "\n".join(relationship_lines),
            "}",
        ]
        return "\n\n".join(sections)

    def render_row(self, row: Row) -> deque[str]:  # noqa: C901
        """Render people and families in a given row, but not their relationships."""
        row_lines: deque[str] = deque()
        if row.get_people_count():
            row_lines.append("{\nrank=same\n")
            for block in row.blocks:
                if block.people:
                    for person_w in block.people:
                        row_lines.append(person_w.person.source)
            people_lists = row.get_people_ids()
            prev_list_node = None
            for lst in people_lists:
                if len(lst) > 0:
                    if prev_list_node:
                        first_node = lst[0]
                        row_lines.append(f"{prev_list_node} -> {first_node} [ weight=20 style=invis ];")
                    if len(lst) > 1:
                        chain = " -> ".join(lst)
                        row_lines.append(chain + "[ weight=100 style=invis ];")
                    prev_list_node = lst[-1]
            row_lines.append("}\n")

        if row.get_family_count():
            row_lines.append("{\nrank=same\n")
            for block in row.blocks:
                if block.families:
                    for family_w in block.families:
                        row_lines.append(family_w.family.source)
            family_lists = row.get_family_ids()
            prev_list_node = None
            for lst in family_lists:
                if len(lst) > 0:
                    if prev_list_node:
                        first_node = lst[0]
                        row_lines.append(f"{prev_list_node} -> {first_node} [ weight=20 style=invis ];")
                    if len(lst) > 1:
                        chain = " -> ".join(lst)
                        row_lines.append(chain + "[ weight=100 style=invis ];")
                    prev_list_node = lst[-1]
            row_lines.append("}\n")
        return row_lines

    def render_block(
        self, block: Block, all_relationships: dict[str, Relationship], rendered_relationships: set[str]
    ) -> deque[str]:
        """Render cluster for one block."""
        cluster_lines: deque[str] = []
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

    def render_block2(  # noqa: C901
        self, block: Block, all_relationships: dict[str, Relationship], rendered_relationships: set[str]
    ) -> deque[str]:
        """Render cluster for one block."""
        cluster_lines: deque[str] = []
        cluster_id = block.create_cluster_id()
        # cluster_lines.append(f'subgraph cluster_{cluster_id}\n{{\nstyle="invis";\n')
        referenced_parents = set()
        if len(block.people) > 0:
            cluster_lines.append("{\nrank=same\n")
            for person_w in block.people:
                cluster_lines.append(person_w.person.source)
            people_ids = [p.id for p in block.people]
            chain = " -> ".join(people_ids)
            cluster_lines.append(chain + "[ weight=100 ];")
            cluster_lines.append("}\n")
        if len(block.families) > 0:
            cluster_lines.append("{\nrank=same\n")
            for family_w in block.families:
                cluster_lines.append(family_w.family.source)
            family_ids = [f.id for f in block.families]
            chain = " -> ".join(family_ids)
            if chain:
                cluster_lines.append(chain + "[ weight=100 ];")
            cluster_lines.append("}\n")
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
        # cluster_lines.append("}")
        return cluster_lines
