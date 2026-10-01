import pytest
from services.state_engine import calculate_skill_states


def test_root_node_becomes_available():
    """Test 1: Root skill with no prerequisites must be AVAILABLE."""
    skills = [
        {"id": "python", "name": "Python Fundamentals"}
    ]
    dependencies = []
    masteries = []

    res = calculate_skill_states(skills, dependencies, masteries)
    assert res[0]["status"] == "AVAILABLE"


def test_dependent_node_remains_locked():
    """Test 2: Dependent node whose prerequisite is NOT verified must remain LOCKED."""
    skills = [
        {"id": "python", "name": "Python Fundamentals"},
        {"id": "pytorch", "name": "PyTorch"}
    ]
    dependencies = [
        {"from": "python", "to": "pytorch"}
    ]
    masteries = []

    res = calculate_skill_states(skills, dependencies, masteries)
    python_skill = next(s for s in res if s["id"] == "python")
    pytorch_skill = next(s for s in res if s["id"] == "pytorch")

    assert python_skill["status"] == "AVAILABLE"
    assert pytorch_skill["status"] == "LOCKED"


def test_one_of_two_prerequisites_verified_remains_locked():
    """
    Test 3: CRITICAL PREREQUISITE UNLOCK RULE
    Computer Vision has two prerequisites: Statistics and PyTorch.
    If Statistics is VERIFIED but PyTorch is UNVERIFIED, Computer Vision MUST remain LOCKED.
    """
    skills = [
        {"id": "stats", "name": "Statistics"},
        {"id": "pytorch", "name": "PyTorch"},
        {"id": "cv", "name": "Computer Vision"}
    ]
    dependencies = [
        {"from": "stats", "to": "cv"},
        {"from": "pytorch", "to": "cv"}
    ]
    masteries = [
        {"skill_id": "stats", "verified": True}  # Only stats is verified, pytorch is not!
    ]

    res = calculate_skill_states(skills, dependencies, masteries)
    stats_skill = next(s for s in res if s["id"] == "stats")
    pytorch_skill = next(s for s in res if s["id"] == "pytorch")
    cv_skill = next(s for s in res if s["id"] == "cv")

    assert stats_skill["status"] == "VERIFIED"
    assert pytorch_skill["status"] == "AVAILABLE"
    assert cv_skill["status"] == "LOCKED"  # Must remain LOCKED because pytorch is not VERIFIED!


def test_both_prerequisites_verified_becomes_available():
    """Test 4: Computer Vision unlocks (becomes AVAILABLE) ONLY when BOTH Statistics AND PyTorch are VERIFIED."""
    skills = [
        {"id": "stats", "name": "Statistics"},
        {"id": "pytorch", "name": "PyTorch"},
        {"id": "cv", "name": "Computer Vision"}
    ]
    dependencies = [
        {"from": "stats", "to": "cv"},
        {"from": "pytorch", "to": "cv"}
    ]
    masteries = [
        {"skill_id": "stats", "verified": True},
        {"skill_id": "pytorch", "verified": True}
    ]

    res = calculate_skill_states(skills, dependencies, masteries)
    cv_skill = next(s for s in res if s["id"] == "cv")

    assert cv_skill["status"] == "AVAILABLE"


def test_verified_skill_becomes_verified():
    """Test 5: Explicitly verified skill must have status VERIFIED."""
    skills = [
        {"id": "html", "name": "HTML5"}
    ]
    dependencies = []
    masteries = [
        {"skill_id": "html", "verified": True}
    ]

    res = calculate_skill_states(skills, dependencies, masteries)
    assert res[0]["status"] == "VERIFIED"


def test_started_skill_becomes_in_progress():
    """Test 6: Started skill (unverified) must have status IN_PROGRESS."""
    skills = [
        {"id": "css", "name": "CSS Layouts"}
    ]
    dependencies = []
    masteries = [
        {"skill_id": "css", "verified": False, "in_progress": True}
    ]

    res = calculate_skill_states(skills, dependencies, masteries)
    assert res[0]["status"] == "IN_PROGRESS"
