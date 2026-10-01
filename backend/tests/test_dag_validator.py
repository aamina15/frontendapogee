import pytest
from services.dag_validator import validate_and_clean_dag, is_acyclic


def test_valid_dag():
    """Test 1: Valid DAG should pass validation unchanged and report acyclic: True."""
    skills = [
        {"id": "python", "name": "Python Fundamentals", "target_level": "Proficient", "importance": 1.0},
        {"id": "numpy", "name": "NumPy & Vectors", "target_level": "Proficient", "importance": 0.8},
        {"id": "pytorch", "name": "PyTorch Deep Learning", "target_level": "Expert", "importance": 0.9},
    ]
    dependencies = [
        {"from": "python", "to": "numpy"},
        {"from": "numpy", "to": "pytorch"},
    ]

    res = validate_and_clean_dag(skills, dependencies)

    assert res["validation"]["acyclic"] is True
    assert res["validation"]["repaired"] is False
    assert len(res["skills"]) == 3
    assert len(res["dependencies"]) == 2
    assert res["dependencies"] == [
        {"from": "python", "to": "numpy"},
        {"from": "numpy", "to": "pytorch"},
    ]


def test_missing_referenced_node():
    """Test 2: Dependencies referencing non-existent nodes should be filtered out."""
    skills = [
        {"id": "python", "name": "Python Fundamentals", "target_level": "Proficient", "importance": 1.0},
        {"id": "pytorch", "name": "PyTorch", "target_level": "Expert", "importance": 0.9},
    ]
    dependencies = [
        {"from": "python", "to": "pytorch"},
        {"from": "ghost_skill", "to": "pytorch"},  # 'ghost_skill' does not exist
        {"from": "python", "to": "non_existent_skill"},  # 'non_existent_skill' does not exist
    ]

    res = validate_and_clean_dag(skills, dependencies)

    assert len(res["dependencies"]) == 1
    assert res["dependencies"] == [{"from": "python", "to": "pytorch"}]
    assert res["validation"]["acyclic"] is True


def test_duplicate_edge():
    """Test 3: Duplicate edges between same pair of nodes should be deduplicated."""
    skills = [
        {"id": "html", "name": "HTML", "target_level": "Proficient", "importance": 0.9},
        {"id": "css", "name": "CSS", "target_level": "Proficient", "importance": 0.9},
    ]
    dependencies = [
        {"from": "html", "to": "css"},
        {"from": "html", "to": "css"},  # Duplicate edge
        {"from": "html", "to": "css"},  # Triplicate edge
    ]

    res = validate_and_clean_dag(skills, dependencies)

    assert len(res["dependencies"]) == 1
    assert res["dependencies"] == [{"from": "html", "to": "css"}]


def test_self_dependency():
    """Test 4: Self dependencies (from == to) must be rejected."""
    skills = [
        {"id": "python", "name": "Python", "target_level": "Proficient", "importance": 1.0},
    ]
    dependencies = [
        {"from": "python", "to": "python"},  # Self loop
    ]

    res = validate_and_clean_dag(skills, dependencies)

    assert len(res["dependencies"]) == 0
    assert res["validation"]["acyclic"] is True


def test_cycle_detection_and_repair():
    """Test 5: Graph containing a cycle (A -> B -> C -> A) must be detected & repaired into an acyclic DAG."""
    skills = [
        {"id": "skill_a", "name": "Skill A", "target_level": "Proficient", "importance": 1.0},
        {"id": "skill_b", "name": "Skill B", "target_level": "Proficient", "importance": 0.9},
        {"id": "skill_c", "name": "Skill C", "target_level": "Proficient", "importance": 0.8},
    ]
    # Cycle: A -> B -> C -> A
    dependencies = [
        {"from": "skill_a", "to": "skill_b"},
        {"from": "skill_b", "to": "skill_c"},
        {"from": "skill_c", "to": "skill_a"},  # Cycle edge
    ]

    # Verify is_acyclic detects cycle
    is_ok, cycle_nodes = is_acyclic(skills, dependencies)
    assert is_ok is False
    assert set(cycle_nodes) == {"skill_a", "skill_b", "skill_c"}

    # Verify validator repairs the graph into an acyclic DAG
    res = validate_and_clean_dag(skills, dependencies)

    assert res["validation"]["acyclic"] is True
    assert res["validation"]["repaired"] is True
    assert len(res["dependencies"]) == 2  # The back-edge was safely dropped
