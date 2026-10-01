import os
import sys

# Add parent directory to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

# Import models so SQLAlchemy registers them before create_all
import models  # noqa: F401 – side-effect import
from db.database import Base, engine

from routes.health import router as health_router
from routes.goals import router as goals_router
from routes.skills import router as skills_router
from routes.mastery import router as mastery_router
from routes.resources import router as resources_router
from routes.routes import router as routes_router
from routes.graph import router as graph_router
from routes.diagnostic import router as diagnostic_router
from routes.verification import router as verification_router

# Create all tables on startup (safe for SQLite + PostgreSQL)
Base.metadata.create_all(bind=engine)

# Add nullable metadata columns to existing local databases without changing progress.
from sqlalchemy import inspect, text
for _table, _fields in {"skills": ["slug"], "goals": ["graph_source", "graph_warning", "graph_validation"]}.items():
    with engine.begin() as _conn:
        _cols = {c["name"] for c in inspect(_conn).get_columns(_table)}
        for _field in _fields:
            if _field not in _cols:
                _conn.execute(text(f"ALTER TABLE {_table} ADD COLUMN {_field} TEXT"))

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="APOGEE Skill Intelligence & Learning Navigator Backend API",
    version="0.1.0",
)

# Configure CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router)
app.include_router(goals_router)
app.include_router(skills_router)
app.include_router(mastery_router)
app.include_router(resources_router)
app.include_router(routes_router)
app.include_router(graph_router)
app.include_router(diagnostic_router)
app.include_router(verification_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)

# Unexpected errors are logged on the server, never exposed to learners.
import logging
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    logging.getLogger("apogee").error("Request failed: %s", request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "We could not complete that request. Please try again."})
