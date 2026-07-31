"""Umbrella container for all objects in the family chart."""

from family_chart.family import Family
from family_chart.person import Person
from family_chart.relationship import Relationship


class FamilyTree:
    """Umbrella container for all objects in the family chart."""

    people: list[Person]
    families: list[Family]
    relationships: list[Relationship]

    def __init__(self, people: list[Person], families: list[Family], relationships: list[Relationship]):
        """Default constructor."""
        self.people = people
        self.families = families
        self.relationships = relationships
