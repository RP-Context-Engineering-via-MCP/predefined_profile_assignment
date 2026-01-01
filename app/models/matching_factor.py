# app/models/matching_factor.py

from sqlalchemy import Column, Integer, String, Numeric
from app.core.database import Base


class MatchingFactor(Base):
    __tablename__ = "matching_factor"

    factor_id = Column(Integer, primary_key=True)
    factor_name = Column(String(50), unique=True, nullable=False)
    weight = Column(Numeric(3, 2), nullable=False)
