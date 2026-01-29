from typing import Optional

from pydantic import BaseModel


class PlayersRequestFilters(BaseModel):
    player_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    number: Optional[str] = None
    grade: Optional[str] = None
    position: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order: Optional[str] = None
    order_by: Optional[str] = None