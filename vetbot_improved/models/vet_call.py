"""
Модель вызова ветеринара
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from vetbot_improved.database.base import Base

class VetCall(Base):
    """Модель заявки на вызов ветеринара"""
    __tablename__ = "vet_calls"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    pet_type = Column(String, nullable=True)
    pet_name = Column(String, nullable=True)
    pet_age = Column(String, nullable=True)
    problem = Column(Text, nullable=True)
    urgency = Column(String, nullable=True)
    preferred_time = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship("User", back_populates="vet_calls")

    def __repr__(self):
        return f"<VetCall {self.id}: {self.name} - {self.status}>"