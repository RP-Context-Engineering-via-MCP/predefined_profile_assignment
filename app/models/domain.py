# app/models/domain.py

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Domain(Base):
    __tablename__ = "domain"

    domain_id = Column(Integer, primary_key=True)
    domain_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
