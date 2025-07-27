"""
Тесты для моделей данных
"""

import pytest
from datetime import datetime

from vetbot_improved.models import (
    User, Doctor, Consultation, ActiveConsultation,
    ConsultationMessage, DoctorNotification, VetCall
)

def test_user_model(db_session, test_user):
    """Тест модели пользователя"""
    # Проверка создания пользователя
    assert test_user.user_id == 123456789
    assert test_user.username == "test_user"
    assert test_user.first_name == "Test"
    assert test_user.last_name == "User"
    
    # Проверка получения пользователя из базы
    user_from_db = db_session.query(User).filter(User.user_id == 123456789).first()
    assert user_from_db is not None
    assert user_from_db.username == "test_user"
    
    # Проверка обновления пользователя
    user_from_db.phone = "+1234567890"
    db_session.commit()
    
    updated_user = db_session.query(User).filter(User.user_id == 123456789).first()
    assert updated_user.phone == "+1234567890"

def test_doctor_model(db_session, test_doctor):
    """Тест модели врача"""
    # Проверка создания врача
    assert test_doctor.telegram_id == 987654321
    assert test_doctor.username == "test_doctor"
    assert test_doctor.full_name == "Test Doctor"
    assert test_doctor.is_approved is True
    assert test_doctor.is_active is True
    
    # Проверка получения врача из базы
    doctor_from_db = db_session.query(Doctor).filter(Doctor.telegram_id == 987654321).first()
    assert doctor_from_db is not None
    assert doctor_from_db.full_name == "Test Doctor"
    
    # Проверка обновления врача
    doctor_from_db.is_active = False
    db_session.commit()
    
    updated_doctor = db_session.query(Doctor).filter(Doctor.telegram_id == 987654321).first()
    assert updated_doctor.is_active is False

def test_consultation_model(db_session, test_user):
    """Тест модели консультации"""
    # Создание консультации
    consultation = Consultation(
        user_id=test_user.user_id,
        question="Тестовый вопрос",
        response="Тестовый ответ",
        consultation_status="ai"
    )
    db_session.add(consultation)
    db_session.commit()
    
    # Проверка создания консультации
    assert consultation.id is not None
    assert consultation.user_id == test_user.user_id
    assert consultation.question == "Тестовый вопрос"
    assert consultation.response == "Тестовый ответ"
    assert consultation.consultation_status == "ai"
    
    # Проверка получения консультации из базы
    consultation_from_db = db_session.query(Consultation).filter(Consultation.id == consultation.id).first()
    assert consultation_from_db is not None
    assert consultation_from_db.question == "Тестовый вопрос"
    
    # Проверка обновления консультации
    consultation_from_db.consultation_status = "waiting_doctor"
    db_session.commit()
    
    updated_consultation = db_session.query(Consultation).filter(Consultation.id == consultation.id).first()
    assert updated_consultation.consultation_status == "waiting_doctor"

def test_active_consultation_model(db_session, test_user, test_doctor):
    """Тест модели активной консультации"""
    # Создание консультации
    consultation = Consultation(
        user_id=test_user.user_id,
        question="Тестовый вопрос",
        response="Тестовый ответ",
        consultation_status="waiting_doctor"
    )
    db_session.add(consultation)
    db_session.commit()
    
    # Создание активной консультации
    active_consultation = ActiveConsultation(
        client_id=test_user.user_id,
        doctor_id=test_doctor.id,
        consultation_id=consultation.id,
        status="assigned",
        client_username=test_user.username,
        client_name=test_user.first_name,
        initial_message="Тестовый вопрос"
    )
    db_session.add(active_consultation)
    db_session.commit()
    
    # Проверка создания активной консультации
    assert active_consultation.id is not None
    assert active_consultation.client_id == test_user.user_id
    assert active_consultation.doctor_id == test_doctor.id
    assert active_consultation.consultation_id == consultation.id
    assert active_consultation.status == "assigned"
    
    # Проверка получения активной консультации из базы
    active_consultation_from_db = db_session.query(ActiveConsultation).filter(
        ActiveConsultation.id == active_consultation.id
    ).first()
    assert active_consultation_from_db is not None
    assert active_consultation_from_db.client_username == test_user.username
    
    # Проверка обновления активной консультации
    active_consultation_from_db.status = "active"
    db_session.commit()
    
    updated_active_consultation = db_session.query(ActiveConsultation).filter(
        ActiveConsultation.id == active_consultation.id
    ).first()
    assert updated_active_consultation.status == "active"

def test_vet_call_model(db_session, test_user):
    """Тест модели вызова ветеринара"""
    # Создание вызова ветеринара
    vet_call = VetCall(
        user_id=test_user.user_id,
        name="Test User",
        phone="+1234567890",
        address="Test Address",
        pet_type="cat",
        pet_name="Murzik",
        pet_age="2",
        problem="Test Problem",
        urgency="medium",
        preferred_time="evening",
        comments="Test Comments",
        status="pending"
    )
    db_session.add(vet_call)
    db_session.commit()
    
    # Проверка создания вызова ветеринара
    assert vet_call.id is not None
    assert vet_call.user_id == test_user.user_id
    assert vet_call.name == "Test User"
    assert vet_call.phone == "+1234567890"
    assert vet_call.address == "Test Address"
    assert vet_call.pet_type == "cat"
    assert vet_call.pet_name == "Murzik"
    assert vet_call.status == "pending"
    
    # Проверка получения вызова ветеринара из базы
    vet_call_from_db = db_session.query(VetCall).filter(VetCall.id == vet_call.id).first()
    assert vet_call_from_db is not None
    assert vet_call_from_db.pet_name == "Murzik"
    
    # Проверка обновления вызова ветеринара
    vet_call_from_db.status = "approved"
    db_session.commit()
    
    updated_vet_call = db_session.query(VetCall).filter(VetCall.id == vet_call.id).first()
    assert updated_vet_call.status == "approved"