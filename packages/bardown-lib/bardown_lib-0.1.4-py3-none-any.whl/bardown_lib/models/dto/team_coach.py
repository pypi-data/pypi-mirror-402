from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TeamCoach(BaseModel):
    team_id: Optional[str] = None
    coach_id: Optional[str] = None
    year: Optional[int] = None
    role: Optional[str] = None
    since: Optional[int] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
