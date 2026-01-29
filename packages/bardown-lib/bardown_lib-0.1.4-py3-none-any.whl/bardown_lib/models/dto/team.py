from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Team(BaseModel):
    team_id: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    img_url: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
