"""Person object augmented with tree placement details."""

from family_chart.constants import MIN_LEVEL
from family_chart.person import Person


class PersonWrapper:
    """Person object augmented with tree placement details."""

    M_COLOR = "#e0e0ff"
    F_COLOR = "#ffe0e0"

    MAN = "M"
    WOMAN = "W"
    UNKNOWN = "N"

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
