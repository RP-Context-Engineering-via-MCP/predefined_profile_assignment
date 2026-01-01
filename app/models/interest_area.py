# app/models/interest_area.py

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class InterestArea(Base):
    __tablename__ = "interest_area"

    interest_id = Column(Integer, primary_key=True)
    interest_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
