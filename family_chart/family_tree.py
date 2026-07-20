"""Umbrella container for all objects in the family chart."""

from family_chart.family_wrapper import FamilyWrapper
from family_chart.person_wrapper import PersonWrapper
from family_chart.relationship import Relationship


class FamilyTree:
    """Umbrella container for all objects in the family chart."""

    people: list[PersonWrapper]
    families: list[FamilyWrapper]
    relationships: list[Relationship]

    def __init__(self, people: list[PersonWrapper], families: list[FamilyWrapper], relationships: list[Relationship]):
        """Default constructor."""
        self.people = people
        self.families = families
        self.relationships = relationships
