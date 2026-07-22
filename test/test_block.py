import pytest

from family_chart.block import Block
from family_chart.family import Family
from family_chart.family_wrapper import FamilyWrapper
from family_chart.person import Person
from family_chart.person_wrapper import PersonWrapper


def make_person_w(person_id: str) -> PersonWrapper:
    return PersonWrapper(Person(id=person_id))


def make_family_w(family_id: str) -> FamilyWrapper:
    return FamilyWrapper(Family(id=family_id))


class TestConstructor:
    def test_default_constructor(self):
        block = Block()
        assert block.people == []
        assert block.families == []

    def test_starts_with_single_person_and_no_families(self):
        person_w = make_person_w("I1")
        block = Block(person_w)
        assert block.people == [person_w]
        assert block.families == []


class TestAddPerson:
    def test_appends_to_end(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        block = Block(person_w1)
        block.add_person(person_w2)
        assert block.people == [person_w1, person_w2]

    def test_appends_multiple_in_order(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        person_w3 = make_person_w("I3")
        block = Block(person_w1)
        block.add_person(person_w2)
        block.add_person(person_w3)
        assert block.people == [person_w1, person_w2, person_w3]


class TestAddPersonRelatively:
    def test_inserts_left_of_anchor_by_default_direction(self):
        anchor = make_person_w("I1")
        new_person = make_person_w("I2")
        block = Block(anchor)
        block.add_person_relatively(new_person, anchor_id="I1", direction="L")
        assert block.people == [new_person, anchor]

    def test_inserts_right_of_anchor(self):
        anchor = make_person_w("I1")
        new_person = make_person_w("I2")
        block = Block(anchor)
        block.add_person_relatively(new_person, anchor_id="I1", direction="R")
        assert block.people == [anchor, new_person]

    def test_inserts_relative_to_middle_anchor(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        person_w3 = make_person_w("I3")
        block = Block(person_w1)
        block.add_person(person_w2)
        new_person = make_person_w("I4")
        block.add_person_relatively(new_person, anchor_id="I2", direction="R")
        assert block.people == [person_w1, person_w2, new_person]
        block.add_person_relatively(person_w3, anchor_id="I2", direction="L")
        assert block.people == [person_w1, person_w3, person_w2, new_person]

    def test_raises_when_anchor_not_found(self):
        anchor_w = make_person_w("I1")
        block = Block(anchor_w)
        with pytest.raises(ValueError) as ex:
            block.add_person_relatively(make_person_w("I2"), anchor_id="unknown", direction="R")
        msg = str(ex.value)
        assert "Person anchor" in msg
        assert "'unknown'" in msg
        assert "not found" in msg
        assert block.people == [anchor_w]


class TestAddFamily:
    def test_appends_to_end(self):
        block = Block(make_person_w("I1"))
        family_w1 = make_family_w("F1")
        family_w2 = make_family_w("F2")
        block.add_family(family_w1)
        block.add_family(family_w2)
        assert block.families == [family_w1, family_w2]


class TestAddFamilyRelatively:
    def test_inserts_left_of_anchor(self):
        block = Block(make_person_w("I1"))
        anchor = make_family_w("F1")
        new_family = make_family_w("F2")
        block.add_family(anchor)
        block.add_family_relatively(new_family, anchor_id="F1", direction="L")
        assert block.families == [new_family, anchor]

    def test_inserts_right_of_anchor(self):
        block = Block(make_person_w("I1"))
        anchor = make_family_w("F1")
        new_family = make_family_w("F2")
        block.add_family(anchor)
        block.add_family_relatively(new_family, anchor_id="F1", direction="R")
        assert block.families == [anchor, new_family]

    def test_inserts_relative_to_middle_anchor(self):
        block = Block(make_person_w("I1"))
        family_w1 = make_family_w("F1")
        family_w2 = make_family_w("F2")
        family_w3 = make_family_w("F3")
        block.add_family(family_w1)
        block.add_family(family_w2)
        new_family = make_family_w("F4")
        block.add_family_relatively(new_family, anchor_id="F2", direction="R")
        assert block.families == [family_w1, family_w2, new_family]
        block.add_family_relatively(family_w3, anchor_id="F2", direction="L")
        assert block.families == [family_w1, family_w3, family_w2, new_family]

    def test_raises_when_anchor_not_found(self):
        block = Block(make_person_w("I1"))
        block.add_family(make_family_w("F1"))
        with pytest.raises(ValueError) as ex:
            block.add_family_relatively(make_family_w("F2"), anchor_id="unknown", direction="R")
        msg = str(ex.value)
        assert "Family anchor" in msg
        assert "'unknown'" in msg
        assert "not found" in msg
