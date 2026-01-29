from typing import Dict, List, Self

from .composite_game_statistics import CompositeGameStatistics
from .composite_season_statistics import CompositeSeasonStatistics


class CompositeStatistics:
    games: List[CompositeGameStatistics]
    season: List[CompositeSeasonStatistics]

    def __init__(
        self,
        game_stats: List[CompositeGameStatistics],
        season_stats: List[CompositeSeasonStatistics],
    ) -> Self:
        self.games = game_stats
        self.season = season_stats

    def to_dict(self) -> Dict:
        return {
            "games": self.games.to_dict(),
            "season": self.season.to_dict(),
        }
