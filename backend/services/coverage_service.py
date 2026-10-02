"""
Deterministic, importance-weighted Verified Goal Coverage calculation.

Coverage = (sum of importance weights of VERIFIED skills) / (sum of importance weights of ALL skills) * 100

Rules:
- Only server-verified skills (mastery.verified=True) count in numerator
- Weights are RELATIVE: skills store importance on a 0.1-1.0 scale (AI graphs)
  or up to 5.0 (older data). Any positive value <= 5.0 is used as-is.
- Zero, negative, missing, or > 5.0 weights safely default to 1.0
- Diagnostic knowledge estimates kept separate (diagnostic_coverage_pct) —
  they NEVER contribute to verified coverage
- Coverage is recomputed from persisted mastery on every route/graph read,
  so it survives refresh and replan; it is also stored in each route snapshot
- Resource format preference changes do NOT affect coverage
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.skill import Skill
from models.mastery import Mastery
from routes.verification import _recalculate_states


def calculate_coverage(db: Session, goal_id: int) -> Dict[str, Any]:
    """
    Calculate Verified Goal Coverage for a goal.

    Returns dict with:
    - verified_coverage_pct: importance-weighted % of verified skills
    - diagnostic_coverage_pct: importance-weighted % of skills with diagnostic_score
    - verified_skills: count of verified skills
    - total_skills: count of all skills
    - remaining_skills: count of unverified skills
    - skill_breakdown: list of {skill_id, name, importance, verified, diagnostic_score}
    """
    skills = db.query(Skill).filter(Skill.goal_id == goal_id).all()
    if not skills:
        return {
            "verified_coverage_pct": 0.0,
            "diagnostic_coverage_pct": 0.0,
            "verified_skills": 0,
            "total_skills": 0,
            "remaining_skills": 0,
            "skill_breakdown": [],
        }

    # Get mastery states
    masteries = db.query(Mastery).filter(Mastery.goal_id == goal_id).all()
    mastery_map = {m.skill_id: m for m in masteries}

    # Get current states from state engine (includes LOCKED/AVAILABLE/IN_PROGRESS/VERIFIED)
    states = _recalculate_states(db, goal_id)
    state_map = {s["db_id"]: s for s in states}

    total_weight = 0.0
    verified_weight = 0.0
    diagnostic_weight = 0.0
    verified_count = 0
    skill_breakdown = []

    for skill in skills:
        mastery = mastery_map.get(skill.id)
        state = state_map.get(skill.id, {})

        # Validate and clamp importance weight
        weight = skill.importance
        if weight is None or weight <= 0 or weight > 5.0:
            weight = 1.0  # safe default

        is_verified = mastery.verified if mastery else False
        has_diagnostic = mastery.diagnostic_score is not None if mastery else False

        total_weight += weight
        if is_verified:
            verified_weight += weight
            verified_count += 1
        if has_diagnostic:
            diagnostic_weight += weight

        skill_breakdown.append({
            "skill_id": skill.id,
            "name": skill.name,
            "importance": weight,
            "verified": is_verified,
            "diagnostic_score": mastery.diagnostic_score if mastery else None,
            "verification_score": mastery.verification_score if mastery else None,
            "status": state.get("status", "LOCKED"),
        })

    # Calculate percentages (safe division)
    verified_pct = (verified_weight / total_weight * 100) if total_weight > 0 else 0.0
    diagnostic_pct = (diagnostic_weight / total_weight * 100) if total_weight > 0 else 0.0

    # Round to 1 decimal place
    verified_pct = round(verified_pct, 1)
    diagnostic_pct = round(diagnostic_pct, 1)

    return {
        "verified_coverage_pct": verified_pct,
        "diagnostic_coverage_pct": diagnostic_pct,
        "verified_skills": verified_count,
        "total_skills": len(skills),
        "remaining_skills": len(skills) - verified_count,
        "skill_breakdown": skill_breakdown,
    }


def format_coverage_summary(coverage: Dict[str, Any]) -> str:
    """Format coverage for display in UI."""
    return (
        f"{coverage['verified_coverage_pct']}% verified "
        f"({coverage['verified_skills']}/{coverage['total_skills']} skills, "
        f"{coverage['remaining_skills']} remaining)"
    )