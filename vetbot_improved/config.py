"""
Конфигурация проекта Vetbot
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Создание необходимых директорий
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Версия приложения
VERSION = "3.0.0"

# Конфигурация Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
VET_BOT_TOKEN = os.getenv("VET_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

# Конфигурация DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Конфигурация базы данных
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/vetbot.db")

# Конфигурация веб-приложения
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:5000")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "5000"))

# Конфигурация админ-панели
ADMIN_PORT = int(os.getenv("ADMIN_PORT", "8501"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# Конфигурация сервиса
VET_SERVICE_PHONE = os.getenv("VET_SERVICE_PHONE", "+7-999-123-45-67")

# Режим отладки
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")