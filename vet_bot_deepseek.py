"""
Тестирование ветеринарного бота с DeepSeek API
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('.env.deepseek')

# Импортируем компоненты бота
try:
    from vet_bot_deepseek import DeepSeekAPI, VeterinarySystem
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

def test_deepseek_connection():
    """Тестирует подключение к DeepSeek API"""
    print("🔍 Тестирование подключения к DeepSeek API...")
    
    try:
        deepseek = DeepSeekAPI()
        
        # Простой тестовый запрос
        test_messages = [
            {"role": "user", "content": "Привет! Ответь кратко: ты работаешь?"}
        ]
        
        response = deepseek.chat_completion(test_messages)
        
        if response and "баланс" not in response.lower() and "ошибка" not in response.lower():
            print("✅ DeepSeek API работает!")
            print(f"Ответ: {response}")
            return True
        else:
            print(f"⚠️ Проблема с API: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_veterinary_consultation():
    """Тестирует ветеринарную консультацию"""
    print("\n🐱 Тестирование ветеринарной консультации...")
    
    try:
        deepseek = DeepSeekAPI()
        vet_system = VeterinarySystem()
        
        # Тестовые случаи
        test_cases = [
            "Кошка 3 года, понос 2 дня, вялая, плохо ест",
            "Котенок 6 месяцев, кашляет и чихает неделю",
            "Кот 5 лет, хромает на переднюю лапу, мяукает при прикосновении"
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📋 Тест {i}: {case}")
            
            messages = vet_system.create_messages(case)
            response = deepseek.chat_completion(messages)
            
            if response:
                print(f"✅ Ответ получен:")
                print(f"{response[:200]}..." if len(response) > 200 else response)
            else:
                print("❌ Ответ не получен")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def test_error_handling():
    """Тестирует обработку ошибок"""
    print("\n🛠️ Тестирование обработки ошибок...")
    
    try:
        # Тест с неверным API ключом
        os.environ['DEEPSEEK_API_KEY'] = 'invalid_key'
        deepseek = DeepSeekAPI()
        
        response = deepseek.chat_completion([{"role": "user", "content": "test"}])
        
        if "авторизации" in response or "ключ" in response:
            print("✅ Обработка неверного API ключа работает")
            return True
        else:
            print(f"⚠️ Неожиданный ответ: {response}")
            return False
            
    except Exception as e:
        print(f"✅ Исключение обработано корректно: {e}")
        return True

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование ветеринарного бота с DeepSeek API\n")
    
    # Проверяем переменные окружения
    required_vars = ['DEEPSEEK_API_KEY', 'TELEGRAM_BOT_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("Создайте .env файл с необходимыми ключами")
        return False
    
    # Восстанавливаем правильный API ключ
    load_dotenv('.env.deepseek', override=True)
    
    # Запускаем тесты
    tests = [
        ("Подключение к DeepSeek API", test_deepseek_connection),
        ("Ветеринарная консультация", test_veterinary_consultation),
        ("Обработка ошибок", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Результаты
    print("\n📊 Результаты тестирования:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nИтого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("\n🎉 Все тесты пройдены! Бот готов к работе.")
        return True
    else:
        print(f"\n⚠️ {len(results) - passed} тестов провалено. Проверьте конфигурацию.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

