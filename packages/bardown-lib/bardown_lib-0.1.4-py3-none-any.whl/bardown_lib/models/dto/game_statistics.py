from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .statistics import Statistics


class GameStatistics(BaseModel):
    player_id: Optional[str] = None
    game_id: Optional[str] = None
    statistics: Optional[Statistics] = None
    created: Optional[datetime] = datetime.now()
    modified: Optional[datetime] = datetime.now()
