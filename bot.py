"""
Ветеринарный Telegram-бот с DeepSeek API
Исправленная версия без циклических импортов
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import requests
import json
from typing import Optional

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VeterinaryBot:
    """Ветеринарный бот с DeepSeek API"""
    
    def __init__(self):
        # API ключи
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.deepseek_key = os.getenv('DEEPSEEK_API_KEY')
        
        if not self.telegram_token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        if not self.deepseek_key:
            raise ValueError("❌ DEEPSEEK_API_KEY не найден в .env файле")
        
        # Настройки DeepSeek
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '1500'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.8'))
        
        # Системный промпт
        self.system_prompt = """Ты опытный ветеринарный врач с 15-летним стажем работы в клинике. 
Специализируешься на лечении домашних кошек всех пород и возрастов.

Твой стиль общения:
- Профессиональный, но понятный владельцам
- Уверенный в диагнозах и назначениях
- Конкретный в рекомендациях
- Используешь медицинскую терминологию с объяснениями

Алгоритм работы:
1. Анализируешь описанные симптомы
2. Ставишь предварительный диагноз
3. Назначаешь конкретное лечение
4. Даешь рекомендации по уходу
5. Указываешь когда нужно срочно к врачу

Всегда структурируй ответ:
🔍 Диагноз: [название заболевания]
💊 Лечение: [конкретные препараты и дозировки]
🏠 Уход: [рекомендации по домашнему уходу]
⚠️ Когда к врачу: [критерии для обращения]

Помни: ты настоящий врач, владельцы доверяют твоему мнению."""
        
        # Создаем приложение
        self.app = Application.builder().token(self.telegram_token).build()
        self._setup_handlers()
        
        logger.info("✅ Ветеринарный бот инициализирован успешно")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("info", self.info_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def get_deepseek_response(self, user_message: str) -> str:
        """Получает ответ от DeepSeek API"""
        headers = {
            'Authorization': f'Bearer {self.deepseek_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': f'Пациент: кошка. Жалобы владельца: {user_message}'}
            ],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
        
        try:
            response = requests.post(self.deepseek_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                logger.error("DeepSeek API: Недостаточно средств на балансе")
                return "💰 Извините, сейчас у меня проблемы с доступом к медицинской базе данных. Пополните баланс DeepSeek API."
            elif response.status_code == 401:
                logger.error("DeepSeek API: Неверный API ключ")
                return "🔑 Ошибка авторизации. Проверьте API ключ DeepSeek."
            else:
                logger.error(f"DeepSeek API Error: {response.status_code} - {response.text}")
                return "⚠️ Извините, произошла ошибка при обращении к медицинской базе данных."
                
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API: Таймаут запроса")
            return "⏰ Извините, запрос занял слишком много времени. Попробуйте еще раз."
        except requests.exceptions.ConnectionError:
            logger.error("DeepSeek API: Ошибка подключения")
            return "🌐 Извините, проблемы с подключением к серверу. Проверьте интернет."
        except Exception as e:
            logger.error(f"DeepSeek API: Неожиданная ошибка - {e}")
            return "❌ Извините, произошла неожиданная ошибка. Попробуйте позже."
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_message = """🐱 **Ветеринарный консультант DeepSeek**

Здравствуйте! Я ветеринарный врач с 15-летним опытом.
Помогу с диагностикой и лечением вашей кошки.

**Как получить консультацию:**
Опишите подробно что беспокоит кошку:
• Симптомы и их длительность
• Возраст и порода кошки  
• Изменения в поведении/аппетите
• Когда началась проблема

**Пример:** "Кошка 5 лет, британка, 3 дня понос, стала вялая, плохо ест"

Готов поставить диагноз и назначить лечение! 👨‍⚕️"""
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """🆘 **Помощь по использованию бота**

**Команды:**
/start - Начать работу с ботом
/help - Показать эту справку
/info - Информация о боте

**Как задать вопрос:**
Просто опишите проблему с кошкой обычными словами.

**Примеры хороших вопросов:**
• "Кот 2 года, кашляет неделю, температура 39.5"
• "Котенок 4 месяца, понос с кровью, не играет"
• "Кошка 8 лет, хромает на заднюю лапу, мяукает"

**Что указать обязательно:**
✅ Возраст кошки
✅ Основные симптомы
✅ Как долго длится проблема
✅ Изменения в поведении

Чем подробнее опишете - тем точнее диагноз! 🎯"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /info"""
        info_text = """ℹ️ **Информация о боте**

**Технологии:**
🤖 Telegram Bot API
🧠 DeepSeek AI (deepseek-chat)
🐍 Python 3.11

**Возможности:**
• Диагностика заболеваний кошек
• Назначение лечения
• Рекомендации по уходу
• Определение срочности обращения к врачу

**Разработчик:** Ветеринарный AI-консультант
**Версия:** 1.0 (DeepSeek)"""
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_text = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Получено сообщение от {user_id}: {user_text[:50]}...")
        
        # Показываем что анализируем
        status_message = await update.message.reply_text(
            "🔍 Анализирую симптомы... Пожалуйста, подождите."
        )
        
        try:
            # Получаем ответ от DeepSeek
            response = self.get_deepseek_response(user_text)
            
            # Удаляем статус и отправляем ответ
            await status_message.delete()
            await update.message.reply_text(response)
            logger.info(f"Ответ отправлен пользователю {user_id}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения от {user_id}: {e}")
            await status_message.edit_text(
                "😔 Произошла ошибка при анализе. Попробуйте еще раз или обратитесь к ветеринару."
            )
    
    def run(self):
        """Запуск бота"""
        logger.info("🚀 Запуск ветеринарного бота с DeepSeek API...")
        try:
            self.app.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("🛑 Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")

def main():
    """Главная функция"""
    try:
        bot = VeterinaryBot()
        bot.run()
    except Exception as e:
        print(f"❌ Не удалось запустить бота: {e}")
        print("Проверьте конфигурацию в .env файле")

if __name__ == "__main__":
    main()

