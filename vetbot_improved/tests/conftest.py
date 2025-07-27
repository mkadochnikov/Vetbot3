"""
Конфигурация для тестов
"""

import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vetbot_improved.database.base import Base
from vetbot_improved.models import (
    User, Doctor, Consultation, ActiveConsultation,
    ConsultationMessage, DoctorNotification, VetCall,
    AdminSession, AdminMessage, AdminMessageQueue
)

# Создаем тестовую базу данных в памяти
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Создание движка базы данных для тестов"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Создание сессии базы данных для тестов"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Создание тестового пользователя"""
    user = User(
        user_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture(scope="function")
def test_doctor(db_session):
    """Создание тестового врача"""
    doctor = Doctor(
        telegram_id=987654321,
        username="test_doctor",
        full_name="Test Doctor",
        is_approved=True,
        is_active=True
    )
    db_session.add(doctor)
    db_session.commit()
    return doctor