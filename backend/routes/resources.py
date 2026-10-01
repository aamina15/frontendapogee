from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.resource import ResourceCreate, ResourceRead
from services import crud

router = APIRouter(prefix="/api/skills", tags=["Resources"])


@router.post("/{skill_id}/resources", response_model=ResourceRead, status_code=201)
def create_resource(skill_id: int, payload: ResourceCreate, db: Session = Depends(get_db)):
    payload.skill_id = skill_id
    return crud.create_resource(db, payload)


@router.get("/{skill_id}/resources", response_model=List[ResourceRead])
def list_resources(skill_id: int, db: Session = Depends(get_db)):
    return crud.list_resources_for_skill(db, skill_id)
