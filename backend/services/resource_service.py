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
    },
    "javascript": {
        "title": "The Modern JavaScript Tutorial",
        "source": "javascript.info",
        "url": "https://javascript.info/",
        "duration_hours": 18.0,
    },
    "react_basics": {
        "title": "React Official Docs: Quick Start & Hooks",
        "source": "React.dev",
        "url": "https://react.dev/learn",
        "duration_hours": 15.0,
    },
    "state_mgmt": {
        "title": "Redux Toolkit: Getting Started",
        "source": "Redux Docs",
        "url": "https://redux-toolkit.js.org/introduction/getting-started",
        "duration_hours": 10.0,
    },
    "typescript": {
        "title": "TypeScript Handbook: The Basics",
        "source": "TypeScript Docs",
        "url": "https://www.typescriptlang.org/docs/handbook/intro.html",
        "duration_hours": 10.0,
    },
    "testing_frontend": {
        "title": "React Testing Library: Introduction",
        "source": "Testing Library Docs",
        "url": "https://testing-library.com/docs/react-testing-library/intro/",
        "duration_hours": 8.0,
    },
    "web_accessibility": {
        "title": "Web Accessibility Initiative (WAI) Tutorials",
        "source": "W3C WAI",
        "url": "https://www.w3.org/WAI/tutorials/",
        "duration_hours": 6.0,
    },
    "performance": {
        "title": "web.dev: Learn Performance",
        "source": "web.dev",
        "url": "https://web.dev/learn/performance",
        "duration_hours": 8.0,
    },
    "css_advanced": {
        "title": "CSS Tricks: Complete Guide to Flexbox & Grid",
        "source": "CSS-Tricks",
        "url": "https://css-tricks.com/snippets/css/a-guide-to-flexbox/",
        "duration_hours": 6.0,
    },

    # ── Python / Data Science / ML ──────────────────────────────────────────
    "python": {
        "title": "Python 3 Official Tutorial",
        "source": "Python.org",
        "url": "https://docs.python.org/3/tutorial/",
        "duration_hours": 15.0,
    },
    "math_stats": {
        "title": "Khan Academy: Linear Algebra & Statistics",
        "source": "Khan Academy",
        "url": "https://www.khanacademy.org/math/linear-algebra",
        "duration_hours": 16.0,
    },
    "data_analysis": {
        "title": "Pandas User Guide",
        "source": "Pandas Docs",
        "url": "https://pandas.pydata.org/docs/user_guide/index.html",
        "duration_hours": 14.0,
    },
    "scikit_learn": {
        "title": "Scikit-Learn: Machine Learning in Python",
        "source": "Scikit-Learn Docs",
        "url": "https://scikit-learn.org/stable/user_guide.html",
        "duration_hours": 16.0,
    },
    "deep_learning": {
        "title": "PyTorch Official Deep Learning Tutorials",
        "source": "PyTorch Docs",
        "url": "https://pytorch.org/tutorials/",
        "duration_hours": 20.0,
    },
    "model_deployment": {
        "title": "FastAPI Tutorial: Build & Deploy ML APIs",
        "source": "FastAPI Docs",
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "duration_hours": 10.0,
    },
    "nlp": {
        "title": "Hugging Face NLP Course",
        "source": "Hugging Face",
        "url": "https://huggingface.co/learn/nlp-course/chapter1/1",
        "duration_hours": 20.0,
    },
    "computer_vision": {
        "title": "PyTorch Vision Tutorials",
        "source": "PyTorch Docs",
        "url": "https://pytorch.org/tutorials/intermediate/torchvision_tutorial.html",
        "duration_hours": 12.0,
    },
    "sql": {
        "title": "SQLZoo: Interactive SQL Tutorial",
        "source": "SQLZoo",
        "url": "https://sqlzoo.net/wiki/SQL_Tutorial",
        "duration_hours": 10.0,
    },
    "data_visualization": {
        "title": "Matplotlib: Getting Started",
        "source": "Matplotlib Docs",
        "url": "https://matplotlib.org/stable/tutorials/introductory/usage.html",
        "duration_hours": 8.0,
    },

    # ── Backend / Systems ───────────────────────────────────────────────────
    "nodejs": {
        "title": "Node.js Official Guides",
        "source": "Node.js Docs",
        "url": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs",
        "duration_hours": 14.0,
    },
    "databases": {
        "title": "PostgreSQL Tutorial",
        "source": "postgresqltutorial.com",
        "url": "https://www.postgresqltutorial.com/",
        "duration_hours": 12.0,
    },
    "rest_api": {
        "title": "RESTful API Design — Best Practices (Swagger Blog)",
        "source": "Swagger Blog",
        "url": "https://swagger.io/resources/articles/best-practices-in-api-design/",
        "duration_hours": 6.0,
    },
    "docker": {
        "title": "Docker Official Get Started Guide",
        "source": "Docker Docs",
        "url": "https://docs.docker.com/get-started/",
        "duration_hours": 8.0,
    },
    "git": {
        "title": "Pro Git Book (free)",
        "source": "git-scm.com",
        "url": "https://git-scm.com/book/en/v2",
        "duration_hours": 8.0,
    },
    "linux": {
        "title": "The Linux Command Line (free online book)",
        "source": "linuxcommand.org",
        "url": "https://linuxcommand.org/tlcl.php",
        "duration_hours": 10.0,
    },
    "networking": {
        "title": "Computer Networking: A Top-Down Approach (lecture slides)",
        "source": "Pearson",
        "url": "https://gaia.cs.umass.edu/kurose_ross/online_lectures.htm",
        "duration_hours": 14.0,
    },

    # ── UX / Design ─────────────────────────────────────────────────────────
    "ux_design": {
        "title": "Google UX Design Certificate — Course Overview",
        "source": "Coursera / Google",
        "url": "https://www.coursera.org/professional-certificates/google-ux-design",
        "duration_hours": 20.0,
    },
    "figma": {
        "title": "Figma: Learn Design Basics",
        "source": "Figma Docs",
        "url": "https://help.figma.com/hc/en-us/categories/360002051613",
        "duration_hours": 8.0,
    },
    "design_systems": {
        "title": "Material Design Guidelines",
        "source": "material.io",
        "url": "https://m3.material.io/",
        "duration_hours": 6.0,
    },

    # ── Generic fallback slugs (deterministic fallback graph) ───────────────
    "foundations": {
        "title": "freeCodeCamp: Full Curriculum (Foundations)",
        "source": "freeCodeCamp",
        "url": "https://www.freecodecamp.org/learn",
        "duration_hours": 15.0,
    },
    "core_concepts": {
        "title": "Khan Academy: Computer Science",
        "source": "Khan Academy",
        "url": "https://www.khanacademy.org/computing/computer-science",
        "duration_hours": 12.0,
    },
    "practical_projects": {
        "title": "The Odin Project: Full-Stack Curriculum",
        "source": "The Odin Project",
        "url": "https://www.theodinproject.com/paths",
        "duration_hours": 20.0,
    },
    "advanced_topics": {
        "title": "MIT OpenCourseWare: Computer Science Courses",
        "source": "MIT OCW",
        "url": "https://ocw.mit.edu/search/?d=Electrical+Engineering+and+Computer+Science",
        "duration_hours": 20.0,
    },
    "capstone_delivery": {
        "title": "GitHub: Building and Publishing Your Portfolio Project",
        "source": "GitHub Docs",
        "url": "https://docs.github.com/en/pages",
        "duration_hours": 10.0,
    },

    # ── Cloud / DevOps ──────────────────────────────────────────────────────
    "cloud_basics": {
        "title": "AWS Cloud Practitioner Essentials (free)",
        "source": "AWS Skill Builder",
        "url": "https://explore.skillbuilder.aws/learn/course/external/view/elearning/134/aws-cloud-practitioner-essentials",
        "duration_hours": 10.0,
    },
    "devops": {
        "title": "DevOps Roadmap",
        "source": "roadmap.sh",
        "url": "https://roadmap.sh/devops",
        "duration_hours": 12.0,
    },
}


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
      - Looks up a verified resource (by slug then keyword).
      - Persists matched resources to DB (upsert-style: updates URL/source/duration).
      - Returns list of resource dicts; duration_hours is always set for the planner.
      - Skills with no catalogue match get has_resource=False, url=None.
    """
    skills = db.query(Skill).filter(Skill.goal_id == goal_id).all()
    results = []

    for s in skills:
        skill_slug = s.slug or ""  # persisted by graph generator
        verified = find_verified_resource_for_skill(s.name, skill_slug)

        existing = db.query(Resource).filter(Resource.skill_id == s.id).first()

        if verified:
            if not existing:
                res_row = Resource(
                    skill_id=s.id,
                    title=verified["title"],
                    url=verified["url"],
                    source=verified["source"],
                    duration_hours=verified["duration_hours"],
                )
                db.add(res_row)
                db.flush()
            else:
                # Refresh from catalogue so stale data is corrected on re-plan
                res_row = existing
                res_row.title = verified["title"]
                res_row.url = verified["url"]
                res_row.source = verified["source"]
                res_row.duration_hours = verified["duration_hours"]

            results.append({
                "id": res_row.id,
                "skill_id": s.id,
                "skill_name": s.name,
                "has_resource": True,
                "title": res_row.title,
                "source": res_row.source,
                "url": res_row.url,
                "duration_hours": res_row.duration_hours or 10.0,
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
                "duration_hours": 8.0,  # conservative estimate for planner scheduling
            })

    db.flush()
    return results
