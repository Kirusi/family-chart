"""Block is a layout unit that groups one person with all their marriages, spouses and marriages of spouses."""

from family_chart.family_wrapper import FamilyWrapper
from family_chart.person_wrapper import PersonWrapper


class Block:
    """Block is a layout unit that groups one person with all their marriages, spouses and marriages of spouses."""

    people: list[PersonWrapper]
    families: list[FamilyWrapper]

    def __init__(self, person_w: PersonWrapper | None = None):
        """Default constructor."""
        self.people = []
        if person_w:
            self.people.append(person_w)
        self.families = []

    def add_person(self, new_person_w: PersonWrapper):
        """Add one more person to the end of the list."""
        self.people.append(new_person_w)

    def add_person_relatively(self, new_person_w: PersonWrapper, anchor_id: str, direction: str):
        """Add one more person to the block relatively to another person."""
        pos = None
        for i, person_w in enumerate(self.people):
            if person_w.id == anchor_id:
                pos = i
                break
        if pos is None:
            raise ValueError(f"Person anchor '{anchor_id}' is not found in the block")
        if direction == "R":
            pos += 1
        self.people.insert(pos, new_person_w)

    def add_family(self, new_family_w: FamilyWrapper):
        """Add one more family to the end of the list."""
        self.families.append(new_family_w)

    def add_family_relatively(self, new_family_w: FamilyWrapper, anchor_id: str, direction: str):
        """Add one more family to the block relatively to another family."""
        pos = None
        for i, family_w in enumerate(self.families):
            if family_w.id == anchor_id:
                pos = i
                break
        if pos is None:
            raise ValueError(f"Family anchor '{anchor_id}' is not found in the block")
        if direction == "R":
            pos += 1
        self.families.insert(pos, new_family_w)
