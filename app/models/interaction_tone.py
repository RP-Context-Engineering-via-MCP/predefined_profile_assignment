"""Interaction Tone domain model.

Defines tone preferences for controlling voice, empathy, and response feel.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class InteractionTone(Base):
    """Interaction tone entity.
    
    Represents different tone preferences that control the voice,
    empathy level, and overall feel of responses.
    
    Attributes:
        tone_id: Unique identifier
        tone_name: Tone name (e.g., 'INSTRUCTIONAL', 'PROFESSIONAL')
        description: Detailed description of the interaction tone
    """
    __tablename__ = "interaction_tone"

    tone_id = Column(Integer, primary_key=True, autoincrement=True)
    tone_name = Column(Text, unique=True, nullable=False)
    description = Column(Text)
