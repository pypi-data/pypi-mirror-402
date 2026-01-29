from typing import List, Optional

from pydantic import BaseModel

from .statistics import Statistics


class PlayerSeasonStatistics(BaseModel):
    player_id: Optional[str] = None
    statistics: Optional[Statistics] = None


class CompositeSeasonStatistics(BaseModel):
    year: Optional[int] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    players: Optional[List[PlayerSeasonStatistics]] = []
