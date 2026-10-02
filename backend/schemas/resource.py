from typing import Optional
from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    skill_id: int
    title: str = Field(..., min_length=1, max_length=400)
    url: Optional[str] = None
    source: Optional[str] = None
    duration_hours: Optional[float] = Field(None, ge=0)


class ResourceRead(BaseModel):
    # id is None for read-only catalogue fallback entries (not persisted rows)
    id: Optional[int] = None
    skill_id: int
    title: str
    url: Optional[str]
    source: Optional[str]
    duration_hours: Optional[float]
    format: Optional[str] = None

    model_config = {"from_attributes": True}
