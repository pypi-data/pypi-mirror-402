from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Game(BaseModel):
    game_id: Optional[str] = None
    title: Optional[str] = None
    date: Optional[datetime] = None
    score: Optional[str] = None
    location: Optional[str] = None
    created: Optional[datetime] = datetime.now()
    modified: Optional[datetime] = datetime.now()

    @property
    def date(self) -> str:
        return datetime.fromisoformat(self.date).strftime("%A \t %m/%d/%Y \t - \t %I:%M %p")
