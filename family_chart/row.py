"""List of blocks for one generation of people and families in a tree."""

from family_chart.block import Block
from family_chart.family_wrapper import FamilyWrapper
from family_chart.person_wrapper import PersonWrapper


class Row:
    """List of blocks for one generation of people and families in a tree."""

    blocks: list[Block] = []

    def __init__(self):
        """Default constructor."""
        self.blocks = []

    def add_block(self, block: Block) -> None:
        """Add block to the list."""
        self.blocks.append(block)

    def get_people(self) -> list[list[PersonWrapper]]:
        """Return list of PersonWrapper objects for each block."""
        res = [[*b.people] for b in self.blocks]
        return res

    def get_people_ids(self) -> list[list[str]]:
        """Return list of people id-lists for each block."""
        res = [[p.id for p in b.people] for b in self.blocks]
        return res

    def get_people_count(self) -> int:
        """Return number of people in all blocks."""
        res = sum(len(b.people) for b in self.blocks)
        return res

    def get_families(self) -> list[list[FamilyWrapper]]:
        """Return list of FamilyWrapper objects for each block."""
        res = [[*b.families] for b in self.blocks]
        return res

    def get_family_ids(self) -> list[list[str]]:
        """Return list of family id-lists for each block."""
        res = [[f.id for f in b.families] for b in self.blocks]
        return res

    def get_family_count(self) -> int:
        """Return number of families in all blocks."""
        res = sum(len(b.families) for b in self.blocks)
        return res
