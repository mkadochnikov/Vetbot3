"""
Модель пользователя
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from vetbot_improved.database.base import Base

class User(Base):
    """Модель пользователя системы"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    vet_calls = relationship("VetCall", back_populates="user")
    consultations = relationship("Consultation", back_populates="user")
    active_consultations = relationship("ActiveConsultation", back_populates="client")

    def __repr__(self):
        return f"<User {self.user_id}: {self.username or self.first_name}>"