"""Person Node in a family chart."""

from dataclasses import dataclass

from family_chart.family import Family
from family_chart.person import Person
from family_chart.relationship import Relationship


@dataclass
class DescendantsResult:
    """Descendants of a founder family, their distances, and the data used to reach them."""

    distances: dict[str, int]
    people: list[Person]
    families: list[Family]
    relationships: list[Relationship]
