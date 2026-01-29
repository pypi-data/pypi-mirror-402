from datetime import datetime
from typing import Optional

from enums.position import Position
from pydantic import BaseModel


class TeamPlayer(BaseModel):
    team_id: Optional[str] = None
    player_id: Optional[str] = None
    year: Optional[int] = None
    number: Optional[int] = None
    position: Optional[Position] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
