"""Matching factor domain model.

Defines weighting factors for profile matching algorithm.
"""

from sqlalchemy import Column, Integer, String, Numeric
from app.core.database import Base


class MatchingFactor(Base):
    """Profile matching factor entity.
    
    Represents configurable weighting factors used in the profile matching
    algorithm. Enables fine-tuning of matching criteria importance.
    
    Attributes:
        factor_id: Unique identifier
        factor_name: Factor category name (e.g., 'INTENT', 'INTEREST')
        weight: Numeric weight value (0.00 to 1.00)
    """
    __tablename__ = "matching_factor"

    factor_id = Column(Integer, primary_key=True)
    factor_name = Column(String(50), unique=True, nullable=False)
    weight = Column(Numeric(3, 2), nullable=False)
