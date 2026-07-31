"""Determines locations for person and family nodes."""

import json
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from family_chart import constants
from family_chart.block import Block
from family_chart.family_tree import FamilyTree
from family_chart.family_wrapper import FamilyWrapper
from family_chart.origin_wrapper import OriginWrapper
from family_chart.person_wrapper import PersonWrapper
from family_chart.row import Row


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
        for person_w in self.people.values():
            verified_marriages = []
            if person_w.person.all_marriages:
                for marriage_id in person_w.person.all_marriages:
                    if marriage_id in self.families:
                        verified_marriages.append(marriage_id)
            person_w.person.all_marriages = verified_marriages
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
                is_adopted = (
                    relationship.attrs and "style" in relationship.attrs and relationship.attrs["style"] != "solid"
                )
                origin_w = OriginWrapper(from_id, is_adopted)
                person_w.origins.append(origin_w)
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
            person_w.find_primary_parent_family_id()
        for family_w in self.families.values():
            if len(family_w.parents) == 2:
                first_parent_id = family_w.parents[0]
                second_parent_id = family_w.parents[1]
                if (
                    self.people[first_parent_id].gender != PersonWrapper.MAN
                    and self.people[second_parent_id].gender == PersonWrapper.MAN
                ):
                    family_w.parents = [second_parent_id, first_parent_id]

    def validate_preliminary_assignments(self):
        """Check whether some people or families were left unassigned."""
        unassigned_people = []
        assigned_people = []
        for person_w in self.people.values():
            if person_w.level == constants.MIN_LEVEL:
                unassigned_people.append(person_w.id)
            else:
                assigned_people.append(person_w.id)
        unassigned_families = []
        assigned_families = []
        for family_w in self.families.values():
            if family_w.level == constants.MIN_LEVEL:
                unassigned_families.append(family_w.id)
            else:
                assigned_families.append(family_w.id)
        if unassigned_people or unassigned_families:
            results = {
                "unassigned_people": sorted(unassigned_people),
                "unassigned_families": sorted(unassigned_families),
                "assigned_people": sorted(assigned_people),
                "assigned_families": sorted(assigned_families),
            }
            raise ValueError(f"Some people and or families were not assigned a level. Details: {json.dumps(results)}")

    def validate_final_assignments(self) -> dict[str, list[str]]:
        """Check that levels are contiguous and homogenous."""
        all_levels = defaultdict(list)
        for person_w in self.people.values():
            level = person_w.level
            all_levels[level].append(person_w)
        for family_w in self.families.values():
            level = family_w.level
            all_levels[level].append(family_w)

        serialized_levels = self.get_ids_by_level()
        for level in range(len(all_levels)):
            nodes = all_levels[level]
            if len(nodes) == 0:
                raise ValueError(f"No nodes are placed at level {level}. Level structure is {serialized_levels}")
            first_node = nodes[0]
            node_type = "person"
            if isinstance(first_node, FamilyWrapper):
                node_type = "family"
            for n in nodes[1:]:
                if (node_type == "person" and not isinstance(n, PersonWrapper)) or (
                    node_type == "family" and not isinstance(n, FamilyWrapper)
                ):
                    raise ValueError(
                        f"Nodes at level '{level}' are expected to be of '{node_type}' type. "
                        f"Actual nodes are {json.dumps(serialized_levels[level])}"
                    )
        return serialized_levels

    def get_ids_by_level(self) -> dict[str, list[str]]:
        """Return a dictionary where level is the key and sorted list of ids is the value."""
        all_object_levels = self.get_objects_by_level()
        all_levels = defaultdict(list)
        for level, node_list in all_object_levels.items():
            for n in node_list:
                all_levels[level].append(n.id)
        for level in all_levels:
            all_levels[level] = sorted(all_levels[level])
        return all_levels

    def get_objects_by_level(self) -> dict[str, list[Any]]:
        """Return a dictionary where level is the key and a list of nodes is the value."""
        all_levels = defaultdict(list)
        for person_w in self.people.values():
            level = person_w.level
            all_levels[level].append(person_w)
        for family_w in self.families.values():
            level = family_w.level
            all_levels[level].append(family_w)
        return all_levels

    def find_founder_families(self) -> list[str]:
        """
        Return sorted ids of founders' families.

        A founders' family is one where none of the parents is a child of another
        family, i.e. every parent has no parents specified. A family without any
        parents is also a founders' family.
        """
        res = []
        for family_w in self.families.values():
            if all(not self.people[parent_id].origins for parent_id in family_w.parents):
                res.append(family_w.id)
        return sorted(res)

    def init_descendant_distances(self, founder_family_id: str, distances: dict[str, int] | None) -> dict[str, int]:
        """Validate and return the starting distances for a descendant traversal."""
        if founder_family_id not in self.families:
            raise ValueError(f"Family '{founder_family_id}' is not a known family")
        if distances is None:
            return {founder_family_id: 0}
        if founder_family_id not in distances:
            raise ValueError(f"Family '{founder_family_id}' has no distance in the given dictionary")
        return distances

    def measure_descendant_distances(
        self, founder_family_id: str, distances: dict[str, int] | None = None
    ) -> dict[str, int]:
        """
        Measure the generation distance of every descendant of a founder family.

        The founder family sits at distance 0. Every child connected by birth of a
        traversed family sits one below the family and each of that child's marriages
        one below the child. A node reachable through several paths keeps the length
        of the longest path. Spouses who married into the tree are left out; they are
        added afterwards by include_spouses.

        When a dictionary of distances is given, the traversal starts from the
        founder family's existing distance in it instead of 0 and pushes already
        known nodes down where a longer path is found; the given dictionary is
        updated in place and returned.
        """
        distances = self.init_descendant_distances(founder_family_id, distances)
        marriages_of = defaultdict(list)
        for family_w in self.families.values():
            for parent_id in family_w.parents:
                marriages_of[parent_id].append(family_w.id)
        # In an acyclic tree no path is longer than the total node count
        max_distance = distances[founder_family_id] + len(self.people) + len(self.families)
        queue = deque([founder_family_id])
        while queue:
            family_id = queue.popleft()
            family_distance = distances[family_id]
            if family_distance > max_distance:
                raise ValueError(
                    f"Ancestry cycle detected while traversing descendants of family '{founder_family_id}'"
                )
            for child_id in self.families[family_id].children:
                child_distance = family_distance + 1
                if distances.get(child_id, constants.MIN_LEVEL) < child_distance:
                    distances[child_id] = child_distance
                    for marriage_id in marriages_of[child_id]:
                        if distances.get(marriage_id, constants.MIN_LEVEL) < child_distance + 1:
                            distances[marriage_id] = child_distance + 1
                            queue.append(marriage_id)
        return distances

    def include_spouses(self, distances: dict[str, int]) -> None:
        """
        Add parents of traversed families who are not descendants themselves.

        Such a spouse sits one above the oldest of their traversed marriages: the
        family with the smallest distance, whichever position it holds in the
        person's marriage list. A spouse whose marriage list contains no traversed
        family sits one above the family that found them.
        """
        spouse_distances: dict[str, int] = {}
        for node_id, node_distance in distances.items():
            if node_id in self.families:
                for parent_id in self.families[node_id].parents:
                    if parent_id not in distances and parent_id not in spouse_distances:
                        oldest_marriage_distance = node_distance
                        for marriage_id in self.people[parent_id].person.all_marriages:
                            if marriage_id in distances and distances[marriage_id] < oldest_marriage_distance:
                                oldest_marriage_distance = distances[marriage_id]
                        spouse_distances[parent_id] = oldest_marriage_distance - 1
        distances.update(spouse_distances)

    def find_closest_common_node(
        self, first_distances: dict[str, int], second_distances: dict[str, int]
    ) -> tuple[str, int, int] | None:
        """
        Return the common node of two descendant traversals and its distance in each of them.

        Both dictionaries are produced by measure_descendant_distances from
        different founders' families. A common node is a family or person present
        in both; among those the node with the smallest distance in the first
        dictionary wins, with ties broken by id. Returns None when the traversals
        share no node.
        """
        common_ids = [node_id for node_id in first_distances if node_id in second_distances]
        if not common_ids:
            return None
        closest_id = min(common_ids, key=lambda node_id: (first_distances[node_id], node_id))
        return closest_id, first_distances[closest_id], second_distances[closest_id]

    def merge_shifted_distances(
        self, first_distances: dict[str, int], second_distances: dict[str, int], shift: int
    ) -> dict[str, int]:
        """
        Merge two distance dictionaries, shifting every distance in the second one by the given amount.

        A node present in both keeps the longest of its two distances, mirroring
        how measure_descendant_distances treats a node reachable through several
        paths.
        """
        res = dict(first_distances)
        for node_id, node_distance in second_distances.items():
            shifted = node_distance + shift
            if res.get(node_id, constants.MIN_LEVEL) < shifted:
                res[node_id] = shifted
        return res

    def assign_levels(self) -> dict[str, list[str]]:  # noqa: C901
        """
        Assign a level to every node by merging the descendant traversals of all founder families.

        Each founder family is traversed with measure_descendant_distances. The
        first traversal seeds the result; on every step a remaining traversal
        that shares a node with the result is aligned and merged into it. The
        comparison sees each traversal with its spouses included, so lines
        connected only through a shared spouse (e.g. one person married twice)
        can be merged too. Spouses who married into the tree are
        added at the end, and the resulting distances are stored as the levels
        of the corresponding PersonWrapper and FamilyWrapper objects. Levels
        are then shifted to start at zero, validated, and returned in
        serialized form. Raises when some founder families are not connected
        to the rest of the tree.
        """
        founder_ids = self.find_founder_families()
        if not founder_ids:
            match len(self.people):
                case 0:
                    return {}
                case 1:
                    base = {list(self.people.keys())[0]: 0}
                case _:
                    all_person_ids = sorted(self.people.keys())
                    raise ValueError(f"People {all_person_ids} share no common nodes")
        else:
            pending = [(founder_id, self.measure_descendant_distances(founder_id)) for founder_id in founder_ids]
            founder_id, base = pending.pop(0)
            while pending:
                # Compare traversals with their spouses included, so lines connected
                # only through a shared spouse (e.g. one person married twice) align.
                # The raw traversals are merged instead, so spouses keep the level
                # include_spouses gives them at the end.
                base_with_spouses = dict(base)
                self.include_spouses(base_with_spouses)
                merged_index = None
                for index, (_founder_id, additional) in enumerate(pending):
                    additional_with_spouses = dict(additional)
                    self.include_spouses(additional_with_spouses)
                    common = self.find_closest_common_node(base_with_spouses, additional_with_spouses)
                    if common is not None:
                        merged_index = index
                        break
                if merged_index is None:
                    unmerged = sorted(founder_id for founder_id, _ in pending)
                    raise ValueError(f"Founder families {unmerged} share no node with the merged tree")
                pending.pop(merged_index)
                _, first_distance, second_distance = common
                base = self.merge_shifted_distances(base, additional, first_distance - second_distance)
            self.include_spouses(base)
        for node_id, node_distance in base.items():
            if node_id in self.people:
                self.people[node_id].level = node_distance
            else:
                self.families[node_id].level = node_distance

        self.validate_preliminary_assignments()
        # Adjust levels to start with zero
        min_level_people = 0
        if self.people:
            min_level_people = min(self.people.values(), key=lambda obj: obj.level).level
        min_level_families = 0
        if self.families:
            min_level_families = min(self.families.values(), key=lambda obj: obj.level).level
        min_level = min(min_level_people, min_level_families)
        for person_w in self.people.values():
            person_w.level -= min_level
        for family_w in self.families.values():
            family_w.level -= min_level

        serialized_levels = self.validate_final_assignments()
        return serialized_levels

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

    def organize_row(  # noqa: C901
        self,
        levels: dict[str, list[Any]],
        reviewed_people: set[str],
        reviewed_families: set[str],
        start_level: int = 0,
        previous_row: Row | None = None,
    ) -> Row:
        """Create blocks for a row, pulling in the previous row's children first when it is provided."""
        res: Row = Row()
        first_level = levels.get(start_level)
        if first_level is None and start_level != 0:
            id_levels = self.get_ids_by_level()
            raise ValueError(
                f"Cannot organize a non-existing row. Requested level is '{start_level}', "
                f"but levels are: {json.dumps(id_levels)}"
            )
        if first_level:
            first_wrapper = first_level[0]
            if isinstance(first_wrapper, FamilyWrapper):
                if previous_row is not None:
                    raise ValueError(f"Expected to find people in row '{start_level}', but found families")
                for family_w in first_level:
                    block = Block()
                    block.add_family(family_w)
                    res.add_block(block)
                    reviewed_families.add(family_w.id)
            elif isinstance(first_wrapper, PersonWrapper):
                if previous_row is not None:
                    parent_families = [
                        family for family_list in previous_row.get_families() for family in family_list
                    ]  # flatten the list
                    children_ids = []
                    for family_w in parent_families:
                        for child_id in family_w.children:
                            child_w = self.people[child_id]
                            if child_w.primary_parent_family_id == family_w.id:
                                children_ids.append(child_w.id)
                    for id in children_ids:
                        if id not in reviewed_people:
                            block = self.order_marriages(id, reviewed_people, reviewed_families)
                            res.add_block(block)
                family_level = levels.get(start_level + 1, [])
                sorted_people = sorted(first_level, key=lambda person_w: person_w.sorting_key)
                for person_w in sorted_people:
                    if person_w.id not in reviewed_people:
                        block = self.order_marriages(person_w.id, reviewed_people, reviewed_families)
                        res.add_block(block)
                for family_w in family_level:
                    if family_w.id not in reviewed_families:
                        block = Block()
                        block.add_family(family_w)
                        res.add_block(block)
                        reviewed_families.add(family_w.id)
            else:
                raise ValueError(f"Unexpected object in one of the assigned levels {first_wrapper}")
        return res

    def organize_tree(self) -> list[Row]:
        """Return list of rows for all people and families in the tree."""
        reviewed_people = set()
        reviewed_families = set()
        res = []
        self.assign_levels()
        levels = self.get_objects_by_level()
        previous_row = None
        current_height = 0
        remaining_levels = len(levels)
        while remaining_levels > 0:
            current_row = self.organize_row(levels, reviewed_people, reviewed_families, current_height, previous_row)
            current_row_height = 0
            if current_row.get_people_count() > 0:
                current_row_height += 1
            if current_row.get_family_count() > 0:
                current_row_height += 1
            current_height += current_row_height
            remaining_levels -= current_row_height
            res.append(current_row)
            previous_row = current_row

        return res
