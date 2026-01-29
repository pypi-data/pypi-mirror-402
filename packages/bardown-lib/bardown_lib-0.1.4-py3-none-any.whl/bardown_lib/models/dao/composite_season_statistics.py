from typing import Dict, Self, Tuple


class CompositeSeasonStatistics:
    def __init__(
        self,
        team_id: str = None,
        name: str = None,
        player_id: str = None,
        year: int = None,
        statistics: str = None,
    ) -> Self:
        self.team_id = team_id
        self.name = name
        self.player_id = player_id
        self.year = year
        self.statistics = statistics

    @classmethod
    def from_tuple(cls, composite_statistics_tuple: Tuple) -> None:
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), composite_statistics_tuple)})

    def to_dict(self) -> Dict:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "player_id": self.player_id,
            "year": self.year,
            "statistics": self.statistics,
        }
