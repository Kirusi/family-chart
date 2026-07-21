"""Person object augmented with tree placement details."""

from family_chart.constants import MIN_LEVEL
from family_chart.origin_wrapper import OriginWrapper
from family_chart.person import Person


class PersonWrapper:
    """Person object augmented with tree placement details."""

    M_COLOR = "#e0e0ff"
    F_COLOR = "#ffe0e0"

    MAN = "M"
    WOMAN = "W"
    UNKNOWN = "N"

    id: str
    person: Person
    gender: str
    level: int
    origins: list[OriginWrapper]
    primary_parent_family_id: str

    def __init__(self, person: Person):
        """Default constructor."""
        self.id = person.id
        self.person = person
        self.gender = PersonWrapper.parse_color(person.fillcolor)
        self.level = MIN_LEVEL
        self.origins = []

    @staticmethod
    def parse_color(color: str):
        """Return person gender based on typical Gramps colors."""
        res = PersonWrapper.UNKNOWN
        if color == PersonWrapper.M_COLOR:
            res = PersonWrapper.MAN
        elif color == PersonWrapper.F_COLOR:
            res = PersonWrapper.WOMAN
        return res

    def find_primary_parent_family_id(self):
        """
        Assign primary_parent_family_id based on data in origins list.

        Primary family is the one where the child is born.
        If a family where child is related by birth is unknown, then it's the first family in the list.
        """
        if len(self.origins) > 0:
            origin_w = self.origins[0]
            family_id = origin_w.parent_family_id
            is_adopted = origin_w.is_adopted
            self.primary_parent_family_id = family_id
            if is_adopted:
                for i in range(1, len(self.origins)):
                    origin_w = self.origins[i]
                    family_id = origin_w.parent_family_id
                    is_adopted = origin_w.is_adopted
                    if not is_adopted:
                        self.primary_parent_family_id = family_id
                        break
