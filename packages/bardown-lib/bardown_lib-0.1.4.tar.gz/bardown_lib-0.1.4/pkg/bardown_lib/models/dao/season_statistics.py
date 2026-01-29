from datetime import datetime
from typing import Dict, Self, Tuple


class SeasonStatistics:
    def __init__(
        self,
        player_id: str = None,
        team_id: str = None,
        year: int = None,
        statistics: str = None,
        created: datetime = None,
        modified: datetime = None,
    ) -> Self:
        self.player_id = player_id
        self.team_id = team_id
        self.year = year
        self.statistics = statistics
        self.created = created
        self.modified = modified

    @classmethod
    def from_tuple(cls, season_statistics_tuple: Tuple) -> None:
        """Create season statistics from a tuple

        Args:
            player_tuple (Tuple): Tuple containing ordered season statistic data
        """
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), season_statistics_tuple)})

    def to_dict(self) -> Dict:
        return {
            "player_id": f"{self.player_id}",
            "team_id": f"{self.team_id}",
            "year": f"{self.year}",
            "statistics": f"{self.statistics}",
            "created": f"{self.created}",
            "modified": f"{self.modified}",
        }
