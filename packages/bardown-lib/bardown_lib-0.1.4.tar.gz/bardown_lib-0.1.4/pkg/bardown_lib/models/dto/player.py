from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Player(BaseModel):
    player_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    number: Optional[int] = None
    position: Optional[str] = None
    grade: Optional[str] = None
    school: Optional[str] = None
    imgurl: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self, full_definition: bool = False) -> dict:
        player_dict = {
            "player_id": self.player_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "position": self.position,
            "number": self.number,
            "grade": self.grade,
            "school": self.school,
            "img_url": self.imgurl,
        }

        if full_definition:
            player_dict.update({"created": self.created, "modified": self.modified})

        return player_dict
