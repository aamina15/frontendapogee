import os
import json
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import httpx
from config import settings

logger = logging.getLogger("apogee.ai_service")


class GeminiSkillItem(BaseModel):
    id: str = Field(..., description="Short snake_case or kebab-case identifier, e.g. python, html_css, pytorch")
    name: str = Field(..., description="Human readable skill name, e.g. Python Fundamentals")
    target_level: str = Field("Proficient", description="Proficiency level: Beginner, Proficient, or Expert")
    importance: float = Field(1.0, description="Importance score from 0.1 to 1.0")


class GeminiDependencyItem(BaseModel):
    from_id: str = Field(..., alias="from", description="Prerequisite skill ID")
    to_id: str = Field(..., alias="to", description="Dependent skill ID that requires the prerequisite")

    class Config:
        populate_by_name = True


class GeminiDAGResponse(BaseModel):
    skills: List[GeminiSkillItem] = Field(..., min_length=1, max_length=20)
    dependencies: List[GeminiDependencyItem]


def get_fallback_dag_for_goal(title: str) -> Dict[str, Any]:
    """
    Smart deterministic fallback generator for when Gemini API key is missing or unavailable.
    Creates 5-8 structured skills and DAG dependencies tailored to the goal title.
    """
    t = title.lower()

    if "frontend" in t or "web" in t or "react" in t:
        skills = [
            {"id": "html_css", "name": "HTML5 & Modern CSS Layouts", "target_level": "Proficient", "importance": 0.9},
            {"id": "javascript", "name": "JavaScript (ES6+)", "target_level": "Proficient", "importance": 1.0},
            {"id": "react_basics", "name": "React Core & Components", "target_level": "Proficient", "importance": 0.95},
            {"id": "state_mgmt", "name": "State Management (Redux/Zustand)", "target_level": "Proficient", "importance": 0.8},
            {"id": "typescript", "name": "TypeScript Fundamentals", "target_level": "Proficient", "importance": 0.85},
            {"id": "testing_frontend", "name": "Frontend Testing (Jest/RTL)", "target_level": "Beginner", "importance": 0.75},
        ]
        dependencies = [
            {"from": "html_css", "to": "javascript"},
            {"from": "javascript", "to": "react_basics"},
            {"from": "javascript", "to": "typescript"},
            {"from": "react_basics", "to": "state_mgmt"},
            {"from": "react_basics", "to": "testing_frontend"},
        ]
    elif "machine learning" in t or "ml" in t or "ai" in t or "python" in t or "data" in t:
        skills = [
            {"id": "python", "name": "Python Programming", "target_level": "Proficient", "importance": 1.0},
            {"id": "math_stats", "name": "Linear Algebra & Statistics", "target_level": "Proficient", "importance": 0.85},
            {"id": "data_analysis", "name": "Data Analysis (Pandas/NumPy)", "target_level": "Proficient", "importance": 0.9},
            {"id": "scikit_learn", "name": "Supervised Learning (Scikit-Learn)", "target_level": "Proficient", "importance": 0.9},
            {"id": "deep_learning", "name": "Deep Learning (PyTorch/TensorFlow)", "target_level": "Proficient", "importance": 0.95},
            {"id": "model_deployment", "name": "Model Serving & MLOps", "target_level": "Beginner", "importance": 0.8},
        ]
        dependencies = [
            {"from": "python", "to": "data_analysis"},
            {"from": "math_stats", "to": "data_analysis"},
            {"from": "data_analysis", "to": "scikit_learn"},
            {"from": "scikit_learn", "to": "deep_learning"},
            {"from": "deep_learning", "to": "model_deployment"},
        ]
    else:
        skills = [
            {"id": "foundations", "name": f"Foundations of {title[:30]}", "target_level": "Proficient", "importance": 1.0},
            {"id": "core_concepts", "name": "Core Principles & Syntax", "target_level": "Proficient", "importance": 0.9},
            {"id": "practical_projects", "name": "Hands-on Implementation", "target_level": "Proficient", "importance": 0.85},
            {"id": "advanced_topics", "name": "Advanced Architecture & Patterns", "target_level": "Proficient", "importance": 0.8},
            {"id": "capstone_delivery", "name": "Production Capstone Project", "target_level": "Expert", "importance": 0.95},
        ]
        dependencies = [
            {"from": "foundations", "to": "core_concepts"},
            {"from": "core_concepts", "to": "practical_projects"},
            {"from": "practical_projects", "to": "advanced_topics"},
            {"from": "advanced_topics", "to": "capstone_delivery"},
        ]

    return {"skills": skills, "dependencies": dependencies, "source": "fallback",
            "warning": "AI generation unavailable. Showing a curated fallback graph."}


def generate_skill_dag_with_gemini(
    goal_title: str,
    hours_per_week: float = 10.0,
    duration_weeks: int = 12,
    budget: float = 0.0
) -> Dict[str, Any]:
    """
    Calls Gemini API to generate structured skill DAG for a learner's goal.
    Uses strict JSON schema and falls back gracefully if Gemini API key is missing or encounters errors.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        logger.info("GEMINI_API_KEY not configured. Using deterministic fallback graph generator.")
        return get_fallback_dag_for_goal(goal_title)

    prompt = f"""
You are APOGEE's Skill Graph AI Architect.
Generate a concise, structured prerequisite Skill Graph (DAG) for a learner's goal:
- Goal Title: "{goal_title}"
- Weekly Time Commitment: {hours_per_week} hours/week
- Target Horizon: {duration_weeks} weeks
- Budget: ${budget}

REQUIREMENTS:
1. Provide between 5 and 10 essential skills necessary to master this goal.
2. Provide directed prerequisite dependencies between skills (from -> to).
3. "from" is the prerequisite skill ID, and "to" is the dependent skill ID.
4. Keep skill IDs short, clean, and lowercase snake_case (e.g. "python", "html_css", "pytorch").
5. The graph must be an ACYCLIC directed graph (no cycles!).

Respond ONLY with JSON matching this exact structure:
{{
  "skills": [
    {{
      "id": "python",
      "name": "Python Fundamentals",
      "target_level": "Proficient",
      "importance": 0.9
    }}
  ],
  "dependencies": [
    {{
      "from": "python",
      "to": "pytorch"
    }}
  ]
}}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        }
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code != 200:
                logger.warning(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
                return get_fallback_dag_for_goal(goal_title)

            res_data = resp.json()
            candidates = res_data.get("candidates", [])
            if not candidates:
                return get_fallback_dag_for_goal(goal_title)

            text_content = candidates[0]["content"]["parts"][0]["text"]
            parsed_json = json.loads(text_content)

            # Validate against Pydantic model
            parsed_response = GeminiDAGResponse.model_validate(parsed_json)
            
            # Convert back to standard dicts with "from" and "to" keys
            return {
                "source": "gemini",
                "warning": None,
                "skills": [s.model_dump() for s in parsed_response.skills],
                "dependencies": [
                    {"from": d.from_id, "to": d.to_id} for d in parsed_response.dependencies
                ]
            }

    except Exception as e:
        logger.error(f"Error calling Gemini API for DAG generation: {e}")
        return get_fallback_dag_for_goal(goal_title)
