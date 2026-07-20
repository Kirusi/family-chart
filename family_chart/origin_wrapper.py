"""Details about a child in a family."""

from dataclasses import dataclass


@dataclass
class OriginWrapper:
    """Details about a child in a family."""

    parent_family_id: str
    is_adopted: bool
