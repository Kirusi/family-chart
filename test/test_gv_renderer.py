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


def make_family_w(family_id: str, source: str | None = None) -> FamilyWrapper:
    return FamilyWrapper(Family(id=family_id, source=source if source is not None else f'"{family_id}"'))


class TestRender:
    def test_empty_renderer_returns_settings_and_closing_brace(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [], [])
        assert renderer.render() == "digraph GRAMPS_graph {\n\n\n\n\n\n}"

    def test_renders_people_and_families_in_row_order(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        family_w1 = make_family_w("F1")
        block1 = Block(person_w1)
        block1.add_family(family_w1)
        block2 = Block(person_w2)
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [row], [])
        result = renderer.render()
        assert result == 'digraph GRAMPS_graph {\n\n"I1"\n"I2"\n"F1"\n\n\n\n}'

    def test_orders_nodes_by_row_then_block(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        person_w3 = make_person_w("I3")
        row1 = Row()
        row1.add_block(Block(person_w1))
        row2 = Row()
        row2.add_block(Block(person_w2))
        row2.add_block(Block(person_w3))
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [row1, row2], [])
        node_lines = renderer.render().split("\n\n")[1]
        assert node_lines == '"I1"\n"I2"\n"I3"'

    def test_renders_relationships_after_nodes(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        relationship = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        renderer = GvRenderer(settings, [], [relationship])
        result = renderer.render()
        assert result == 'digraph GRAMPS_graph {\n\n\n\n"I1" -> "F1"\n\n}'

    def test_renders_multiple_relationships_in_order(self):
        settings = GraphSettings(sources=[])
        relationship1 = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        relationship2 = Relationship(from_id="I2", to_id="F1", source='"I2" -> "F1"')
        renderer = GvRenderer(settings, [], [relationship1, relationship2])
        relationship_lines = renderer.render().split("\n\n")[2]
        assert relationship_lines == '"I1" -> "F1"\n"I2" -> "F1"'

    def test_ends_with_closing_brace(self):
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [], [])
        assert renderer.render().endswith("}")

    def test_renders_settings_sources_first(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {", 'bgcolor="white"'])
        renderer = GvRenderer(settings, [], [])
        settings_lines = renderer.render().split("\n\n")[0]
        assert settings_lines == 'digraph GRAMPS_graph {\nbgcolor="white"'

    def test_block_with_no_people_or_families_contributes_nothing(self):
        row = Row()
        row.add_block(Block())
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [row], [])
        node_lines = renderer.render().split("\n\n")[1]
        assert node_lines == ""
