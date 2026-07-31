import pytest

from family_chart.block import Block
from family_chart.family import Family
from family_chart.family_tree import FamilyTree
from family_chart.organizer import BlockQueueItem, Organizer, PersonWrapper
from family_chart.person import Person
from family_chart.relationship import Relationship
from family_chart.text_line import TextLine
from family_chart.utils import Utils


def test_parse_color_unknown():
    assert PersonWrapper.parse_color("#123456") == "N"


def test_parse_color_none():
    assert PersonWrapper.parse_color(None) == "N"


class TestConstructor:
    def test_unknown_family_used_in_all_marriages_and_in_relationships(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [],
            [
                Relationship(from_id="I1", to_id="F1"),
            ],
        )
        with pytest.raises(ValueError) as ex:
            _ = Organizer(t)
        msg = str(ex)
        assert "from 'I1'" in msg
        assert "to 'F1'" in msg
        assert "does not reference any known family" in msg

    def test_unknown_family_used_only_in_relationships(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
            ],
            [],
            [Relationship(from_id="I1", to_id="F1")],
        )
        try:
            _ = Organizer(t)
            raise AssertionError("No Exception was raised")
        except ValueError as ex:
            msg = str(ex)
        assert "from 'I1'" in msg
        assert "to 'F1'" in msg
        assert "does not reference any known family" in msg

    def test_unknown_to_person(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family("F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="F1", to_id="I2")],
        )
        with pytest.raises(ValueError) as ex:
            _ = Organizer(t)
        msg = str(ex)
        assert "from 'F1'" in msg
        assert "to 'I2'" in msg
        assert "not listed among person nodes" in msg

    def test_unknown_from_person(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family("F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        with pytest.raises(ValueError) as ex:
            _ = Organizer(t)
        msg = str(ex)
        assert "from 'I2'" in msg
        assert "to 'F1'" in msg
        assert "not listed among person nodes" in msg


class TestValidatePreliminaryAssignments:
    def make_organizer(self):
        return Organizer(
            FamilyTree(
                [
                    Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
                    Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
                ],
                [Family(id="F1")],
                [],
            )
        )

    def test_all_nodes_assigned_passes(self):
        o = self.make_organizer()
        o.people["I1"].level = 0
        o.people["I2"].level = 0
        o.families["F1"].level = 1
        assert o.validate_preliminary_assignments() is None

    def test_unassigned_person_and_family_are_reported(self):
        # I2 and F1 keep their default level and land in the unassigned lists.
        o = self.make_organizer()
        o.people["I1"].level = 0
        with pytest.raises(ValueError) as ex:
            o.validate_preliminary_assignments()
        payload = Utils.extract_json(str(ex))
        assert payload["unassigned_people"] == ["I2"]
        assert payload["unassigned_families"] == ["F1"]
        assert payload["assigned_people"] == ["I1"]
        assert payload["assigned_families"] == []


class TestValidateFinalAssignments:
    def test_gap_in_levels_raises_value_error(self):
        # Levels 0 and 2 are populated but level 1 is left empty, simulating a broken
        # assignment that validate_final_assignments is meant to catch.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
            ],
            [],
            [],
        )
        o = Organizer(t)
        o.people["I1"].level = 0
        o.people["I2"].level = 2
        with pytest.raises(ValueError) as ex:
            o.validate_final_assignments()
        msg = str(ex.value)
        assert "No nodes are placed at level 1" in msg
        assert "Level structure is" in msg

    def test_mixed_node_types_at_same_level_raises_value_error(self):
        # Force a person and a family onto the same level to simulate a broken assignment;
        # this can't happen through normal traversal since person and family levels always
        # differ by at least one hop.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        o.people["I1"].level = 0
        o.families["F1"].level = 0
        with pytest.raises(ValueError) as ex:
            o.validate_final_assignments()
        msg = str(ex.value)
        assert "Nodes at level '0' are expected to be of 'person' type" in msg
        assert "Actual nodes are" in msg


class TestFindOtherParent:
    def test_unknown_family_raises_value_error(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.find_other_parent("unknown", "I1")
        msg = str(ex.value)
        assert "'unknown'" in msg
        assert "not a known family" in msg

    def test_two_parents_returns_the_other_one(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        assert o.find_other_parent("F1", "I1") == "I2"
        assert o.find_other_parent("F1", "I2") == "I1"

    def test_single_parent_returns_none(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        assert o.find_other_parent("F1", "I1") is None

    def test_person_not_a_parent_raises_value_error(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.find_other_parent("F1", "I2")
        msg = str(ex.value)
        assert "'I2'" in msg
        assert "'F1'" in msg


class TestFilterMarriagesByLevel:
    def test_empty_marriage_ids_returns_empty_list(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        assert o.filter_marriages_by_level([], 1, set()) == []

    def test_family_at_expected_level_is_included(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.filter_marriages_by_level(["F1"], 1, set())
        assert [f.id for f in res] == ["F1"]

    def test_family_at_unexpected_level_is_excluded(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.filter_marriages_by_level(["F1"], 2, set())
        assert res == []

    def test_already_reviewed_family_is_excluded(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.filter_marriages_by_level(["F1"], 1, {"F1"})
        assert res == []

    def test_unknown_family_raises_value_error(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.filter_marriages_by_level(["F ghost"], 1, set())
        msg = str(ex.value)
        assert "Family 'F ghost'" in msg
        assert "is unknown" in msg

    def test_mix_of_reviewed_wrong_level_unknown_and_matching_families(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("man")],
                    all_marriages=["F1", "F2", "F3"],
                ),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I1", to_id="F3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        # F1 is already reviewed, F2 is forced to the wrong level, F3 matches and should survive.
        o.families["F2"].level += 1
        res = o.filter_marriages_by_level(["F1", "F2", "F3"], 1, {"F1"})
        assert [f.id for f in res] == ["F3"]

    def test_preserves_input_order(self):
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1", "F2"]
                ),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.filter_marriages_by_level(["F2", "F1"], 1, set())
        assert [f.id for f in res] == ["F2", "F1"]


class TestOrderMarriages:
    def test_unknown_person_raises_value_error(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        with pytest.raises(ValueError) as ex:
            o.order_marriages("unknown", reviewed_people, reviewed_families)
        msg = str(ex.value)
        assert "'unknown'" in msg
        assert "not a known person" in msg
        assert reviewed_people == set()
        assert reviewed_families == set()

    def test_person_already_reviewed_returns_none(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = {"I1"}
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert res is None
        assert reviewed_people == {"I1"}
        assert reviewed_families == set()

    def test_no_marriages(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1"]
        assert res.families == []
        assert reviewed_people == {"I1"}
        assert reviewed_families == set()

    def test_one_marriage_family_already_reviewed_is_skipped(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = {"F1"}
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1"]
        assert res.families == []
        assert reviewed_people == {"I1"}
        assert reviewed_families == {"F1"}

    def test_one_marriage_no_other_parent(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1"]
        assert [f.id for f in res.families] == ["F1"]
        assert reviewed_people == {"I1"}
        assert reviewed_families == {"F1"}

    def test_one_marriage_man_places_other_parent_to_the_right(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1", "I2"]
        assert [f.id for f in res.families] == ["F1"]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1"}

    def test_one_marriage_woman_places_other_parent_to_the_left(self):
        t = FamilyTree(
            [
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I2", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1", "I2"]
        assert [f.id for f in res.families] == ["F1"]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1"}

    def test_one_marriage_other_parent_already_reviewed_is_not_added_again(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = {"I2"}
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1"]
        assert [f.id for f in res.families] == ["F1"]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1"}

    def test_one_marriage_woman_other_parent_already_reviewed_is_not_added_again(self):
        t = FamilyTree(
            [
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = {"I1"}
        reviewed_families = set()
        res = o.order_marriages("I2", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I2"]
        assert [f.id for f in res.families] == ["F1"]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1"}

    def test_multiple_marriages_orders_families_and_other_parents(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("man")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        # First other parent found is inserted left of the person; later ones are appended.
        assert [p.id for p in res.people] == ["I2", "I1", "I3"]
        assert [f.id for f in res.families] == ["F1", "F2"]
        assert reviewed_people == {"I1", "I2", "I3"}
        assert reviewed_families == {"F1", "F2"}

    def test_multiple_marriages_woman_with_four_marriages_orders_families_and_other_parents(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2", "F3", "F4"],
                ),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
                Person(id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F3"]),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F4"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="F4")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I1", to_id="F3"),
                Relationship(from_id="I4", to_id="F3"),
                Relationship(from_id="I1", to_id="F4"),
                Relationship(from_id="I5", to_id="F4"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        # First other parent found is inserted left of the person; later ones are appended.
        assert [p.id for p in res.people] == ["I2", "I1", "I3", "I4", "I5"]
        assert [f.id for f in res.families] == ["F1", "F2", "F3", "F4"]
        assert reviewed_people == {"I1", "I2", "I3", "I4", "I5"}
        assert reviewed_families == {"F1", "F2", "F3", "F4"}

    def test_multiple_marriages_skips_already_reviewed_family(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("man")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = {"F1"}
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1", "I3"]
        assert [f.id for f in res.families] == ["F2"]
        assert reviewed_people == {"I1", "I3"}
        assert reviewed_families == {"F1", "F2"}

    def test_multiple_marriages_skips_already_reviewed_family_f2(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("man")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = {"F2"}
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1", "I2"]
        assert [f.id for f in res.families] == ["F1"]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1", "F2"}

    def test_multiple_marriages_first_family_with_no_other_parent_still_inserts_second_on_the_left(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("man")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I3", "I1"]
        assert [f.id for f in res.families] == ["F1", "F2"]
        assert reviewed_people == {"I1", "I3"}
        assert reviewed_families == {"F1", "F2"}

    def test_cycles_in_marriages(self):
        # I1 and I4 share marriage F4, I2 and I3 share marriage F2, alongside I1/I2's F1
        # and I3/I4's F3 - order_marriages must handle these criss-crossing marriages
        # without stalling or double-processing.
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1", "F4"]
                ),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
                Person(
                    id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("woman")], all_marriages=["F3", "F4"]
                ),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="F4")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="I4", to_id="F3"),
                Relationship(from_id="I1", to_id="F4"),
                Relationship(from_id="I4", to_id="F4"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        block = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I3", "I2", "I1", "I4"]
        assert [f.id for f in block.families] == ["F2", "F1", "F4", "F3"]
        assert reviewed_people == {"I1", "I2", "I3", "I4"}
        assert reviewed_families == {"F1", "F2", "F3", "F4"}

    def test_marriage_referencing_unknown_family_raises_value_error(self):
        # Organizer's constructor filters all_marriages down to known families, so this state
        # can't arise through normal construction; corrupt it directly to exercise the guard.
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        o.people["I1"].person.all_marriages.append("F ghost")
        reviewed_people = set()
        reviewed_families = set()
        with pytest.raises(ValueError) as ex:
            o.order_marriages("I1", reviewed_people, reviewed_families)
        msg = str(ex.value)
        assert "Family 'F ghost'" in msg
        assert "is unknown" in msg

    def test_marriage_family_at_unexpected_level_is_filtered_out(self):
        # A marriage's family only diverges from person level + 1 under malformed level
        # assignment; force that state directly to exercise the level-mismatch filter.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        o.families["F1"].level += 1
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1"]
        assert res.families == []
        assert reviewed_people == {"I1"}
        assert reviewed_families == set()

    def test_marriage_family_at_unexpected_level_is_filtered_out_alongside_valid_marriage(self):
        # A marriage's family only diverges from person level + 1 under malformed level
        # assignment; force that state directly to exercise the level-mismatch filter.
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1", "F2"]
                ),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F3"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        o.families["F1"].level += 1
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I1", "I3"]
        assert [f.id for f in res.families] == ["F2"]
        assert reviewed_people == {"I1", "I3"}
        assert reviewed_families == {"F2"}


class TestOrderMarriagesFromQueue:
    def test_empty_queue_is_a_no_op(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        block = Block(o.people["I1"])
        reviewed_people = {"I1"}
        reviewed_families = set()
        o.order_marriages_from_queue(block, 1, [], reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1"]
        assert block.families == []
        assert reviewed_people == {"I1"}
        assert reviewed_families == set()

    def test_person_with_no_other_marriages_does_nothing(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2"]
        assert [f.id for f in block.families] == ["F1"]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1"}

    def test_adds_spouse_of_spouse_and_marks_reviewed(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2", "I3"]
        assert [f.id for f in block.families] == ["F1", "F2"]
        assert reviewed_people == {"I1", "I2", "I3"}
        assert reviewed_families == {"F1", "F2"}

    def test_propagates_transitively_through_chain_of_spouses(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
                Person(
                    id="I3",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("man")],
                    all_marriages=["F2", "F3"],
                ),
                Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F3"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="I4", to_id="F3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        # Queued spouses of spouses are themselves re-queued, so a whole chain gets pulled in, not just one hop.
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2", "I3", "I4"]
        assert [f.id for f in block.families] == ["F1", "F2", "F3"]
        assert reviewed_people == {"I1", "I2", "I3", "I4"}
        assert reviewed_families == {"F1", "F2", "F3"}

    def test_direction_left_inserts_before_the_anchor(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person_relatively(o.people["I2"], "I1", "L")
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="L")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I3", "I2", "I1"]
        assert [f.id for f in block.families] == ["F2", "F1"]
        assert reviewed_people == {"I1", "I2", "I3"}
        assert reviewed_families == {"F1", "F2"}

    def test_second_extra_marriage_is_inserted_in_chronological_order(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2", "F3"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
                Person(id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F3"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I2", to_id="F3"),
                Relationship(from_id="I4", to_id="F3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2", "I3", "I4"]
        assert [f.id for f in block.families] == ["F1", "F2", "F3"]
        assert reviewed_people == {"I1", "I2", "I3", "I4"}
        assert reviewed_families == {"F1", "F2", "F3"}

    def test_does_not_mutate_the_original_queue_argument(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        original_queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, original_queue, {"I1", "I2"}, {"F1"})
        assert original_queue == [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]

    def test_missing_anchor_person_in_block_raises_value_error(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        # I2 was never actually added to the block, so it can't serve as an anchor.
        block = Block(o.people["I1"])
        reviewed_people = {"I1"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        with pytest.raises(ValueError) as ex:
            o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        msg = str(ex.value)
        assert "'I2'" in msg
        assert "not found in the block" in msg

    def test_second_marriage_with_no_other_parent_adds_family_without_spouse(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2"]
        assert [f.id for f in block.families] == ["F1", "F2"]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1", "F2"}

    def test_unknown_person_in_queue_raises_value_error(self):
        # self.people.get(person_id) returns None rather than raising for a missing id,
        # so this test exercises that "is None" guard directly with an id that was
        # never registered in the first place.
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        reviewed_people = {"I1"}
        reviewed_families = set()
        queue = [BlockQueueItem(person_id="ghost", family_id="F1", direction="R")]
        with pytest.raises(ValueError) as ex:
            o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        msg = str(ex)
        assert "Person 'ghost'" in msg
        assert "unknown" in msg

    def test_missing_person_referenced_in_queue_raises_value_error(self):
        # self.people[person_id] only ever yields None if the dict itself is corrupted;
        # corrupt it directly to exercise this defensive guard.
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        o.people["I1"] = None
        reviewed_people = {"I1"}
        reviewed_families = set()
        queue = [BlockQueueItem(person_id="I1", family_id="F1", direction="R")]
        with pytest.raises(ValueError) as ex:
            o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        msg = str(ex.value)
        assert "'I1'" in msg
        assert "is unknown" in msg

    def test_other_marriage_referencing_unknown_family_raises_value_error(self):
        # Organizer's constructor filters all_marriages down to known families, so this state
        # can't arise through normal construction; corrupt it directly to exercise the guard.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        o.people["I2"].person.all_marriages.append("F ghost")
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        with pytest.raises(ValueError) as ex:
            o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        msg = str(ex.value)
        assert "Family 'F ghost'" in msg
        assert "is unknown" in msg

    def test_other_marriage_with_unknown_co_parent_raises_value_error(self):
        # family_w.parents is only ever populated with known person ids in normal use;
        # corrupt it directly to exercise the guard against a co-parent that can't be found.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2"],
                ),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        o.families["F2"].parents.append("I ghost")
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        with pytest.raises(ValueError) as ex:
            o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        msg = str(ex.value)
        assert "Person 'I ghost'" in msg
        assert "not found" in msg

    def test_already_reviewed_marriage_is_skipped_but_later_marriages_still_process(self):
        # F2 is pre-marked reviewed (and its other parent I3 pre-marked reviewed too), so
        # that marriage must be skipped without adding anything, and the loop must still
        # continue on to F3 afterwards instead of stopping early.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1", "F2", "F3"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
                Person(id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F3"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I2", to_id="F3"),
                Relationship(from_id="I4", to_id="F3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2", "I3"}
        reviewed_families = {"F1", "F2"}
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2", "I4"]
        assert [f.id for f in block.families] == ["F1", "F3"]
        assert reviewed_people == {"I1", "I2", "I3", "I4"}
        assert reviewed_families == {"F1", "F2", "F3"}

    def test_queue_items_own_family_is_skipped_when_not_marked_reviewed(self):
        # In normal use reviewed_families always already contains the item's own family_id
        # (order_marriages adds it before enqueueing), so filter_marriages_by_level would
        # exclude it. Omit it here to force filter_marriages_by_level to hand it back, which
        # exercises the guard that skips re-processing the family the person was reached through.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        block = Block(o.people["I1"])
        block.add_family(o.families["F1"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = set()
        queue = [BlockQueueItem(person_id="I2", family_id="F1", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2"]
        assert [f.id for f in block.families] == ["F1"]
        assert reviewed_people == {"I1", "I2"}
        assert (
            reviewed_families == set()
        )  # this does not happen during normal execution. This result is due to an unusual test setup

    def test_duplicate_marriage_id_second_occurrence_is_skipped(self):
        # Duplicate the marriage id on I2 so filter_marriages_by_level (which only checks
        # reviewed_families up front) hands back the same family twice. The first occurrence
        # processes normally; the second must be skipped since it's reviewed by then.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F0"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F0", "F1"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F0"), Family(id="F1")],
            [
                Relationship(from_id="I1", to_id="F0"),
                Relationship(from_id="I2", to_id="F0"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I3", to_id="F1"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        o.people["I2"].person.all_marriages.append("F1")
        block = Block(o.people["I1"])
        block.add_family(o.families["F0"])
        block.add_person(o.people["I2"])
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F0"}
        queue = [BlockQueueItem(person_id="I2", family_id="F0", direction="R")]
        o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)
        assert [p.id for p in block.people] == ["I1", "I2", "I3"]
        assert [f.id for f in block.families] == ["F0", "F1"]
        assert reviewed_people == {"I1", "I2", "I3"}
        assert reviewed_families == {"F0", "F1"}


class TestOrganizeRow:
    def test_raises_when_level_zero_contains_neither_people_nor_families(self):
        # levels is caller-supplied data; feed it something malformed directly to exercise
        # the defensive else-branch that neither organize_by_level nor real usage can trigger.
        t = FamilyTree([], [], [])
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            # It's not possible to trigger exception during normal execution, hence the use of synthetic data
            o.organize_row({0: ["not a wrapper"]}, set(), set())
        msg = str(ex.value)
        assert "Unexpected object in one of the assigned levels" in msg
        assert "not a wrapper" in msg

    def test_empty_tree_returns_empty_list(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.blocks == []
        assert reviewed_people == set()
        assert reviewed_families == set()

    def test_single_unmarried_person_with_no_level_one_at_all(self):
        # There is no family anywhere in the tree, so levels.get(1) is missing entirely;
        # this exercises the default-to-empty-list guard on that lookup.
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.get_people_ids() == [["I1"]]
        assert res.get_family_ids() == [[]]
        assert reviewed_people == {"I1"}
        assert reviewed_families == set()

    def test_request_to_order_non_existing_row_fails(self):
        # There is no family anywhere in the tree, so levels.get(1) is missing entirely;
        # this exercises the default-to-empty-list guard on that lookup.
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        first_row = o.organize_row(levels, reviewed_people, reviewed_families)
        with pytest.raises(ValueError) as ex:
            o.organize_row(levels, reviewed_people, reviewed_families, 2, first_row)
        msg = str(ex)
        assert "Cannot organize a non-existing row" in msg
        assert "Requested level is \\'2\\'" in msg
        assert '{"0": ["I1"]}' in msg

    def test_families_at_level_zero_creates_one_block_per_family(self):
        # F0 sits above I1/I2 with its parents list cleared, so level 0 is made up of
        # families rather than people, exercising the FamilyWrapper branch.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F0"), Family(id="F1")],
            [
                Relationship(from_id="F0", to_id="I1"),
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
            ],
        )
        o = Organizer(t)
        o.families["F0"].parents = []
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.get_people_ids() == [[]]
        assert res.get_family_ids() == [["F0"]]
        assert reviewed_people == set()
        assert reviewed_families == {"F0"}

    def test_couple_at_level_zero_is_a_single_block(self):
        # I1 and I2 are spouses in F1, both at level 0. order_marriages pulls the family
        # in on I1's turn, so no separate block should be produced for F1 at level 1.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.get_people_ids() == [["I1", "I2"]]
        assert res.get_family_ids() == [["F1"]]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1"}

    def test_already_reviewed_person_at_level_zero_is_skipped(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = {"I1", "I2"}
        reviewed_families = {"F1"}
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.blocks == []
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1"}

    def test_extra_family_in_level_1(self):
        # I3 is a child of F2. The trailing "for family_w in level1" loop must then create a standalone block for it.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("parent")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("boy")], all_marriages=["F3"]),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("girl")], all_marriages=["F3"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="F2", to_id="I3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.get_people_ids() == [["I1"], []]
        assert res.get_family_ids() == [["F1"], ["F2"]]
        assert reviewed_people == {"I1"}
        assert reviewed_families == {"F1", "F2"}

    def test_already_reviewed_level_one_family_is_not_duplicated(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("parent")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="F1", to_id="I2")],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = {"F1"}
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.get_people_ids() == [["I1"]]
        assert res.get_family_ids() == [[]]
        assert reviewed_people == {"I1"}
        assert reviewed_families == {"F1"}

    def test_multiple_people_at_level_zero_are_sorted_by_gender_then_name(self):
        # I1 (man, "Bob") is married to I2 (woman, "Zoe").
        # I3 (woman, "Amy") and I4 (man, "Albert) are unmarried to each
        # other and only connected through an adopted child's three origins, so each
        # produces its own block. They're listed in mixed of the expected output order
        # to confirm organize_row sorts by sorting_key rather than input order.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Bob")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("Zoe")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("Amy")], all_marriages=["F3"]),
                Person(id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Albert")], all_marriages=["F4"]),
                Person(
                    id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]
                ),  # adopted by all families
            ],
            [Family(id="F1"), Family(id="F3"), Family(id="F4")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I5"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="F3", to_id="I5"),
                Relationship(from_id="I4", to_id="F4"),
                Relationship(from_id="F4", to_id="I5"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        res = o.organize_row(levels, reviewed_people, reviewed_families)
        assert res.get_people_ids() == [["I4"], ["I1", "I2"], ["I3"]]
        assert res.get_family_ids() == [["F4"], ["F1"], ["F3"]]
        assert reviewed_people == {"I1", "I2", "I3", "I4"}
        assert reviewed_families == {"F1", "F3", "F4"}

    def test_raises_when_non_root_level_contains_families_not_people(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
            ],
            [
                Family(id="F1"),
                Family(id="F2"),
            ],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="I2", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        levels = o.get_objects_by_level()
        reviewed_people = set()
        reviewed_families = set()
        previous_row = o.organize_row(levels, reviewed_people, reviewed_families)
        o.people["I2"].level = 3
        o.families["F2"].level = 2
        levels = o.get_objects_by_level()
        with pytest.raises(ValueError) as ex:
            o.organize_row(levels, reviewed_people, reviewed_families, 2, previous_row)
        msg = str(ex.value)
        assert "Expected to find people" in msg
        assert "row '2'" in msg
        assert "found families" in msg

    def test_pulls_primary_children_of_previous_row_families(self):
        # Two generations: I1/I2 marry via F1, their child I3 marries I4 via F2, and
        # childless I5 is also a child of F1. organize_row must pull both I3
        # and I5 in as children of the previous row's F1, pair I3 with its spouse I4, and
        # fold F2 in automatically without a separate standalone block.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("gf")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("gm")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F2"]),
                Person(
                    id="I4",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("daughter-in-law")],
                    all_marriages=["F2"],
                ),
                Person(id="I5", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("granddaughter")]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="F1", to_id="I5"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I4", to_id="F2"),
            ],
        )
        o = Organizer(t)
        reviewed_people = set()
        reviewed_families = set()
        levels = o.assign_levels()
        all_levels = o.get_objects_by_level()
        previous_row = o.organize_row(all_levels, reviewed_people, reviewed_families)
        assert levels == {0: ["I1", "I2"], 1: ["F1"], 2: ["I3", "I4", "I5"], 3: ["F2"]}
        res = o.organize_row(all_levels, reviewed_people, reviewed_families, start_level=2, previous_row=previous_row)
        assert res.get_people_ids() == [["I3", "I4"], ["I5"]]
        assert res.get_family_ids() == [["F2"], []]
        assert reviewed_people == {"I1", "I2", "I3", "I4", "I5"}
        assert reviewed_families == {"F1", "F2"}

    def test_child_pulled_in_only_through_its_primary_family(self):
        # I5 is an adopted child of F1
        # The test verifies that the marriage of I3 and I5 shows them as being in separate blocks (unlike siblings)
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("gf1")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("gm1")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")]),
                Person(id="I8", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("gf2")], all_marriages=["F3"]),
                Person(id="I9", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("gm2")], all_marriages=["F3"]),
                Person(id="I5", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("adopted-daughter")]),
            ],
            [Family(id="F1"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="I8", to_id="F3"),
                Relationship(from_id="I9", to_id="F3"),
                Relationship(from_id="F3", to_id="I5"),
                Relationship(from_id="F1", to_id="I5", attrs={"style": "dashed"}),
            ],
        )
        o = Organizer(t)
        assert o.people["I5"].primary_parent_family_id == "F3"
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        all_levels = o.get_objects_by_level()
        previous_row = o.organize_row(all_levels, reviewed_people, reviewed_families)
        assert previous_row.get_family_ids() == [["F1"], ["F3"]]
        res = o.organize_row(all_levels, reviewed_people, reviewed_families, start_level=2, previous_row=previous_row)
        assert res.get_people_ids() == [["I3"], ["I5"]]
        assert reviewed_people == {"I1", "I2", "I3", "I5", "I8", "I9"}

    def test_child_of_second_previous_family_already_reviewed_via_spouse_is_skipped(self):
        # I3 (child of F1) marries I4 (child of F3) via F2. Both F1 and F3 sit in the
        # previous row. Processing I3 first pulls I4 in as a spouse and marks it reviewed,
        # so when the children loop reaches I4 (child of F3) it must be skipped rather than
        # re-added as a duplicate/empty block.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("gf1")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("gm1")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F2"]),
                Person(id="I8", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("gf2")], all_marriages=["F3"]),
                Person(id="I9", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("gm2")], all_marriages=["F3"]),
                Person(
                    id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["F2"]
                ),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="I8", to_id="F3"),
                Relationship(from_id="I9", to_id="F3"),
                Relationship(from_id="F3", to_id="I4"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I4", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        all_levels = o.get_objects_by_level()
        previous_row = o.organize_row(all_levels, reviewed_people, reviewed_families)
        assert previous_row.get_family_ids() == [["F1"], ["F3"]]
        res = o.organize_row(all_levels, reviewed_people, reviewed_families, start_level=2, previous_row=previous_row)
        assert res.get_people_ids() == [["I3", "I4"]]
        assert res.get_family_ids() == [["F2"]]
        assert reviewed_people == {"I1", "I2", "I3", "I4", "I8", "I9"}
        assert reviewed_families == {"F1", "F2", "F3"}

    def test_in_laws_are_collected(self):
        # I5 has no direct connection to I2. They are connected as in-laws
        # Nevertheless, both I2 and I5 are shown in the second row
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("gf")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("father")], all_marriages=["F2"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F3"]),
                Person(
                    id="I4",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("gf-in-law")],
                    all_marriages=["F4"],
                ),
                Person(
                    id="I5",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("mother-in-law")],
                    all_marriages=["F5"],
                ),
                Person(
                    id="I6",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("daughter")],
                    all_marriages=["F3"],
                ),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="F4"), Family(id="F5")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="F2", to_id="I3"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="I4", to_id="F4"),
                Relationship(from_id="F4", to_id="I5"),
                Relationship(from_id="I5", to_id="F5"),
                Relationship(from_id="F5", to_id="I6"),
                Relationship(from_id="I6", to_id="F3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        levels = o.get_objects_by_level()
        reviewed_people = set()
        reviewed_families = set()
        previous_row = o.organize_row(levels, reviewed_people, reviewed_families)
        res = o.organize_row(levels, reviewed_people, reviewed_families, start_level=2, previous_row=previous_row)
        assert res.get_people_ids() == [["I2"], ["I5"]]
        assert res.get_family_ids() == [["F2"], ["F5"]]
        assert reviewed_people == {"I1", "I2", "I4", "I5"}
        assert reviewed_families == {"F1", "F2", "F4", "F5"}

    def test_extra_family_in_next_level_creates_standalone_block(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("gf")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("father")], all_marriages=["F2"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F3"]),
                Person(
                    id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["F3"]
                ),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="F4")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="F2", to_id="I3"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="F4", to_id="I4"),
                Relationship(from_id="I4", to_id="F3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        previous_row = o.organize_row(levels, reviewed_people, reviewed_families)
        res = o.organize_row(levels, reviewed_people, reviewed_families, start_level=2, previous_row=previous_row)
        assert res.get_people_ids() == [["I2"], []]
        assert res.get_family_ids() == [["F2"], ["F4"]]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1", "F2", "F4"}

    def test_already_reviewed_family_in_next_level_is_not_duplicated(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("parent")],
                    all_marriages=["F1"],
                ),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="I2", to_id="F2"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        levels = o.get_objects_by_level()
        reviewed_people = set()
        reviewed_families = set()
        previous_row = o.organize_row(levels, reviewed_people, reviewed_families)
        reviewed_families.add("F2")
        res = o.organize_row(levels, reviewed_people, reviewed_families, start_level=2, previous_row=previous_row)
        assert res.get_people_ids() == [["I2"]]
        assert res.get_family_ids() == [[]]
        assert reviewed_people == {"I1", "I2"}
        assert reviewed_families == {"F1", "F2"}

    def test_remaining_people_are_sorted_by_gender_then_name(self):
        # Mirrors the first-level scenario's sorting behavior: people not swept in as children
        # of the previous row still come out ordered by sorting_key, not input order.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("mother")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("Zoe")], all_marriages=["F2"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Bob")], all_marriages=["F3"]),
                Person(id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Albert")], all_marriages=["F4"]),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("adopted child")]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="F4")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="F2", to_id="I5"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="F3", to_id="I5"),
                Relationship(from_id="I4", to_id="F4"),
                Relationship(from_id="F4", to_id="I5"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        reviewed_people = set()
        reviewed_families = set()
        levels = o.get_objects_by_level()
        first_row = o.organize_row(levels, reviewed_people, reviewed_families)
        res = o.organize_row(levels, reviewed_people, reviewed_families, start_level=2, previous_row=first_row)
        assert res.get_people_ids() == [["I2"], ["I4"], ["I3"]]
        assert res.get_family_ids() == [["F2"], ["F4"], ["F3"]]


class TestOrganizeTree:
    def test_empty_tree_returns_empty_list(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        res = o.organize_tree()
        assert res == []

    def test_single_unmarried_person_produces_one_row(self):
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])],
            [],
            [],
        )
        o = Organizer(t)
        res = o.organize_tree()
        assert len(res) == 1
        assert res[0].get_people_ids() == [["I1"]]
        assert res[0].get_family_ids() == [[]]

    def test_married_couple_with_no_children_folds_into_a_single_row(self):
        # The couple and their marriage share levels 0 and 1, but organize_tree's height
        # accounting advances by both levels in the same iteration, so only one Row comes out.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        res = o.organize_tree()
        assert len(res) == 1
        assert res[0].get_people_ids() == [["I1", "I2"]]
        assert res[0].get_family_ids() == [["F1"]]

    def test_three_generations_produces_three_rows(self):
        # Same tree as TestAssignLevels.test_two_families_three_generations:
        # I1/I2 (level 0) marry via F1 (level 1) and have children I3/I5 (level 2);
        # I3 marries I4 via F2 (level 3) and they have children I6/I7 (level 4).
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandfather")], all_marriages=["F1"]
                ),
                Person(
                    id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("grandmother")], all_marriages=["F1"]
                ),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
                Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
                Person(id="I5", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
                Person(id="I6", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")]),
                Person(id="I7", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="F1", to_id="I5"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I4", to_id="F2"),
                Relationship(from_id="F2", to_id="I6"),
                Relationship(from_id="F2", to_id="I7"),
            ],
        )
        o = Organizer(t)
        res = o.organize_tree()
        assert len(res) == 3
        assert res[0].get_people_ids() == [["I1", "I2"]]
        assert res[0].get_family_ids() == [["F1"]]
        assert res[1].get_people_ids() == [["I3", "I4"], ["I5"]]
        assert res[1].get_family_ids() == [["F2"], []]
        assert res[2].get_people_ids() == [["I6"], ["I7"]]
        assert res[2].get_family_ids() == [[], []]
        all_reviewed_people = {p for row in res for block in row.get_people_ids() for p in block}
        all_reviewed_families = {f for row in res for block in row.get_family_ids() for f in block}
        assert all_reviewed_people == {"I1", "I2", "I3", "I4", "I5", "I6", "I7"}
        assert all_reviewed_families == {"F1", "F2"}

    def test_family_without_parents_at_top_folds_into_two_rows(self):
        # Same tree as TestAssignLevels.test_family_without_parents_at_top_of_hierarchy:
        # F0 (level 0, no parents) has child I1 (level 1), who marries I2 via F1 (level 2).
        # organize_row pulls I1 in as a child of F0's row and immediately folds in I1's own
        # marriage/family, so the 3 assigned levels collapse into 2 Rows instead of 3.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1"],
                ),
            ],
            [Family(id="F0"), Family(id="F1")],
            [
                Relationship(from_id="F0", to_id="I1"),
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
            ],
        )
        o = Organizer(t)
        o.families["F0"].parents = []
        res = o.organize_tree()
        assert len(res) == 2
        assert res[0].get_people_ids() == [[]]
        assert res[0].get_family_ids() == [["F0"]]
        assert res[1].get_people_ids() == [["I1", "I2"]]
        assert res[1].get_family_ids() == [["F1"]]

    def test_previous_row_carries_forward_to_drive_next_row_child_order(self):
        # organize_tree sets previous_row = current_row at the end of each loop iteration, so the
        # row just built is what organize_row consults to pull the next row's children in birth-
        # family order. I3/I4 are both children of F1, listed on F1 in reverse of their sorting_key
        # order (M sorts before W). If previous_row were not carried forward, organize_row would
        # fall back to sorting first_level by sorting_key, producing [I3, I4] instead of [I4, I3].
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Adam")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("Beth")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Carl")]),
                Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("Dana")]),
            ],
            [Family(id="F1")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I4"),
                Relationship(from_id="F1", to_id="I3"),
            ],
        )
        o = Organizer(t)
        res = o.organize_tree()
        assert len(res) == 2
        assert res[0].get_people_ids() == [["I1", "I2"]]
        assert res[0].get_family_ids() == [["F1"]]
        assert res[1].get_people_ids() == [["I4"], ["I3"]]
        assert res[1].get_family_ids() == [[], []]


class TestFindFounderFamilies:
    def test_empty_tree_returns_empty_list(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        assert o.find_founder_families() == []

    def test_single_family_with_parents_without_ancestors(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        assert o.find_founder_families() == ["F1"]

    def test_family_without_parents_is_included(self):
        # F0's parents list is cleared the same way as in
        # TestAssignLevels.test_family_without_parents_at_top_of_hierarchy to model a
        # family whose parents are unknown.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F0"), Family(id="F1")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
            ],
        )
        o = Organizer(t)
        assert o.find_founder_families() == ["F0", "F1"]

    def test_family_with_one_parent_having_ancestors_is_excluded(self):
        # I3 is a child of F1, so F2 has a parent with known parents and is not a
        # founders' family even though I4's parents are unknown.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F2"]),
                Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I4", to_id="F2"),
            ],
        )
        o = Organizer(t)
        assert o.find_founder_families() == ["F1"]

    def test_family_with_adopted_parent_is_included(self):
        # I3 is only an adopted child of F1, but an adoptive origin still counts as
        # having parents specified, so F2 is not a founders' family.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F2"]),
                Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I4", attrs={"style": "dashed"}),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="F2", to_id="I4"),
            ],
        )
        o = Organizer(t)
        assert o.find_founder_families() == ["F1", "F2"]

    def test_multiple_founder_families_are_sorted(self):
        # Two unrelated founder couples F2 and F1 marry off their children into F3,
        # which is therefore not a founders' family.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F3"]),
                Person(
                    id="I6", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["F3"]
                ),
            ],
            [Family(id="F2"), Family(id="F1"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="I3", to_id="F1"),
                Relationship(from_id="I4", to_id="F1"),
                Relationship(from_id="F2", to_id="I5"),
                Relationship(from_id="F1", to_id="I6"),
                Relationship(from_id="I5", to_id="F3"),
                Relationship(from_id="I6", to_id="F3"),
            ],
        )
        o = Organizer(t)
        assert o.find_founder_families() == ["F1", "F2"]


def three_generations_tree() -> FamilyTree:
    # F1 (I1 + I2) has children I3 and I5; I3 marries I4 via F2, with children I6 and I7.
    return FamilyTree(
        [
            Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F2"]),
            Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            Person(id="I5", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")]),
            Person(id="I6", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")]),
            Person(id="I7", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("granddaughter")]),
        ],
        [Family(id="F1"), Family(id="F2")],
        [
            Relationship(from_id="I1", to_id="F1"),
            Relationship(from_id="I2", to_id="F1"),
            Relationship(from_id="F1", to_id="I3"),
            Relationship(from_id="F1", to_id="I5"),
            Relationship(from_id="I3", to_id="F2"),
            Relationship(from_id="I4", to_id="F2"),
            Relationship(from_id="F2", to_id="I6"),
            Relationship(from_id="F2", to_id="I7"),
        ],
    )


class TestInitDescendantDistances:
    def test_unknown_family_raises_value_error(self):
        o = Organizer(FamilyTree([], [Family(id="F1")], []))
        with pytest.raises(ValueError) as ex:
            o.init_descendant_distances("F9", None)
        assert "'F9'" in str(ex.value)
        assert "not a known family" in str(ex.value)

    def test_none_distances_start_the_founder_at_zero(self):
        o = Organizer(FamilyTree([], [Family(id="F1")], []))
        assert o.init_descendant_distances("F1", None) == {"F1": 0}

    def test_given_distances_are_returned_unchanged(self):
        # The dictionary itself is returned, so the traversal updates it in place.
        o = Organizer(FamilyTree([], [Family(id="F1")], []))
        distances = {"F1": 4, "X": 5}
        res = o.init_descendant_distances("F1", distances)
        assert res is distances
        assert res == {"F1": 4, "X": 5}

    def test_founder_missing_from_the_given_distances_raises_value_error(self):
        o = Organizer(FamilyTree([], [Family(id="F1")], []))
        with pytest.raises(ValueError) as ex:
            o.init_descendant_distances("F1", {"X": 3})
        assert "'F1'" in str(ex.value)
        assert "no distance in the given dictionary" in str(ex.value)


class TestMeasureDescendantDistances:
    def test_unknown_family_raises_value_error(self):
        o = Organizer(FamilyTree([], [], []))
        with pytest.raises(ValueError) as ex:
            o.measure_descendant_distances("F1")
        msg = str(ex.value)
        assert "'F1'" in msg
        assert "not a known family" in msg

    def test_three_generations_excludes_all_spouses(self):
        # Only the founder family and its blood descendants get a distance; the
        # founder parents I1/I2 and the in-marrying spouse I4 are left for
        # include_spouses to add.
        o = Organizer(three_generations_tree())
        res = o.measure_descendant_distances("F1")
        assert res == {"F1": 0, "I3": 1, "I5": 1, "F2": 2, "I6": 3, "I7": 3}

    def test_mid_tree_family_excludes_ancestors(self):
        # Starting from F2, everything above it (F1, I1, I2, I5) stays out, and
        # even F2's own parents are left for include_spouses to add.
        o = Organizer(three_generations_tree())
        res = o.measure_descendant_distances("F2")
        assert res == {"F2": 0, "I6": 1, "I7": 1}

    def test_adopted_child_keeps_longest_path(self):
        # I5 is a birth child of the founder family F1 (distance 1) and is also
        # adopted by F2, the family of his older sister I3 (distance 3). The longest
        # path wins.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("father")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("mother")], all_marriages=["F1"]),
                Person(
                    id="I3",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("older-sister")],
                    all_marriages=["F2"],
                ),
                Person(
                    id="I4",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("brother-in-law")],
                    all_marriages=["F2"],
                ),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="F1", to_id="I5"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I4", to_id="F2"),
                Relationship(from_id="F2", to_id="I5", attrs={"style": "dashed"}),
            ],
        )
        o = Organizer(t)
        res = o.measure_descendant_distances("F1")
        assert res == {"F1": 0, "I3": 1, "F2": 2, "I5": 3}

    def test_cousin_marriage_and_same_level_adoption(self):
        # Founder family F0 has no recorded parents. Its children A and B marry
        # outsiders SA and SB; the cousins CA and CB marry each other via FC, so FC
        # sits one below both of them. CB is also adopted by her uncle's family FA at
        # the same depth as her birth family FB, which must not change her distance.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(id="B", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FB"]),
                Person(id="SA", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("wife")], all_marriages=["FA"]),
                Person(id="SB", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("wife")], all_marriages=["FB"]),
                Person(id="CA", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("cousin")], all_marriages=["FC"]),
                Person(id="CB", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("cousin")], all_marriages=["FC"]),
                Person(id="CC", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]),
            ],
            [Family(id="F0"), Family(id="FA"), Family(id="FB"), Family(id="FC")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="B"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="SA", to_id="FA"),
                Relationship(from_id="B", to_id="FB"),
                Relationship(from_id="SB", to_id="FB"),
                Relationship(from_id="FA", to_id="CA"),
                Relationship(from_id="FA", to_id="CB", attrs={"style": "dashed"}),
                Relationship(from_id="FB", to_id="CB"),
                Relationship(from_id="CA", to_id="FC"),
                Relationship(from_id="CB", to_id="FC"),
                Relationship(from_id="FC", to_id="CC"),
            ],
        )
        o = Organizer(t)
        res = o.measure_descendant_distances("F0")
        assert res == {
            "F0": 0,
            "A": 1,
            "B": 1,
            "FA": 2,
            "FB": 2,
            "CA": 3,
            "CB": 3,
            "FC": 4,
            "CC": 5,
        }

    def test_uncle_marrying_niece_keeps_his_blood_distance(self):
        # A is a child of the founder family FG (distance 1) and later marries his
        # niece N (distance 3) via FAN. FAN is first reached through A at 2 and
        # re-placed at 4 through N, but A himself keeps his blood distance 1: the
        # traversal only places children of traversed families, never their parents.
        t = FamilyTree(
            [
                Person(
                    id="G", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandparent")], all_marriages=["FG"]
                ),
                Person(
                    id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("uncle")], all_marriages=["FA", "FAN"]
                ),
                Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("parent")], all_marriages=["FB"]),
                Person(id="N", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("niece")], all_marriages=["FAN"]),
            ],
            [Family(id="FG"), Family(id="FA"), Family(id="FB"), Family(id="FAN")],
            [
                Relationship(from_id="G", to_id="FG"),
                Relationship(from_id="FG", to_id="A"),
                Relationship(from_id="FG", to_id="B"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="B", to_id="FB"),
                Relationship(from_id="FB", to_id="N"),
                Relationship(from_id="A", to_id="FAN"),
                Relationship(from_id="N", to_id="FAN"),
            ],
        )
        o = Organizer(t)
        res = o.measure_descendant_distances("FG")
        assert res == {"FG": 0, "A": 1, "B": 1, "FA": 2, "FB": 2, "N": 3, "FAN": 4}

    def test_ancestry_cycle_raises_value_error(self):
        # Corrupt data: I1 is simultaneously a parent and a child of F1, so descending
        # from F1 keeps finding longer paths forever.
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="F1", to_id="I1")],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.measure_descendant_distances("F1")
        msg = str(ex.value)
        assert "Ancestry cycle detected" in msg
        assert "'F1'" in msg


class TestIncludeSpouses:
    def test_missing_parent_is_added_one_above_the_family(self):
        # I1 is a descendant of the founder family F0; his wife I2 married in and
        # lands at 1, one above their family F1.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("wife")], all_marriages=["F1"]),
            ],
            [Family(id="F0"), Family(id="F1")],
            [
                Relationship(from_id="F0", to_id="I1"),
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F0")
        assert distances == {"F0": 0, "I1": 1, "F1": 2}
        o.include_spouses(distances)
        assert distances == {"F0": 0, "I1": 1, "F1": 2, "I2": 1}

    def test_both_missing_parents_are_added(self):
        # Neither parent of the founder family is a descendant; both land at -1.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F1")
        assert distances == {"F1": 0}
        o.include_spouses(distances)
        assert distances == {"F1": 0, "I1": -1, "I2": -1}

    def test_parent_already_in_distances_is_not_changed(self):
        # A married his niece N via FAN (distance 4). Both parents of FAN are already
        # descendants, so nothing is added and A keeps his blood distance 1 even
        # though FAN would place him at 3.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("uncle")], all_marriages=["FAN"]),
                Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("parent")], all_marriages=["FB"]),
                Person(id="N", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("niece")], all_marriages=["FAN"]),
            ],
            [Family(id="FG"), Family(id="FB"), Family(id="FAN")],
            [
                Relationship(from_id="FG", to_id="A"),
                Relationship(from_id="FG", to_id="B"),
                Relationship(from_id="B", to_id="FB"),
                Relationship(from_id="FB", to_id="N"),
                Relationship(from_id="A", to_id="FAN"),
                Relationship(from_id="N", to_id="FAN"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("FG")
        expected = {"FG": 0, "A": 1, "B": 1, "FB": 2, "N": 3, "FAN": 4}
        assert distances == expected
        o.include_spouses(distances)
        assert distances == expected

    def test_spouse_of_two_families_is_placed_above_the_older_marriage(self):
        # Outsider S married A (a child of the founder family, via FA at distance 2)
        # and also D (a grandchild, via FD at distance 4). FA is the older marriage
        # (lower level), so S sits at 1, one above FA.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(id="B", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FB"]),
                Person(
                    id="D", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FD"]
                ),
                Person(
                    id="S",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("outsider")],
                    all_marriages=["FA", "FD"],
                ),
            ],
            [Family(id="F0"), Family(id="FA"), Family(id="FB"), Family(id="FD")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="B"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="S", to_id="FA"),
                Relationship(from_id="B", to_id="FB"),
                Relationship(from_id="FB", to_id="D"),
                Relationship(from_id="D", to_id="FD"),
                Relationship(from_id="S", to_id="FD"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F0")
        assert distances == {"F0": 0, "A": 1, "B": 1, "FA": 2, "FB": 2, "D": 3, "FD": 4}
        o.include_spouses(distances)
        assert distances == {"F0": 0, "A": 1, "B": 1, "FA": 2, "FB": 2, "D": 3, "FD": 4, "S": 1}

    def test_spouse_of_two_families_is_placed_above_the_older_marriage_regardless_of_list_order(self):
        # Same tree as above, but FD comes first in S's marriage list. The order of
        # the list does not matter: FA is the older marriage (lower level), so S
        # still sits at 1, one above FA.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(id="B", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FB"]),
                Person(
                    id="D", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FD"]
                ),
                Person(
                    id="S",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("outsider")],
                    all_marriages=["FD", "FA"],
                ),
            ],
            [Family(id="F0"), Family(id="FA"), Family(id="FB"), Family(id="FD")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="B"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="S", to_id="FA"),
                Relationship(from_id="B", to_id="FB"),
                Relationship(from_id="FB", to_id="D"),
                Relationship(from_id="D", to_id="FD"),
                Relationship(from_id="S", to_id="FD"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F0")
        assert distances == {"F0": 0, "A": 1, "B": 1, "FA": 2, "FB": 2, "D": 3, "FD": 4}
        o.include_spouses(distances)
        assert distances == {"F0": 0, "A": 1, "B": 1, "FA": 2, "FB": 2, "D": 3, "FD": 4, "S": 1}

    def test_spouse_found_via_deeper_family_is_placed_above_their_older_marriage(self):
        # I5 is a birth child of the founder family F1 and is also adopted by his
        # older sister I3's family F2, which sinks his marriage F5 to distance 4.
        # F5 is the family that finds outsider S, but she also married I6 via F6 at
        # distance 2, so S sits at 1, above her older marriage F6.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("father")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("mother")], all_marriages=["F1"]),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")], all_marriages=["F5"]),
                Person(
                    id="I3",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("older-sister")],
                    all_marriages=["F2"],
                ),
                Person(id="I6", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["F6"]),
                Person(
                    id="S",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("outsider")],
                    all_marriages=["F5", "F6"],
                ),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F5"), Family(id="F6")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I5"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="F1", to_id="I6"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="F2", to_id="I5", attrs={"style": "dashed"}),
                Relationship(from_id="I5", to_id="F5"),
                Relationship(from_id="S", to_id="F5"),
                Relationship(from_id="I6", to_id="F6"),
                Relationship(from_id="S", to_id="F6"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F1")
        assert distances == {"F1": 0, "I5": 3, "F5": 4, "I3": 1, "F2": 2, "I6": 1, "F6": 2}
        o.include_spouses(distances)
        assert distances == {
            "F1": 0,
            "I5": 3,
            "F5": 4,
            "I3": 1,
            "F2": 2,
            "I6": 1,
            "F6": 2,
            "I1": -1,
            "I2": -1,
            "S": 1,
        }

    def test_spouse_of_two_siblings_is_added_once(self):
        # Outsider S married both children of the founder family; both marriages sit
        # at the same level, S lands at 1 and the second family FB does not add her
        # again.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(id="B", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FB"]),
                Person(
                    id="S",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("outsider")],
                    all_marriages=["FA", "FB"],
                ),
            ],
            [Family(id="F0"), Family(id="FA"), Family(id="FB")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="B"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="S", to_id="FA"),
                Relationship(from_id="B", to_id="FB"),
                Relationship(from_id="S", to_id="FB"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F0")
        assert distances == {"F0": 0, "A": 1, "B": 1, "FA": 2, "FB": 2}
        o.include_spouses(distances)
        assert distances == {"F0": 0, "A": 1, "B": 1, "FA": 2, "FB": 2, "S": 1}

    def test_spouse_marriage_outside_the_tree_is_ignored(self):
        # S's marriage F2 was never traversed, so it cannot be her oldest traversed
        # marriage; her distance comes from FA.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(
                    id="S",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("outsider")],
                    all_marriages=["F2", "FA"],
                ),
                Person(
                    id="X", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("outsider")], all_marriages=["F2"]
                ),
            ],
            [Family(id="F0"), Family(id="FA"), Family(id="F2")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="S", to_id="FA"),
                Relationship(from_id="S", to_id="F2"),
                Relationship(from_id="X", to_id="F2"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F0")
        assert distances == {"F0": 0, "A": 1, "FA": 2}
        o.include_spouses(distances)
        assert distances == {"F0": 0, "A": 1, "FA": 2, "S": 1}

    def test_spouse_without_marriage_list_lands_one_above_the_family_that_found_them(self):
        # S is a parent of FA only through a relationship edge; her marriage list is
        # empty, so she falls back to sitting one above FA, the family that found her.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(id="S", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("outsider")]),
            ],
            [Family(id="F0"), Family(id="FA")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="S", to_id="FA"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F0")
        assert distances == {"F0": 0, "A": 1, "FA": 2}
        o.include_spouses(distances)
        assert distances == {"F0": 0, "A": 1, "FA": 2, "S": 1}

    def test_added_spouse_does_not_cascade_to_their_other_families(self):
        # S married descendant A via FA, but also has an outside marriage F2 with X.
        # F2 was never traversed, so adding S pulls in neither F2 nor X.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(
                    id="S",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("outsider")],
                    all_marriages=["FA", "F2"],
                ),
                Person(
                    id="X", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("outsider")], all_marriages=["F2"]
                ),
            ],
            [Family(id="F0"), Family(id="FA"), Family(id="F2")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="S", to_id="FA"),
                Relationship(from_id="S", to_id="F2"),
                Relationship(from_id="X", to_id="F2"),
            ],
        )
        o = Organizer(t)
        distances = o.measure_descendant_distances("F0")
        assert distances == {"F0": 0, "A": 1, "FA": 2}
        o.include_spouses(distances)
        assert distances == {"F0": 0, "A": 1, "FA": 2, "S": 1}


class TestFindClosestCommonNode:
    def test_lines_merging_at_a_marriage_return_the_marriage(self):
        # A descends from F0 and B from F1; their marriage FAB is where the two
        # lines merge, so FAB wins over the deeper common nodes C and FC.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(
                    id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB"]
                ),
                Person(
                    id="C", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FC"]
                ),
            ],
            [Family(id="F0"), Family(id="F1"), Family(id="FAB"), Family(id="FC")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
                Relationship(from_id="FAB", to_id="C"),
                Relationship(from_id="C", to_id="FC"),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {"F0": 0, "A": 1, "FAB": 2, "C": 3, "FC": 4}
        assert second == {"F1": 0, "B": 1, "FAB": 2, "C": 3, "FC": 4}
        assert o.find_closest_common_node(first, second) == ("FAB", 2, 2)

    def test_distance_comes_from_the_first_dictionary(self):
        # B is a grandchild of F1, so the common family FAB sits at 2 in F0's
        # traversal but at 4 in F1's; the reported distance follows the first
        # dictionary in each call.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(id="P", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FP"]),
                Person(
                    id="B",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("granddaughter")],
                    all_marriages=["FAB"],
                ),
            ],
            [Family(id="F0"), Family(id="F1"), Family(id="FP"), Family(id="FAB")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F1", to_id="P"),
                Relationship(from_id="P", to_id="FP"),
                Relationship(from_id="FP", to_id="B"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {"F0": 0, "A": 1, "FAB": 2}
        assert second == {"F1": 0, "P": 1, "FP": 2, "B": 3, "FAB": 4}
        assert o.find_closest_common_node(first, second) == ("FAB", 2, 4)
        assert o.find_closest_common_node(second, first) == ("FAB", 4, 2)

    def test_tie_is_broken_by_id(self):
        # A married two children of F1, so both marriages sit at distance 2 in
        # both traversals; the smaller id FAB wins over FAB2.
        t = FamilyTree(
            [
                Person(
                    id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB", "FAB2"]
                ),
                Person(
                    id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB"]
                ),
                Person(
                    id="B2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB2"]
                ),
            ],
            [Family(id="F0"), Family(id="F1"), Family(id="FAB"), Family(id="FAB2")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="F1", to_id="B2"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
                Relationship(from_id="A", to_id="FAB2"),
                Relationship(from_id="B2", to_id="FAB2"),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {"F0": 0, "A": 1, "FAB": 2, "FAB2": 2}
        assert second == {"F1": 0, "B": 1, "B2": 1, "FAB": 2, "FAB2": 2}
        assert o.find_closest_common_node(first, second) == ("FAB", 2, 2)

    def test_common_person_is_returned(self):
        # E was born to FA in F0's line and adopted by FB in F1's line, so the
        # only node the two traversals share is the person E.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"]),
                Person(id="B", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FB"]),
                Person(id="E", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]),
            ],
            [Family(id="F0"), Family(id="F1"), Family(id="FA"), Family(id="FB")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="A", to_id="FA"),
                Relationship(from_id="B", to_id="FB"),
                Relationship(from_id="FA", to_id="E"),
                Relationship(from_id="FB", to_id="E", attrs={"style": "dashed"}),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {"F0": 0, "A": 1, "FA": 2, "E": 3}
        assert second == {"F1": 0, "B": 1, "FB": 2, "E": 3}
        assert o.find_closest_common_node(first, second) == ("E", 3, 3)

    def test_disjoint_traversals_return_none(self):
        # The two founders' families have no descendants in common.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")]),
                Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")]),
            ],
            [Family(id="F0"), Family(id="F1")],
            [Relationship(from_id="F0", to_id="A"), Relationship(from_id="F1", to_id="B")],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {"F0": 0, "A": 1}
        assert second == {"F1": 0, "B": 1}
        assert o.find_closest_common_node(first, second) is None


class TestMergeShiftedDistances:
    def make_organizer(self):
        # merge_shifted_distances works on plain distance dictionaries and never
        # touches the tree, so an empty one is enough.
        return Organizer(FamilyTree([], [], []))

    def test_second_dictionary_is_shifted_by_the_given_amount(self):
        o = self.make_organizer()
        res = o.merge_shifted_distances({"A": 0, "FA": 1}, {"B": 1, "FB": 2}, 3)
        assert res == {"A": 0, "FA": 1, "B": 4, "FB": 5}

    def test_negative_shift_moves_the_second_dictionary_up(self):
        o = self.make_organizer()
        res = o.merge_shifted_distances({"A": 0}, {"B": 3}, -2)
        assert res == {"A": 0, "B": 1}

    def test_common_node_keeps_the_longest_distance_from_the_first_dictionary(self):
        # A sits at 5 in the first dictionary, deeper than its shifted 3.
        o = self.make_organizer()
        res = o.merge_shifted_distances({"A": 5, "B": 0}, {"A": 1, "C": 2}, 2)
        assert res == {"A": 5, "B": 0, "C": 4}

    def test_common_node_keeps_the_longest_distance_from_the_second_dictionary(self):
        # Shifted by 6, A lands at 7 and pushes past its 5 in the first dictionary.
        o = self.make_organizer()
        res = o.merge_shifted_distances({"A": 5, "B": 0}, {"A": 1, "C": 2}, 6)
        assert res == {"A": 7, "B": 0, "C": 8}

    def test_input_dictionaries_are_not_mutated(self):
        o = self.make_organizer()
        first = {"A": 0}
        second = {"A": 3, "B": 1}
        res = o.merge_shifted_distances(first, second, 1)
        assert res == {"A": 4, "B": 2}
        assert first == {"A": 0}
        assert second == {"A": 3, "B": 1}


class TestMeasureDescendantDistancesWithSeed:
    def make_tree(self):
        return FamilyTree(
            [Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA"])],
            [Family(id="F0"), Family(id="FA")],
            [Relationship(from_id="F0", to_id="A"), Relationship(from_id="A", to_id="FA")],
        )

    def test_traversal_starts_from_the_seeded_distance(self):
        # The founder is seeded at 2, so the whole traversal shifts down with it.
        o = Organizer(self.make_tree())
        distances = {"F0": 2}
        res = o.measure_descendant_distances("F0", distances)
        assert res == {"F0": 2, "A": 3, "FA": 4}
        assert res is distances

    def test_seeded_node_with_a_longer_distance_is_not_pulled_up(self):
        # FA is seeded deeper than the traversal would place it and keeps its distance.
        o = Organizer(self.make_tree())
        res = o.measure_descendant_distances("F0", {"F0": 0, "FA": 9})
        assert res == {"F0": 0, "A": 1, "FA": 9}

    def test_founder_missing_from_the_seed_raises_value_error(self):
        o = Organizer(self.make_tree())
        with pytest.raises(ValueError) as ex:
            o.measure_descendant_distances("F0", {"FA": 4})
        assert "'F0'" in str(ex.value)
        assert "no distance" in str(ex.value)


class TestAssignLevels:
    def test_two_founder_families_merge_at_a_marriage_and_spouses_are_added(self):
        # A descends from F0 and B from F1; the traversals merge at FAB. Their
        # child C married outsider S, who is added at the end by include_spouses.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(
                    id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB"]
                ),
                Person(
                    id="C", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FC"]
                ),
                Person(
                    id="S", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("outsider")], all_marriages=["FC"]
                ),
            ],
            [Family(id="F0"), Family(id="F1"), Family(id="FAB"), Family(id="FC")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
                Relationship(from_id="FAB", to_id="C"),
                Relationship(from_id="C", to_id="FC"),
                Relationship(from_id="S", to_id="FC"),
            ],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["F0", "F1"], 1: ["A", "B"], 2: ["FAB"], 3: ["C", "S"], 4: ["FC"]}

    def test_second_founder_family_of_a_grandchild_is_shifted_up(self):
        # B is a grandchild of F1, so aligning the traversals at FAB places F1
        # two levels above F0.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(id="P", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FP"]),
                Person(
                    id="B",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("granddaughter")],
                    all_marriages=["FAB"],
                ),
            ],
            [Family(id="F0"), Family(id="F1"), Family(id="FP"), Family(id="FAB")],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F1", to_id="P"),
                Relationship(from_id="P", to_id="FP"),
                Relationship(from_id="FP", to_id="B"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
            ],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["F1"], 1: ["P"], 2: ["F0", "FP"], 3: ["A", "B"], 4: ["FAB"]}

    def test_founder_family_without_a_common_node_is_merged_once_a_bridge_arrives(self):
        # F1's and F2's traversals share nothing, but F3's children married into
        # both lines. F3 is merged first, which lets F2 merge afterwards.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAC"]),
                Person(id="B", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FBD"]),
                Person(
                    id="C", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAC"]
                ),
                Person(
                    id="D", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FBD"]
                ),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="FAC"), Family(id="FBD")],
            [
                Relationship(from_id="F1", to_id="A"),
                Relationship(from_id="F2", to_id="B"),
                Relationship(from_id="F3", to_id="C"),
                Relationship(from_id="F3", to_id="D"),
                Relationship(from_id="A", to_id="FAC"),
                Relationship(from_id="C", to_id="FAC"),
                Relationship(from_id="B", to_id="FBD"),
                Relationship(from_id="D", to_id="FBD"),
            ],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["F1", "F2", "F3"], 1: ["A", "B", "C", "D"], 2: ["FAC", "FBD"]}

    def test_disconnected_founder_families_raise_value_error(self):
        # F0's and F1's lines never meet, so F1 can never be merged.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")]),
                Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")]),
            ],
            [Family(id="F0"), Family(id="F1")],
            [Relationship(from_id="F0", to_id="A"), Relationship(from_id="F1", to_id="B")],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.assign_levels()
        assert "['F1']" in str(ex.value)
        assert "share no node" in str(ex.value)

    def test_two_marriages_of_a_single_person(self):
        # I1 is the only recorded parent of both F1 and F2, so both count as
        # founder families and each traversal contains only the family itself.
        # The traversals share no descendant, but comparing them with spouses
        # included aligns them at I1 and both marriages land on the same level.
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1", "F2"]
                )
            ],
            [Family(id="F1"), Family(id="F2")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I1", to_id="F2")],
        )
        o = Organizer(t)
        assert o.assign_levels() == {0: ["I1"], 1: ["F1", "F2"]}

    def test_family_without_people_gets_level_zero(self):
        t = FamilyTree([], [Family(id="F1")], [])
        o = Organizer(t)
        assert o.assign_levels() == {0: ["F1"]}

    def test_tree_without_families_returns_dictionary_with_one_person(self):
        t = FamilyTree(
            [Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("loner")])],
            [],
            [],
        )
        o = Organizer(t)
        assert o.assign_levels() == {0: ["A"]}

    def test_two_people_without_families_raise_value_error(self):
        # With no families there is nothing to connect A and B, so no common
        # level structure exists.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("loner")]),
                Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("loner")]),
            ],
            [],
            [],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.assign_levels()
        assert "['A', 'B']" in str(ex.value)
        assert "share no common nodes" in str(ex.value)

    def test_three_people_without_families_raise_value_error(self):
        # The wildcard arm covers any number of disconnected people, not just two.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("loner")]),
                Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("loner")]),
                Person(id="C", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("loner")]),
            ],
            [],
            [],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.assign_levels()
        assert "['A', 'B', 'C']" in str(ex.value)
        assert "share no common nodes" in str(ex.value)

    def test_second_shared_node_deeper_in_the_second_traversal_keeps_the_longest_distance(self):
        # The marriage FAB sits at 2 in both traversals and is the closest
        # common node, so no shift is applied. X was born to FA2 in F0's line
        # (distance 3) but adopted by FG deep in F1's line (distance 5), so
        # after merging X keeps the longest distance. X's two generations of
        # descendants (FX, Y, FY, Z) are shared too and follow X down.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(id="A2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA2"]),
                Person(
                    id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB"]
                ),
                Person(
                    id="B2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FB2"]
                ),
                Person(
                    id="G", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FG"]
                ),
                Person(id="X", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")], all_marriages=["FX"]),
                Person(id="Y", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FY"]),
                Person(id="Z", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")]),
            ],
            [
                Family(id="F0"),
                Family(id="F1"),
                Family(id="FAB"),
                Family(id="FA2"),
                Family(id="FB2"),
                Family(id="FG"),
                Family(id="FX"),
                Family(id="FY"),
            ],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="A2"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="F1", to_id="B2"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
                Relationship(from_id="A2", to_id="FA2"),
                Relationship(from_id="FA2", to_id="X"),
                Relationship(from_id="B2", to_id="FB2"),
                Relationship(from_id="FB2", to_id="G"),
                Relationship(from_id="G", to_id="FG"),
                Relationship(from_id="FG", to_id="X", attrs={"style": "dashed"}),
                Relationship(from_id="X", to_id="FX"),
                Relationship(from_id="FX", to_id="Y"),
                Relationship(from_id="Y", to_id="FY"),
                Relationship(from_id="FY", to_id="Z"),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {"F0": 0, "A": 1, "A2": 1, "FAB": 2, "FA2": 2, "X": 3, "FX": 4, "Y": 5, "FY": 6, "Z": 7}
        assert second == {
            "F1": 0,
            "B": 1,
            "B2": 1,
            "FAB": 2,
            "FB2": 2,
            "G": 3,
            "FG": 4,
            "X": 5,
            "FX": 6,
            "Y": 7,
            "FY": 8,
            "Z": 9,
        }
        res = o.assign_levels()
        assert res == {
            0: ["F0", "F1"],
            1: ["A", "A2", "B", "B2"],
            2: ["FA2", "FAB", "FB2"],
            3: ["G"],
            4: ["FG"],
            5: ["X"],
            6: ["FX"],
            7: ["Y"],
            8: ["FY"],
            9: ["Z"],
        }

    def test_second_shared_node_deeper_in_the_first_traversal_keeps_the_longest_distance(self):
        # Mirror of the previous test: FAB sits at 2 in both traversals and is
        # the closest common node, so no shift is applied. X was born to FB2 in
        # F1's line (distance 3) but adopted by FG deep in F0's line
        # (distance 5), so after merging X keeps the longest distance from the
        # first dictionary. X's two generations of descendants (FX, Y, FY, Z)
        # are shared too and stay down with X.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(id="A2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA2"]),
                Person(
                    id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB"]
                ),
                Person(
                    id="B2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FB2"]
                ),
                Person(
                    id="G", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FG"]
                ),
                Person(id="X", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")], all_marriages=["FX"]),
                Person(id="Y", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FY"]),
                Person(id="Z", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")]),
            ],
            [
                Family(id="F0"),
                Family(id="F1"),
                Family(id="FAB"),
                Family(id="FA2"),
                Family(id="FB2"),
                Family(id="FG"),
                Family(id="FX"),
                Family(id="FY"),
            ],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="A2"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="F1", to_id="B2"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
                Relationship(from_id="A2", to_id="FA2"),
                Relationship(from_id="FA2", to_id="G"),
                Relationship(from_id="G", to_id="FG"),
                Relationship(from_id="FG", to_id="X", attrs={"style": "dashed"}),
                Relationship(from_id="B2", to_id="FB2"),
                Relationship(from_id="FB2", to_id="X"),
                Relationship(from_id="X", to_id="FX"),
                Relationship(from_id="FX", to_id="Y"),
                Relationship(from_id="Y", to_id="FY"),
                Relationship(from_id="FY", to_id="Z"),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {
            "F0": 0,
            "A": 1,
            "A2": 1,
            "FAB": 2,
            "FA2": 2,
            "G": 3,
            "FG": 4,
            "X": 5,
            "FX": 6,
            "Y": 7,
            "FY": 8,
            "Z": 9,
        }
        assert second == {"F1": 0, "B": 1, "B2": 1, "FAB": 2, "FB2": 2, "X": 3, "FX": 4, "Y": 5, "FY": 6, "Z": 7}
        res = o.assign_levels()
        assert res == {
            0: ["F0", "F1"],
            1: ["A", "A2", "B", "B2"],
            2: ["FA2", "FAB", "FB2"],
            3: ["G"],
            4: ["FG"],
            5: ["X"],
            6: ["FX"],
            7: ["Y"],
            8: ["FY"],
            9: ["Z"],
        }

    def test_shared_family_deeper_in_the_second_traversal_keeps_the_longest_distance(self):
        # Like the previous tests, FAB sits at 2 in both traversals and is the
        # closest common node, so no shift is applied. Here the second shared
        # node is a family: X from F0's line (distance 3) married H from F1's
        # line (distance 5), so their marriage FXY is reached at 4 in the first
        # traversal and at 6 in the second and keeps the longest distance. Its
        # two generations of descendants (Y, FY, Z) are shared too and follow
        # it down, while the spouses X and H keep their own levels.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(id="A2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA2"]),
                Person(
                    id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB"]
                ),
                Person(
                    id="B2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FB2"]
                ),
                Person(
                    id="G", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FG"]
                ),
                Person(id="X", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")], all_marriages=["FXY"]),
                Person(
                    id="H",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("great-granddaughter")],
                    all_marriages=["FXY"],
                ),
                Person(id="Y", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FY"]),
                Person(id="Z", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")]),
            ],
            [
                Family(id="F0"),
                Family(id="F1"),
                Family(id="FAB"),
                Family(id="FA2"),
                Family(id="FB2"),
                Family(id="FG"),
                Family(id="FXY"),
                Family(id="FY"),
            ],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="A2"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="F1", to_id="B2"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
                Relationship(from_id="A2", to_id="FA2"),
                Relationship(from_id="FA2", to_id="X"),
                Relationship(from_id="B2", to_id="FB2"),
                Relationship(from_id="FB2", to_id="G"),
                Relationship(from_id="G", to_id="FG"),
                Relationship(from_id="FG", to_id="H"),
                Relationship(from_id="X", to_id="FXY"),
                Relationship(from_id="H", to_id="FXY"),
                Relationship(from_id="FXY", to_id="Y"),
                Relationship(from_id="Y", to_id="FY"),
                Relationship(from_id="FY", to_id="Z"),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {"F0": 0, "A": 1, "A2": 1, "FAB": 2, "FA2": 2, "X": 3, "FXY": 4, "Y": 5, "FY": 6, "Z": 7}
        assert second == {
            "F1": 0,
            "B": 1,
            "B2": 1,
            "FAB": 2,
            "FB2": 2,
            "G": 3,
            "FG": 4,
            "H": 5,
            "FXY": 6,
            "Y": 7,
            "FY": 8,
            "Z": 9,
        }
        res = o.assign_levels()
        assert res == {
            0: ["F0", "F1"],
            1: ["A", "A2", "B", "B2"],
            2: ["FA2", "FAB", "FB2"],
            3: ["G", "X"],
            4: ["FG"],
            5: ["H"],
            6: ["FXY"],
            7: ["Y"],
            8: ["FY"],
            9: ["Z"],
        }

    def test_shared_family_deeper_in_the_first_traversal_keeps_the_longest_distance(self):
        # Mirror of the previous test: FAB sits at 2 in both traversals and is
        # the closest common node, so no shift is applied. The deep line now
        # belongs to F0: H from F0's line (distance 5) married X from F1's line
        # (distance 3), so their marriage FXY is reached at 6 in the first
        # traversal and at 4 in the second and keeps the longest distance from
        # the first dictionary. Its two generations of descendants (Y, FY, Z)
        # stay down with it, while the spouses H and X keep their own levels.
        t = FamilyTree(
            [
                Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FAB"]),
                Person(id="A2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FA2"]),
                Person(
                    id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FAB"]
                ),
                Person(
                    id="B2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")], all_marriages=["FB2"]
                ),
                Person(
                    id="G", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")], all_marriages=["FG"]
                ),
                Person(
                    id="H",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("great-granddaughter")],
                    all_marriages=["FXY"],
                ),
                Person(id="X", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")], all_marriages=["FXY"]),
                Person(id="Y", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")], all_marriages=["FY"]),
                Person(id="Z", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandson")]),
            ],
            [
                Family(id="F0"),
                Family(id="F1"),
                Family(id="FAB"),
                Family(id="FA2"),
                Family(id="FB2"),
                Family(id="FG"),
                Family(id="FXY"),
                Family(id="FY"),
            ],
            [
                Relationship(from_id="F0", to_id="A"),
                Relationship(from_id="F0", to_id="A2"),
                Relationship(from_id="F1", to_id="B"),
                Relationship(from_id="F1", to_id="B2"),
                Relationship(from_id="A", to_id="FAB"),
                Relationship(from_id="B", to_id="FAB"),
                Relationship(from_id="A2", to_id="FA2"),
                Relationship(from_id="FA2", to_id="G"),
                Relationship(from_id="G", to_id="FG"),
                Relationship(from_id="FG", to_id="H"),
                Relationship(from_id="B2", to_id="FB2"),
                Relationship(from_id="FB2", to_id="X"),
                Relationship(from_id="X", to_id="FXY"),
                Relationship(from_id="H", to_id="FXY"),
                Relationship(from_id="FXY", to_id="Y"),
                Relationship(from_id="Y", to_id="FY"),
                Relationship(from_id="FY", to_id="Z"),
            ],
        )
        o = Organizer(t)
        first = o.measure_descendant_distances("F0")
        second = o.measure_descendant_distances("F1")
        assert first == {
            "F0": 0,
            "A": 1,
            "A2": 1,
            "FAB": 2,
            "FA2": 2,
            "G": 3,
            "FG": 4,
            "H": 5,
            "FXY": 6,
            "Y": 7,
            "FY": 8,
            "Z": 9,
        }
        assert second == {"F1": 0, "B": 1, "B2": 1, "FAB": 2, "FB2": 2, "X": 3, "FXY": 4, "Y": 5, "FY": 6, "Z": 7}
        res = o.assign_levels()
        assert res == {
            0: ["F0", "F1"],
            1: ["A", "A2", "B", "B2"],
            2: ["FA2", "FAB", "FB2"],
            3: ["G", "X"],
            4: ["FG"],
            5: ["H"],
            6: ["FXY"],
            7: ["Y"],
            8: ["FY"],
            9: ["Z"],
        }

    def test_raises_when_person_is_both_parent_and_child_of_same_family(self):
        # Corrupt data: I1 is simultaneously a parent and a child of F1. F1 cannot be
        # a founder family because its parent I1 has origins, so no traversal ever
        # reaches F1 and it is reported as unassigned.
        t = FamilyTree(
            [Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"])],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="F1", to_id="I1")],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.assign_levels()
        payload = Utils.extract_json(str(ex))
        assert payload["unassigned_people"] == []
        assert payload["unassigned_families"] == ["F1"]

    def test_raises_when_person_is_their_own_grandparent(self):
        # Corrupt data: I1 is a parent of F1, whose child I2 is a parent of F2, whose
        # child is I1 again. The cycle gives every parent origins, so no family
        # qualifies as a founder family and the people are reported as disconnected.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="F2", to_id="I1"),
            ],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.assign_levels()
        msg = str(ex.value)
        assert "['I1', 'I2']" in msg
        assert "share no common nodes" in msg

    def test_empty_tree(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {}

    def test_one_family_one_parent_no_relationships(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["I1"], 1: ["F1"]}

    def test_one_family_two_parents_no_relationships(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["I1", "I2"], 1: ["F1"]}

    def test_one_family_one_parent(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["I1"], 1: ["F1"]}

    def test_one_family_two_parents(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["I1", "I2"], 1: ["F1"]}

    def test_one_family_two_parents_unused_marriages(self):
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1", "F3"]
                ),
                Person(
                    id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1", "F4"]
                ),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1"), Relationship(from_id="I2", to_id="F1")],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["I1", "I2"], 1: ["F1"]}

    def test_two_families_three_generations(self):
        people = [
            Person(
                id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandfather")], all_marriages=["F1"]
            ),
            Person(
                id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("grandmother")], all_marriages=["F1"]
            ),
            Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
            Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            Person(id="I5", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
            Person(id="I6", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")]),
            Person(id="I7", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")]),
        ]
        families = [Family(id="F1"), Family(id="F2")]
        relationships = [
            Relationship(from_id="I1", to_id="F1"),
            Relationship(from_id="I2", to_id="F1"),
            Relationship(from_id="F1", to_id="I3"),
            Relationship(from_id="F1", to_id="I5"),
            Relationship(from_id="I3", to_id="F2"),
            Relationship(from_id="I4", to_id="F2"),
            Relationship(from_id="F2", to_id="I6"),
            Relationship(from_id="F2", to_id="I7"),
        ]
        o = Organizer(FamilyTree(people, families, relationships))
        res = o.assign_levels()
        assert res == {0: ["I1", "I2"], 1: ["F1"], 2: ["I3", "I4", "I5"], 3: ["F2"], 4: ["I6", "I7"]}

    def test_call_assign_levels2_twice(self):
        people = [
            Person(
                id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandfather")], all_marriages=["F1"]
            ),
            Person(
                id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("grandmother")], all_marriages=["F1"]
            ),
            Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2"]),
            Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            Person(id="I5", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
            Person(id="I6", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")]),
            Person(id="I7", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")]),
        ]
        families = [Family(id="F1"), Family(id="F2")]
        relationships = [
            Relationship(from_id="I1", to_id="F1"),
            Relationship(from_id="I2", to_id="F1"),
            Relationship(from_id="F1", to_id="I3"),
            Relationship(from_id="F1", to_id="I5"),
            Relationship(from_id="I3", to_id="F2"),
            Relationship(from_id="I4", to_id="F2"),
            Relationship(from_id="F2", to_id="I6"),
            Relationship(from_id="F2", to_id="I7"),
        ]
        expected = {0: ["I1", "I2"], 1: ["F1"], 2: ["I3", "I4", "I5"], 3: ["F2"], 4: ["I6", "I7"]}
        # Verify assign_levels2() is idempotent when called a second time
        o = Organizer(FamilyTree(people, families, relationships))
        res = o.assign_levels()
        assert res == expected
        res = o.assign_levels()
        assert res == expected

    def test_three_generations_with_many_marriages(self):
        people = [
            Person(
                id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandfather")], all_marriages=["F1"]
            ),
            Person(
                id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("grandmother")], all_marriages=["F1"]
            ),
            Person(
                id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F2", "F3", "F4"]
            ),
            Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F2"]),
            Person(id="I5", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")]),
            Person(id="I6", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("son")]),
            Person(id="I7", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("daughter")]),
            Person(
                id="I8", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F3", "F5"]
            ),
            Person(id="I9", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F4"]),
            Person(id="I10", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F5"]),
        ]
        families = [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="F4"), Family(id="F5")]
        relationships = [
            Relationship(from_id="I1", to_id="F1"),
            Relationship(from_id="I2", to_id="F1"),
            Relationship(from_id="F1", to_id="I3"),
            Relationship(from_id="F1", to_id="I5"),
            Relationship(from_id="I3", to_id="F2"),
            Relationship(from_id="I4", to_id="F2"),
            Relationship(from_id="F2", to_id="I6"),
            Relationship(from_id="F2", to_id="I7"),
            Relationship(from_id="I3", to_id="F3"),
            Relationship(from_id="I8", to_id="F3"),
            Relationship(from_id="I3", to_id="F4"),
            Relationship(from_id="I9", to_id="F4"),
            Relationship(from_id="I8", to_id="F5"),
            Relationship(from_id="I10", to_id="F5"),
        ]
        expected = {
            0: ["I1", "I2"],
            1: ["F1"],
            2: ["I10", "I3", "I4", "I5", "I8", "I9"],
            3: ["F2", "F3", "F4", "F5"],
            4: ["I6", "I7"],
        }
        # Test that we can parse tree starting with any node
        for pos in range(len(people)):
            # print(f"Test position {pos}")  # noqa: T201
            people_clone = [*people]
            moved = people_clone.pop(pos)
            people_clone.insert(0, moved)
            o = Organizer(FamilyTree(people_clone, families, relationships))
            res = o.assign_levels()
            assert res == expected

    def test_uncle_marries_niece(self):
        # G has two children, A (uncle) and B. B's child N (niece) marries A.
        # This closes a cycle in the person/family graph (G -> A -> N -> B -> G). Blood
        # relationships pin A's level (sibling of B), so the cross-generational marriage
        # FAN cannot pull A down; FAN is pushed below its youngest spouse N instead and
        # its edge to A spans levels.
        people = [
            Person(id="G", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandparent")], all_marriages=["FG"]),
            Person(
                id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("uncle")], all_marriages=["FA", "FAN"]
            ),
            Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("parent")], all_marriages=["FB"]),
            Person(id="N", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("niece")], all_marriages=["FAN"]),
        ]
        families = [Family(id="FG"), Family(id="FA"), Family(id="FB"), Family(id="FAN")]
        relationships = [
            Relationship(from_id="G", to_id="FG"),
            Relationship(from_id="FG", to_id="A"),
            Relationship(from_id="FG", to_id="B"),
            Relationship(from_id="A", to_id="FA"),
            Relationship(from_id="B", to_id="FB"),
            Relationship(from_id="FB", to_id="N"),
            Relationship(from_id="A", to_id="FAN"),
            Relationship(from_id="N", to_id="FAN"),
        ]
        o = Organizer(FamilyTree(people, families, relationships))
        res = o.assign_levels()
        assert res == {0: ["G"], 1: ["FG"], 2: ["A", "B"], 3: ["FA", "FB"], 4: ["N"], 5: ["FAN"]}

    def test_uncle_marries_niece_without_own_second_marriage(self):
        # G has two children, A (uncle) and B. B's child N (niece) marries A.
        # This closes a cycle in the person/family graph (G -> A -> N -> B -> G). Blood
        # relationships pin A's level (sibling of B), so the cross-generational marriage
        # FAN cannot pull A down; FAN is pushed below its youngest spouse N instead and
        # its edge to A spans levels.
        people = [
            Person(id="G", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("grandparent")], all_marriages=["FG"]),
            Person(id="A", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("uncle")], all_marriages=["FAN"]),
            Person(id="B", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("parent")], all_marriages=["FB"]),
            Person(id="N", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("niece")], all_marriages=["FAN"]),
        ]
        families = [Family(id="FG"), Family(id="FB"), Family(id="FAN")]
        relationships = [
            Relationship(from_id="G", to_id="FG"),
            Relationship(from_id="FG", to_id="A"),
            Relationship(from_id="FG", to_id="B"),
            Relationship(from_id="B", to_id="FB"),
            Relationship(from_id="FB", to_id="N"),
            Relationship(from_id="A", to_id="FAN"),
            Relationship(from_id="N", to_id="FAN"),
        ]
        o = Organizer(FamilyTree(people, families, relationships))
        res = o.assign_levels()
        assert res == {0: ["G"], 1: ["FG"], 2: ["A", "B"], 3: ["FB"], 4: ["N"], 5: ["FAN"]}

    def test_grandfather_marries_grandniece(self):
        # P has two children, Gf (grandfather) and S (sibling). S's child N has child GN
        # (Gf's grandniece), who marries Gf. This closes a cycle spanning three generations
        # (P -> Gf -> GN -> N -> S -> P), a wider gap than test_uncle_marries_niece. Gf's level
        # is locked in via its blood relationship to P as soon as it is assigned, so the much
        # deeper traversal down S -> N -> GN cannot pull Gf down when it reaches the marriage
        # to GN.
        people = [
            Person(id="P", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("root")], all_marriages=["FP"]),
            Person(
                id="Gf",
                fillcolor=PersonWrapper.M_COLOR,
                text_lines=[TextLine("grandfather")],
                all_marriages=["FGf", "FGD"],
            ),
            Person(id="S", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("sibling")], all_marriages=["FS"]),
            Person(id="N", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("nephew")], all_marriages=["FN"]),
            Person(
                id="GN", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("grandniece")], all_marriages=["FGN"]
            ),
        ]
        families = [Family(id="FP"), Family(id="FGf"), Family(id="FS"), Family(id="FN"), Family(id="FGN")]
        relationships = [
            Relationship(from_id="P", to_id="FP"),
            Relationship(from_id="FP", to_id="Gf"),
            Relationship(from_id="FP", to_id="S"),
            Relationship(from_id="Gf", to_id="FGf"),
            Relationship(from_id="S", to_id="FS"),
            Relationship(from_id="FS", to_id="N"),
            Relationship(from_id="N", to_id="FN"),
            Relationship(from_id="FN", to_id="GN"),
            Relationship(from_id="Gf", to_id="FGN"),
            Relationship(from_id="GN", to_id="FGN"),
        ]
        o = Organizer(FamilyTree(people, families, relationships))
        res = o.assign_levels()
        assert res == {
            0: ["P"],
            1: ["FP"],
            2: ["Gf", "S"],
            3: ["FGf", "FS"],
            4: ["N"],
            5: ["FN"],
            6: ["GN"],
            7: ["FGN"],
        }

    def test_junction_at_grandchild_level(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("mother")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("Zoe")], all_marriages=["F2"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Bob")], all_marriages=["F3"]),
                Person(id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("Albert")], all_marriages=["F4"]),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("adopted child")]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3"), Family(id="F4")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="F1", to_id="I2"),
                Relationship(from_id="I2", to_id="F2"),
                Relationship(from_id="F2", to_id="I5"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="F3", to_id="I5"),
                Relationship(from_id="I4", to_id="F4"),
                Relationship(from_id="F4", to_id="I5"),
            ],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {
            0: ["I1"],
            1: ["F1"],
            2: ["I2", "I3", "I4"],
            3: ["F2", "F3", "F4"],
            4: ["I5"],
        }

    def test_child_adopted_by_grandparents_on_mother_side(self):
        # I5 is the biological child of I3 (mother) and I4 (father) via F2 and is also
        # adopted (dashed edge) by the maternal grandparents' family F1. Only the birth
        # link to F2 is rigid; the adopted link is soft, so F1 stays on the grandparent
        # generation and its edge to I5 spans levels instead of dragging F1 and F2 onto
        # the same level (which would be unsolvable, since F2's parent I3 is herself a
        # child of F1).
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("grandfather")],
                    all_marriages=["F1"],
                ),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("grandmother")],
                    all_marriages=["F1"],
                ),
                Person(id="I3", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("mother")], all_marriages=["F2"]),
                Person(id="I4", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("father")], all_marriages=["F2"]),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I4", to_id="F2"),
                Relationship(from_id="F2", to_id="I5"),
                Relationship(from_id="F1", to_id="I5", attrs={"style": "dashed"}),
            ],
        )
        o = Organizer(t)
        # The birth family stays primary; the grandparents' family is only an extra origin.
        assert o.people["I5"].primary_parent_family_id == "F2"
        res = o.assign_levels()
        assert res == {0: ["I1", "I2"], 1: ["F1"], 2: ["I3", "I4"], 3: ["F2"], 4: ["I5"]}

    def test_child_adopted_by_older_sister(self):
        # I5 is the birth child of I1 and I2 via F1 and is also adopted (dashed edge)
        # by F2, the family of his older sister I3 and her husband I4. The adoption
        # makes both of I5's links soft, so he sinks below all of his origin families:
        # one level under F2, next to where its birth children would sit, while the
        # birth edge from F1 spans two levels down to him.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("father")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("mother")], all_marriages=["F1"]),
                Person(
                    id="I3",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("older-sister")],
                    all_marriages=["F2"],
                ),
                Person(
                    id="I4",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("brother-in-law")],
                    all_marriages=["F2"],
                ),
                Person(id="I5", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="F1", to_id="I5"),
                Relationship(from_id="I3", to_id="F2"),
                Relationship(from_id="I4", to_id="F2"),
                Relationship(from_id="F2", to_id="I5", attrs={"style": "dashed"}),
            ],
        )
        o = Organizer(t)
        assert o.people["I5"].primary_parent_family_id == "F1"
        res = o.assign_levels()
        assert res == {0: ["I1", "I2"], 1: ["F1"], 2: ["I3", "I4"], 3: ["F2"], 4: ["I5"]}

    def test_adoptive_family_reached_only_through_adopted_child(self):
        # I3 is the birth child of I1 and I2 via F1 and is also adopted (dashed edge)
        # by F2, whose single parent I4 has no other connection to the tree. The only
        # path to F2 and I4 runs through the soft adopted link from I3, so placement
        # must follow adoption links from the child's side; the adoptive family lands
        # one level above the child, next to the birth family.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("child")]),
                Person(
                    id="I4",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("adoptive-mother")],
                    all_marriages=["F2"],
                ),
            ],
            [Family(id="F1"), Family(id="F2")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="F1", to_id="I3"),
                Relationship(from_id="I4", to_id="F2"),
                Relationship(from_id="F2", to_id="I3", attrs={"style": "dashed"}),
            ],
        )
        o = Organizer(t)
        assert o.people["I3"].primary_parent_family_id == "F1"
        res = o.assign_levels()
        assert res == {0: ["I1", "I2", "I4"], 1: ["F1", "F2"], 2: ["I3"]}

    def test_family_without_parents_at_top_of_hierarchy(self):
        # The constructor always registers whoever references a family in all_marriages
        # as one of its parents, so a family can't naturally end up with an empty parents
        # list. F0 is only referenced via I1 (F0 -> I1 makes I1 a child of F0, not a
        # parent) purely to satisfy the "family must be referenced" check; its parents
        # list is cleared afterward to model a family whose parents are unknown (e.g. a
        # Gramps export that stops short of the grandparents). Such a family has no
        # parents to climb further, so it ends up at the top of the hierarchy with only
        # its children below it.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
                Person(
                    id="I2",
                    fillcolor=PersonWrapper.F_COLOR,
                    text_lines=[TextLine("woman")],
                    all_marriages=["F1"],
                ),
            ],
            [Family(id="F0"), Family(id="F1")],
            [
                Relationship(from_id="F0", to_id="I1"),
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I2", to_id="F1"),
            ],
        )
        o = Organizer(t)
        o.families["F0"].parents = []
        res = o.assign_levels()
        assert res == {0: ["F0"], 1: ["I1", "I2"], 2: ["F1"]}

    def test_one_family_one_parent_only_relationships(self):
        # The parent link comes only from the relationship, not all_marriages; the
        # constructor still registers I1 as F1's parent, so F1 is a founder family.
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        res = o.assign_levels()
        assert res == {0: ["I1"], 1: ["F1"]}

    def test_three_families_two_parents_no_relationships_unused_family(self):
        # Nobody references F3, so it has no parents and counts as a founder family,
        # but its traversal shares nothing with the rest of the tree.
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1", "F2"]
                ),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [],
        )
        o = Organizer(t)
        with pytest.raises(ValueError) as ex:
            o.assign_levels()
        msg = str(ex.value)
        assert "['F3']" in msg
        assert "share no node" in msg
