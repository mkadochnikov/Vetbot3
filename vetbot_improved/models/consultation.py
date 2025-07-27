"""
Модели для консультаций
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from vetbot_improved.database.base import Base

class Consultation(Base):
    """Модель консультации"""
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    question = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_response = Column(Text, nullable=True)
    admin_username = Column(String, nullable=True)
    consultation_status = Column(String, default="ai")  # ai, waiting_doctor, with_doctor, completed
    assigned_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)

    # Отношения
    user = relationship("User", back_populates="consultations")
    active_consultation = relationship("ActiveConsultation", back_populates="consultation", uselist=False)

    def __repr__(self):
        return f"<Consultation {self.id}: {self.consultation_status}>"


class ActiveConsultation(Base):
    """Модель активной консультации"""
    __tablename__ = "active_consultations"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="waiting")  # waiting, assigned, active, completed
    client_username = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    initial_message = Column(Text, nullable=True)

    # Отношения
    client = relationship("User", back_populates="active_consultations")
    doctor = relationship("Doctor", back_populates="active_consultations")
    consultation = relationship("Consultation", back_populates="active_consultation")
    messages = relationship("ConsultationMessage", back_populates="consultation")
    notifications = relationship("DoctorNotification", back_populates="consultation")

    def __repr__(self):
        return f"<ActiveConsultation {self.id}: {self.status}>"


class ConsultationMessage(Base):
    """Модель сообщения в консультации"""
    __tablename__ = "consultation_messages"

    id = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("active_consultations.id"), nullable=False)
    sender_type = Column(String, nullable=False)  # client, doctor, admin, ai
    sender_id = Column(Integer, nullable=True)
    sender_name = Column(String, nullable=True)
    message_text = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    telegram_message_id = Column(Integer, nullable=True)

    # Отношения
    consultation = relationship("ActiveConsultation", back_populates="messages")

    def __repr__(self):
        return f"<ConsultationMessage {self.id}: {self.sender_type}>"


class DoctorNotification(Base):
    """Модель уведомления врача"""
    __tablename__ = "doctor_notifications"

    id = Column(Integer, primary_key=True)
    consultation_id = Column(Integer, ForeignKey("active_consultations.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    message_id = Column(Integer, nullable=True)
    is_responded = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    consultation = relationship("ActiveConsultation", back_populates="notifications")
    doctor = relationship("Doctor", back_populates="notifications")

    def __repr__(self):
        return f"<DoctorNotification {self.id}: responded={self.is_responded}>"