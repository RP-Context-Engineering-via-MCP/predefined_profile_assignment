# app/models/intent.py

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Intent(Base):
    __tablename__ = "intent"

    intent_id = Column(Integer, primary_key=True)
    intent_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
