"""Behavior signal domain model.

Defines interaction style signals for behavioral pattern recognition.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class BehaviorSignal(Base):
    """Behavioral interaction signal entity.
    
    Represents different interaction styles or behavioral patterns exhibited
    by users during system interaction.
    
    Attributes:
        signal_id: Unique identifier
        signal_name: Signal category name (e.g., 'ITERATIVE', 'GOAL_ORIENTED')
        description: Detailed description of the behavioral signal
    """
    __tablename__ = "behavior_signal"

    signal_id = Column(Integer, primary_key=True)
    signal_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
