"""Determines locations for person and family nodes."""

from collections import defaultdict
from dataclasses import dataclass

from family_chart.block import Block
from family_chart.constants import MIN_LEVEL
from family_chart.family_tree import FamilyTree
from family_chart.family_wrapper import FamilyWrapper
from family_chart.person_wrapper import PersonWrapper


@dataclass
class BlockQueueItem:
    """Person Node in a family chart."""

    person_id: str
    family_id: str
    direction: str


class Organizer:
    """Determines locations for person and family nodes."""

    family_tree: FamilyTree
    people: dict[str, PersonWrapper]
    families: dict[str, FamilyWrapper]

    def __init__(self, family_tree: FamilyTree):  # noqa: C901
        """Default constructor."""
        self.family_tree = family_tree
        self.people = {}
        self.families = {}
        for person in family_tree.people:
            id = person.id
            self.people[id] = PersonWrapper(person)
        for family in family_tree.families:
            id = family.id
            self.families[id] = FamilyWrapper(family)
        referenced_families = set()
        for person_w in self.people.values():
            verified_marriages = []
            if person_w.person.all_marriages:
                for marriage_id in person_w.person.all_marriages:
                    if marriage_id in self.families:
                        verified_marriages.append(marriage_id)
                        referenced_families.add(marriage_id)
            person_w.person.all_marriages = verified_marriages
        for family_id in self.families:
            if family_id not in referenced_families:
                raise ValueError(
                    f"Family '{family_id}' is provided in GraphViz file, but not referenced in any marriages"
                )
        for relationship in self.family_tree.relationships:
            from_id = relationship.from_id
            to_id = relationship.to_id
            if from_id in self.families:
                family_w = self.families[from_id]
                if to_id not in self.people:
                    raise ValueError(
                        f"Relationship from '{from_id}' to '{to_id}' refences '{to_id}' "
                        "which is not listed among person nodes."
                    )
                family_w.children.append(to_id)
                person_w = self.people[to_id]
                person_w.origins.append(from_id)
            elif to_id in self.families:
                family_w = self.families[to_id]
                if from_id not in self.people:
                    raise ValueError(
                        f"Relationship from '{from_id}' to '{to_id}' refences '{from_id}' "
                        "which is not listed among person nodes."
                    )
                family_w.parents.append(from_id)
            else:
                raise ValueError(f"Relationship from '{from_id}' to '{to_id}' does not reference any known family")
        for person_w in self.people.values():
            if person_w.person.all_marriages:
                for family_id in person_w.person.all_marriages:
                    family_w = self.families.get(family_id)
                    if family_w and person_w.id not in family_w.parents:
                        family_w.parents.append(person_w.id)
        for family_w in self.families.values():
            if len(family_w.parents) == 2:
                first_parent_id = family_w.parents[0]
                second_parent_id = family_w.parents[1]
                if (
                    self.people[first_parent_id].gender != PersonWrapper.MAN
                    and self.people[second_parent_id].gender == PersonWrapper.MAN
                ):
                    family_w.parents = [second_parent_id, first_parent_id]

    def assign_levels(self) -> None:  # noqa: C901
        """Assign levels to all families and people in the tree."""
        if self.people:
            while True:
                start_id = None
                for person_w in self.people.values():
                    if person_w.level == MIN_LEVEL:
                        start_id = person_w.id
                        break
                if start_id:
                    self.assign_levels_for_source(start_id)
                else:
                    break
            for person_w in self.people.values():
                if person_w.level == MIN_LEVEL:
                    raise RuntimeError(f"Person node id '{person_w.id}' was not assigned a level")  # pragma: no cover
            for family_w in self.families.values():
                if family_w.id == MIN_LEVEL:
                    raise RuntimeError(f"Family node id '{family_w.id}' was not assigned a level")  # pragma: no cover
            min_level_people = min(self.people.values(), key=lambda obj: obj.level).level
            min_level_families = 0
            if self.families:
                min_level_families = min(self.families.values(), key=lambda obj: obj.level).level
            min_level = min(min_level_people, min_level_families)
            for person_w in self.people.values():
                person_w.level -= min_level
            for family_w in self.families.values():
                family_w.level -= min_level

    def assign_levels_for_source(self, start_id: str):  # noqa: C901
        """Assign levels to all families and people in the tree."""
        if self.people:
            first_person_w = self.people[start_id]
            first_person_w.level = 0
            visited_node_ids = {start_id}
            nodes_to_track = []
            for fam_id in first_person_w.person.all_marriages:
                family_w = self.families[fam_id]
                family_w.level = 1
                visited_node_ids.add(fam_id)
                nodes_to_track.append(family_w)
            for fam_id in first_person_w.origins:
                family_w = self.families[fam_id]
                family_w.level = -1
                visited_node_ids.add(fam_id)
                nodes_to_track.append(family_w)

            while len(nodes_to_track) > 0:
                tracked_node = nodes_to_track.pop()
                level = tracked_node.level
                if tracked_node.id in self.families:
                    family_node_w = tracked_node
                    for id in family_node_w.parents:
                        if id not in visited_node_ids:
                            person_w = self.people[id]
                            person_w.level = level - 1
                            visited_node_ids.add(id)
                            nodes_to_track.append(person_w)
                    for id in family_node_w.children:
                        if id not in visited_node_ids:
                            person_w = self.people[id]
                            person_w.level = level + 1
                            visited_node_ids.add(id)
                            nodes_to_track.append(person_w)
                elif tracked_node.id in self.people:  # pragma: no branch
                    person_node_w = tracked_node
                    for id in person_node_w.origins:
                        if id not in visited_node_ids:
                            family_w = self.families[id]
                            family_w.level = level - 1
                            visited_node_ids.add(id)
                            nodes_to_track.append(family_w)
                    for id in person_node_w.person.all_marriages:
                        if id not in visited_node_ids:
                            family_w = self.families[id]
                            family_w.level = level + 1
                            visited_node_ids.add(id)
                            nodes_to_track.append(family_w)

    def serialize_by_level(self):
        """Return a dictionary where level is the key and sorted list od ids is the value."""
        all_levels = defaultdict(list)
        for person_w in self.people.values():
            level = person_w.level
            all_levels[level].append(person_w.id)
        for family_w in self.families.values():
            level = family_w.level
            all_levels[level].append(family_w.id)
        for level in all_levels:
            all_levels[level] = sorted(all_levels[level])
        return all_levels

    def find_other_parent(self, family_id: str, person_id: str) -> str | None:
        """Return the id of the other parent in a family, or None if there isn't one."""
        if family_id not in self.families:
            raise ValueError(f"Family '{family_id}' is not a known family")
        family_w = self.families[family_id]
        if person_id not in family_w.parents:
            raise ValueError(f"Person '{person_id}' is not one of the parents in family '{family_id}'")
        for parent_id in family_w.parents:
            if parent_id != person_id:
                return parent_id
        return None

    def filter_marriages_by_level(
        self, marriage_ids: list[str], expected_level: int, reviewed_families: set[str]
    ) -> list[FamilyWrapper]:
        """Check that all provided familes have the expected level and were not previously reviewed."""
        filtered_marriages: list[FamilyWrapper] = []
        for family_id in marriage_ids:
            if family_id not in reviewed_families:
                family_w = self.families.get(family_id)
                if family_w is None:
                    raise ValueError(f"Family '{family_id}' is unknown")
                if family_w.level == expected_level:
                    filtered_marriages.append(family_w)
        return filtered_marriages

    def order_marriages(  # noqa: C901
        self, person_id: str, reviewed_people: set[str], reviewed_families: set[str]
    ) -> Block:
        """For each row order people and marriages in chronological order."""
        if person_id not in self.people:
            raise ValueError(f"Person '{person_id}' is not a known person")
        res = None
        if person_id not in reviewed_people:
            queue: list[BlockQueueItem] = []
            person_w = self.people[person_id]
            expected_level = person_w.level
            res = Block(person_w)
            reviewed_people.add(person_id)
            gender = person_w.gender
            all_marriages = person_w.person.all_marriages
            filtered_marriages = self.filter_marriages_by_level(all_marriages, expected_level + 1, reviewed_families)
            match len(filtered_marriages):
                case 0:
                    pass
                case 1:
                    family_w = filtered_marriages[0]
                    family_id = family_w.id
                    reviewed_families.add(family_id)
                    res.add_family(family_w)
                    other_parent_id = self.find_other_parent(family_id, person_id)
                    if other_parent_id is not None:
                        other_parent_w = self.people[other_parent_id]
                        if gender == PersonWrapper.MAN:
                            if other_parent_id not in reviewed_people:
                                res.add_person_relatively(other_parent_w, person_id, "R")
                                queue.append(
                                    BlockQueueItem(person_id=other_parent_id, family_id=family_id, direction="R")
                                )
                        else:
                            if other_parent_id not in reviewed_people:
                                res.add_person_relatively(other_parent_w, person_id, "L")
                                queue.append(
                                    BlockQueueItem(person_id=other_parent_id, family_id=family_id, direction="L")
                                )
                        reviewed_people.add(other_parent_id)
                case _:
                    is_first = True
                    for family_w in filtered_marriages:
                        family_id = family_w.id
                        reviewed_families.add(family_id)
                        res.add_family(family_w)
                        other_parent_id = self.find_other_parent(family_id, person_id)
                        if other_parent_id is not None and other_parent_id not in reviewed_people:
                            other_parent_w = self.people[other_parent_id]
                            reviewed_people.add(other_parent_id)
                            if is_first:
                                res.add_person_relatively(other_parent_w, person_id, "L")
                                queue.append(
                                    BlockQueueItem(person_id=other_parent_id, family_id=family_id, direction="L")
                                )
                                is_first = False
                            else:
                                res.add_person(other_parent_w)
                                queue.append(
                                    BlockQueueItem(person_id=other_parent_id, family_id=family_id, direction="R")
                                )
            self.order_marriages_from_queue(res, expected_level, queue, reviewed_people, reviewed_families)
        return res

    def order_marriages_from_queue(
        self,
        block: Block,
        expected_level: int,
        _queue: list[BlockQueueItem],
        reviewed_people: set[str],
        reviewed_families: set[str],
    ) -> None:
        """Review and add spouses of spouses."""
        queue = [*_queue]
        for item in queue:
            person_id = item.person_id
            family_id = item.family_id
            direction = item.direction
            person_w = self.people.get(person_id)
            if person_w is None:
                raise ValueError(f"Person '{person_id}' is unknown")
            anchor_person_id = person_id
            anchor_family_id = family_id
            all_marriages = person_w.person.all_marriages
            expected_level = person_w.level
            filtered_marriages = self.filter_marriages_by_level(all_marriages, expected_level + 1, reviewed_families)
            for marriage_w in filtered_marriages:
                marriage_id = marriage_w.id
                if marriage_id != family_id:
                    other_parent_id = self.find_other_parent(marriage_id, person_id)
                    if other_parent_id is not None and other_parent_id not in reviewed_people:
                        other_parent_w = self.people.get(other_parent_id)
                        if other_parent_w is None:
                            raise ValueError(f"Person '{other_parent_id}' not found")
                        reviewed_people.add(other_parent_id)
                        queue.append(BlockQueueItem(other_parent_id, marriage_id, direction))
                        block.add_person_relatively(other_parent_w, anchor_person_id, direction)
                        anchor_person_id = other_parent_id
                    if marriage_id not in reviewed_families:
                        reviewed_families.add(marriage_id)
                        block.add_family_relatively(marriage_w, anchor_family_id, direction)
                        anchor_family_id = marriage_id
