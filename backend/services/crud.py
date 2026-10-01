from typing import Optional, List
from sqlalchemy.orm import Session
from models.goal import Goal
from models.skill import Skill, SkillDependency
from models.mastery import Mastery
from models.resource import Resource
from models.route import Route
from schemas.goal import GoalCreate, GoalUpdate
from schemas.skill import SkillCreate, SkillDependencyCreate
from schemas.mastery import MasteryCreate, MasteryUpdate
from schemas.resource import ResourceCreate
from schemas.route import RouteCreate


# ── Goals ─────────────────────────────────────────────────────────────────────

def create_goal(db: Session, payload: GoalCreate) -> Goal:
    goal = Goal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goal(db: Session, goal_id: int) -> Optional[Goal]:
    return db.query(Goal).filter(Goal.id == goal_id).first()


def list_goals(db: Session) -> List[Goal]:
    return db.query(Goal).order_by(Goal.created_at.desc()).all()


def get_active_goal(db: Session) -> Optional[Goal]:
    """Return the most recently created active goal (MVP: single active goal)."""
    return db.query(Goal).filter(Goal.status == "active").order_by(Goal.created_at.desc(), Goal.id.desc()).first()


def update_goal(db: Session, goal_id: int, payload: GoalUpdate) -> Optional[Goal]:
    goal = get_goal(db, goal_id)
    if not goal:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


# ── Skills ────────────────────────────────────────────────────────────────────

def create_skill(db: Session, payload: SkillCreate) -> Skill:
    skill = Skill(**payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def list_skills_for_goal(db: Session, goal_id: int) -> List[Skill]:
    return db.query(Skill).filter(Skill.goal_id == goal_id).all()


def create_skill_dependency(db: Session, payload: SkillDependencyCreate) -> SkillDependency:
    dep = SkillDependency(**payload.model_dump())
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def list_dependencies_for_goal(db: Session, goal_id: int) -> List[SkillDependency]:
    return db.query(SkillDependency).filter(SkillDependency.goal_id == goal_id).all()


# ── Mastery ───────────────────────────────────────────────────────────────────

def upsert_mastery(db: Session, payload: MasteryCreate) -> Mastery:
    existing = (
        db.query(Mastery)
        .filter(Mastery.goal_id == payload.goal_id, Mastery.skill_id == payload.skill_id)
        .first()
    )
    if existing:
        existing.diagnostic_score = payload.diagnostic_score
        db.commit()
        db.refresh(existing)
        return existing
    mastery = Mastery(**payload.model_dump())
    db.add(mastery)
    db.commit()
    db.refresh(mastery)
    return mastery


def update_mastery(db: Session, mastery_id: int, payload: MasteryUpdate) -> Optional[Mastery]:
    mastery = db.query(Mastery).filter(Mastery.id == mastery_id).first()
    if not mastery:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mastery, field, value)
    db.commit()
    db.refresh(mastery)
    return mastery


def list_mastery_for_goal(db: Session, goal_id: int) -> List[Mastery]:
    return db.query(Mastery).filter(Mastery.goal_id == goal_id).all()


# ── Resources ─────────────────────────────────────────────────────────────────

def create_resource(db: Session, payload: ResourceCreate) -> Resource:
    resource = Resource(**payload.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def list_resources_for_skill(db: Session, skill_id: int) -> List[Resource]:
    return db.query(Resource).filter(Resource.skill_id == skill_id).all()


# ── Routes ────────────────────────────────────────────────────────────────────

def create_route(db: Session, payload: RouteCreate) -> Route:
    route = Route(**payload.model_dump())
    db.add(route)
    db.commit()
    db.refresh(route)
    return route


def get_latest_route(db: Session, goal_id: int) -> Optional[Route]:
    return (
        db.query(Route)
        .filter(Route.goal_id == goal_id)
        .order_by(Route.version.desc())
        .first()
    )


def list_routes_for_goal(db: Session, goal_id: int) -> List[Route]:
    return db.query(Route).filter(Route.goal_id == goal_id).order_by(Route.version.asc()).all()
