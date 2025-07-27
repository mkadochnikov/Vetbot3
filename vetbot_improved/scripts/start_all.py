"""
Скрипт для запуска всех компонентов системы
"""

import os
import sys
import time
import logging
import subprocess
import signal
import argparse
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vetbot_improved.config import BASE_DIR

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'system.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Пути к скриптам
MAIN_BOT_SCRIPT = os.path.join(BASE_DIR, 'bot', 'main_bot.py')
DOCTOR_BOT_SCRIPT = os.path.join(BASE_DIR, 'bot', 'doctor_bot.py')
WEBAPP_SCRIPT = os.path.join(BASE_DIR, 'web', 'webapp_server.py')
ADMIN_SCRIPT = os.path.join(BASE_DIR, 'web', 'admin_panel.py')

# Директории для логов и PID файлов
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
PIDS_DIR = os.path.join(BASE_DIR, 'pids')

# Создаем директории, если они не существуют
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(PIDS_DIR, exist_ok=True)

def start_process(script_path, log_file, pid_file):
    """
    Запуск процесса
    
    Args:
        script_path: Путь к скрипту
        log_file: Путь к файлу логов
        pid_file: Путь к PID файлу
        
    Returns:
        subprocess.Popen: Запущенный процесс
    """
    logger.info(f"Запуск {os.path.basename(script_path)}...")
    
    with open(log_file, 'a') as log:
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=log,
            stderr=log,
            start_new_session=True
        )
    
    # Сохраняем PID
    with open(pid_file, 'w') as f:
        f.write(str(process.pid))
    
    logger.info(f"{os.path.basename(script_path)} запущен (PID: {process.pid})")
    return process

def stop_process(pid_file):
    """
    Остановка процесса
    
    Args:
        pid_file: Путь к PID файлу
        
    Returns:
        bool: Успешность остановки
    """
    if not os.path.exists(pid_file):
        logger.warning(f"PID файл не найден: {pid_file}")
        return False
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        logger.info(f"Остановка процесса с PID {pid}...")
        
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            
            # Проверяем, остановился ли процесс
            if is_process_running(pid):
                logger.warning(f"Процесс с PID {pid} не остановился, отправляем SIGKILL...")
                os.kill(pid, signal.SIGKILL)
                time.sleep(1)
        except ProcessLookupError:
            logger.info(f"Процесс с PID {pid} уже не существует")
        
        # Удаляем PID файл
        os.remove(pid_file)
        logger.info(f"Процесс с PID {pid} остановлен")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при остановке процесса: {e}")
        return False

def is_process_running(pid):
    """
    Проверка, запущен ли процесс
    
    Args:
        pid: PID процесса
        
    Returns:
        bool: Запущен ли процесс
    """
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except Exception:
        return False

def start_all():
    """Запуск всех компонентов системы"""
    logger.info("Запуск всех компонентов системы...")
    
    # Запуск основного бота
    main_bot_log = os.path.join(LOGS_DIR, 'main_bot.log')
    main_bot_pid = os.path.join(PIDS_DIR, 'main_bot.pid')
    main_bot_process = start_process(MAIN_BOT_SCRIPT, main_bot_log, main_bot_pid)
    
    time.sleep(3)
    
    # Запуск бота врачей
    doctor_bot_log = os.path.join(LOGS_DIR, 'doctor_bot.log')
    doctor_bot_pid = os.path.join(PIDS_DIR, 'doctor_bot.pid')
    doctor_bot_process = start_process(DOCTOR_BOT_SCRIPT, doctor_bot_log, doctor_bot_pid)
    
    time.sleep(3)
    
    # Запуск веб-приложения
    webapp_log = os.path.join(LOGS_DIR, 'webapp.log')
    webapp_pid = os.path.join(PIDS_DIR, 'webapp.pid')
    webapp_process = start_process(WEBAPP_SCRIPT, webapp_log, webapp_pid)
    
    time.sleep(3)
    
    # Запуск админ-панели
    admin_log = os.path.join(LOGS_DIR, 'admin_panel.log')
    admin_pid = os.path.join(PIDS_DIR, 'admin_panel.pid')
    admin_process = start_process(ADMIN_SCRIPT, admin_log, admin_pid)
    
    logger.info("Все компоненты системы запущены")
    
    # Проверка статуса
    time.sleep(5)
    check_status()

def stop_all():
    """Остановка всех компонентов системы"""
    logger.info("Остановка всех компонентов системы...")
    
    # Остановка админ-панели
    admin_pid = os.path.join(PIDS_DIR, 'admin_panel.pid')
    stop_process(admin_pid)
    
    # Остановка веб-приложения
    webapp_pid = os.path.join(PIDS_DIR, 'webapp.pid')
    stop_process(webapp_pid)
    
    # Остановка бота врачей
    doctor_bot_pid = os.path.join(PIDS_DIR, 'doctor_bot.pid')
    stop_process(doctor_bot_pid)
    
    # Остановка основного бота
    main_bot_pid = os.path.join(PIDS_DIR, 'main_bot.pid')
    stop_process(main_bot_pid)
    
    logger.info("Все компоненты системы остановлены")

def restart_all():
    """Перезапуск всех компонентов системы"""
    logger.info("Перезапуск всех компонентов системы...")
    stop_all()
    time.sleep(5)
    start_all()
    logger.info("Все компоненты системы перезапущены")

def check_status():
    """Проверка статуса всех компонентов системы"""
    logger.info("Проверка статуса компонентов системы...")
    
    components = [
        ('Основной бот', os.path.join(PIDS_DIR, 'main_bot.pid')),
        ('Бот врачей', os.path.join(PIDS_DIR, 'doctor_bot.pid')),
        ('Веб-приложение', os.path.join(PIDS_DIR, 'webapp.pid')),
        ('Админ-панель', os.path.join(PIDS_DIR, 'admin_panel.pid'))
    ]
    
    all_running = True
    
    for name, pid_file in components:
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                if is_process_running(pid):
                    logger.info(f"✅ {name} работает (PID: {pid})")
                else:
                    logger.warning(f"❌ {name} не работает (PID: {pid})")
                    all_running = False
            except Exception as e:
                logger.error(f"Ошибка при проверке статуса {name}: {e}")
                all_running = False
        else:
            logger.warning(f"❌ {name} не запущен (PID файл не найден)")
            all_running = False
    
    if all_running:
        logger.info("✅ Все компоненты системы работают")
    else:
        logger.warning("⚠️ Не все компоненты системы работают")
    
    return all_running

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Управление системой ветеринарных ботов')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'], help='Действие')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_all()
    elif args.action == 'stop':
        stop_all()
    elif args.action == 'restart':
        restart_all()
    elif args.action == 'status':
        check_status()

if __name__ == "__main__":
    main()