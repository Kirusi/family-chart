import pytest

from family_chart.block import Block
from family_chart.family import Family
from family_chart.family_tree import FamilyTree
from family_chart.family_wrapper import FamilyWrapper
from family_chart.graph_settings import GraphSettings
from family_chart.gv_renderer import GvRenderer
from family_chart.organizer import Organizer
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


def make_person(person_id: str, gender: str | None = None, all_marriages: list[str] | None = None) -> Person:
    fillcolor = {"M": PersonWrapper.M_COLOR, "W": PersonWrapper.F_COLOR}.get(gender)
    return Person(id=person_id, fillcolor=fillcolor, all_marriages=all_marriages or [], source=f'"{person_id}"')


def make_family(family_id: str) -> Family:
    return Family(id=family_id, source=f'"{family_id}"')


def make_relationship(from_id: str, to_id: str) -> Relationship:
    return Relationship(from_id=from_id, to_id=to_id, source=f'"{from_id}" -> "{to_id}"')


def organize_and_render(
    people: list[Person],
    families: list[Family],
    relationships: list[Relationship],
    settings: GraphSettings | None = None,
    render_relationships: list[Relationship] | None = None,
) -> str:
    family_tree = FamilyTree(people, families, relationships)
    rows = Organizer(family_tree).organize_tree()
    settings = settings if settings is not None else GraphSettings(sources=["digraph GRAMPS_graph {"])
    renderer = GvRenderer(settings, rows, render_relationships if render_relationships is not None else relationships)
    return renderer.render()


class TestRender:
    def test_empty_renderer_returns_settings_and_closing_brace(self):
        result = organize_and_render([], [], [])
        assert result == "digraph GRAMPS_graph {\n\n\n\n\n\n}"

    def test_renders_settings_sources_first(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {", 'bgcolor="white"'])
        result = organize_and_render([], [], [], settings=settings)
        settings_lines = result.split("\n\n")[0]
        assert settings_lines == 'digraph GRAMPS_graph {\nbgcolor="white"'

    def test_ends_with_closing_brace(self):
        result = organize_and_render([], [], [], settings=GraphSettings(sources=[]))
        assert result.endswith("}")

    def test_row_with_no_blocks_contributes_nothing(self):
        settings = GraphSettings(sources=["digraph GRAMPS_graph {"])
        renderer = GvRenderer(settings, [Row()], [])
        assert renderer.render() == "digraph GRAMPS_graph {\n\n\n\n\n\n}"

    def test_block_with_single_person_and_no_family_wraps_person_in_cluster(self):
        result = organize_and_render([make_person("I1")], [], [])
        assert result == 'digraph GRAMPS_graph {\n\nsubgraph cluster_I1\n{\nstyle="invis";\n\n"I1"\n}\n\n\n\n}'

    def test_cluster_id_is_sorted_but_node_lines_preserve_insertion_order(self):
        # I2 is the man, so Organizer picks him as the block's anchor and inserts I1 after
        # him even though I1 sorts first alphabetically into the cluster id.
        people = [
            make_person("I2", gender="M", all_marriages=["F1"]),
            make_person("I1", gender="W", all_marriages=["F1"]),
        ]
        relationships = [make_relationship("I2", "F1"), make_relationship("I1", "F1")]
        result = organize_and_render(people, [make_family("F1")], relationships)
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_I2_F1\n{\nstyle="invis";\n\n'
            '"I2"\n"I1"\n"F1"\n"I2" -> "F1"\n"I1" -> "F1"\n}\n\n\n\n}'
        )

    def test_renders_parent_relationships_inside_the_cluster_of_their_family(self):
        people = [
            make_person("I1", gender="M", all_marriages=["F1"]),
            make_person("I2", gender="W", all_marriages=["F1"]),
        ]
        relationships = [make_relationship("I1", "F1"), make_relationship("I2", "F1")]
        result = organize_and_render(people, [make_family("F1")], relationships)
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_I2_F1\n{\nstyle="invis";\n\n'
            '"I1"\n"I2"\n"F1"\n"I1" -> "F1"\n"I2" -> "F1"\n}\n\n\n\n}'
        )

    def test_relationships_rendered_inside_a_cluster_are_excluded_from_the_trailing_section(self):
        people = [make_person("I1", gender="M", all_marriages=["F1"])]
        relationships = [make_relationship("I1", "F1")]
        result = organize_and_render(people, [make_family("F1")], relationships)
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_F1\n{\nstyle="invis";\n\n'
            '"I1"\n"F1"\n"I1" -> "F1"\n}\n\n\n\n}'
        )

    def test_relationships_not_consumed_by_a_family_are_rendered_in_the_trailing_section(self):
        people = [make_person("I1", gender="M", all_marriages=["F1"]), make_person("I3")]
        relationships = [make_relationship("I1", "F1"), make_relationship("F1", "I3")]
        result = organize_and_render(people, [make_family("F1")], relationships)
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_F1\n{\nstyle="invis";\n\n'
            '"I1"\n"F1"\n"I1" -> "F1"\n}\n'
            'subgraph cluster_I3\n{\nstyle="invis";\n\n"I3"\n}\n\n"F1" -> "I3"\n\n}'
        )

    def test_trailing_relationships_preserve_original_order(self):
        # Neither parent of F1 is known, so its children are unclaimed and both the family
        # and children render as their own clusters, with the two child relationships trailing.
        people = [make_person("I3"), make_person("I4")]
        relationships = [make_relationship("F1", "I3"), make_relationship("F1", "I4")]
        result = organize_and_render(people, [make_family("F1")], relationships)
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_F1\n{\nstyle="invis";\n\n"F1"\n}\n'
            'subgraph cluster_I3\n{\nstyle="invis";\n\n"I3"\n}\n'
            'subgraph cluster_I4\n{\nstyle="invis";\n\n"I4"\n}\n\n"F1" -> "I3"\n"F1" -> "I4"\n\n}'
        )

    def test_raises_when_a_parent_relationship_cannot_be_found(self):
        people = [make_person("I1", gender="M", all_marriages=["F1"])]
        relationships = [make_relationship("I1", "F1")]
        with pytest.raises(ValueError) as ex:
            organize_and_render(
                people, [make_family("F1")], relationships, settings=GraphSettings(sources=[]), render_relationships=[]
            )
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
        # I1 and I2 are a married couple whose two unmarried children, I3 and I4, land
        # as separate blocks in the next row - exercising both row order and block order.
        people = [
            make_person("I1", gender="M", all_marriages=["F1"]),
            make_person("I2", gender="W", all_marriages=["F1"]),
            make_person("I3"),
            make_person("I4"),
        ]
        relationships = [
            make_relationship("I1", "F1"),
            make_relationship("I2", "F1"),
            make_relationship("F1", "I3"),
            make_relationship("F1", "I4"),
        ]
        result = organize_and_render(people, [make_family("F1")], relationships)
        assert result == (
            "digraph GRAMPS_graph {\n\n"
            'subgraph cluster_I1_I2_F1\n{\nstyle="invis";\n\n"I1"\n"I2"\n"F1"\n"I1" -> "F1"\n"I2" -> "F1"\n}\n'
            'subgraph cluster_I3\n{\nstyle="invis";\n\n"I3"\n}\n'
            'subgraph cluster_I4\n{\nstyle="invis";\n\n"I4"\n}\n\n"F1" -> "I3"\n"F1" -> "I4"\n\n}'
        )

    def test_multiple_families_in_one_block_are_all_included_in_the_cluster_id(self):
        # I1 married twice (F1, F2) with no recorded spouse in either family, so Organizer
        # keeps both marriages in I1's own block instead of pulling in a second person.
        people = [make_person("I1", gender="M", all_marriages=["F1", "F2"])]
        relationships = [make_relationship("I1", "F1"), make_relationship("I1", "F2")]
        result = organize_and_render(people, [make_family("F1"), make_family("F2")], relationships)
        assert result == (
            'digraph GRAMPS_graph {\n\nsubgraph cluster_I1_F1_F2\n{\nstyle="invis";\n\n'
            '"I1"\n"F1"\n"F2"\n"I1" -> "F1"\n"I1" -> "F2"\n}\n\n\n\n}'
        )


class TestRenderBlock:
    def test_returns_cluster_lines_for_a_single_person_with_no_families(self):
        block = Block(make_person_w("I1"))
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [], [])
        result = renderer.render_block(block, {}, set())
        assert result == ['subgraph cluster_I1\n{\nstyle="invis";\n', '"I1"', "}"]

    def test_marks_consumed_parent_relationships_as_rendered(self):
        person_w1 = make_person_w("I1")
        family_w = make_family_w("F1", parents=["I1"])
        block = Block(person_w1)
        block.add_family(family_w)
        rel = Relationship(from_id="I1", to_id="F1", source='"I1" -> "F1"')
        all_relationships = {"I1_F1": rel}
        rendered_relationships: set[str] = set()
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [], [])
        renderer.render_block(block, all_relationships, rendered_relationships)
        assert rendered_relationships == {"I1_F1"}

    def test_raises_when_a_parent_relationship_is_missing_from_all_relationships(self):
        person_w1 = make_person_w("I1")
        family_w = make_family_w("F1", parents=["I1"])
        block = Block(person_w1)
        block.add_family(family_w)
        settings = GraphSettings(sources=[])
        renderer = GvRenderer(settings, [], [])
        with pytest.raises(ValueError) as ex:
            renderer.render_block(block, {}, set())
        msg = str(ex.value)
        assert "Cannot find relationship from 'I1' to 'F1'" in msg
