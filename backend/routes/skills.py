from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.goal import Goal
from models.skill import Skill, SkillDependency
from schemas.skill import SkillCreate, SkillRead, SkillDependencyCreate, SkillDependencyRead
from services import crud

router = APIRouter(prefix="/api/goals", tags=["Skills"])


def _require_goal(db: Session, goal_id: int) -> None:
    """Parent-goal guard: skills and dependencies must never be created for a
    nonexistent goal (SQLite does not enforce the FK; orphan rows would later
    attach to whichever goal reuses the id)."""
    if not db.query(Goal).filter(Goal.id == goal_id).first():
        raise HTTPException(status_code=404, detail="Goal not found")


def _require_goal_skill(db: Session, goal_id: int, skill_id: int) -> None:
    if not db.query(Skill).filter(Skill.id == skill_id, Skill.goal_id == goal_id).first():
        raise HTTPException(status_code=404, detail="Skill not found in this goal")


@router.post("/{goal_id}/skills", response_model=SkillRead, status_code=201)
def create_skill(goal_id: int, payload: SkillCreate, db: Session = Depends(get_db)):
    _require_goal(db, goal_id)
    payload.goal_id = goal_id
    return crud.create_skill(db, payload)


@router.get("/{goal_id}/skills", response_model=List[SkillRead])
def list_skills(goal_id: int, db: Session = Depends(get_db)):
    return crud.list_skills_for_goal(db, goal_id)


@router.post("/{goal_id}/skill-dependencies", response_model=SkillDependencyRead, status_code=201)
def create_skill_dependency(goal_id: int, payload: SkillDependencyCreate, db: Session = Depends(get_db)):
    _require_goal(db, goal_id)
    _require_goal_skill(db, goal_id, payload.prerequisite_skill_id)
    _require_goal_skill(db, goal_id, payload.dependent_skill_id)
    payload.goal_id = goal_id
    return crud.create_skill_dependency(db, payload)


@router.get("/{goal_id}/skill-dependencies", response_model=List[SkillDependencyRead])
def list_skill_dependencies(goal_id: int, db: Session = Depends(get_db)):
    return crud.list_dependencies_for_goal(db, goal_id)
