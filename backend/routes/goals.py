from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.goal import GoalCreate, GoalRead, GoalUpdate
from services import crud

router = APIRouter(prefix="/api/goals", tags=["Goals"])


@router.post("", response_model=GoalRead, status_code=201)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)):
    return crud.create_goal(db, payload)


@router.get("", response_model=List[GoalRead])
def list_goals(db: Session = Depends(get_db)):
    return crud.list_goals(db)


@router.get("/active", response_model=GoalRead)
def get_active_goal(db: Session = Depends(get_db)):
    goal = crud.get_active_goal(db)
    if not goal:
        raise HTTPException(status_code=404, detail="No active goal found")
    return goal


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = crud.get_goal(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(goal_id: int, payload: GoalUpdate, db: Session = Depends(get_db)):
    goal = crud.update_goal(db, goal_id, payload)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal
