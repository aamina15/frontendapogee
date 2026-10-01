from sqlalchemy import Column, String, Integer, Float, ForeignKey
from db.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=True)  # AI-generated snake_case id e.g. "html_css", "python"
    target_level = Column(String, nullable=False, default="Proficient")  # Beginner | Proficient | Expert
    importance = Column(Float, nullable=False, default=1.0)  # 1.0 - 5.0


class SkillDependency(Base):
    __tablename__ = "skill_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    dependent_skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
   