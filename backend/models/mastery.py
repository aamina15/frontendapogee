from sqlalchemy import Column, Integer, Float, Boolean, ForeignKey, DateTime, func
from db.database import Base

class Mastery(Base):
    __tablename__ = "masteries"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    diagnostic_score = Column(Float, nullable=True)    # 0.0 – 1.0, set after diagnostic
    verification_score = Column(Float, nullable=True)  # 0.0 – 1.0, set after quiz
    verified = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
