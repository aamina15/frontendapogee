from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class RouteCreate(BaseModel):
    goal_id: int
    version: int = 1
    total_hours: Optional[float] = None
    total_weeks: Optional[int] = None
    route_json: Optional[str] = None   # JSON string
    change_reason: Optional[str] = None


class RouteRead(BaseModel):
    id: int
    goal_id: int
    version: int
    total_hours: Optional[float]
    total_weeks: Optional[int]
    route_json: Optional[str]
    change_reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
