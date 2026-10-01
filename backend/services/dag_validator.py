from collections import defaultdict, deque
from typing import List, Dict, Any, Tuple, Set


def is_acyclic(skills: List[Dict[str, Any]], dependencies: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Checks if a graph defined by skills and dependencies is acyclic using Kahn's algorithm (Topological Sort).
    Returns (is_acyclic_boolean, cycle_node_ids_if_any).
    """
    skill_ids = {s["id"] for s in skills if "id" in s}
    in_degree = {sid: 0 for sid in skill_ids}
    adj_list = defaultdict(list)

    for dep in dependencies:
        u = dep.get("from")
        v = dep.get("to")
        if u in skill_ids and v in skill_ids:
            adj_list[u].append(v)
            in_degree[v] += 1

    queue = deque([sid for sid in skill_ids if in_degree[sid] == 0])
    visited_count = 0

    while queue:
        curr = queue.popleft()
        visited_count += 1
        for neighbor in adj_list[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count == len(skill_ids):
        return True, []
    
    # Return nodes involved in remaining non-zero in-degree (part of cycle)
    cycle_nodes = [sid for sid, deg in in_degree.items() if deg > 0]
    return False, cycle_nodes


def validate_and_clean_dag(
    skills: List[Dict[str, Any]],
    dependencies: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Deterministic DAG Validator and Cleaner.
    
    Rule 1: Deduplicate skills by ID (and normalize name).
    Rule 2: Validate every referenced skill in dependencies exists.
    Rule 3: Remove duplicate edges.
    Rule 4: Reject self-dependencies (from == to).
    Rule 5: Cycle detection & controlled repair (break cycle-causing edges).
    """
    # 1. Deduplicate skills by ID
    unique_skills = []
    seen_skill_ids = set()
    for s in skills:
        sid = str(s.get("id", "")).strip()
        if not sid or sid in seen_skill_ids:
            continue
        seen_skill_ids.add(sid)
        unique_skills.append({
            "id": sid,
            "name": s.get("name", sid).strip(),
            "target_level": s.get("target_level", "Proficient"),
            "importance": float(s.get("importance", 1.0))
        })

    valid_skill_ids = {s["id"] for s in unique_skills}

    # 2. Clean dependencies (Filter missing nodes, self-deps, duplicates)
    cleaned_dependencies = []
    seen_edges: Set[Tuple[str, str]] = set()

    for dep in dependencies:
        u = str(dep.get("from", "")).strip()
        v = str(dep.get("to", "")).strip()

        # Rule 2: Must reference existing skill
        if u not in valid_skill_ids or v not in valid_skill_ids:
            continue

        # Rule 4: Reject self-dependency
        if u == v:
            continue

        # Rule 3: Deduplicate edges
        edge = (u, v)
        if edge in seen_edges:
            continue

        seen_edges.add(edge)
        cleaned_dependencies.append({"from": u, "to": v})

    # 5. Cycle Detection & Controlled Repair
    acyclic, cycle_nodes = is_acyclic(unique_skills, cleaned_dependencies)
    was_repaired = False

    if not acyclic:
        # Controlled repair: Greedy removal of back-edges until acyclic
        repaired_deps = []
        temp_seen_edges: Set[Tuple[str, str]] = set()
        
        for dep in cleaned_dependencies:
            # Test if adding this edge introduces a cycle
            test_deps = repaired_deps + [dep]
            check_ok, _ = is_acyclic(unique_skills, test_deps)
            if check_ok:
                repaired_deps.append(dep)
            else:
                was_repaired = True  # Dropped edge to break cycle

        cleaned_dependencies = repaired_deps
        acyclic, _ = is_acyclic(unique_skills, cleaned_dependencies)

    return {
        "skills": unique_skills,
        "dependencies": cleaned_dependencies,
        "validation": {
            "acyclic": acyclic,
            "repaired": was_repaired,
            "total_skills": len(unique_skills),
            "total_dependencies": len(cleaned_dependencies)
        }
    }
