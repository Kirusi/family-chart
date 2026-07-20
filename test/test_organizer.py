import pytest

from family_chart.block import Block
from family_chart.family import Family
from family_chart.family_tree import FamilyTree
from family_chart.organizer import BlockQueueItem, Organizer, PersonWrapper
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

    def test_uncle_marries_niece(self):
        # G has two children, A (uncle) and B. B's child N (niece) marries A.
        # This closes a cycle in the person/family graph (G -> A -> N -> B -> G). A's level
        # is first assigned via its blood relationship to G (sibling of B), and that
        # assignment is locked in immediately (assign_levels_for_source marks a node as
        # visited as soon as it is assigned/queued, not only when it is later popped), so the
        # cross-generational marriage FAN cannot overwrite it once B's branch reaches N.
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
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["G"], 1: ["FG"], 2: ["A", "B"], 3: ["FA", "FB"], 4: ["N"], 5: ["FAN"]}

    def test_uncle_marries_niece2(self):
        # G has two children, A (uncle) and B. B's child N (niece) marries A.
        # This closes a cycle in the person/family graph (G -> A -> N -> B -> G). A's level
        # is first assigned via its blood relationship to G (sibling of B), and that
        # assignment is locked in immediately (assign_levels_for_source marks a node as
        # visited as soon as it is assigned/queued, not only when it is later popped), so the
        # cross-generational marriage FAN cannot overwrite it once B's branch reaches N.
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
        o.assign_levels()
        res = o.serialize_by_level()
        assert res == {0: ["G"], 1: ["FG"], 2: ["A", "B"], 3: ["FB"], 4: ["N"], 5: ["FAN"]}

    def test_grandfather_marries_grandniece(self):
        # P has two children, Gf (grandfather) and S (sibling). S's child C has child D
        # (Gf's grandniece), who marries Gf. This closes a cycle spanning three generations
        # (P -> Gf -> D -> C -> S -> P), a wider gap than test_uncle_marries_niece. Gf's level
        # is locked in via its blood relationship to P as soon as it is assigned, so the much
        # deeper traversal down S -> C -> D cannot pull Gf down when it reaches the marriage
        # to D.
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
        o.assign_levels()
        res = o.serialize_by_level()
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
        # F2 is pre-marked reviewed (and its other parent I3 pre-marked reviewed too), so
        # that marriage must be skipped without adding anything, and the loop must still
        # continue on to F3 afterwards instead of stopping early.
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

    def test_marriage_family_at_unexpected_level_is_filtered_out2(self):
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

    def test_unknown_person_in_queue_raises_key_error(self):
        # person_w is never actually None here: a missing id raises KeyError on lookup
        # before the "is None" check below it can ever fire.
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
        with pytest.raises(ValueError):
            o.order_marriages_from_queue(block, 1, queue, reviewed_people, reviewed_families)

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
