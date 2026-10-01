from .goals import router as goals_router
from .skills import router as skills_router
from .mastery import router as mastery_router
from .resources import router as resources_router
from .routes import router as routes_router
from .graph import router as graph_router
from .diagnostic import router as diagnostic_router

__all__ = [
    "goals_router",
    "skills_router",
    "mastery_router",
    "resources_router",
    "routes_router",
    "graph_router",
    "diagnostic_router",
]
