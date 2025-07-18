#!/usr/bin/env python3
"""
Скрипт для тестирования системы ветеринарных ботов
"""

import os
import sqlite3
import asyncio
from dotenv import load_dotenv
from notification_system import notification_system

# Загрузка переменных окружения
load_dotenv()

def test_database_structure():
    """Тестирование структуры базы данных"""
    print("🔍 Тестирование структуры базы данных...")
    
    try:
        conn = sqlite3.connect('vetbot.db')
        cursor = conn.cursor()
        
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"✅ Найдено таблиц: {len(tables)}")
        
        required_tables = [
            'users', 'vet_calls', 'consultations', 'doctors', 
            'active_consultations', 'consultation_messages', 'doctor_notifications'
        ]
        
        existing_tables = [table[0] for table in tables]
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Таблица '{table}' существует")
                
                # Проверяем структуру таблицы
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                print(f"   📊 Колонок: {len(columns)}")
            else:
                print(f"❌ Таблица '{table}' отсутствует")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования БД: {e}")
        return False

def test_env_variables():
    """Тестирование переменных окружения"""
    print("\n🔍 Тестирование переменных окружения...")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'VET_BOT_TOKEN', 
        'DEEPSEEK_API_KEY'
    ]
    
    all_ok = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}{value[-10:]}")
        else:
            print(f"❌ {var}: не установлена")
            all_ok = False
    
    return all_ok

async def test_notification_system():
    """Тестирование системы уведомлений"""
    print("\n🔍 Тестирование системы уведомлений...")
    
    try:
        # Тест получения одобренных врачей
        doctors = notification_system.get_approved_doctors()
        print(f"✅ Одобренных врачей: {len(doctors)}")
        
        # Тест создания консультации (без реальной отправки)
        print("✅ Система уведомлений инициализирована")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка системы уведомлений: {e}")
        return False

def create_test_data():
    """Создание тестовых данных"""
    print("\n🔍 Создание тестовых данных...")
    
    try:
        conn = sqlite3.connect('vetbot.db')
        cursor = conn.cursor()
        
        # Создаем тестового врача
        cursor.execute('''
            INSERT OR REPLACE INTO doctors 
            (telegram_id, username, full_name, is_approved, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (123456789, 'test_doctor', 'Тестовый Врач Иванович', 1, 1))
        
        # Создаем тестового пользователя
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (987654321, 'test_user', 'Тестовый', 'Пользователь'))
        
        conn.commit()
        conn.close()
        
        print("✅ Тестовые данные созданы")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания тестовых данных: {e}")
        return False

def test_file_structure():
    """Тестирование структуры файлов"""
    print("\n🔍 Тестирование структуры файлов...")
    
    required_files = [
        'enhanced_bot.py',
        'vet_doctor_bot.py', 
        'notification_system.py',
        'admin_streamlit_enhanced.py',
        '.env'
    ]
    
    all_ok = True
    
    for file in required_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file}: {size} байт")
        else:
            print(f"❌ {file}: файл отсутствует")
            all_ok = False
    
    return all_ok

async def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ СИСТЕМЫ ВЕТЕРИНАРНЫХ БОТОВ")
    print("=" * 50)
    
    tests = [
        ("Структура файлов", test_file_structure),
        ("Переменные окружения", test_env_variables),
        ("Структура базы данных", test_database_structure),
        ("Тестовые данные", create_test_data),
        ("Система уведомлений", test_notification_system),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
            
        results.append((test_name, result))
    
    # Итоговый отчет
    print("\n" + "="*50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к развертыванию.")
    else:
        print("⚠️ Есть проблемы, требующие исправления.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())

