"""Behavior level domain model.

Defines behavioral complexity levels used to classify user interaction sophistication.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class BehaviorLevel(Base):
    """Behavioral complexity level entity.
    
    Represents different levels of user behavioral sophistication.
    Used to classify interaction patterns from basic to advanced.
    
    Attributes:
        behavior_level_id: Unique identifier
        level_name: Level name (e.g., 'BASIC', 'INTERMEDIATE', 'ADVANCED')
        description: Detailed description of the behavior level
    """
    __tablename__ = "behavior_level"

    behavior_level_id = Column(Integer, primary_key=True)
    level_name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
