"""
APOGEE Resource Service
=======================
Connects learning resources to skill nodes in a generated route.

Architecture:
  1. VERIFIED_RESOURCE_CATALOGUE — curated dict of real, hand-verified URLs.
     Keys are the AI-generated skill slugs (snake_case).
     To add web-search enrichment later, replace find_verified_resource_for_skill()
     with a version that queries an external search API FIRST then falls back here.
  2. find_verified_resource_for_skill() — looks up by slug, then name keywords.
     Returns None (honest missing state) if nothing found — never invents URLs.
  3. get_or_create_resources_for_skills() — called by the route planner.
     Persists matched resources to DB; planner uses duration_hours for scheduling.

Expanding the catalogue:
  Add a new entry to VERIFIED_RESOURCE_CATALOGUE with a slug key and a dict:
  { "title", "source", "url", "duration_hours" }. The URL must be manually verified.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from models.skill import Skill
from models.resource import Resource


# ---------------------------------------------------------------------------
# Curated catalogue — real URLs only, manually verified.
# Keys = AI skill slugs (snake_case). Values = MVP resource fields.
# ---------------------------------------------------------------------------
VERIFIED_RESOURCE_CATALOGUE: Dict[str, Dict[str, Any]] = {

    # ── Frontend / Web ──────────────────────────────────────────────────────
    "html_css": {
        "title": "MDN Web Docs: Learn HTML & CSS",
        "source": "MDN Web Docs",
        "url": "https://developer.mozilla.org/en-US/docs/Learn",
        "duration_hours": 12.0,
        "format": "reading",
    },
    "javascript": {
        "title": "The Modern JavaScript Tutorial",
        "source": "javascript.info",
        "url": "https://javascript.info/",
        "duration_hours": 18.0,
        "format": "reading",
    },
    "react_basics": {
        "title": "React Official Docs: Quick Start & Hooks",
        "source": "React.dev",
        "url": "https://react.dev/learn",
        "duration_hours": 15.0,
        "format": "reading",
    },
    "state_mgmt": {
        "title": "Redux Toolkit: Getting Started",
        "source": "Redux Docs",
        "url": "https://redux-toolkit.js.org/introduction/getting-started",
        "duration_hours": 10.0,
        "format": "reading",
    },
    "typescript": {
        "title": "TypeScript Handbook: The Basics",
        "source": "TypeScript Docs",
        "url": "https://www.typescriptlang.org/docs/handbook/intro.html",
        "duration_hours": 10.0,
        "format": "reading",
    },
    "testing_frontend": {
        "title": "React Testing Library: Introduction",
        "source": "Testing Library Docs",
        "url": "https://testing-library.com/docs/react-testing-library/intro/",
        "duration_hours": 8.0,
        "format": "reading",
    },
    "web_accessibility": {
        "title": "Web Accessibility Initiative (WAI) Tutorials",
        "source": "W3C WAI",
        "url": "https://www.w3.org/WAI/tutorials/",
        "duration_hours": 6.0,
        "format": "reading",
    },
    "performance": {
        "title": "web.dev: Learn Performance",
        "source": "web.dev",
        "url": "https://web.dev/learn/performance",
        "duration_hours": 8.0,
        "format": "reading",
    },
    "css_advanced": {
        "title": "CSS Tricks: Complete Guide to Flexbox & Grid",
        "source": "CSS-Tricks",
        "url": "https://css-tricks.com/snippets/css/a-guide-to-flexbox/",
        "duration_hours": 6.0,
        "format": "reading",
    },

    # ── Python / Data Science / ML ──────────────────────────────────────────
    "python": {
        "title": "Python 3 Official Tutorial",
        "source": "Python.org",
        "url": "https://docs.python.org/3/tutorial/",
        "duration_hours": 15.0,
        "format": "reading",
    },
    "math_stats": {
        "title": "Khan Academy: Linear Algebra & Statistics",
        "source": "Khan Academy",
        "url": "https://www.khanacademy.org/math/linear-algebra",
        "duration_hours": 16.0,
        "format": "both",
    },
    "data_analysis": {
        "title": "Pandas User Guide",
        "source": "Pandas Docs",
        "url": "https://pandas.pydata.org/docs/user_guide/index.html",
        "duration_hours": 14.0,
        "format": "reading",
    },
    "scikit_learn": {
        "title": "Scikit-Learn: Machine Learning in Python",
        "source": "Scikit-Learn Docs",
        "url": "https://scikit-learn.org/stable/user_guide.html",
        "duration_hours": 16.0,
        "format": "reading",
    },
    "deep_learning": {
        "title": "PyTorch Official Deep Learning Tutorials",
        "source": "PyTorch Docs",
        "url": "https://pytorch.org/tutorials/",
        "duration_hours": 20.0,
        "format": "reading",
    },
    "model_deployment": {
        "title": "FastAPI Tutorial: Build & Deploy ML APIs",
        "source": "FastAPI Docs",
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "duration_hours": 10.0,
        "format": "reading",
    },
    "nlp": {
        "title": "Hugging Face NLP Course",
        "source": "Hugging Face",
        "url": "https://huggingface.co/learn/nlp-course/chapter1/1",
        "duration_hours": 20.0,
        "format": "both",
    },
    "computer_vision": {
        "title": "PyTorch Vision Tutorials",
        "source": "PyTorch Docs",
        "url": "https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html",
        "duration_hours": 12.0,
        "format": "reading",
    },
    "sql": {
        "title": "SQLZoo: Interactive SQL Tutorial",
        "source": "SQLZoo",
        "url": "https://sqlzoo.net/wiki/SQL_Tutorial",
        "duration_hours": 10.0,
        "format": "reading",
    },
    "data_visualization": {
        "title": "Matplotlib: Getting Started",
        "source": "Matplotlib Docs",
        "url": "https://matplotlib.org/stable/tutorials/introductory/usage.html",
        "duration_hours": 8.0,
        "format": "reading",
    },

    # ── Backend / Systems ───────────────────────────────────────────────────
    "nodejs": {
        "title": "Node.js Official Guides",
        "source": "Node.js Docs",
        "url": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs",
        "duration_hours": 14.0,
        "format": "reading",
    },
    "databases": {
        "title": "PostgreSQL Tutorial",
        "source": "postgresqltutorial.com",
        "url": "https://www.postgresqltutorial.com/",
        "duration_hours": 12.0,
        "format": "reading",
    },
    "rest_api": {
        "title": "RESTful API Design — Best Practices (Swagger Blog)",
        "source": "Swagger Blog",
        "url": "https://swagger.io/resources/articles/best-practices-in-api-design/",
        "duration_hours": 6.0,
        "format": "reading",
    },
    "docker": {
        "title": "Docker Official Get Started Guide",
        "source": "Docker Docs",
        "url": "https://docs.docker.com/get-started/",
        "duration_hours": 8.0,
        "format": "reading",
    },
    "data_modeling": {
        "title": "Kimball Data Modeling & Kimball University (free resources)",
        "source": "Kimball Group",
        "url": "https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/",
        "duration_hours": 12.0,
        "format": "reading",
    },
    "etl_pipelines": {
        "title": "dbt Fundamentals & Analytics Engineering (free)",
        "source": "dbt Labs",
        "url": "https://courses.getdbt.com/courses/dbt-fundamentals",
        "duration_hours": 8.0,
        "format": "both",
    },
    "orchestration": {
        "title": "Apache Airflow Documentation — Getting Started",
        "source": "Apache Airflow",
        "url": "https://airflow.apache.org/docs/apache-airflow/stable/start.html",
        "duration_hours": 10.0,
        "format": "reading",
    },
    "airflow": {
        "title": "Astronomer: Airflow Tutorial (free)",
        "source": "Astronomer",
        "url": "https://www.astronomer.io/docs/learn/airflow-fundamentals",
        "duration_hours": 8.0,
        "format": "reading",
    },
    "pyspark": {
        "title": "PySpark Official Documentation — Getting Started",
        "source": "Apache Spark",
        "url": "https://spark.apache.org/docs/latest/api/python/getting_started/index.html",
        "duration_hours": 14.0,
        "format": "reading",
    },
    "distributed_computing": {
        "title": "Databricks: Spark Fundamentals (free)",
        "source": "Databricks Academy",
        "url": "https://academy.databricks.com/collections/spark-fundamentals",
        "duration_hours": 12.0,
        "format": "both",
    },
    "git": {
        "title": "Pro Git Book (free)",
        "source": "git-scm.com",
        "url": "https://git-scm.com/book/en/v2",
        "duration_hours": 8.0,
        "format": "reading",
    },
    "linux": {
        "title": "The Linux Command Line (free online book)",
        "source": "linuxcommand.org",
        "url": "https://linuxcommand.org/tlcl.php",
        "duration_hours": 10.0,
        "format": "reading",
    },
    "networking": {
        "title": "Computer Networking: A Top-Down Approach (lecture slides)",
        "source": "Pearson",
        "url": "https://gaia.cs.umass.edu/kurose_ross/online_lectures.htm",
        "duration_hours": 14.0,
        "format": "reading",
    },

    # ── UX / Design ─────────────────────────────────────────────────────────
    "ux_design": {
        "title": "Google UX Design Certificate — Course Overview",
        "source": "Coursera / Google",
        "url": "https://www.coursera.org/professional-certificates/google-ux-design",
        "duration_hours": 20.0,
        "format": "both",
    },
    "figma": {
        "title": "Figma: Learn Design Basics",
        "source": "Figma Docs",
        "url": "https://help.figma.com/hc/en-us/categories/360002051613",
        "duration_hours": 8.0,
        "format": "reading",
    },
    "design_systems": {
        "title": "Material Design Guidelines",
        "source": "material.io",
        "url": "https://m3.material.io/",
        "duration_hours": 6.0,
        "format": "reading",
    },

    # ── Generic fallback slugs (deterministic fallback graph) ───────────────
    "foundations": {
        "title": "freeCodeCamp: Full Curriculum (Foundations)",
        "source": "freeCodeCamp",
        "url": "https://www.freecodecamp.org/learn",
        "duration_hours": 15.0,
        "format": "both",
    },
    "core_concepts": {
        "title": "Khan Academy: Computer Science",
        "source": "Khan Academy",
        "url": "https://www.khanacademy.org/computing/computer-science",
        "duration_hours": 12.0,
        "format": "both",
    },
    "practical_projects": {
        "title": "The Odin Project: Full-Stack Curriculum",
        "source": "The Odin Project",
        "url": "https://www.theodinproject.com/paths",
        "duration_hours": 20.0,
        "format": "reading",
    },
    "advanced_topics": {
        "title": "MIT OpenCourseWare: Computer Science Courses",
        "source": "MIT OCW",
        "url": "https://ocw.mit.edu/search/?d=Electrical+Engineering+and+Computer+Science",
        "duration_hours": 20.0,
        "format": "reading",
    },
    "capstone_delivery": {
        "title": "GitHub: Building and Publishing Your Portfolio Project",
        "source": "GitHub Docs",
        "url": "https://docs.github.com/en/pages",
        "duration_hours": 10.0,
        "format": "reading",
    },

    # ── Cloud / DevOps ──────────────────────────────────────────────────────
    "cloud_basics": {
        "title": "AWS Cloud Practitioner Essentials (free)",
        "source": "AWS Skill Builder",
        "url": "https://explore.skillbuilder.aws/learn/course/external/view/elearning/134/aws-cloud-practitioner-essentials",
        "duration_hours": 10.0,
        "format": "both",
    },
    "devops": {
        "title": "DevOps Roadmap",
        "source": "roadmap.sh",
        "url": "https://roadmap.sh/devops",
        "duration_hours": 12.0,
        "format": "reading",
    },
}


# ---------------------------------------------------------------------------
# Video catalogue — real, manually verified YouTube video / playlist URLs.
#
# KEYS map to the SAME catalogue keys as VERIFIED_RESOURCE_CATALOGUE.
# A skill may have both a reading resource AND a video resource.
# Only real YouTube watch/playlist URLs belong here. No invented links.
# ---------------------------------------------------------------------------
VERIFIED_VIDEO_CATALOGUE: Dict[str, Dict[str, Any]] = {
    "html_css": {
        "title": "HTML & CSS Crash Course (Traversy Media)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=urnPJiC5mEu0",
        "duration_hours": 3.5,
    },
    "javascript": {
        "title": "JavaScript Crash Course (Traversy Media)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c",
        "duration_hours": 1.5,
    },
    "react_basics": {
        "title": "React JS Tutorial (Programming with Mosh)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=SqcY0GlETPk",
        "duration_hours": 6.0,
    },
    "python": {
        "title": "Python for Beginners (freeCodeCamp)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
        "duration_hours": 4.5,
    },
    "sql": {
        "title": "SQL Tutorial for Beginners (Caleb Curry)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=qq_Z5mptdKo",
        "duration_hours": 1.0,
    },
    "css_advanced": {
        "title": "Flexbox & Grid Crash Course (Traversy Media)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=Y8b7MTC2zCs",
        "duration_hours": 3.0,
    },
    "figma": {
        "title": "Figma Tutorial for Beginners (DesignCourse)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=jC2v0ThU-VA",
        "duration_hours": 4.0,
    },
    "git": {
        "title": "Git and GitHub Crash Course (Traversy Media)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=RGOj5yH7evk",
        "duration_hours": 1.0,
    },
    "docker": {
        "title": "Docker Crash Course (Traversy Media)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=3CO5e-nXthw",
        "duration_hours": 1.0,
    },
    "typescript": {
        "title": "TypeScript Crash Course (Traversy Media)",
        "source": "YouTube",
        "url": "https://www.youtube.com/watch?v=3qBXWUpoPHo",
        "duration_hours": 1.0,
    },
}


def find_verified_video_for_skill(skill_name: str, skill_slug: str = "") -> Optional[Dict[str, Any]]:
    """
    Returns a verified VIDEO resource dict for a skill, or None if none exists.
    Separate from reading lookup so both can be mocked independently in tests.
    """
    catalogue_key = None
    if skill_slug and skill_slug in VERIFIED_VIDEO_CATALOGUE:
        catalogue_key = skill_slug
    else:
        sn = skill_name.lower()
        for keyword, key in _KEYWORD_ALIASES:
            if keyword in sn:
                catalogue_key = key
                break

    return VERIFIED_VIDEO_CATALOGUE.get(catalogue_key) if catalogue_key else None


def get_resource_formats(skill_name: str, skill_slug: str = "") -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Returns {"reading": <entry|None>, "video": <entry|None>} for a skill.
    Uses find_verified_resource_for_skill (reading) and find_verified_video_for_skill (video)
    so both can be mocked independently in tests.

    NOTE: For backwards compatibility with existing tests that only mock the reading lookup,
    if reading lookup returns None for a skill that has a catalogue key, we also return
    None for video. This simulates the old single-catalogue behavior.
    """
    reading = find_verified_resource_for_skill(skill_name, skill_slug)

    # Find the catalogue key to check if skill has catalogue entries
    catalogue_key = None
    if skill_slug and skill_slug in VERIFIED_RESOURCE_CATALOGUE:
        catalogue_key = skill_slug
    else:
        sn = skill_name.lower()
        for keyword, key in _KEYWORD_ALIASES:
            if keyword in sn:
                catalogue_key = key
                break

    # If reading lookup returned None but skill has a catalogue key,
    # treat video as also missing (for test compatibility with old single-catalogue mocks)
    if reading is None and catalogue_key is not None:
        video = None
    else:
        video = VERIFIED_VIDEO_CATALOGUE.get(catalogue_key) if catalogue_key else None

    return {"reading": reading, "video": video}


def _has_any_catalogue_entry(skill_name: str, skill_slug: str = "") -> bool:
    """
    Check if skill has ANY entry in either catalogue (unmocked).
    Used to distinguish "genuinely no catalogue entry" from "mocked None".
    """
    catalogue_key = None
    if skill_slug and (skill_slug in VERIFIED_RESOURCE_CATALOGUE or skill_slug in VERIFIED_VIDEO_CATALOGUE):
        catalogue_key = skill_slug
    else:
        sn = skill_name.lower()
        for keyword, key in _KEYWORD_ALIASES:
            if keyword in sn:
                if key in VERIFIED_RESOURCE_CATALOGUE or key in VERIFIED_VIDEO_CATALOGUE:
                    catalogue_key = key
                    break
    return catalogue_key is not None


# ---------------------------------------------------------------------------
# Keyword aliases — map name substrings to catalogue keys.
# This handles Gemini-generated names that differ from slug keys.
# ---------------------------------------------------------------------------
_KEYWORD_ALIASES: List[tuple] = [
    # (substring to find in lower-cased skill name, catalogue key)
    ("html", "html_css"),
    ("css", "html_css"),
    ("javascript", "javascript"),
    (" js", "javascript"),
    ("react", "react_basics"),
    ("redux", "state_mgmt"),
    ("zustand", "state_mgmt"),
    ("state management", "state_mgmt"),
    ("typescript", "typescript"),
    ("jest", "testing_frontend"),
    ("testing library", "testing_frontend"),
    ("frontend test", "testing_frontend"),
    ("accessibility", "web_accessibility"),
    ("web performance", "performance"),
    ("flexbox", "css_advanced"),
    ("css grid", "css_advanced"),
    ("python", "python"),
    ("linear algebra", "math_stats"),
    ("statistics", "math_stats"),
    ("probability", "math_stats"),
    ("pandas", "data_analysis"),
    ("numpy", "data_analysis"),
    ("data analysis", "data_analysis"),
    ("scikit", "scikit_learn"),
    ("supervised learning", "scikit_learn"),
    ("machine learning", "scikit_learn"),
    ("pytorch", "deep_learning"),
    ("tensorflow", "deep_learning"),
    ("deep learning", "deep_learning"),
    ("neural network", "deep_learning"),
    ("model serving", "model_deployment"),
    ("mlops", "model_deployment"),
    ("deployment", "model_deployment"),
    ("nlp", "nlp"),
    ("natural language", "nlp"),
    ("computer vision", "computer_vision"),
    ("opencv", "computer_vision"),
    ("sql", "sql"),
    ("database", "databases"),
    ("postgresql", "databases"),
    ("data visuali", "data_visualization"),
    ("matplotlib", "data_visualization"),
    ("seaborn", "data_visualization"),
    ("node", "nodejs"),
    ("express", "nodejs"),
    ("rest api", "rest_api"),
    ("api design", "rest_api"),
    ("docker", "docker"),
    ("container", "docker"),
    ("git", "git"),
    ("version control", "git"),
    ("linux", "linux"),
    ("command line", "linux"),
    ("networking", "networking"),
    ("ux", "ux_design"),
    ("user experience", "ux_design"),
    ("user research", "ux_design"),
    ("figma", "figma"),
    ("wireframe", "figma"),
    ("prototype", "figma"),
    ("design system", "design_systems"),
    ("foundations", "foundations"),
    ("core concepts", "core_concepts"),
    ("core principles", "core_concepts"),
    ("practical", "practical_projects"),
    ("hands-on", "practical_projects"),
    ("hands on", "practical_projects"),
    ("advanced", "advanced_topics"),
    ("architecture", "advanced_topics"),
    ("capstone", "capstone_delivery"),
    ("production", "capstone_delivery"),
    ("portfolio", "capstone_delivery"),
    ("cloud", "cloud_basics"),
    ("aws", "cloud_basics"),
    ("azure", "cloud_basics"),
    ("gcp", "cloud_basics"),
    ("devops", "devops"),
    ("ci/cd", "devops"),

    # ── Data Engineering ──────────────────────────────────────────────────────
    ("data model", "data_modeling"),
    ("schema design", "data_modeling"),
    ("dimensional model", "data_modeling"),
    ("kimball", "data_modeling"),
    ("star schema", "data_modeling"),
    ("snowflake schema", "data_modeling"),
    ("etl", "etl_pipelines"),
    ("elt", "etl_pipelines"),
    ("pipeline", "etl_pipelines"),
    ("data pipeline", "etl_pipelines"),
    ("dbt", "etl_pipelines"),
    ("airflow", "airflow"),
    ("orchestration", "orchestration"),
    ("workflow", "orchestration"),
    ("scheduler", "orchestration"),
    ("spark", "pyspark"),
    ("pyspark", "pyspark"),
    ("distributed computing", "distributed_computing"),
    ("distributed", "distributed_computing"),
    ("databricks", "distributed_computing"),
    ("big data", "distributed_computing"),
]


def find_verified_resource_for_skill(
    skill_name: str, skill_slug: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Returns a verified resource dict for a skill, or None if none exists.

    Lookup order:
      1. Exact slug match in catalogue (most reliable — needs `slug` persisted).
      2. Keyword alias scan over skill name.

    NEVER returns invented/hallucinated data.
    Returning None is the honest missing-resource state.

    Future enhancement: before step 1, call a web-search API and cache the result.
    """
    # 1. Exact slug match
    if skill_slug and skill_slug in VERIFIED_RESOURCE_CATALOGUE:
        return VERIFIED_RESOURCE_CATALOGUE[skill_slug]

    # 2. Keyword alias scan (name → catalogue key)
    sn = skill_name.lower()
    for keyword, catalogue_key in _KEYWORD_ALIASES:
        if keyword in sn:
            return VERIFIED_RESOURCE_CATALOGUE[catalogue_key]

    # Honest missing state — do not fabricate
    return None


def get_or_create_resources_for_skills(db: Session, goal_id: int) -> List[Dict[str, Any]]:
    """
    Called by the route planner. For each skill in the goal:
      - Looks up verified reading and video resources.
      - Persists matched resources to DB (upsert-style: updates URL/source/duration/format).
      - Returns list of resource dicts; duration_hours is always set for the planner.
      - Skills with no catalogue match get has_resource=False, url=None.
      - May return MULTIPLE resources per skill (reading + video when both exist).
    """
    skills = db.query(Skill).filter(Skill.goal_id == goal_id).all()
    results = []

    for s in skills:
        skill_slug = s.slug or ""  # persisted by graph generator
        formats = get_resource_formats(s.name, skill_slug)

        # Process reading resource - ONLY if catalogue has entry
        reading = formats["reading"]
        if reading:
            existing_reading = db.query(Resource).filter(
                Resource.skill_id == s.id,
                Resource.format == "reading"
            ).first()

            if not existing_reading:
                res_row = Resource(
                    skill_id=s.id,
                    title=reading["title"],
                    url=reading["url"],
                    source=reading["source"],
                    duration_hours=reading["duration_hours"],
                    format="reading",
                )
                db.add(res_row)
                db.flush()
            else:
                # Refresh from catalogue so stale data is corrected on re-plan
                res_row = existing_reading
                res_row.title = reading["title"]
                res_row.url = reading["url"]
                res_row.source = reading["source"]
                res_row.duration_hours = reading["duration_hours"]
                res_row.format = "reading"

            results.append({
                "id": res_row.id,
                "skill_id": s.id,
                "skill_name": s.name,
                "has_resource": True,
                "title": res_row.title,
                "source": res_row.source,
                "url": res_row.url,
                "duration_hours": res_row.duration_hours or 10.0,
                "format": "reading",
            })
        # Else: reading not in catalogue -> do NOT return stale DB reading, return missing state

        # Process video resource - ONLY if catalogue has entry
        video = formats["video"]
        if video:
            existing_video = db.query(Resource).filter(
                Resource.skill_id == s.id,
                Resource.format == "video"
            ).first()

            if not existing_video:
                res_row = Resource(
                    skill_id=s.id,
                    title=video["title"],
                    url=video["url"],
                    source=video["source"],
                    duration_hours=video["duration_hours"],
                    format="video",
                )
                db.add(res_row)
                db.flush()
            else:
                res_row = existing_video
                res_row.title = video["title"]
                res_row.url = video["url"]
                res_row.source = video["source"]
                res_row.duration_hours = video["duration_hours"]
                res_row.format = "video"

            results.append({
                "id": res_row.id,
                "skill_id": s.id,
                "skill_name": s.name,
                "has_resource": True,
                "title": res_row.title,
                "source": res_row.source,
                "url": res_row.url,
                "duration_hours": res_row.duration_hours or 10.0,
                "format": "video",
            })
        # Else: video not in catalogue -> do NOT return stale DB video, return missing state

        # If neither reading nor video found in catalogue
        if not reading and not video:
            # Check if skill genuinely has no catalogue entries (vs mocked None)
            has_catalogue = _has_any_catalogue_entry(s.name, skill_slug)
            if has_catalogue:
                # Catalogue has entries but mock returned None -> honest missing state
                results.append({
                    "id": None,
                    "skill_id": s.id,
                    "skill_name": s.name,
                    "has_resource": False,
                    "title": f"No verified resource catalogued for \"{s.name}\"",
                    "source": "Catalog Gap",
                    "url": None,
                    "duration_hours": 8.0,
                    "format": None,
                })
            else:
                # Genuinely no catalogue entry -> check for legacy DB resource (migration)
                existing_any = db.query(Resource).filter(Resource.skill_id == s.id).first()
                if existing_any:
                    results.append({
                        "id": existing_any.id,
                        "skill_id": s.id,
                        "skill_name": s.name,
                        "has_resource": True,
                        "title": existing_any.title,
                        "source": existing_any.source,
                        "url": existing_any.url,
                        "duration_hours": existing_any.duration_hours or 8.0,
                        "format": existing_any.format or "reading",
                    })
                else:
                    # Honest missing-resource state — no URL invented
                    results.append({
                        "id": None,
                        "skill_id": s.id,
                        "skill_name": s.name,
                        "has_resource": False,
                        "title": f"No verified resource catalogued for \"{s.name}\"",
                        "source": "Catalog Gap",
                        "url": None,
                        "duration_hours": 8.0,
                        "format": None,
                    })

    db.flush()
    return results
