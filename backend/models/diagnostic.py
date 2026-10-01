from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from db.database import Base


class DiagnosticQuestion(Base):
    __tablename__ = "diagnostic_questions"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_db_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=True)
    skill_slug = Column(String, nullable=False)
    skill_name = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)             # JSON array of option strings
    correct_index = Column(Integer, nullable=False)   # Server-side answer index (0..3)
    explanation = Column(Text, nullable=True)          # Server-side explanation
