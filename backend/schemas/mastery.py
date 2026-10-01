from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MasteryCreate(BaseModel):
    goal_id: int
    skill_id: int
    diagnostic_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class MasteryUpdate(BaseModel):
    diagnostic_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    verification_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    verified: Optional[bool] = None


class MasteryRead(BaseModel):
    id: int
    goal_id: int
    skill_id: int
    diagnostic_score: Optional[float]
    verification_score: Optional[float]
    verified: bool
    updated_at: datetime

    model_config = {"from_attributes": True}
