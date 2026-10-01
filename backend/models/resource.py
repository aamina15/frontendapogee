from sqlalchemy import Column, Integer, Float, String, ForeignKey
from db.database import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    url = Column(String, nullable=True)
    source = Column(String, nullable=True)       # e.g. "Coursera", "YouTube", "Book"
    duration_hours = Column(Float, nullable=True)
