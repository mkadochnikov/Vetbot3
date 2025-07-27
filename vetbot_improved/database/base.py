"""
Базовая конфигурация базы данных
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from vetbot_improved.config import DATABASE_URL

# Создание движка SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()

def get_db():
    """
    Функция-генератор для получения сессии базы данных
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()