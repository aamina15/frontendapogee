from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.mastery import MasteryCreate, MasteryRead, MasteryUpdate
from services import crud

router = APIRouter(prefix="/api/goals", tags=["Mastery"])


@router.post("/{goal_id}/mastery", response_model=MasteryRead, status_code=201)
def upsert_mastery(goal_id: int, payload: MasteryCreate, db: Session = Depends(get_db)):
    payload.goal_id = goal_id
    return crud.upsert_mastery(db, payload)


@router.get("/{goal_id}/mastery", response_model=List[MasteryRead])
def list_mastery(goal_id: int, db: Session = Depends(get_db)):
    return crud.list_mastery_for_goal(db, goal_id)


@router.patch("/{goal_id}/mastery/{mastery_id}", response_model=MasteryRead)
def update_mastery(goal_id: int, mastery_id: int, payload: MasteryUpdate, db: Session = Depends(get_db)):
    mastery = crud.update_mastery(db, mastery_id, payload)
    if not mastery:
        raise HTTPException(status_code=404, detail="Mastery record not found")
    return mastery
