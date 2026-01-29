from typing import List

from pydantic import BaseModel

from .statistics import Statistics


class PlayerGameStatistics(BaseModel):
    player_id: str = None
    statistics: Statistics = None


class CompositeGameStatistics(BaseModel):
    game_id: str = None
    title: str = None
    statistics: List[PlayerGameStatistics] = []
