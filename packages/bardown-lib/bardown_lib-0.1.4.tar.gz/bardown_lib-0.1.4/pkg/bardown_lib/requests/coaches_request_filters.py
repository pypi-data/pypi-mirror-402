from typing import Optional

from pydantic import BaseModel


class CoachesRequestFilters(BaseModel):
    coach_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order: Optional[str] = None
    order_by: Optional[str] = None
