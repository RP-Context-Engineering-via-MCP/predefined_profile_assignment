"""Trait domain model.

Defines user personality or behavioral traits for advanced profiling.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Trait(Base):
    """User personality or behavioral trait entity.
    
    Represents personality characteristics or behavioral traits used for
    advanced user profiling and segmentation.
    
    Attributes:
        trait_id: Unique identifier
        trait_name: Trait category name
        description: Detailed description of the trait
    """
    __tablename__ = "trait"

    trait_id = Column(Integer, primary_key=True)
    trait_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
