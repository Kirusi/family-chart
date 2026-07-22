from family_chart.origin_wrapper import OriginWrapper
from family_chart.person import Person
from family_chart.person_wrapper import PersonWrapper


def make_person_w(person_id: str = "I1") -> PersonWrapper:
    return PersonWrapper(Person(id=person_id))


class TestFindPrimaryParentFamilyId:
    def test_no_origins_does_not_set_attribute(self):
        person_w = make_person_w()
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id is None

    def test_single_origin_not_adopted(self):
        person_w = make_person_w()
        person_w.origins = [OriginWrapper(parent_family_id="F1", is_adopted=False)]
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id == "F1"

    def test_single_origin_adopted_stays_as_only_option(self):
        person_w = make_person_w()
        person_w.origins = [OriginWrapper(parent_family_id="F1", is_adopted=True)]
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id == "F1"

    def test_first_origin_not_adopted_is_primary_even_with_others(self):
        person_w = make_person_w()
        person_w.origins = [
            OriginWrapper(parent_family_id="F1", is_adopted=False),
            OriginWrapper(parent_family_id="F2", is_adopted=False),
        ]
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id == "F1"

    def test_first_adopted_second_not_adopted_switches_to_second(self):
        person_w = make_person_w()
        person_w.origins = [
            OriginWrapper(parent_family_id="F1", is_adopted=True),
            OriginWrapper(parent_family_id="F2", is_adopted=False),
        ]
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id == "F2"

    def test_first_adopted_skips_further_adopted_until_birth_family_found(self):
        person_w = make_person_w()
        person_w.origins = [
            OriginWrapper(parent_family_id="F1", is_adopted=True),
            OriginWrapper(parent_family_id="F2", is_adopted=True),
            OriginWrapper(parent_family_id="F3", is_adopted=False),
        ]
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id == "F3"

    def test_all_origins_adopted_falls_back_to_first(self):
        person_w = make_person_w()
        person_w.origins = [
            OriginWrapper(parent_family_id="F1", is_adopted=True),
            OriginWrapper(parent_family_id="F2", is_adopted=True),
        ]
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id == "F1"

    def test_stops_at_first_non_adopted_ignoring_later_ones(self):
        person_w = make_person_w()
        person_w.origins = [
            OriginWrapper(parent_family_id="F1", is_adopted=True),
            OriginWrapper(parent_family_id="F2", is_adopted=False),
            OriginWrapper(parent_family_id="F3", is_adopted=False),
        ]
        person_w.find_primary_parent_family_id()
        assert person_w.primary_parent_family_id == "F2"
