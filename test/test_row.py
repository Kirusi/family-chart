from family_chart.block import Block
from family_chart.family import Family
from family_chart.family_wrapper import FamilyWrapper
from family_chart.person import Person
from family_chart.person_wrapper import PersonWrapper
from family_chart.row import Row


def make_person_w(person_id: str) -> PersonWrapper:
    return PersonWrapper(Person(id=person_id))


def make_family_w(family_id: str) -> FamilyWrapper:
    return FamilyWrapper(Family(id=family_id))


class TestConstructor:
    def test_default_constructor(self):
        row = Row()
        assert row.blocks == []

    def test_instances_do_not_share_blocks_list(self):
        row1 = Row()
        row2 = Row()
        row1.add_block(Block(make_person_w("I1")))
        assert row1.blocks != row2.blocks
        assert row2.blocks == []


class TestAddBlock:
    def test_appends_to_end(self):
        block1 = Block(make_person_w("I1"))
        block2 = Block(make_person_w("I2"))
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        assert row.blocks == [block1, block2]


class TestGetPeople:
    def test_empty_row_returns_empty_list(self):
        row = Row()
        assert row.get_people() == []

    def test_returns_people_grouped_by_block(self):
        person_w1 = make_person_w("I1")
        person_w2 = make_person_w("I2")
        person_w3 = make_person_w("I3")
        block1 = Block(person_w1)
        block1.add_person(person_w2)
        block2 = Block(person_w3)
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        assert row.get_people() == [[person_w1, person_w2], [person_w3]]

    def test_returned_lists_are_copies(self):
        person_w1 = make_person_w("I1")
        block = Block(person_w1)
        row = Row()
        row.add_block(block)
        res = row.get_people()
        res[0].append(make_person_w("I2"))
        assert block.people == [person_w1]


class TestGetPeopleIds:
    def test_empty_row_returns_empty_list(self):
        row = Row()
        assert row.get_people_ids() == []

    def test_returns_ids_grouped_by_block(self):
        block1 = Block(make_person_w("I1"))
        block1.add_person(make_person_w("I2"))
        block2 = Block(make_person_w("I3"))
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        assert row.get_people_ids() == [["I1", "I2"], ["I3"]]


class TestGetPeopleCount:
    def test_empty_row_returns_zero(self):
        row = Row()
        assert row.get_people_count() == 0

    def test_counts_people_across_all_blocks(self):
        block1 = Block(make_person_w("I1"))
        block1.add_person(make_person_w("I2"))
        block2 = Block(make_person_w("I3"))
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        assert row.get_people_count() == 3

    def test_counts_block_with_no_people(self):
        row = Row()
        row.add_block(Block())
        assert row.get_people_count() == 0


class TestGetFamilies:
    def test_empty_row_returns_empty_list(self):
        row = Row()
        assert row.get_families() == []

    def test_returns_families_grouped_by_block(self):
        family_w1 = make_family_w("F1")
        family_w2 = make_family_w("F2")
        family_w3 = make_family_w("F3")
        block1 = Block(make_person_w("I1"))
        block1.add_family(family_w1)
        block1.add_family(family_w2)
        block2 = Block(make_person_w("I2"))
        block2.add_family(family_w3)
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        assert row.get_families() == [[family_w1, family_w2], [family_w3]]

    def test_returned_lists_are_copies(self):
        family_w1 = make_family_w("F1")
        block = Block(make_person_w("I1"))
        block.add_family(family_w1)
        row = Row()
        row.add_block(block)
        res = row.get_families()
        res[0].append(make_family_w("F2"))
        assert block.families == [family_w1]


class TestGetFamilyIds:
    def test_empty_row_returns_empty_list(self):
        row = Row()
        assert row.get_family_ids() == []

    def test_returns_ids_grouped_by_block(self):
        block1 = Block(make_person_w("I1"))
        block1.add_family(make_family_w("F1"))
        block1.add_family(make_family_w("F2"))
        block2 = Block(make_person_w("I2"))
        block2.add_family(make_family_w("F3"))
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        assert row.get_family_ids() == [["F1", "F2"], ["F3"]]


class TestGetFamilyCount:
    def test_empty_row_returns_zero(self):
        row = Row()
        assert row.get_family_count() == 0

    def test_counts_families_across_all_blocks(self):
        block1 = Block(make_person_w("I1"))
        block1.add_family(make_family_w("F1"))
        block1.add_family(make_family_w("F2"))
        block2 = Block(make_person_w("I2"))
        block2.add_family(make_family_w("F3"))
        row = Row()
        row.add_block(block1)
        row.add_block(block2)
        assert row.get_family_count() == 3

    def test_counts_block_with_no_families(self):
        row = Row()
        row.add_block(Block(make_person_w("I1")))
        assert row.get_family_count() == 0
