from typing import List, Self

from models.composite_season_statistics import CompositeSeasonStatistics
from models.player_statistics import PlayerStatistics


class CompositeSeasonStatistics:
    _year: int


class CompositeSeasonStatisticsFull(CompositeSeasonStatistics):
    _team_id: str
    _team_name: str
    _players: List[PlayerStatistics]

    def __init__(
        self, year: int, team_id: str, team_name: str, players: List[PlayerStatistics]
    ) -> Self:
        super().__init__()
        self._year = year
        self._team_id = team_id
        self._team_name = team_name
        self._players = players

    @property
    def year(self) -> int:
        return self._year

    @property
    def team_id(self) -> str:
        return self._team_id

    @property
    def team_name(self) -> str:
        return self._team_name

    @property
    def players(self) -> List[PlayerStatistics]:
        return self._players

    def to_dict(self) -> dict:
        return {
            "year": self._year,
            "team_id": self._team_id,
            "team_name": self._team_name,
            "players": [player_stats.to_dict() for player_stats in self.players],
        }


class CompositeSeasonByYear(CompositeSeasonStatistics):
    _data: List[CompositeSeasonStatisticsFull]

    def __init__(self, year: int, data: List[CompositeSeasonStatisticsFull]) -> None:
        self._year = year
        self._data = data

    @property
    def year(self) -> int:
        return self._year

    @property
    def data(self) -> List[CompositeSeasonStatisticsFull]:
        return self._data

    def to_dict(self) -> dict:
        return {
            "year": self._year,
            "data": [data.to_dict() for data in self._data],
        }
