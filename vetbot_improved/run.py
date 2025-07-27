"""
Основной файл для запуска всей системы
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Основная функция для запуска системы"""
    parser = argparse.ArgumentParser(description='Система ветеринарных ботов')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'migrate'], 
                        help='Действие')
    
    args = parser.parse_args()
    
    # Импортируем модули только после парсинга аргументов
    from vetbot_improved.scripts.start_all import start_all, stop_all, restart_all, check_status
    
    if args.action == 'start':
        logger.info("Запуск системы...")
        start_all()
    elif args.action == 'stop':
        logger.info("Остановка системы...")
        stop_all()
    elif args.action == 'restart':
        logger.info("Перезапуск системы...")
        restart_all()
    elif args.action == 'status':
        logger.info("Проверка статуса системы...")
        check_status()
    elif args.action == 'migrate':
        logger.info("Миграция данных...")
        from vetbot_improved.scripts.migrate_data import migrate_all_data
        migrate_all_data()

if __name__ == "__main__":
    main()