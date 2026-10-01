from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.skill import SkillCreate, SkillRead, SkillDependencyCreate, SkillDependencyRead
from services import crud

router = APIRouter(prefix="/api/goals", tags=["Skills"])


@router.post("/{goal_id}/skills", response_model=SkillRead, status_code=201)
def create_skill(goal_id: int, payload: SkillCreate, db: Session = Depends(get_db)):
    payload.goal_id = goal_id
    return crud.create_skill(db, payload)


@router.get("/{goal_id}/skills", response_model=List[SkillRead])
def list_skills(goal_id: int, db: Session = Depends(get_db)):
    return crud.list_skills_for_goal(db, goal_id)


@router.post("/{goal_id}/skill-dependencies", response_model=SkillDependencyRead, status_code=201)
def create_skill_dependency(goal_id: int, payload: SkillDependencyCreate, db: Session = Depends(get_db)):
    payload.goal_id = goal_id
    return crud.create_skill_dependency(db, payload)


@router.get("/{goal_id}/skill-dependencies", response_model=List[SkillDependencyRead])
def list_skill_dependencies(goal_id: int, db: Session = Depends(get_db)):
    return crud.list_dependencies_for_goal(db, goal_id)
