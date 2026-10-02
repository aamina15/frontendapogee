from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.database import get_db
from models.goal import Goal
from models.mastery import Mastery
from models.skill import Skill
from services.question_service import question_source
from services.diagnostic_service import (
    generate_and_save_diagnostic_questions,
    grade_diagnostic_submission
)

router = APIRouter(prefix="/api/goals", tags=["Diagnostic"])


class PublicQuestionResponse(BaseModel):
    id: int
    skill_id: str
    skill_db_id: int
    skill_name: str
    question: str
    options: List[str]
    source: str = 'legacy_bank'


class DiagnosticResponse(BaseModel):
    goal_id: int
    questions: List[PublicQuestionResponse]
    unassessed_skills: List[str] = Field(default_factory=list)


class AnswerItem(BaseModel):
    question_id: int
    selected_option: int = Field(..., ge=0, le=3)


class SubmitDiagnosticRequest(BaseModel):
    answers: List[AnswerItem]


class SkillMasteryItem(BaseModel):
    skill_id: str
    skill_db_id: int
    skill_name: str
    score: int
    assessed: bool = True


class SubmitDiagnosticResponse(BaseModel):
    goal_id: int
    mastery: List[SkillMasteryItem]


@router.post("/{goal_id}/diagnostic", response_model=DiagnosticResponse)
def get_or_generate_diagnostic(
    goal_id: int,
    depth: str = Query("quick", pattern="^(quick|deep)$"),
    db: Session = Depends(get_db),
):
    """
    Generates the goal-aware diagnostic for this goal's skill graph.
    IMPORTANT SECURITY REQUIREMENT: Excludes correct_index and explanation from response.

    depth=quick (default): one question per skill (capped) — the question count
    reflects the graph. depth=deep: tops up to two questions per skill (capped).
    """
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    questions = generate_and_save_diagnostic_questions(db, goal_id, depth=depth)

    public_questions = [
        PublicQuestionResponse(
            id=q.id,
            skill_id=q.skill_slug,
            skill_db_id=q.skill_db_id,
            skill_name=q.skill_name,
            question=q.question,
            options=q.options,
            source=question_source(q.explanation),
        )
        for q in questions
    ]

    return {
        "goal_id": goal_id,
        "questions": public_questions,
        "unassessed_skills": [s.name for s in db.query(Skill).filter(Skill.goal_id == goal_id).all()
                               if s.id not in {q.skill_db_id for q in questions}],
    }


@router.post("/{goal_id}/diagnostic/submit", response_model=SubmitDiagnosticResponse)
def submit_diagnostic(
    goal_id: int,
    payload: SubmitDiagnosticRequest,
    db: Session = Depends(get_db)
):
    """
    Grades user submitted answers against server-side correct_index,
    calculates per-skill mastery scores, updates Masteries table, and persists results.
    """
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    user_answers = [a.model_dump() for a in payload.answers]
    result = grade_diagnostic_submission(db, goal_id, user_answers)
    return result


@router.get("/{goal_id}/diagnostic/mastery", response_model=SubmitDiagnosticResponse)
def get_goal_diagnostic_mastery(goal_id: int, db: Session = Depends(get_db)):
    """
    Retrieves persisted diagnostic mastery results for a goal (for page refresh persistence).
    """
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    masteries = db.query(Mastery).filter(Mastery.goal_id == goal_id).all()
    skills = {s.id: s for s in db.query(Skill).filter(Skill.goal_id == goal_id).all()}

    mastery_items = []
    for m in masteries:
        skill = skills.get(m.skill_id)
        skill_name = skill.name if skill else f"Skill {m.skill_id}"
        score_pct = int(round((m.diagnostic_score or 0.0) * 100))

        mastery_items.append({
            "skill_id": f"skill_{m.skill_id}",
            "skill_db_id": m.skill_id,
            "skill_name": skill_name,
            "score": score_pct,
            # A mastery row can exist from verification alone (diagnostic_score
            # is None) — that skill was never diagnostically assessed.
            "assessed": m.diagnostic_score is not None,
        })

    return {
        "goal_id": goal_id,
        "mastery": mastery_items
    }
