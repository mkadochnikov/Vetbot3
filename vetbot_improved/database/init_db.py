"""
Инициализация базы данных
"""

import logging
from sqlalchemy.exc import SQLAlchemyError

from vetbot_improved.database.base import Base, engine
from vetbot_improved.models import (
    User, Doctor, Consultation, ActiveConsultation,
    ConsultationMessage, DoctorNotification, VetCall,
    AdminSession, AdminMessage, AdminMessageQueue
)

logger = logging.getLogger(__name__)

def init_database():
    """
    Инициализация базы данных - создание всех таблиц
    """
    try:
        logger.info("Создание таблиц базы данных...")
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы базы данных успешно созданы")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при создании таблиц базы данных: {e}")
        return False

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Инициализация базы данных
    init_database()