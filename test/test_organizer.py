import pytest

from family_chart.family import Family
from family_chart.family_tree import FamilyTree
from family_chart.organizer import Organizer, PersonWrapper
from family_chart.person import Person
from family_chart.relationship import Relationship
from family_chart.text_line import TextLine


def test_parse_color_unknown():
    assert PersonWrapper.parse_color("#123456") == "N"


def test_parse_color_none():
    assert PersonWrapper.parse_color(None) == "N"


class TestConstructor:
    def test_three_families_two_parents_no_relationships_unused_family(self):
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
        with pytest.raises(ValueError) as ex:
            _ = Organizer(t)
        msg = str(ex)
        assert "'F3'" in msg
        assert "not referenced" in msg

    def test_one_family_one_parent_only_relationships(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        with pytest.raises(ValueError) as ex:
            _ = Organizer(t)
        msg = str(ex)
        assert "'F1'" in msg
        assert "not referenced in any marriages" in msg

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
        try:
            _ = Organizer(t)
            raise AssertionError("No Exception was raised")
        except ValueError as ex:
            msg = str(ex)
        assert "from 'I1'" in msg
        assert "to 'F1'" in msg
        assert "does not reference any known family" in msg

    def test_unknown_marriage(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
            ],
            [Family(id="F1")],
            [],
        )
        try:
            _ = Organizer(t)
            raise AssertionError("No Exception was raised")
        except ValueError as ex:
            msg = str(ex)
        assert "Family 'F1'" in msg
        assert "not referenced in any marriages" in msg

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
        try:
            _ = Organizer(t)
            raise AssertionError("No Exception was raised")
        except ValueError as ex:
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
        try:
            _ = Organizer(t)
            raise AssertionError("No Exception was raised")
        except ValueError as ex:
            msg = str(ex)
        assert "from 'I2'" in msg
        assert "to 'F1'" in msg
        assert "not listed among person nodes" in msg


class TestAssignLevels:
    def test_for_source_direct_call_no_people(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        o.assign_levels_for_source("I1")
        res = o.serialize_by_level()
        assert res == {}

    def test_empty_tree(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {}

    def test_empty_tree_without_assign(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
        # o.assign_levels()
        res = o.serialize_by_level()
        assert res == {}

    def test_one_person_without_connections(self):
        t = FamilyTree([Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")])], [], [])
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1"]}

    def test_two_people_without_connections(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
            ],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1", "I2"]}

    def test_two_people_without_connections_different_order(self):
        t = FamilyTree(
            [
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
            ],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1", "I2"]}

    def test_three_people_without_connections(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
                Person(id="I2", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")]),
            ],
            [],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1", "I2", "I3"]}

    def test_one_family_one_parent_no_relationships(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
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
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1", "I2"], 1: ["F1"]}

    def test_three_families_two_parents_no_relationships(self):
        t = FamilyTree(
            [
                Person(
                    id="I1",
                    fillcolor=PersonWrapper.M_COLOR,
                    text_lines=[TextLine("man")],
                    all_marriages=["F1", "F2", "F3"],
                ),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1", "I2"], 1: ["F1", "F2", "F3"]}

    def test_one_family_one_parent(self):
        t = FamilyTree(
            [
                Person(id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1"]),
            ],
            [Family(id="F1")],
            [Relationship(from_id="I1", to_id="F1")],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
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
        o.assign_levels()
        res = o.serialize_by_level()
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
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1", "I2"], 1: ["F1"]}

    def test_two_unrelated_families_four_parents_three_marriages(self):
        t = FamilyTree(
            [
                Person(
                    id="I1", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F1", "F2"]
                ),
                Person(id="I2", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F1"]),
                Person(id="I3", fillcolor=PersonWrapper.M_COLOR, text_lines=[TextLine("man")], all_marriages=["F3"]),
                Person(id="I4", fillcolor=PersonWrapper.F_COLOR, text_lines=[TextLine("woman")], all_marriages=["F3"]),
            ],
            [Family(id="F1"), Family(id="F2"), Family(id="F3")],
            [
                Relationship(from_id="I1", to_id="F1"),
                Relationship(from_id="I1", to_id="F2"),
                Relationship(from_id="I2", to_id="F1"),
                Relationship(from_id="I3", to_id="F3"),
                Relationship(from_id="I4", to_id="F3"),
            ],
        )
        o = Organizer(t)
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["I1", "I2", "I3", "I4"], 1: ["F1", "F2", "F3"]}

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
        expected = {0: ["I1", "I2"], 1: ["F1"], 2: ["I3", "I4", "I5"], 3: ["F2"], 4: ["I6", "I7"]}
        # Test that we can parse tree starting with any node
        for pos in range(0, len(people)):
            people_clone = [*people]
            moved = people_clone.pop(pos)
            people_clone.insert(0, moved)
            o = Organizer(FamilyTree(people_clone, families, relationships))
            o.assign_levels()
            res = o.serialize_by_level()
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
        for pos in range(0, len(people)):
            # print(f"Test position {pos}")  # noqa: T201
            people_clone = [*people]
            moved = people_clone.pop(pos)
            people_clone.insert(0, moved)
            o = Organizer(FamilyTree(people_clone, families, relationships))
            o.assign_levels()
            res = o.serialize_by_level()
            assert res == expected


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


class TestOrderMarriages:
    def test_unknown_person_raises_value_error(self):
        t = FamilyTree([], [], [])
        o = Organizer(t)
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
        reviewed_people = set()
        reviewed_families = {"F1"}
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I3", "I1"]
        assert [f.id for f in res.families] == ["F2"]
        assert reviewed_people == {"I1", "I3"}
        assert reviewed_families == {"F1", "F2"}

    def test_multiple_marriages_skips_already_reviewed_family2(self):
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
        reviewed_people = set()
        reviewed_families = {"F2"}
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I2", "I1"]
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
        reviewed_people = set()
        reviewed_families = set()
        res = o.order_marriages("I1", reviewed_people, reviewed_families)
        assert [p.id for p in res.people] == ["I3", "I1"]
        assert [f.id for f in res.families] == ["F1", "F2"]
        assert reviewed_people == {"I1", "I3"}
        assert reviewed_families == {"F1", "F2"}
