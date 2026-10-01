from sqlalchemy import Column, String, Integer, Float, DateTime, func
from db.database import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    hours_per_week = Column(Float, nullable=False, default=10.0)
    duration_weeks = Column(Integer, nullable=False, default=12)
    budget = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="active")  # active | completed | archived
    graph_source = Column(String, nullable=True)
    graph_warning = Column(String, nullable=True)
    graph_validation = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
