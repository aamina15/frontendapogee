from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime, func
from db.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    total_hours = Column(Float, nullable=True)
    total_weeks = Column(Integer, nullable=True)
    route_json = Column(Text, nullable=True)    # Full serialized route structure
    change_reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
