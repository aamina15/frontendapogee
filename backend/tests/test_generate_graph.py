import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import Base, engine, SessionLocal
from models.goal import Goal

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Create test goal
    test_goal = Goal(
        title="Full Stack Developer Internship",
        hours_per_week=10.0,
        duration_weeks=12,
        budget=100.0,
        status="active"
    )
    db.add(test_goal)
    db.commit()
    db.refresh(test_goal)
    goal_id = test_goal.id
    db.close()
    yield goal_id


def test_generate_graph_endpoint(setup_db):
    goal_id = setup_db

    response = client.post(f"/api/goals/{goal_id}/generate-graph")
    assert response.status_code == 200

    data = response.json()
    assert data["goal_id"] == goal_id
    assert "skills" in data
    assert "dependencies" in data
    assert "validation" in data
    assert data["validation"]["acyclic"] is True
    assert len(data["skills"]) >= 3

    # Check node structure
    first_skill = data["skills"][0]
    assert "id" in first_skill
    assert "name" in first_skill
    assert "target_level" in first_skill
    assert "importance" in first_skill
    assert "db_id" in first_skill


def test_generate_graph_not_found():
    response = client.post("/api/goals/999999/generate-graph")
    assert response.status_code == 404
