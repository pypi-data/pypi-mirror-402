from typing import Dict, Optional, Self


class Pagination:
    _limit: Optional[int]
    _offset: Optional[int]

    def __init__(self, limit: int = None, offset: int = None) -> Self:
        self._limit = self._limit_value(limit)
        self._offset = self._offset_value(offset)

    def _limit_value(self, limit: int) -> int | None:
        if limit is None or limit < 0 or limit > 10000:
            return None
        return limit

    def _offset_value(self, offset: int) -> int | None:
        if offset is None or offset < 0 or offset > 10000:
            return None
        return offset

    @property
    def limit(self) -> int:
        return self._limit

    @limit.setter
    def limit(self, new_limit: int) -> None:
        self._limit = self._limit_value(new_limit)

    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, new_offset) -> None:
        self._offset = self._offset_value(new_offset)

    def to_dict(self) -> Dict:
        data = {}

        if self._limit is not None:
            data["limit"] = self._limit
        if self._offset is not None:
            data["offset"] = self._offset

        return data
