from typing import Optional
from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    goal_id: int
    name: str = Field(..., min_length=1, max_length=200)
    target_level: str = Field("Proficient")
    importance: float = Field(1.0, ge=1.0, le=5.0)


class SkillRead(BaseModel):
    id: int
    goal_id: int
    name: str
    target_level: str
    importance: float

    model_config = {"from_attributes": True}


class SkillDependencyCreate(BaseModel):
    goal_id: int
    prerequisite_skill_id: int
    dependent_skill_id: int


class SkillDependencyRead(BaseModel):
    id: int
    goal_id: int
    prerequisite_skill_id: int
    dependent_skill_id: int

    model_config = {"from_attributes": True}
