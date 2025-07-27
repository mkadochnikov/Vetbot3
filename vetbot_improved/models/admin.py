"""
Модели для администрирования
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from vetbot_improved.database.base import Base

class AdminSession(Base):
    """Модель сессии администратора"""
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    admin_username = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<AdminSession {self.id}: {self.admin_username}>"


class AdminMessage(Base):
    """Модель сообщения от администратора"""
    __tablename__ = "admin_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    admin_username = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    telegram_message_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<AdminMessage {self.id}: {self.admin_username}>"


class AdminMessageQueue(Base):
    """Модель очереди сообщений от администраторов"""
    __tablename__ = "admin_message_queue"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent = Column(Boolean, default=False)

    def __repr__(self):
        return f"<AdminMessageQueue {self.id}: sent={self.sent}>"