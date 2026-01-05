"""Output Preference domain model.

Defines response format preferences for controlling how responses are structured.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class OutputPreference(Base):
    """Output preference entity.
    
    Represents different response format preferences that control how
    responses are structured and delivered to users.
    
    Attributes:
        output_pref_id: Unique identifier
        format_name: Preference format name (e.g., 'STEP_BY_STEP', 'BULLET_POINTS')
        description: Detailed description of the output format
    """
    __tablename__ = "output_preference"

    output_pref_id = Column(Integer, primary_key=True, autoincrement=True)
    format_name = Column(Text, unique=True, nullable=False)
    description = Column(Text)
