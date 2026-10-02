from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MasteryCreate(BaseModel):
    model_config = {"extra": "forbid"}

    goal_id: int
    skill_id: int
    diagnostic_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class MasteryUpdate(BaseModel):
    # Assessment results can only be written by server-side quiz grading.
    model_config = {"extra": "forbid"}

    diagnostic_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class MasteryRead(BaseModel):
    id: int
    goal_id: int
    skill_id: int
    diagnostic_score: Optional[float]
    verification_score: Optional[float]
    verified: bool
    updated_at: datetime

    model_config = {"from_attributes": True}
