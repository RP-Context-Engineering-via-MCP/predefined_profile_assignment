"""Interest area domain model.

Defines specific interest areas for detailed user profiling.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class InterestArea(Base):
    """User interest area entity.
    
    Represents specific areas of user interest used for profile matching.
    Enables detailed categorization of user preferences and focus areas.
    
    Attributes:
        interest_id: Unique identifier
        interest_name: Interest area name (e.g., 'ACADEMIC', 'TECHNICAL')
        description: Detailed description of the interest area
    """
    __tablename__ = "interest_area"

    interest_id = Column(Integer, primary_key=True)
    interest_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
