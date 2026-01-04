"""Intent domain model.

Defines user intent categories for behavioral analysis and profile matching.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Intent(Base):
    """User intent category entity.
    
    Represents different user purposes or goals when interacting with the system.
    Used for behavioral analysis and profile matching.
    
    Attributes:
        intent_id: Unique identifier
        intent_name: Intent category name (e.g., 'LEARNING', 'TASK_COMPLETION')
        description: Detailed description of the intent
    """
    __tablename__ = "intent"

    intent_id = Column(Integer, primary_key=True)
    intent_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
