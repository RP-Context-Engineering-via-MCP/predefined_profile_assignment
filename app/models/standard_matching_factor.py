"""Standard matching factor model.

Defines weighting factors for standard profile matching algorithm.
"""

from sqlalchemy import Column, Integer, String, Numeric
from app.core.database import Base


class StandardMatchingFactor(Base):
    """Standard matching factor entity.
    
    Represents configurable weighting factors used in the standard profile
    matching algorithm (full behavioral analysis with all factors).
    
    Attributes:
        factor_id: Unique identifier
        factor_name: Factor category name (e.g., 'INTENT', 'INTEREST')
        weight: Numeric weight value (0.00 to 1.00)
    """
    __tablename__ = "standard_matching_factor"

    factor_id = Column(Integer, primary_key=True, autoincrement=True)
    factor_name = Column(String(50), unique=True, nullable=False)
    weight = Column(Numeric(3, 2), nullable=False)
