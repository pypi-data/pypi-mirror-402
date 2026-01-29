from typing import Dict, List, Self


class TeamFilters:
    def __init__(
        self,
        team_ids: List[str] = None,
        names: List[str] = None,
        limit: int = 40,
        offset: int = 0,
        order: str = "ASC",
        order_by: str = "name",
    ) -> Self:
        self.team_ids = team_ids
        self.names = names
        self.limit = limit
        self.offset = offset
        self.order = order
        self.order_by = order_by

    def _should_add_contents_of_list(self, data: List) -> bool:
        return data is not None and len(data) > 0

    def to_dict(self) -> Dict:
        filters = {}

        if self._should_add_contents_of_list(self.team_ids):
            filters["filter.teamId"] = str.join(",", self.team_ids)
        if self._should_add_contents_of_list(self.names):
            filters["filter.name"] = str.join(",", self.names)

        filters["limit"] = self.limit
        filters["offset"] = self.offset
        filters["order"] = self.order
        filters["orderBy"] = self.order_by

        return filters
