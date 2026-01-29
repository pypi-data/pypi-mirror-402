from typing import Optional, Self

from .statistics import Statistics


class PlayerStatistics:
    _player_id: str
    _statistics: Optional[Statistics] = None

    def __init__(self, player_id: str, statistics: Statistics) -> Self:
        self._player_id = player_id
        self._statistics = statistics

    @property
    def player_id(self) -> str:
        return self._player_id

    @property
    def statistics(self) -> Statistics:
        return self._statistics

    def to_dict(self) -> dict:
        return {"player_id": self._player_id, "statistics": self._statistics.to_dict()}
