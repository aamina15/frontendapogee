from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    model_config = {"str_strip_whitespace": True}

    title: str = Field(..., min_length=3, max_length=300)
    hours_per_week: float = Field(10.0, ge=1, le=168)
    duration_weeks: int = Field(12, ge=1, le=104)
    budget: Optional[float] = Field(None, ge=0)


class GoalUpdate(BaseModel):
    model_config = {"str_strip_whitespace": True}

    title: Optional[str] = Field(None, min_length=3, max_length=300)
    hours_per_week: Optional[float] = Field(None, ge=1, le=168)
    duration_weeks: Optional[int] = Field(None, ge=1, le=104)
    budget: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None


class GoalRead(BaseModel):
    id: int
    title: str
    hours_per_week: float
    duration_weeks: int
    budget: Optional[float]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
