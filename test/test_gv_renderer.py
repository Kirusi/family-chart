import pytest

from family_chart.block import Block
from family_chart.family import Family
from family_chart.family_wrapper import FamilyWrapper
from family_chart.graph_settings import GraphSettings
from family_chart.gv_renderer import GvRenderer
from family_chart.person import Person
from family_chart.person_wrapper import PersonWrapper
from family_chart.relationship import Relationship
from family_chart.row import Row


def make_person_w(person_id: str, source: str | None = None) -> PersonWrapper:
    return PersonWrapper(Person(id=person_id, source=source if source is not None else f'"{person_id}"'))


def make_family_w(family_id: str, parents: list[str] | None = None, source: str | None = None) -> FamilyWrapper:
    family_w = FamilyWrapper(Family(id=family_id, source=source if source is not None else f'"{family_id}"'))
    family_w.parents = parents if parents is not None else []
    return family_w


class TestRender:
    def test_empty_renderer_returns_settings_and_closing_brace(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [], [])
        assert renderer.render() == "digraph GRAMPS_graph {\n\n\n\n\n\n}"

    def test_renders_settings_sources_first(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {", 'bgcolor="white"'])
        renderer = GvRenderer(settings, [], [])
        settings_lines = renderer.render().split("\n\n")[0]
        assert settings_lines == 'digraph GRAMPS_graph {\nbgcolor="white"'

    def test_ends_with_closing_brace(self):
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [], [])
        assert renderer.render().endswith("}")

    def test_row_with_no_blocks_contributes_nothing(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [Row()], [])
        assert renderer.render() == "digraph GRAMPS_graph {\n\n\n\n\n\n}"

    def test_block_with_single_person_and_no_family_wraps_person_in_cluster(self):
        block = Block(make_person_w("I1"))
        row = Row()
        row.add_block(block)
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [])
        result = renderer.render()
        assert result == 'digraph GRAMPS_graph {\n\nsubgraph cluster_I1\n{\nstyle="invis";\n\n"I1"\n}\n\n\n\n}'

    def test_cluster_id_is_sorted_but_node_lines_preserve_insertion_order(self):
        block = Block(make_person_w("I2"))
        block.add_person(make_person_w("I1"))
        row = Row()
        row.add_block(block)
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [])
        result = renderer.render()
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_I2\n{\nstyle="invis";\n\n"I2"\n"I1"\n}\n\n\n\n}'
        )

    def test_renders_parent_relationships_inside_the_cluster_of_their_family(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        family_w = make_family_w("F1", parents=["I1", "I2"])
        block = Block(person_w1)
        block.add_person(person_w2)
        block.add_family(family_w)
        row = Row()
        row.add_block(block)
        rel1 = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        rel2 = Relationship(from_id="I2", to_id="F1", source='"I2" -> "F1"')
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [rel1, rel2])
        result = renderer.render()
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_I2_F1\n{\nstyle="invis";\n\n'
            '"I1"\n"I2"\n"F1"\n"I1" -> "F1"\n"I2" -> "F1"\n}\n\n\n\n}'
        )

    def test_relationships_rendered_inside_a_cluster_are_excluded_from_the_trailing_section(self):
        person_w1 = make_person_w("I1")
        family_w = make_family_w("F1", parents=["I1"])
        block = Block(person_w1)
        block.add_family(family_w)
        row = Row()
        row.add_block(block)
        rel = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [rel])
        result = renderer.render()
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_F1\n{\nstyle="invis";\n\n'
            '"I1"\n"F1"\n"I1" -> "F1"\n}\n\n\n\n}'
        )

    def test_relationships_not_consumed_by_a_family_are_rendered_in_the_trailing_section(self):
        person_w1 = make_person_w("I1")
        family_w = make_family_w("F1", parents=["I1"])
        block = Block(person_w1)
        block.add_family(family_w)
        row = Row()
        row.add_block(block)
        parent_rel = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        child_rel = Relationship(from_id="F1", to_id="I3", source='"F1" -> "I3"')
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [parent_rel, child_rel])
        result = renderer.render()
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_F1\n{\nstyle="invis";\n\n'
            '"I1"\n"F1"\n"I1" -> "F1"\n}\n\n"F1" -> "I3"\n\n}'
        )

    def test_trailing_relationships_preserve_original_order(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        child_rel1 = Relationship(from_id="F1", to_id="I3", source='"F1" -> "I3"')
        child_rel2 = Relationship(from_id="F1", to_id="I4", source='"F1" -> "I4"')
        renderer = GvRenderer(settings, [], [child_rel1, child_rel2])
        result = renderer.render()
        assert result == 'digraph GRAMPS_graph {\n\n\n\n"F1" -> "I3"\n"F1" -> "I4"\n\n}'

    def test_raises_when_a_parent_relationship_cannot_be_found(self):
        person_w1 = make_person_w("I1")
        family_w = make_family_w("F1", parents=["I1"])
        block = Block(person_w1)
        block.add_family(family_w)
        row = Row()
        row.add_block(block)
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [row], [])
        with pytest.raises(ValueError) as ex:
            renderer.render()
        msg = str(ex.value)
        assert "Cannot find relationship" in msg
        assert "'I1'" in msg
        assert "'F1'" in msg

    def test_raises_when_a_person_in_the_block_is_not_a_parent_of_any_family(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        family_w = make_family_w("F1", parents=["I1"])
        block = Block(person_w1)
        block.add_person(person_w2)
        block.add_family(family_w)
        row = Row()
        row.add_block(block)
        rel = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [row], [rel])
        with pytest.raises(ValueError) as ex:
            renderer.render()
        msg = str(ex.value)
        assert "Parent 'I2' is not referenced in cluster" in msg
        assert "'I1_I2_F1'" in msg

    def test_does_not_raise_for_unreferenced_person_when_block_has_no_families(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        block = Block(person_w1)
        block.add_person(person_w2)
        row = Row()
        row.add_block(block)
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [])
        result = renderer.render()
        assert result == 'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_I2\n{\nstyle="invis";\n\n"I1"\n"I2"\n}\n\n\n\n}'

    def test_renders_clusters_in_row_then_block_order(self):
        row1 = Row()
        row1.add_block(Block(make_person_w("I1")))
        row2 = Row()
        row2.add_block(Block(make_person_w("I2")))
        row2.add_block(Block(make_person_w("I3")))
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row1, row2], [])
        result = renderer.render()
        assert result == (
            "digraph GRAMPS_graph {\n\n"
            'subgraph cluster_I1\n{\nstyle="invis";\n\n"I1"\n}\n'
            'subgraph cluster_I2\n{\nstyle="invis";\n\n"I2"\n}\n'
            'subgraph cluster_I3\n{\nstyle="invis";\n\n"I3"\n}\n\n\n\n}'
        )

    def test_multiple_families_in_one_block_are_all_included_in_the_cluster_id(self):
        person_w1 = make_person_w("I1")
        family_w1 = make_family_w("F1", parents=["I1"])
        family_w2 = make_family_w("F2", parents=["I1"])
        block = Block(person_w1)
        block.add_family(family_w1)
        block.add_family(family_w2)
        row = Row()
        row.add_block(block)
        rel1 = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        rel2 = Relationship(from_id="I1", to_id="F2", source='"I1" -> "F2"')
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [rel1, rel2])
        result = renderer.render()
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_F1_F2\n{\nstyle="invis";\n\n'
            '"I1"\n"F1"\n"F2"\n"I1" -> "F1"\n"I1" -> "F2"\n}\n\n\n\n}'
        )
