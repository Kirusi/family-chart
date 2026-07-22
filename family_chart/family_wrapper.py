"""Family object augmented with layout details."""

from family_chart.constants import MIN_LEVEL
from family_chart.family import Family
from family_chart.person_wrapper import PersonWrapper


class FamilyWrapper:
    """Family object augmented with layout details."""

    id: str
    family: Family
    children: list[PersonWrapper]
    parents: list[PersonWrapper]
    level: int

    def __init__(self, family: Family):
        """Default constructor."""
        self.id = family.id
        self.family = family
        self.children = []
        self.parents = []
        self.level = MIN_LEVEL
