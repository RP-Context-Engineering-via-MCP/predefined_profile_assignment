"""Cold-start matching factor model.

Defines weighting factors for cold-start profile matching algorithm.
"""

from sqlalchemy import Column, Integer, String, Numeric
from app.core.database import Base


class ColdStartMatchingFactor(Base):
    """Cold-start matching factor entity.
    
    Represents configurable weighting factors used in the cold-start profile
    matching algorithm (simplified matching for new users with limited data).
    
    Attributes:
        factor_id: Unique identifier
        factor_name: Factor category name (e.g., 'INTENT', 'INTEREST')
        weight: Numeric weight value (0.00 to 1.00)
    """
    __tablename__ = "cold_start_matching_factor"

    factor_id = Column(Integer, primary_key=True, autoincrement=True)
    factor_name = Column(String(50), unique=True, nullable=False)
    weight = Column(Numeric(3, 2), nullable=False)
