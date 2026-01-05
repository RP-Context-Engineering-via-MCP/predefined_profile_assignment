"""Domain Expertise Level domain model.

Defines expertise levels for domain knowledge assessment.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class DomainExpertiseLevel(Base):
    """Domain expertise level entity.
    
    Represents different expertise states that can be assigned to users
    based on their knowledge level in specific domains.
    
    Attributes:
        expertise_level_id: Unique identifier
        level_name: Expertise level name (e.g., 'BEGINNER', 'INTERMEDIATE', 'ADVANCED')
        description: Detailed description of the expertise level
    """
    __tablename__ = "domain_expertise_level"

    expertise_level_id = Column(Integer, primary_key=True, autoincrement=True)
    level_name = Column(Text, unique=True, nullable=False)
    description = Column(Text)
