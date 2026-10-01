"""Prerequisite-ordered, persisted routes and atomic availability replanning."""
import json
import math
from collections import deque
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.database import get_db, lock_goal_write
from models.goal import Goal
from models.skill import Skill, SkillDependency
from models.route import Route
from services.resource_service import get_or_create_resources_for_skills
from routes.verification import _recalculate_states

router = APIRouter(prefix="/api/goals", tags=["Routes & Planner"])


def _build_route(db, goal, hpw):
    skills = db.query(Skill).filter(Skill.goal_id == goal.id).order_by(Skill.id).all()
    if not skills:
        raise HTTPException(409, "Generate your skill graph before building a route.")
    deps = db.query(SkillDependency).filter(SkillDependency.goal_id == goal.id).all()
    indegree = {s.id: 0 for s in skills}
    children = {s.id: [] for s in skills}
    for d in deps:
        if d.prerequisite_skill_id not in indegree or d.dependent_skill_id not in indegree:
            raise HTTPException(409, "The skill graph has an invalid prerequisite. Please rebuild your goal.")
        children[d.prerequisite_skill_id].append(d.dependent_skill_id)
        indegree[d.dependent_skill_id] += 1
    queue = deque(sid for sid, degree in indegree.items() if degree == 0)
    ordered = []
    while queue:
        sid = queue.popleft()
        ordered.append(sid)
        for child in children[sid]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(ordered) != len(skills):
        raise HTTPException(409, "The skill graph contains a cycle. A safe route cannot be generated.")
    resources = {r["skill_id"]: r for r in get_or_create_resources_for_skills(db, goal.id)}
    states = {s["db_id"]: s["status"] for s in _recalculate_states(db, goal.id)}
    items = []
    elapsed = 0.0
    for sid in ordered:
        r = resources[sid]
        hours = 0.0 if states[sid] == "VERIFIED" else r["duration_hours"]
        items.append({**r, "target_skill_name": r["skill_name"], "status": states[sid],
                      "remaining_hours": hours, "start_hour": elapsed, "end_hour": elapsed + hours})
        elapsed += hours
    weeks = math.ceil(elapsed / hpw)
    time_budget = hpw * goal.duration_weeks
    gaps = [r["skill_name"] for r in items if not r["has_resource"] and r["status"] != "VERIFIED"]
    feasible = elapsed <= time_budget and not gaps
    if gaps:
        message = "Route incomplete: no learning resource is catalogued for " + ", ".join(gaps) + ". Timing includes estimates."
    elif not feasible:
        message = f"Infeasible within {goal.duration_weeks} weeks: {elapsed:g} hours required, {time_budget:g} available. Allow {weeks} weeks or increase weekly hours."
    else:
        message = f"Fits your {goal.duration_weeks}-week budget: {elapsed:g} hours remaining of {time_budget:g} available."
    return {"goal_id": goal.id, "total_hours": elapsed, "total_weeks": weeks,
            "hours_per_week": hpw, "duration_weeks": goal.duration_weeks,
            "available_hours": time_budget, "feasible": feasible, "feasibility_message": message,
            "missing_resources": gaps, "prerequisite_safe": True,
            "phases": [{"phase_num": 1, "title": "Prerequisite-ordered learning route",
                        "duration_weeks": weeks, "hours_total": elapsed,
                        "skill_coverage": [r["skill_name"] for r in items], "resources": items}]}


def _latest(db, goal_id):
    return db.query(Route).filter(Route.goal_id == goal_id).order_by(Route.version.desc()).first()


def _save(db, goal_id, data, version, reason):
    data["version"] = version
    db.add(Route(goal_id=goal_id, version=version, total_hours=data["total_hours"],
                 total_weeks=data["total_weeks"], route_json=json.dumps(data), change_reason=reason))
    db.flush()


@router.get("/{goal_id}/route")
@router.post("/{goal_id}/routes")
def generate_or_get_route(goal_id: int, db: Session = Depends(get_db)):
    lock_goal_write(db, goal_id)
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    try:
        data = _build_route(db, goal, goal.hours_per_week)
        latest = _latest(db, goal_id)
        data["version"] = latest.version if latest else 1
        old = json.loads(latest.route_json or '{}') if latest else None
        if old != data:
            _save(db, goal_id, data, latest.version + 1 if latest else 1,
                  "Progress updated" if latest else "Initial route")
        db.commit()
        return data
    except Exception:
        db.rollback()
        raise


class StoredRouteRead(BaseModel):
    id: int
    goal_id: int
    version: int
    total_hours: Optional[float]
    total_weeks: Optional[int]
    change_reason: Optional[str]
    route_json: Optional[str]
    model_config = {"from_attributes": True}


@router.get("/{goal_id}/routes", response_model=List[StoredRouteRead])
def list_stored_routes(goal_id: int, db: Session = Depends(get_db)):
    if not db.get(Goal, goal_id):
        raise HTTPException(404, "Goal not found")
    return db.query(Route).filter(Route.goal_id == goal_id).order_by(Route.version).all()


@router.get("/{goal_id}/routes/latest", response_model=StoredRouteRead)
def get_latest_stored_route(goal_id: int, db: Session = Depends(get_db)):
    route = _latest(db, goal_id)
    if not route:
        raise HTTPException(404, "No stored routes found for this goal")
    return route


class ReplanRequest(BaseModel):
    hours_per_week: float = Field(..., ge=1, le=168)


@router.post("/{goal_id}/replan")
def replan_goal(goal_id: int, payload: ReplanRequest, db: Session = Depends(get_db)):
    lock_goal_write(db, goal_id)
    goal = db.get(Goal, goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    old_hpw = goal.hours_per_week
    try:
        latest = _latest(db, goal_id)
        if not latest:
            initial = _build_route(db, goal, old_hpw)
            _save(db, goal_id, initial, 1, "Initial route")
            latest = _latest(db, goal_id)
        data = _build_route(db, goal, payload.hours_per_week)
        previous_version = latest.version
        _save(db, goal_id, data, previous_version + 1, f"Availability {old_hpw:g} → {payload.hours_per_week:g} h/week")
        goal.hours_per_week = payload.hours_per_week
        db.commit()
    except Exception:
        db.rollback()
        raise
    items = [r for p in data["phases"] for r in p["resources"]]
    return {"previous_version": previous_version, "new_version": data["version"],
            "previous_hours_per_week": old_hpw, "new_hours_per_week": payload.hours_per_week,
            "preserved_verified_skills": [r["skill_name"] for r in items if r["status"] == "VERIFIED"],
            "remaining_unverified_skills": [r["skill_name"] for r in items if r["status"] != "VERIFIED"],
            "changes": [{"skill_name": r["skill_name"],
                         "previous_duration_weeks": round(r["remaining_hours"] / old_hpw, 1),
                         "new_duration_weeks": round(r["remaining_hours"] / payload.hours_per_week, 1),
                         "change_type": "preserved_verified" if r["status"] == "VERIFIED" else "rescheduled"}
                        for r in items], "route": data}
