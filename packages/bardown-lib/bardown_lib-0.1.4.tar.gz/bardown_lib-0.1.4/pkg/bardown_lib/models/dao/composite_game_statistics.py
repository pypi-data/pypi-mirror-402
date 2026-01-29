from typing import Dict, Self, Tuple


class CompositeGameStatistics:
    def __init__(
        self, game_id: str = None, title: str = None, statistics: str = None, player_id: str = None
    ) -> Self:
        self.game_id = game_id
        self.title = title
        self.player_id = player_id
        self.statistics = statistics

    @classmethod
    def from_tuple(cls, composite_statistics_tuple: Tuple) -> None:
        return cls(**{k: v for k, v in zip(cls().to_dict().keys(), composite_statistics_tuple)})

    def to_dict(self) -> Dict:
        return {
            "game_id": self.game_id,
            "title": self.title,
            "player_id": self.player_id,
            "statistics": self.statistics,
        }
