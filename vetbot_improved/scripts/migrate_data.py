"""
Скрипт для миграции данных из старой базы данных в новую
"""

import os
import logging
import sqlite3
from datetime import datetime
from sqlalchemy.orm import Session

from vetbot_improved.database.base import engine, Base, get_db
from vetbot_improved.models import (
    User, Doctor, Consultation, ActiveConsultation,
    ConsultationMessage, DoctorNotification, VetCall,
    AdminSession, AdminMessage, AdminMessageQueue
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Путь к старой базе данных
OLD_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'vetbot.db')

def init_new_database():
    """Инициализация новой базы данных"""
    logger.info("Инициализация новой базы данных...")
    Base.metadata.create_all(bind=engine)
    logger.info("Новая база данных инициализирована")

def migrate_users(old_conn, new_session):
    """Миграция пользователей"""
    logger.info("Миграция пользователей...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    for user in users:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        user_dict = dict(zip(columns, user))
        
        # Создаем нового пользователя в новой базе
        new_user = User(
            user_id=user_dict['user_id'],
            username=user_dict['username'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'],
            phone=user_dict['phone'],
            created_at=datetime.fromisoformat(user_dict['created_at']) if user_dict['created_at'] else datetime.utcnow()
        )
        
        new_session.add(new_user)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(users)} пользователей")

def migrate_doctors(old_conn, new_session):
    """Миграция врачей"""
    logger.info("Миграция врачей...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    
    for doctor in doctors:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        doctor_dict = dict(zip(columns, doctor))
        
        # Создаем нового врача в новой базе
        new_doctor = Doctor(
            id=doctor_dict['id'],
            telegram_id=doctor_dict['telegram_id'],
            username=doctor_dict['username'],
            full_name=doctor_dict['full_name'],
            photo_path=doctor_dict['photo_path'],
            is_approved=bool(doctor_dict['is_approved']),
            is_active=bool(doctor_dict['is_active']),
            registered_at=datetime.fromisoformat(doctor_dict['registered_at']) if doctor_dict['registered_at'] else datetime.utcnow(),
            last_activity=datetime.fromisoformat(doctor_dict['last_activity']) if doctor_dict['last_activity'] else datetime.utcnow()
        )
        
        new_session.add(new_doctor)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(doctors)} врачей")

def migrate_consultations(old_conn, new_session):
    """Миграция консультаций"""
    logger.info("Миграция консультаций...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM consultations")
    consultations = cursor.fetchall()
    
    for consultation in consultations:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        consultation_dict = dict(zip(columns, consultation))
        
        # Создаем новую консультацию в новой базе
        new_consultation = Consultation(
            id=consultation_dict['id'],
            user_id=consultation_dict['user_id'],
            question=consultation_dict['question'],
            response=consultation_dict['response'],
            created_at=datetime.fromisoformat(consultation_dict['created_at']) if consultation_dict['created_at'] else datetime.utcnow(),
            admin_response=consultation_dict['admin_response'],
            admin_username=consultation_dict['admin_username'],
            consultation_status=consultation_dict['consultation_status'],
            assigned_doctor_id=consultation_dict['assigned_doctor_id']
        )
        
        new_session.add(new_consultation)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(consultations)} консультаций")

def migrate_active_consultations(old_conn, new_session):
    """Миграция активных консультаций"""
    logger.info("Миграция активных консультаций...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM active_consultations")
    active_consultations = cursor.fetchall()
    
    for consultation in active_consultations:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        consultation_dict = dict(zip(columns, consultation))
        
        # Создаем новую активную консультацию в новой базе
        new_consultation = ActiveConsultation(
            id=consultation_dict['id'],
            client_id=consultation_dict['client_id'],
            doctor_id=consultation_dict['doctor_id'],
            consultation_id=consultation_dict['consultation_id'],
            started_at=datetime.fromisoformat(consultation_dict['started_at']) if consultation_dict['started_at'] else datetime.utcnow(),
            status=consultation_dict['status'],
            client_username=consultation_dict['client_username'],
            client_name=consultation_dict['client_name'],
            initial_message=consultation_dict['initial_message']
        )
        
        new_session.add(new_consultation)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(active_consultations)} активных консультаций")

def migrate_consultation_messages(old_conn, new_session):
    """Миграция сообщений консультаций"""
    logger.info("Миграция сообщений консультаций...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM consultation_messages")
    messages = cursor.fetchall()
    
    for message in messages:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        message_dict = dict(zip(columns, message))
        
        # Создаем новое сообщение в новой базе
        new_message = ConsultationMessage(
            id=message_dict['id'],
            consultation_id=message_dict['consultation_id'],
            sender_type=message_dict['sender_type'],
            sender_id=message_dict['sender_id'],
            sender_name=message_dict['sender_name'],
            message_text=message_dict['message_text'],
            sent_at=datetime.fromisoformat(message_dict['sent_at']) if message_dict['sent_at'] else datetime.utcnow(),
            telegram_message_id=message_dict['telegram_message_id']
        )
        
        new_session.add(new_message)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(messages)} сообщений консультаций")

def migrate_doctor_notifications(old_conn, new_session):
    """Миграция уведомлений врачей"""
    logger.info("Миграция уведомлений врачей...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM doctor_notifications")
    notifications = cursor.fetchall()
    
    for notification in notifications:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        notification_dict = dict(zip(columns, notification))
        
        # Создаем новое уведомление в новой базе
        new_notification = DoctorNotification(
            id=notification_dict['id'],
            consultation_id=notification_dict['consultation_id'],
            doctor_id=notification_dict['doctor_id'],
            message_id=notification_dict['message_id'],
            is_responded=bool(notification_dict['is_responded']),
            sent_at=datetime.fromisoformat(notification_dict['sent_at']) if notification_dict['sent_at'] else datetime.utcnow()
        )
        
        new_session.add(new_notification)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(notifications)} уведомлений врачей")

def migrate_vet_calls(old_conn, new_session):
    """Миграция заявок на вызов врача"""
    logger.info("Миграция заявок на вызов врача...")
    
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM vet_calls")
    calls = cursor.fetchall()
    
    for call in calls:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        call_dict = dict(zip(columns, call))
        
        # Создаем новую заявку в новой базе
        new_call = VetCall(
            id=call_dict['id'],
            user_id=call_dict['user_id'],
            name=call_dict['name'],
            phone=call_dict['phone'],
            address=call_dict['address'],
            pet_type=call_dict['pet_type'],
            pet_name=call_dict['pet_name'],
            pet_age=call_dict['pet_age'],
            problem=call_dict['problem'],
            urgency=call_dict['urgency'],
            preferred_time=call_dict['preferred_time'],
            comments=call_dict['comments'],
            status=call_dict['status'],
            created_at=datetime.fromisoformat(call_dict['created_at']) if call_dict['created_at'] else datetime.utcnow()
        )
        
        new_session.add(new_call)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(calls)} заявок на вызов врача")

def migrate_admin_data(old_conn, new_session):
    """Миграция данных администраторов"""
    logger.info("Миграция данных администраторов...")
    
    # Миграция сессий администраторов
    cursor = old_conn.cursor()
    cursor.execute("SELECT * FROM admin_sessions")
    sessions = cursor.fetchall()
    
    for session in sessions:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        session_dict = dict(zip(columns, session))
        
        # Создаем новую сессию в новой базе
        new_session_obj = AdminSession(
            id=session_dict['id'],
            user_id=session_dict['user_id'],
            admin_username=session_dict['admin_username'],
            started_at=datetime.fromisoformat(session_dict['started_at']) if session_dict['started_at'] else datetime.utcnow(),
            ended_at=datetime.fromisoformat(session_dict['ended_at']) if session_dict['ended_at'] else None,
            is_active=bool(session_dict['is_active'])
        )
        
        new_session.add(new_session_obj)
    
    # Миграция сообщений администраторов
    cursor.execute("SELECT * FROM admin_messages")
    messages = cursor.fetchall()
    
    for message in messages:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        message_dict = dict(zip(columns, message))
        
        # Создаем новое сообщение в новой базе
        new_message = AdminMessage(
            id=message_dict['id'],
            user_id=message_dict['user_id'],
            admin_username=message_dict['admin_username'],
            message=message_dict['message'],
            sent_at=datetime.fromisoformat(message_dict['sent_at']) if message_dict['sent_at'] else datetime.utcnow(),
            telegram_message_id=message_dict['telegram_message_id']
        )
        
        new_session.add(new_message)
    
    # Миграция очереди сообщений администраторов
    cursor.execute("SELECT * FROM admin_message_queue")
    queue_messages = cursor.fetchall()
    
    for message in queue_messages:
        # Получаем имена столбцов
        columns = [column[0] for column in cursor.description]
        message_dict = dict(zip(columns, message))
        
        # Создаем новое сообщение в очереди в новой базе
        new_queue_message = AdminMessageQueue(
            id=message_dict['id'],
            user_id=message_dict['user_id'],
            message=message_dict['message'],
            created_at=datetime.fromisoformat(message_dict['created_at']) if message_dict['created_at'] else datetime.utcnow(),
            sent=bool(message_dict['sent'])
        )
        
        new_session.add(new_queue_message)
    
    new_session.commit()
    logger.info(f"Мигрировано {len(sessions)} сессий администраторов, {len(messages)} сообщений и {len(queue_messages)} сообщений в очереди")

def migrate_all_data():
    """Миграция всех данных из старой базы в новую"""
    logger.info(f"Начало миграции данных из {OLD_DB_PATH}")
    
    # Проверка существования старой базы данных
    if not os.path.exists(OLD_DB_PATH):
        logger.error(f"Старая база данных не найдена: {OLD_DB_PATH}")
        return False
    
    try:
        # Инициализация новой базы данных
        init_new_database()
        
        # Подключение к старой базе данных
        old_conn = sqlite3.connect(OLD_DB_PATH)
        
        # Получение сессии новой базы данных
        db = next(get_db())
        
        try:
            # Миграция данных
            migrate_users(old_conn, db)
            migrate_doctors(old_conn, db)
            migrate_consultations(old_conn, db)
            migrate_active_consultations(old_conn, db)
            migrate_consultation_messages(old_conn, db)
            migrate_doctor_notifications(old_conn, db)
            migrate_vet_calls(old_conn, db)
            migrate_admin_data(old_conn, db)
            
            logger.info("Миграция данных успешно завершена")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при миграции данных: {e}")
            db.rollback()
            return False
        finally:
            db.close()
            old_conn.close()
            
    except Exception as e:
        logger.error(f"Ошибка при миграции данных: {e}")
        return False

if __name__ == "__main__":
    migrate_all_data()