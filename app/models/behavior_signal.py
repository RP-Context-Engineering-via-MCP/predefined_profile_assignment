# app/models/behavior_signal.py

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class BehaviorSignal(Base):
    __tablename__ = "behavior_signal"

    signal_id = Column(Integer, primary_key=True)
    signal_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
