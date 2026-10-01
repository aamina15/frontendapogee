from typing import List, Dict, Any, Set


def calculate_skill_states(
    skills: List[Dict[str, Any]],
    dependencies: List[Dict[str, Any]],
    masteries: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Deterministic Skill State Engine (APOGEE Core State Engine)
    
    Valid States:
    - VERIFIED
    - IN_PROGRESS
    - AVAILABLE
    - LOCKED
    
    Rules:
    1. If mastery.verified == True: status = VERIFIED
    2. Else if learner has started the skill/resource: status = IN_PROGRESS
    3. Else if ALL prerequisite skills are VERIFIED: status = AVAILABLE
    4. Otherwise: status = LOCKED
    
    CRITICAL RULE:
    A node with multiple prerequisites MUST remain LOCKED until ALL prerequisites are VERIFIED.
    """
    if masteries is None:
        masteries = []

    # Map skill identifiers -> mastery info
    # Support mapping by skill string ID, numeric DB ID, or skill_slug
    mastery_map: Dict[str, Dict[str, Any]] = {}

    for m in masteries:
        info = {
            "verified": bool(m.get("verified", False) or (m.get("verification_score") or 0) >= 0.70),
            "in_progress": bool(m.get("in_progress", False) or ((m.get("diagnostic_score") or 0) > 0))
        }

        if "skill_id" in m:
            mastery_map[str(m["skill_id"])] = info
        if "skill_db_id" in m:
            mastery_map[str(m["skill_db_id"])] = info
        if "skill_slug" in m:
            mastery_map[str(m["skill_slug"])] = info

    # Build prerequisite mapping: skill_id -> list of prerequisite skill_ids
    prereqs: Dict[str, List[str]] = {str(s["id"]): [] for s in skills if "id" in s}

    for dep in dependencies:
        u = str(dep.get("from", ""))
        v = str(dep.get("to", ""))
        if v in prereqs:
            prereqs[v].append(u)

    # Initial state map
    computed_states: Dict[str, str] = {}

    # Topological / iterative evaluation to resolve state dependencies
    # Maximum iterations = number of skills
    for _ in range(len(skills) + 1):
        changed = False

        for s in skills:
            sid = str(s["id"])
            m_info = mastery_map.get(sid, {})
            db_id_str = str(s.get("db_id", ""))
            if db_id_str in mastery_map:
                m_info = mastery_map[db_id_str]

            # Rule 1: Verified skill -> VERIFIED
            if m_info.get("verified", False):
                new_state = "VERIFIED"
            # Rule 2: Started skill -> IN_PROGRESS
            elif m_info.get("in_progress", False) and all(
                computed_states.get(p) == "VERIFIED" for p in prereqs.get(sid, [])
            ):
                new_state = "IN_PROGRESS"
            else:
                p_list = prereqs.get(sid, [])
                if len(p_list) == 0:
                    # Rule 3: Root skill with no prerequisites -> AVAILABLE
                    new_state = "AVAILABLE"
                else:
                    # Rule 3 & 4: Available ONLY if ALL prerequisites are VERIFIED
                    all_prereqs_verified = all(
                        computed_states.get(p_id) == "VERIFIED"
                        for p_id in p_list
                    )
                    if all_prereqs_verified:
                        new_state = "AVAILABLE"
                    else:
                        new_state = "LOCKED"

            if computed_states.get(sid) != new_state:
                computed_states[sid] = new_state
                changed = True

        if not changed:
            break

    # Attach computed state to skill objects
    result_skills = []
    for s in skills:
        sid = str(s["id"])
        s_copy = dict(s)
        s_copy["status"] = computed_states.get(sid, "LOCKED")
        result_skills.append(s_copy)

    return result_skills
