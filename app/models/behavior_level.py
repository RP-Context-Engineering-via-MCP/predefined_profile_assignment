# app/models/behavior_level.py

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class BehaviorLevel(Base):
    __tablename__ = "behavior_level"

    behavior_level_id = Column(Integer, primary_key=True)
    level_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
