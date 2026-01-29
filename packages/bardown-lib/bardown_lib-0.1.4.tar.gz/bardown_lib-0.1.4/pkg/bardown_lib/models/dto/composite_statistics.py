from typing import List, Optional

from pydantic import BaseModel

from .composite_game_statistics import CompositeGameStatistics
from .composite_season_statistics import CompositeSeasonStatistics


class CompositeStatistics(BaseModel):
    games: Optional[List[CompositeGameStatistics]] = []
    season: Optional[List[CompositeSeasonStatistics]] = []
