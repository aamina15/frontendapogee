from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from models.skill import Skill
from schemas.resource import ResourceCreate, ResourceRead
from services import crud
from services.resource_service import get_resource_formats

router = APIRouter(prefix="/api/skills", tags=["Resources"])


@router.post("/{skill_id}/resources", response_model=ResourceRead, status_code=201)
def create_resource(skill_id: int, payload: ResourceCreate, db: Session = Depends(get_db)):
    payload.skill_id = skill_id
    return crud.create_resource(db, payload)


@router.get("/{skill_id}/resources", response_model=List[ResourceRead])
def list_resources(skill_id: int, db: Session = Depends(get_db)):
    """Persisted resources for a skill. When nothing has been materialized yet
    (the planner persists catalogue matches only when a route is built), fall
    back to the verified catalogue READ-ONLY: read-only surfaces such as the
    capability map must never create route rows, versions, or resources."""
    rows = crud.list_resources_for_skill(db, skill_id)
    if rows:
        return rows
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        return []
    formats = get_resource_formats(skill.name, skill.slug or "")
    catalogue = []
    for fmt, entry in (("reading", formats["reading"]), ("video", formats["video"])):
        if entry:
            catalogue.append(ResourceRead(
                id=None,
                skill_id=skill_id,
                title=entry["title"],
                url=entry["url"],
                source=entry["source"],
                duration_hours=entry["duration_hours"],
                format=entry.get("format", fmt),
            ))
    return catalogue
