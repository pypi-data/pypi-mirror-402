from datetime import datetime
from typing import Dict, Self, Tuple


class GameStatistics:
    def __init__(
        self,
        player_id: str = None,
        game_id: str = None,
        statistics: str = None,
        created: datetime = None,
        modified: datetime = None,
    ) -> Self:
        self.player_id = player_id
        self.game_id = game_id
        self.statistics = statistics
        self.created = created
        self.modified = modified

    @classmethod
    def from_tuple(cls, game_statistics_tuple: Tuple) -> None:
        """Create game statistics from a tuple

        Args:
            player_tuple (Tuple): Tuple containing ordered game statistic data
        """
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), game_statistics_tuple)})

    def to_dict(self) -> Dict:
        return {
            "player_id": f"{self.player_id}",
            "game_id": f"{self.game_id}",
            "statistics": f"{self.statistics}",
            "created": f"{self.created}",
            "modified": f"{self.modified}",
        }
