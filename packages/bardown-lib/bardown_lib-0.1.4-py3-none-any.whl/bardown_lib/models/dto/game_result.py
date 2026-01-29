from datetime import datetime
from typing import List, Optional

from enums.position import Position
from pydantic import BaseModel

from .statistics import Statistics


class PlayerWithStatistics(BaseModel):
    player_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    position: Optional[Position] = None
    number: Optional[int] = 0
    statistics: Optional[Statistics] = None
    img_url: Optional[str] = "static/blank.jpg"


class GameTeamResult(BaseModel):
    team_id: Optional[str] = None
    name: Optional[str] = "Team"
    img_url: Optional[str] = "static/blank.jpg"
    roster: Optional[List[PlayerWithStatistics]] = []


class GameResult(BaseModel):
    game_id: Optional[str] = None
    title: Optional[str] = "Away @ Home"
    date: Optional[datetime] = None
    score: Optional[str] = "0-0"
    location: Optional[str] = None
    home: Optional[GameTeamResult] = GameTeamResult()
    away: Optional[GameTeamResult] = GameTeamResult()
