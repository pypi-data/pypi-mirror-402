from typing import Dict, List, Self


class PlayersFilters:
    def __init__(
        self,
        player_ids: List[str] = None,
        first_names: List[str] = None,
        last_names: List[str] = None,
        numbers: List[str] = None,
        positions: List[str] = None,
        grades: List[str] = None,
        limit: int = 40,
        offset: int = 0,
        order: str = None,
        order_by: str = None,
    ) -> Self:
        self.player_ids = player_ids
        self.first_names = first_names
        self.last_names = last_names
        self.numbers = numbers
        self.positions = positions
        self.grades = grades
        self.limit = limit
        self.offset = offset
        self.order = order
        self.order_by = order_by

    def _should_add_contents_of_list(self, data: List) -> bool:
        return data is not None and len(data) > 0

    def to_dict(self) -> Dict:
        filters = {}

        if self._should_add_contents_of_list(self.player_ids):
            filters["filter.playerId"] = str.join(",", self.player_ids)
        if self._should_add_contents_of_list(self.first_names):
            filters["filter.firstName"] = str.join(",", self.first_names)
        if self._should_add_contents_of_list(self.last_names):
            filters["filter.lastName"] = str.join(",", self.last_names)
        if self._should_add_contents_of_list(self.positions):
            filters["filter.position"] = str.join(",", self.positions)
        if self._should_add_contents_of_list(self.numbers):
            filters["filter.number"] = str.join(",", self.numbers)
        if self._should_add_contents_of_list(self.grades):
            filters["filter.grade"] = str.join(",", self.grades)

        if self.limit is not None:
            filters["limit"] = self.limit
        if self.offset is not None:
            filters["offset"] = self.offset
        if self.order is not None:
            filters["order"] = self.order
        if self.order_by is not None:
            filters["orderBy"] = self.order_by

        return filters
