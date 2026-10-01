import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

DATABASE_URL = getattr(settings, "DATABASE_URL", None) or os.getenv("DATABASE_URL", "sqlite:///./apogee.db")

# SQLite connection args for multithreading
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def lock_goal_write(db, goal_id):
    """Serialize idempotent creation/versioning for a goal across worker requests."""
    from sqlalchemy import text
    if db.bind.dialect.name == "sqlite":
        if not db.connection().connection.in_transaction:
            db.execute(text("BEGIN IMMEDIATE"))
    else:
        from models.goal import Goal
        db.query(Goal).filter(Goal.id == goal_id).with_for_update().first()
