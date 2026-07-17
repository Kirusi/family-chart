"""Family object augmented with layout details."""

from family_chart.constants import MIN_LEVEL
from family_chart.family import Family


class FamilyWrapper:
    """Family object augmented with layout details."""

    def __init__(self, family: Family):
        """Default constructor."""
        self.id = family.id
        self.family = family
        self.children = []
        self.parents = []
        self.level = MIN_LEVEL
