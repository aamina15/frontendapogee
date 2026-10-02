import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.database import get_db, lock_goal_write
from models.goal import Goal
from models.skill import Skill, SkillDependency
from models.mastery import Mastery
from services.ai_service import generate_skill_dag_with_gemini
from services.dag_validator import validate_and_clean_dag
from services.state_engine import calculate_skill_states
from services.coverage_service import calculate_coverage

router = APIRouter(prefix="/api/goals", tags=["AI Skill Graph Generator & State Engine"])


class GraphGenerationResponse(BaseModel):
    goal_id: int
    skills: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]
    validation: Dict[str, Any]
    source: str = "unknown"
    warning: Optional[str] = None
    coverage: Optional[Dict[str, Any]] = None


@router.post("/{goal_id}/generate-graph", response_model=GraphGenerationResponse)
def generate_graph_for_goal(goal_id: int, db: Session = Depends(get_db)):
    """
    APOGEE AI Core Capability #1 & State Engine:
    
    1. Fetches Goal metadata.
    2. Calls Gemini on the backend to generate raw skill nodes & directed dependencies.
    3. Runs deterministic DAG validation (Kahn's algorithm cycle detection & repair).
    4. Persists verified valid skills and dependencies to DB.
    5. Runs deterministic State Engine (Rule 1-4) to compute skill states (LOCKED, AVAILABLE, IN_PROGRESS, VERIFIED).
    6. Returns validated DAG response with calculated skill states.
    """
    lock_goal_write(db, goal_id)
    # 1. Fetch Goal
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if db.query(Skill).filter(Skill.goal_id == goal_id).first():
        return get_graph(goal_id, db)

    # 2. Call Gemini AI on backend
    raw_dag = generate_skill_dag_with_gemini(
        goal_title=goal.title,
        hours_per_week=goal.hours_per_week,
        duration_weeks=goal.duration_weeks,
        budget=goal.budget or 0.0
    )

    # 3. Deterministic Backend DAG Validation & Cleaning
    clean_dag = validate_and_clean_dag(
        skills=raw_dag.get("skills", []),
        dependencies=raw_dag.get("dependencies", [])
    )

    # Guarantee acyclic
    if not clean_dag["validation"]["acyclic"]:
        raise HTTPException(status_code=500, detail="Failed to produce valid acyclic skill DAG")

    if not clean_dag["skills"]:
        raise HTTPException(502, "No valid skills were generated. Please try again.")
    goal.graph_source = raw_dag.get("source", "unknown")
    goal.graph_warning = raw_dag.get("warning")
    goal.graph_validation = json.dumps(clean_dag["validation"])

    # 5. Persist Skills & Dependencies to DB
    slug_to_db_id: Dict[str, int] = {}
    persisted_skills = []

    for s in clean_dag["skills"]:
        skill_row = Skill(
            goal_id=goal_id,
            name=s["name"],
            slug=s["id"],  # persist AI snake_case slug for resource catalogue lookup
            target_level=str(s["target_level"]),
            importance=float(s["importance"])
        )
        db.add(skill_row)
        db.flush()  # gets generated skill_row.id
        slug_to_db_id[s["id"]] = skill_row.id

        skill_dict = dict(s)
        skill_dict["db_id"] = skill_row.id
        persisted_skills.append(skill_dict)

    persisted_deps = []
    for dep in clean_dag["dependencies"]:
        u_slug = dep["from"]
        v_slug = dep["to"]

        u_db_id = slug_to_db_id.get(u_slug)
        v_db_id = slug_to_db_id.get(v_slug)

        if u_db_id and v_db_id:
            dep_row = SkillDependency(
                goal_id=goal_id,
                prerequisite_skill_id=u_db_id,
                dependent_skill_id=v_db_id
            )
            db.add(dep_row)
            persisted_deps.append({"from": u_slug, "to": v_slug})

    db.commit()

    return get_graph(goal_id, db)


@router.get("/{goal_id}/graph", response_model=GraphGenerationResponse)
def get_graph(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    skills = db.query(Skill).filter(Skill.goal_id == goal_id).all()
    if not skills:
        raise HTTPException(404, "Generate the skill graph first.")
    from routes.verification import _recalculate_states
    ids = {s.id: s.slug or str(s.id) for s in skills}
    deps = [{"from": ids[d.prerequisite_skill_id], "to": ids[d.dependent_skill_id]}
            for d in db.query(SkillDependency).filter(SkillDependency.goal_id == goal_id).all()]
    return {"goal_id": goal_id, "skills": _recalculate_states(db, goal_id),
            "dependencies": deps,
            "validation": json.loads(goal.graph_validation or '{"acyclic": true}'),
            "source": goal.graph_source or "unknown", "warning": goal.graph_warning,
            "coverage": calculate_coverage(db, goal_id)}