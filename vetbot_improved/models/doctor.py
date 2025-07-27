"""
Модель врача
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from vetbot_improved.database.base import Base

class Doctor(Base):
    """Модель врача в системе"""
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    photo_path = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Отношения
    active_consultations = relationship("ActiveConsultation", back_populates="doctor")
    notifications = relationship("DoctorNotification", back_populates="doctor")

    def __repr__(self):
        return f"<Doctor {self.id}: {self.full_name}>"