"""
Тест DeepSeek API для проверки подключения
"""

import requests
import json

def test_deepseek_api():
    """Тестирует подключение к DeepSeek API"""
    
    api_key = "sk-6c32104420624e3483ef173804d8abde"
    base_url = "https://api.deepseek.com/v1"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Тестовый запрос
    data = {
        'model': 'deepseek-chat',
        'messages': [
            {
                'role': 'user', 
                'content': 'Привет! Ты работаешь?'
            }
        ],
        'temperature': 0.7,
        'max_tokens': 100
    }
    
    print("🔍 Тестирование DeepSeek API...")
    print(f"URL: {base_url}/chat/completions")
    print(f"Model: {data['model']}")
    
    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ DeepSeek API работает!")
            print(f"Ответ: {result['choices'][0]['message']['content']}")
            print(f"Использовано токенов: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_veterinary_prompt():
    """Тестирует ветеринарный промпт"""
    
    api_key = "sk-6c32104420624e3483ef173804d8abde"
    base_url = "https://api.deepseek.com/v1"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Ветеринарный системный промпт
    system_prompt = """Ты опытный ветеринарный врач с 15-летним стажем. 
Специализируешься на лечении кошек. Общаешься как настоящий врач - уверенно, 
профессионально, ставишь диагнозы и назначаешь лечение. 

Отвечай кратко и по делу. Давай конкретные рекомендации по лечению.
Используй медицинскую терминологию, но объясняй понятно."""
    
    # Тестовый случай
    user_message = "У кошки 3 года понос уже 2 дня, стала вялой, плохо ест"
    
    data = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'Пациент: кошка. Жалобы: {user_message}'}
        ],
        'temperature': 0.8,
        'max_tokens': 500
    }
    
    print("\n🐱 Тестирование ветеринарного промпта...")
    print(f"Запрос: {user_message}")
    
    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            vet_response = result['choices'][0]['message']['content']
            print("✅ Ветеринарный ответ получен!")
            print(f"Ответ врача:\n{vet_response}")
            print(f"\nИспользовано токенов: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование DeepSeek API для ветеринарного бота\n")
    
    # Тест 1: Базовое подключение
    basic_test = test_deepseek_api()
    
    # Тест 2: Ветеринарный промпт
    if basic_test:
        vet_test = test_veterinary_prompt()
        
        if vet_test:
            print("\n🎉 Все тесты пройдены! DeepSeek API готов для использования в боте.")
        else:
            print("\n⚠️ Базовое подключение работает, но есть проблемы с ветеринарным промптом.")
    else:
        print("\n❌ Базовое подключение не работает. Проверьте API ключ и интернет.")

