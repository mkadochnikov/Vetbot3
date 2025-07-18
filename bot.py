"""
Улучшенный ветеринарный Telegram-бот
Версия с правильной обработкой сигналов и предотвращением зомби-процессов
"""

import os
import logging
import signal
import sys
import asyncio
import atexit
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./vetbot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class VeterinaryBot:
    """Профессиональный ветеринарный консультант с улучшенной обработкой процессов"""
    
    def __init__(self):
        # API ключи
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.ai_key = os.getenv('DEEPSEEK_API_KEY')
        
        if not self.telegram_token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        if not self.ai_key:
            raise ValueError("❌ API ключ не найден в .env файле")
        
        # Настройки AI API
        self.ai_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '1500'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
        
        # Флаг для корректного завершения
        self.running = True
        self.application = None
        
        # Системный промпт
        self.system_prompt = """Ты опытный ветеринарный врач с 15-летним стажем работы в специализированной клинике для кошек. 
Ты фелинолог - специалист именно по кошкам всех пород и возрастов.

Твоя экспертиза:
- Диагностика и лечение заболеваний кошек
- Знание особенностей разных пород
- Профилактика и вакцинация
- Питание и уход за кошками
- Поведенческие проблемы кошек
- Экстренная помощь

Принципы работы:
1. Всегда начинай с сочувствия к владельцу
2. Задавай уточняющие вопросы для точной диагностики
3. Объясняй медицинские термины простым языком
4. При серьезных симптомах настоятельно рекомендуй очную консультацию
5. Давай практические советы по уходу
6. Будь профессиональным, но дружелюбным

ВАЖНО: При любых серьезных симптомах (рвота, понос, отказ от еды более суток, затрудненное дыхание, травмы) обязательно рекомендуй срочное обращение к ветеринару!

Отвечай на русском языке, используй эмодзи для лучшего восприятия."""
        
        # Настройка обработчиков сигналов
        self.setup_signal_handlers()
        
        # Регистрация функции очистки при выходе
        atexit.register(self.cleanup)
        
        logger.info("🤖 VeterinaryBot инициализирован")

    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для корректного завершения"""
        def signal_handler(signum, frame):
            logger.info(f"Получен сигнал {signum}, начинаю корректное завершение...")
            self.running = False
            if self.application:
                # Останавливаем приложение
                asyncio.create_task(self.application.stop())
                asyncio.create_task(self.application.shutdown())
            sys.exit(0)
        
        # Обработка сигналов завершения
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Игнорируем SIGCHLD для предотвращения зомби-процессов
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        
        logger.info("Обработчики сигналов настроены")

    def cleanup(self):
        """Функция очистки ресурсов"""
        logger.info("Выполняется очистка ресурсов...")
        self.running = False

    async def get_ai_response(self, user_message: str, user_id: int) -> str:
        """Получение ответа от AI с обработкой ошибок"""
        try:
            headers = {
                'Authorization': f'Bearer {self.ai_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            response = requests.post(
                self.ai_url, 
                headers=headers, 
                json=data, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                logger.info(f"AI ответ получен для пользователя {user_id}")
                return ai_response
            else:
                logger.error(f"Ошибка AI API: {response.status_code} - {response.text}")
                return "😔 Извините, сейчас у меня технические проблемы. Попробуйте позже или обратитесь к ветеринару напрямую."
                
        except requests.exceptions.Timeout:
            logger.error("Таймаут запроса к AI API")
            return "⏰ Запрос занял слишком много времени. Попробуйте переформулировать вопрос."
        except Exception as e:
            logger.error(f"Ошибка при обращении к AI: {e}")
            return "😔 Произошла ошибка при обработке вашего запроса. Попробуйте позже."

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.first_name}) запустил бота")
        
        welcome_message = f"""🐱 Добро пожаловать, {user.first_name}!

Я ветеринарный врач-фелинолог с 15-летним опытом работы с кошками. Готов помочь вам с любыми вопросами о здоровье и уходе за вашим питомцем.

🔹 Опишите симптомы или проблему
🔹 Укажите возраст и породу кошки
🔹 Расскажите о поведении питомца

⚠️ ВАЖНО: При серьезных симптомах обязательно обратитесь к ветеринару очно!

Задавайте ваш вопрос! 🩺"""
        
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """🆘 Как я могу помочь:

🔸 Диагностика симптомов
🔸 Советы по питанию
🔸 Вопросы о поведении
🔸 Профилактика заболеваний
🔸 Уход за котятами
🔸 Экстренная помощь

📝 Для лучшей консультации укажите:
• Возраст кошки
• Породу (если известна)
• Симптомы и их длительность
• Изменения в поведении

⚠️ При серьезных симптомах - срочно к ветеринару!"""
        
        await update.message.reply_text(help_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        if not self.running:
            return
            
        user = update.effective_user
        user_message = update.message.text
        
        logger.info(f"Сообщение от {user.id}: {user_message[:100]}...")
        
        # Отправляем индикатор печати
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Получаем ответ от AI
        ai_response = await self.get_ai_response(user_message, user.id)
        
        # Отправляем ответ пользователю
        try:
            await update.message.reply_text(ai_response)
            logger.info(f"Ответ отправлен пользователю {user.id}")
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка: {context.error}")
        
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="😔 Произошла ошибка. Попробуйте позже или обратитесь к администратору."
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

    async def run(self):
        """Запуск бота"""
        try:
            # Создаем приложение
            self.application = Application.builder().token(self.telegram_token).build()
            
            # Добавляем обработчики
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            
            # Добавляем обработчик ошибок
            self.application.add_error_handler(self.error_handler)
            
            logger.info("🚀 Запуск ветеринарного бота...")
            
            # Запускаем бота
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)
            
            logger.info("✅ Бот успешно запущен и работает")
            
            # Ожидаем завершения
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
        finally:
            # Корректное завершение
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            logger.info("🛑 Бот остановлен")

def main():
    """Главная функция"""
    try:
        # Создаем и запускаем бота
        bot = VeterinaryBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания, завершение работы...")
    except Exception as e:
        logger.error(f"Критическая ошибка в main: {e}")
    finally:
        logger.info("Программа завершена")

if __name__ == "__main__":
    main()

