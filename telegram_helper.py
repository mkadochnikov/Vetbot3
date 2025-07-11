"""
Вспомогательный модуль для работы с Telegram API
Используется админ-панелью для отправки сообщений
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramHelper:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    
    def send_message(self, chat_id, text, parse_mode='HTML'):
        """
        Отправить сообщение пользователю
        
        Args:
            chat_id: ID чата/пользователя
            text: Текст сообщения
            parse_mode: Режим парсинга (HTML, Markdown)
        
        Returns:
            dict: Ответ от Telegram API
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return {
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else response.text,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def get_chat_info(self, chat_id):
        """
        Получить информацию о чате/пользователе
        
        Args:
            chat_id: ID чата/пользователя
        
        Returns:
            dict: Информация о чате
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/getChat"
        
        data = {'chat_id': chat_id}
        
        try:
            response = requests.post(url, data=data, timeout=10)
            return {
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else response.text,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
    def test_connection(self):
        """
        Проверить подключение к Telegram API
        
        Returns:
            dict: Результат проверки
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
        
        try:
            response = requests.get(url, timeout=10)
            return {
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else response.text,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'status_code': 0
            }

# Функция для быстрого тестирования
def test_telegram_connection():
    """Быстрый тест подключения к Telegram"""
    try:
        helper = TelegramHelper()
        result = helper.test_connection()
        
        if result['success']:
            bot_info = result['response']['result']
            print(f"✅ Подключение к Telegram успешно!")
            print(f"🤖 Бот: {bot_info['first_name']} (@{bot_info['username']})")
            print(f"🆔 ID: {bot_info['id']}")
            return True
        else:
            print(f"❌ Ошибка подключения: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    test_telegram_connection()

