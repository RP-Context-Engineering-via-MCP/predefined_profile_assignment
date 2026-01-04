"""Domain domain model.

Defines knowledge or interest domains for user classification.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Domain(Base):
    """Knowledge or interest domain entity.
    
    Represents different subject areas or domains of interest.
    Used for categorizing user interests and knowledge areas.
    
    Attributes:
        domain_id: Unique identifier
        domain_name: Domain category name (e.g., 'TECHNICAL', 'BUSINESS')
        description: Detailed description of the domain
    """
    __tablename__ = "domain"

    domain_id = Column(Integer, primary_key=True)
    domain_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
