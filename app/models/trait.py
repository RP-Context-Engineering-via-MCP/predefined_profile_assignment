# app/models/trait.py

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Trait(Base):
    __tablename__ = "trait"

    trait_id = Column(Integer, primary_key=True)
    trait_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
