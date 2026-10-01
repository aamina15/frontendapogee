"""
APOGEE Skill Verification Routes
=================================
POST /api/goals/{goal_id}/skills/{skill_id}/verification
    → Returns ~5 MCQ questions (no correct_index sent to frontend).

POST /api/goals/{goal_id}/skills/{skill_id}/verify
    → Grades submitted answers, persists mastery, recalculates graph states,
      returns pass/fail receipt with newly_unlocked skills.
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db, lock_goal_write
from models.goal import Goal
from models.skill import Skill, SkillDependency
from models.mastery import Mastery
from models.diagnostic import DiagnosticQuestion
from services.diagnostic_service import get_verification_questions_for_skill
from services.state_engine import calculate_skill_states

router = APIRouter(prefix="/api/goals", tags=["Skill Verification"])

VERIFICATION_PASS_THRESHOLD = 70  # percent — MVP default


# ── Schemas ────────────────────────────────────────────────────────────────────

class QuestionOut(BaseModel):
    """Safe question payload: no correct_index, no explanation."""
    id: int
    question: str
    options: List[str]


class VerificationQuestionsResponse(BaseModel):
    skill_id: int
    skill_name: str
    questions: List[QuestionOut]
    threshold: int


class AnswerItem(BaseModel):
    question_id: int
    selected_option: int = Field(..., ge=0, le=3)


class VerifyRequest(BaseModel):
    answers: List[AnswerItem]


class SkillStateOut(BaseModel):
    id: str
    db_id: int
    name: str
    status: str


class VerifyReceipt(BaseModel):
    score: int                          # 0-100
    threshold: int                      # pass threshold used
    passed: bool
    skill: SkillStateOut
    newly_unlocked: List[SkillStateOut]
    feedback: List[Dict[str, Any]]      # per-question feedback (shown after grading)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_verification_questions(
    db: Session, goal_id: int, skill: Skill
) -> List[DiagnosticQuestion]:
    """
    Returns existing verification questions for this skill (stored under a
    special skill_slug prefix), or generates and persists fresh ones.
    Uses a distinct slug namespace 'verif_{skill_id}' to avoid mixing with
    diagnostic questions.
    """
    verif_slug = f"verif_{skill.id}"
    existing = (
        db.query(DiagnosticQuestion)
        .filter(
            DiagnosticQuestion.goal_id == goal_id,
            DiagnosticQuestion.skill_slug == verif_slug,
        )
        .all()
    )
    if existing:
        return existing

    # Generate from catalogue
    templates = get_verification_questions_for_skill(skill.name, skill.slug or "")
    rows = []
    for t in templates:
        row = DiagnosticQuestion(
            goal_id=goal_id,
            skill_db_id=skill.id,
            skill_slug=verif_slug,
            skill_name=skill.name,
            question=t["question"],
            options=t["options"],
            correct_index=t["correct_index"],
            explanation=t.get("explanation", ""),
        )
        db.add(row)
        db.flush()
        rows.append(row)
    db.commit()
    return rows


def _recalculate_states(db: Session, goal_id: int) -> List[Dict[str, Any]]:
    """
    Runs the deterministic State Engine over all skills + masteries for a goal.
    Returns list of {id (slug), db_id, name, status}.
    """
    skills = db.query(Skill).filter(Skill.goal_id == goal_id).all()
    deps = db.query(SkillDependency).filter(SkillDependency.goal_id == goal_id).all()
    masteries = db.query(Mastery).filter(Mastery.goal_id == goal_id).all()

    # Build structures for state_engine
    skill_dicts = [
        {"id": s.slug or str(s.id), "db_id": s.id, "name": s.name,
         "target_level": s.target_level, "importance": s.importance}
        for s in skills
    ]
    dep_dicts = []
    id_map = {s.id: s.slug or str(s.id) for s in skills}
    for d in deps:
        dep_dicts.append({
            "from": id_map.get(d.prerequisite_skill_id, str(d.prerequisite_skill_id)),
            "to": id_map.get(d.dependent_skill_id, str(d.dependent_skill_id)),
        })

    mastery_dicts = [
        {
            "skill_id": id_map.get(m.skill_id, str(m.skill_id)),
            "skill_db_id": m.skill_id,
            "diagnostic_score": m.diagnostic_score,
            "verification_score": m.verification_score,
            "verified": bool(m.verified),
        }
        for m in masteries
    ]

    evaluated = calculate_skill_states(skill_dicts, dep_dicts, mastery_dicts)
    return evaluated


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/{goal_id}/skills/{skill_id}/verification",
    response_model=VerificationQuestionsResponse,
)
def get_verification_questions(
    goal_id: int, skill_id: int, db: Session = Depends(get_db)
):
    """
    Returns ~5 MCQ verification questions for a skill.
    correct_index is NEVER included in the response.
    """
    lock_goal_write(db, goal_id)
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    skill = db.query(Skill).filter(Skill.id == skill_id, Skill.goal_id == goal_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found in this goal")

    state = next(s for s in _recalculate_states(db, goal_id) if s["db_id"] == skill_id)
    if state["status"] == "LOCKED":
        raise HTTPException(409, "Verify all prerequisite skills first.")
    questions = _get_or_create_verification_questions(db, goal_id, skill)

    return {
        "skill_id": skill_id,
        "skill_name": skill.name,
        "questions": [
            {"id": q.id, "question": q.question, "options": q.options}
            for q in questions
        ],
        "threshold": VERIFICATION_PASS_THRESHOLD,
    }


@router.post(
    "/{goal_id}/skills/{skill_id}/verify",
    response_model=VerifyReceipt,
)
def verify_skill(
    goal_id: int,
    skill_id: int,
    payload: VerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Grades answers against server-side correct_index.
    1. Compute score (0-100).
    2. Compare against VERIFICATION_PASS_THRESHOLD (70%).
    3. Persist verification_score on Mastery; set verified=True if passed.
    4. Recalculate all skill states with the State Engine.
    5. Return receipt with newly_unlocked skills.
    """
    lock_goal_write(db, goal_id)
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    skill = db.query(Skill).filter(Skill.id == skill_id, Skill.goal_id == goal_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found in this goal")

    # Fetch the verification questions (must have been generated first)
    verif_slug = f"verif_{skill_id}"
    questions = (
        db.query(DiagnosticQuestion)
        .filter(
            DiagnosticQuestion.goal_id == goal_id,
            DiagnosticQuestion.skill_slug == verif_slug,
        )
        .all()
    )
    if not questions:
        # Auto-generate if not yet fetched (idempotent)
        questions = _get_or_create_verification_questions(db, goal_id, skill)

    q_map = {q.id: q for q in questions}
    answer_map = {a.question_id: a.selected_option for a in payload.answers}

    if len(answer_map) != len(payload.answers) or set(answer_map) != set(q_map):
        raise HTTPException(422, "Answer every verification question exactly once.")
    state = next(s for s in _recalculate_states(db, goal_id) if s["db_id"] == skill_id)
    if state["status"] == "LOCKED":
        raise HTTPException(409, "Verify all prerequisite skills first.")

    # 1. Grade
    correct = 0
    total = len(questions)
    feedback = []
    for q in questions:
        selected = answer_map.get(q.id)
        is_correct = selected is not None and selected == q.correct_index
        if is_correct:
            correct += 1
        feedback.append({
            "question_id": q.id,
            "question": q.question,
            "selected_option": selected,
            "correct_index": q.correct_index,
            "is_correct": is_correct,
            "explanation": q.explanation or "",
        })

    score_pct = int(round((correct / total) * 100)) if total > 0 else 0
    passed = score_pct >= VERIFICATION_PASS_THRESHOLD

    # 2. Snapshot states BEFORE update (to detect newly unlocked)
    states_before = {s["db_id"]: s["status"] for s in _recalculate_states(db, goal_id)}

    # 3. Persist mastery
    mastery = (
        db.query(Mastery)
        .filter(Mastery.goal_id == goal_id, Mastery.skill_id == skill_id)
        .first()
    )
    if not mastery:
        mastery = Mastery(goal_id=goal_id, skill_id=skill_id)
        db.add(mastery)

    mastery.verification_score = max(mastery.verification_score or 0, score_pct / 100.0)
    if passed:
        mastery.verified = True

    db.commit()

    # 4. Recalculate states AFTER update
    states_after = _recalculate_states(db, goal_id)
    states_after_map = {s["db_id"]: s for s in states_after}

    # 5. Find this skill's new state
    this_state = states_after_map.get(skill_id, {})
    skill_slug_val = skill.slug or str(skill_id)

    # 6. Newly unlocked = skills that were LOCKED before and are now AVAILABLE
    newly_unlocked = []
    for s in states_after:
        s_db_id = s["db_id"]
        if s_db_id == skill_id:
            continue
        was_locked = states_before.get(s_db_id) == "LOCKED"
        now_available = s["status"] == "AVAILABLE"
        if was_locked and now_available:
            newly_unlocked.append({
                "id": s["id"],
                "db_id": s_db_id,
                "name": s["name"],
                "status": "AVAILABLE",
            })

    return {
        "score": score_pct,
        "threshold": VERIFICATION_PASS_THRESHOLD,
        "passed": passed,
        "skill": {
            "id": skill_slug_val,
            "db_id": skill_id,
            "name": skill.name,
            "status": this_state.get("status", "VERIFIED" if passed else "IN_PROGRESS"),
        },
        "newly_unlocked": newly_unlocked,
        "feedback": feedback,
    }
