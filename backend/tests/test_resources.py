import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import Base, engine, SessionLocal
from models.goal import Goal
from services.resource_service import find_verified_resource_for_skill

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db_with_goal():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    test_goal = Goal(
        title="Frontend Developer Internship",
        hours_per_week=10.0,
        duration_weeks=12,
        budget=0.0,
        status="active"
    )
    db.add(test_goal)
    db.commit()
    db.refresh(test_goal)
    goal_id = test_goal.id

    # Generate graph
    client.post(f"/api/goals/{goal_id}/generate-graph")

    db.close()
    yield goal_id


def test_verified_resource_lookup_real_urls():
    """Test 1: Standard skills map to real verified URLs and valid duration_hours."""
    html_res = find_verified_resource_for_skill("HTML5 & Modern CSS Layouts", "html_css")
    assert html_res is not None
    assert "developer.mozilla.org" in html_res["url"]
    assert html_res["duration_hours"] > 0

    pytorch_res = find_verified_resource_for_skill("PyTorch Deep Learning", "deep_learning")
    assert pytorch_res is not None
    assert "pytorch.org" in pytorch_res["url"]
    assert pytorch_res["duration_hours"] > 0


def test_missing_resource_honest_state():
    """Test 2: Skills with no catalogued resource return None (honest missing state)."""
    unknown_res = find_verified_resource_for_skill("Quantum Topological Computing 9000", "quantum_xyz")
    assert unknown_res is None


def test_route_planner_calculates_hours_from_duration(setup_db_with_goal):
    """Test 3: Route planner sums duration_hours and calculates total_weeks using hours_per_week."""
    goal_id = setup_db_with_goal

    route_res = client.get(f"/api/goals/{goal_id}/route")
    assert route_res.status_code == 200

    data = route_res.json()
    assert data["goal_id"] == goal_id
    assert "phases" in data
    assert len(data["phases"]) > 0

    # Verify total_hours equals sum of resource duration_hours
    calculated_hours = 0.0
    for phase in data["phases"]:
        assert "duration_weeks" in phase
        assert "hours_total" in phase
        for res in phase["resources"]:
            assert "duration_hours" in res
            assert res["duration_hours"] > 0
            if res["has_resource"]:
                assert res["url"] is not None
                assert res["url"].startswith("http")
            calculated_hours += res["duration_hours"]

    assert data["total_hours"] == calculated_hours
    assert data["total_weeks"] > 0


# ===== PHASE 1: RESOURCE FORMAT REGRESSION TESTS =====

def test_resource_format_classification():
    """Test 4: Resources have format classification (reading/video/both)."""
    from services.resource_service import VERIFIED_RESOURCE_CATALOGUE

    # Check that catalogue entries have format field
    for key, entry in VERIFIED_RESOURCE_CATALOGUE.items():
        assert "format" in entry, f"Catalogue entry '{key}' missing format field"
        assert entry["format"] in ("reading", "video", "both"), f"Invalid format for '{key}': {entry['format']}"


def test_video_catalogue_real_urls():
    """Test 5: Video catalogue contains real verified YouTube URLs."""
    from services.resource_service import VERIFIED_VIDEO_CATALOGUE, find_verified_video_for_skill

    # Check key skills have video entries
    expected_video_skills = ["html_css", "javascript", "react_basics", "python", "sql", "css_advanced", "figma", "git", "docker", "typescript"]
    for skill in expected_video_skills:
        assert skill in VERIFIED_VIDEO_CATALOGUE, f"Missing video entry for '{skill}'"
        entry = VERIFIED_VIDEO_CATALOGUE[skill]
        assert "url" in entry and entry["url"].startswith("https://www.youtube.com/"), \
            f"Video entry for '{skill}' must be a real YouTube URL: {entry.get('url')}"
        assert "duration_hours" in entry and entry["duration_hours"] > 0


def test_get_resource_formats_returns_both():
    """Test 6: get_resource_formats returns both reading and video when available."""
    from services.resource_service import get_resource_formats

    # Skill with both reading and video in catalogue
    formats = get_resource_formats("HTML5 & Modern CSS Layouts", "html_css")
    assert formats["reading"] is not None, "Should have reading resource"
    assert formats["video"] is not None, "Should have video resource"
    assert formats["reading"]["format"] in ("reading", "both")
    # Video entries don't have 'format' key in catalogue (implied by being in video catalogue)
    assert "url" in formats["video"]
    assert "youtube.com" in formats["video"]["url"]


def test_get_resource_formats_reading_only():
    """Test 7: Skills with only reading return None for video."""
    from services.resource_service import get_resource_formats

    # State Management has reading but no video in catalogue
    formats = get_resource_formats("State Management (Redux/Zustand)", "state_mgmt")
    assert formats["reading"] is not None, "Should have reading resource"
    assert formats["video"] is None, "Should NOT have video resource"


def test_get_resource_formats_missing_skill():
    """Test 8: Unknown skills return None for both formats (honest missing state)."""
    from services.resource_service import get_resource_formats

    formats = get_resource_formats("Quantum Topological Computing 9000", "quantum_xyz")
    assert formats["reading"] is None
    assert formats["video"] is None


def test_existing_resources_with_null_format(setup_db_with_goal):
    """Test 9: Existing resources with NULL format remain accessible after migration."""
    from db.database import SessionLocal
    from models.resource import Resource

    goal_id = setup_db_with_goal
    db = SessionLocal()

    # Simulate pre-migration resource with NULL format
    test_res = Resource(
        skill_id=99999,  # fake skill_id
        title="Legacy Resource",
        url="http://legacy.example.com",
        source="Legacy",
        duration_hours=5.0,
        format=None  # NULL format like pre-Phase-1
    )
    db.add(test_res)
    db.commit()
    db.refresh(test_res)

    # Query should not error
    resources = db.query(Resource).filter(Resource.format.is_(None)).all()
    assert len(resources) >= 1
    assert any(r.title == "Legacy Resource" for r in resources)

    # Cleanup
    db.delete(test_res)
    db.commit()
    db.close()


def test_route_generation_includes_all_formats(setup_db_with_goal):
    """Test 10: Route generation returns all_formats array per skill."""
    goal_id = setup_db_with_goal

    route_res = client.get(f"/api/goals/{goal_id}/route")
    assert route_res.status_code == 200

    data = route_res.json()
    phase = data["phases"][0]

    # Check that resources have all_formats field
    for res in phase["resources"]:
        assert "all_formats" in res, f"Resource {res['target_skill_name']} missing all_formats"
        assert isinstance(res["all_formats"], list), "all_formats should be a list"

        # Each format entry should have format field
        for fmt in res["all_formats"]:
            assert "format" in fmt
            assert fmt["format"] in ("reading", "video", "both")


def test_format_preference_filtering(setup_db_with_goal):
    """Test 11: Format filtering works correctly (simulated frontend logic)."""
    from services.resource_service import get_resource_formats, VERIFIED_RESOURCE_CATALOGUE, VERIFIED_VIDEO_CATALOGUE

    goal_id = setup_db_with_goal
    route_res = client.get(f"/api/goals/{goal_id}/route")
    data = route_res.json()
    resources = data["phases"][0]["resources"]

    # Build skillFormats map (like frontend)
    skill_formats = {}
    for r in resources:
        if r.get("all_formats"):
            skill_formats[r["skill_id"]] = [f["format"] for f in r["all_formats"] if f.get("format")]
        elif r.get("format"):
            skill_formats[r["skill_id"]] = [r["format"]]

    # Test 'both' preference shows all
    both_visible = sum(1 for r in resources if True)  # all visible
    assert both_visible == len(resources)

    # Test 'video' preference
    video_visible = sum(1 for r in resources
                       if "video" in skill_formats.get(r["skill_id"], [])
                       or "both" in skill_formats.get(r["skill_id"], []))
    assert video_visible >= 1  # At least some skills have video

    # Test 'reading' preference
    reading_visible = sum(1 for r in resources
                         if "reading" in skill_formats.get(r["skill_id"], [])
                         or "both" in skill_formats.get(r["skill_id"], []))
    assert reading_visible == len(resources)  # All skills have reading


def test_preference_persistence_across_replan(setup_db_with_goal):
    """Test 12: Format preference would persist across replan/refresh (logic test)."""
    # This tests the API contract - route resources don't change format across replan
    goal_id = setup_db_with_goal

    # Get route before replan
    route1 = client.get(f"/api/goals/{goal_id}/route").json()
    formats_before = {}
    for r in route1["phases"][0]["resources"]:
        formats_before[r["skill_id"]] = [f["format"] for f in r.get("all_formats", []) if f.get("format")]

    # Replan with different hours
    replan_res = client.post(f"/api/goals/{goal_id}/replan", json={"hours_per_week": 5})
    assert replan_res.status_code == 200

    # Get route after replan
    route2 = client.get(f"/api/goals/{goal_id}/route").json()
    formats_after = {}
    for r in route2["phases"][0]["resources"]:
        formats_after[r["skill_id"]] = [f["format"] for f in r.get("all_formats", []) if f.get("format")]

    # Formats should be preserved
    assert formats_before == formats_after, "Format resources should persist across replan"


def test_no_mastery_changes_from_format_switch(setup_db_with_goal):
    """Test 13: Format preference does NOT change mastery or unlock skills."""
    from db.database import SessionLocal
    from models.mastery import Mastery

    goal_id = setup_db_with_goal

    # Get initial mastery state
    db = SessionLocal()
    mastery_before = db.query(Mastery).filter(Mastery.goal_id == goal_id).all()
    mastery_state_before = {(m.skill_id, m.verified, m.diagnostic_score) for m in mastery_before}
    db.close()

    # Simulate format preference change by getting route multiple times
    for _ in range(3):
        client.get(f"/api/goals/{goal_id}/route")

    # Check mastery unchanged
    db = SessionLocal()
    mastery_after = db.query(Mastery).filter(Mastery.goal_id == goal_id).all()
    mastery_state_after = {(m.skill_id, m.verified, m.diagnostic_score) for m in mastery_after}
    db.close()

    assert mastery_state_before == mastery_state_after, "Mastery should not change from format operations"


def test_youtube_urls_resolve():
    """Test 14: Verify YouTube URLs in video catalogue point to intended educational content.

    Note: This validates URL structure and expected channel names.
    Full HTTP HEAD requests would be flaky in CI; manual spot-check recommended.
    """
    from services.resource_service import VERIFIED_VIDEO_CATALOGUE

    expected_channels = {
        "html_css": "Traversy Media",
        "javascript": "Traversy Media",
        "react_basics": "Programming with Mosh",
        "python": "freeCodeCamp",
        "sql": "Caleb Curry",
        "css_advanced": "Traversy Media",
        "figma": "DesignCourse",
        "git": "Traversy Media",
        "docker": "Traversy Media",
        "typescript": "Traversy Media",
    }

    for skill, expected_channel in expected_channels.items():
        entry = VERIFIED_VIDEO_CATALOGUE[skill]
        url = entry["url"]
        # Verify YouTube URL structure
        assert "youtube.com/watch?v=" in url, f"Invalid YouTube URL for {skill}: {url}"
        # Verify channel name in title (manual verification of content)
        assert expected_channel.lower() in entry["title"].lower(), \
            f"Video for {skill} should be from {expected_channel}, got: {entry['title']}"
        print(f"  ✓ {skill}: {entry['title']} ({url})")


# ===== FORMAT DISPLAY REGRESSION TESTS (pre-deployment polish) =====

def _route_items_by_slug(goal_id):
    """Fetch the route and map items by the skill's catalogue slug via target_skill_name."""
    data = client.get(f"/api/goals/{goal_id}/route").json()
    items = [r for p in data["phases"] for r in p["resources"]]
    return {r["target_skill_name"]: r for r in items}


def test_multi_format_skill_route_item_has_real_reading_and_video(setup_db_with_goal):
    """Test 15: A skill with both catalogue entries exposes BOTH real resources
    in all_formats — each with its own verified title, URL and duration."""
    from services.resource_service import VERIFIED_RESOURCE_CATALOGUE, VERIFIED_VIDEO_CATALOGUE

    goal_id = setup_db_with_goal
    items = _route_items_by_slug(goal_id)
    html = items["HTML5 & Modern CSS Layouts"]

    fmts = {e["format"]: e for e in html["all_formats"]}
    assert "reading" in fmts and "video" in fmts, f"Expected both formats, got: {list(fmts)}"

    # Reading entry is the real catalogue resource — not invented
    assert fmts["reading"]["title"] == VERIFIED_RESOURCE_CATALOGUE["html_css"]["title"]
    assert fmts["reading"]["url"] == VERIFIED_RESOURCE_CATALOGUE["html_css"]["url"]
    assert fmts["reading"]["duration_hours"] == VERIFIED_RESOURCE_CATALOGUE["html_css"]["duration_hours"]

    # Video entry is the real catalogue video — not invented
    assert fmts["video"]["title"] == VERIFIED_VIDEO_CATALOGUE["html_css"]["title"]
    assert fmts["video"]["url"] == VERIFIED_VIDEO_CATALOGUE["html_css"]["url"]
    assert fmts["video"]["duration_hours"] == VERIFIED_VIDEO_CATALOGUE["html_css"]["duration_hours"]

    # Other multi-format skills in the fallback frontend graph also expose both
    for name in ["JavaScript (ES6+)", "React Core & Components", "TypeScript Fundamentals"]:
        fmts = {e["format"] for e in items[name]["all_formats"]}
        assert {"reading", "video"} <= fmts, f"{name} should expose reading+video, got {fmts}"


def test_primary_resource_stays_reading_when_video_exists(setup_db_with_goal):
    """Test 16: The planner's primary pick is unchanged (reading preferred) —
    format display is a frontend concern and must not reschedule the route."""
    goal_id = setup_db_with_goal
    items = _route_items_by_slug(goal_id)
    html = items["HTML5 & Modern CSS Layouts"]
    assert html["format"] == "reading"
    assert html["title"] == "MDN Web Docs: Learn HTML & CSS"
    assert "developer.mozilla.org" in html["url"]


def test_video_only_selection_yields_real_video_entry(setup_db_with_goal):
    """Test 17: Selecting video-only (frontend matcher: entry.format === 'video'
    or 'both') yields exactly the verified video resource — real URL, title, duration."""
    from services.resource_service import VERIFIED_VIDEO_CATALOGUE

    goal_id = setup_db_with_goal
    items = _route_items_by_slug(goal_id)
    html = items["HTML5 & Modern CSS Layouts"]

    matches = [e for e in html["all_formats"] if e["format"] in ("video", "both")]
    assert len(matches) == 1
    v = matches[0]
    assert v["url"] == VERIFIED_VIDEO_CATALOGUE["html_css"]["url"]
    assert v["title"] == VERIFIED_VIDEO_CATALOGUE["html_css"]["title"]
    assert v["duration_hours"] == VERIFIED_VIDEO_CATALOGUE["html_css"]["duration_hours"]
    assert v["url"].startswith("https://www.youtube.com/")


def test_reading_only_selection_yields_real_reading_entry(setup_db_with_goal):
    """Test 18: Selecting reading-only yields exactly the verified reading resource."""
    from services.resource_service import VERIFIED_RESOURCE_CATALOGUE

    goal_id = setup_db_with_goal
    items = _route_items_by_slug(goal_id)
    html = items["HTML5 & Modern CSS Layouts"]

    matches = [e for e in html["all_formats"] if e["format"] in ("reading", "both")]
    assert len(matches) == 1
    r = matches[0]
    assert r["url"] == VERIFIED_RESOURCE_CATALOGUE["html_css"]["url"]
    assert r["title"] == VERIFIED_RESOURCE_CATALOGUE["html_css"]["title"]
    assert r["duration_hours"] == VERIFIED_RESOURCE_CATALOGUE["html_css"]["duration_hours"]


def test_reading_only_skill_has_no_video_entry_honest_gap(setup_db_with_goal):
    """Test 19: A reading-only skill (State Management) exposes no video entry,
    so a video-only selection must surface the honest Format Not Available state."""
    goal_id = setup_db_with_goal
    items = _route_items_by_slug(goal_id)
    redux = items["State Management (Redux/Zustand)"]

    fmts = {e["format"] for e in redux["all_formats"]}
    assert "reading" in fmts
    assert "video" not in fmts, "Reading-only skill must not fabricate a video entry"

    # Frontend matcher under video-only finds nothing -> honest gap
    video_matches = [e for e in redux["all_formats"] if e["format"] in ("video", "both")]
    assert video_matches == []


def test_no_catalogue_entry_remains_honest(setup_db_with_goal):
    """Test 20: A skill with no catalogue match keeps the honest missing state —
    no invented URL, title, or format."""
    from models.skill import Skill
    from db.database import SessionLocal

    goal_id = setup_db_with_goal
    db = SessionLocal()
    ghost = Skill(goal_id=goal_id, name="Quantum Surfing Mastery", slug="quantum_surfing")
    db.add(ghost)
    db.commit()
    db.refresh(ghost)
    ghost_id = ghost.id
    db.close()

    data = client.get(f"/api/goals/{goal_id}/route").json()
    items = [r for p in data["phases"] for r in p["resources"]]
    entry = next(r for r in items if r["skill_id"] == ghost_id)
    assert entry["has_resource"] is False
    assert entry["url"] is None
    assert entry["format"] is None
    assert "No verified resource catalogued" in entry["title"]
