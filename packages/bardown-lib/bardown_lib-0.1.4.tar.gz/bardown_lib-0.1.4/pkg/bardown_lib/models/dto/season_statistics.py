from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from .statistics import Statistics


class SeasonStatistics(BaseModel):
    player_id: Optional[str] = None
    team_id: Optional[str] = None
    year: Optional[int] = None
    statistics: Optional[Statistics] = None
    created: Optional[datetime] = datetime.now()
    modified: Optional[datetime] = datetime.now()
