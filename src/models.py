from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from src.database import Base


class ReviewRecord(Base):
    # This explicitly names the table inside the SQLite database
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    language = Column(String, index=True)
    issues_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
