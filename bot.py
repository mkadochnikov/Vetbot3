"""
Ветеринарный Telegram-бот
Профессиональный консультант по лечению кошек
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
    """Профессиональный ветеринарный консультант"""
    
    def __init__(self):
        # API ключи
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.ai_key = os.getenv('DEEPSEEK_API_KEY')  # Используем тот же ключ для совместимости
        
        if not self.telegram_token:
            raise ValueError("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        if not self.ai_key:
            raise ValueError("❌ API ключ не найден в .env файле")
        
        # Настройки AI API
        self.ai_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '1500'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
        
        # Системный промпт - профессиональный ветеринар-фелинолог
        self.system_prompt = """Ты опытный ветеринарный врач с 15-летним стажем работы в специализированной клинике для кошек. 
Ты фелинолог - специалист именно по кошкам всех пород и возрастов.

Твоя экспертиза:
- Диагностика и лечение заболеваний кошек
- Знание особенностей разных пород
- Опыт работы с котятами, взрослыми и пожилыми кошками
- Специализация на инфекционных, паразитарных и хронических заболеваниях кошек

Твой стиль общения:
- Профессиональный, но доступный для владельцев
- Уверенный в диагнозах благодаря большому опыту
- Конкретный в назначениях и рекомендациях
- Используешь ветеринарную терминологию с пояснениями
- Всегда указываешь дозировки препаратов для кошек

Алгоритм консультации:
1. Анализируешь симптомы с учетом породы и возраста
2. Ставишь предварительный диагноз на основе опыта
3. Назначаешь конкретное лечение с дозировками для кошек
4. Даешь рекомендации по домашнему уходу
5. Четко указываешь критерии для срочного обращения в клинику

Структура ответа:
🔍 **Предварительный диагноз:** [название заболевания]
💊 **Лечение:** [конкретные препараты с дозировками для кошек]
🏠 **Домашний уход:** [подробные рекомендации]
⚠️ **Срочно к врачу если:** [тревожные симптомы]
📋 **Профилактика:** [как избежать повторения]

Помни: владельцы доверяют твоему 15-летнему опыту работы с кошками."""
        
        # Создаем приложение
        self.app = Application.builder().token(self.telegram_token).build()
        self._setup_handlers()
        
        logger.info("✅ Ветеринарный бот-фелинолог инициализирован успешно")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("info", self.info_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def get_ai_response(self, user_message: str) -> str:
        """Получает профессиональную консультацию"""
        headers = {
            'Authorization': f'Bearer {self.ai_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': f'Пациент: кошка. Обращение владельца: {user_message}'}
            ],
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }
        
        try:
            response = requests.post(self.ai_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                logger.error("AI API: Недостаточно средств на балансе")
                return "💰 Извините, сейчас у меня проблемы с доступом к медицинской системе. Обратитесь к администратору."
            elif response.status_code == 401:
                logger.error("AI API: Неверный API ключ")
                return "🔑 Ошибка доступа к медицинской системе. Обратитесь к администратору."
            else:
                logger.error(f"AI API Error: {response.status_code} - {response.text}")
                return "⚠️ Извините, произошла ошибка при обращении к медицинской системе."
                
        except requests.exceptions.Timeout:
            logger.error("AI API: Таймаут запроса")
            return "⏰ Извините, анализ занял слишком много времени. Попробуйте еще раз."
        except requests.exceptions.ConnectionError:
            logger.error("AI API: Ошибка подключения")
            return "🌐 Извините, проблемы с подключением. Проверьте интернет."
        except Exception as e:
            logger.error(f"AI API: Неожиданная ошибка - {e}")
            return "❌ Извините, произошла неожиданная ошибка. Попробуйте позже."
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_message = """🐱 **Ветеринарный консультант-фелинолог**

Здравствуйте! Я ветеринарный врач с 15-летним опытом работы с кошками.
Специализируюсь на диагностике и лечении заболеваний кошек всех пород и возрастов.

**Как получить профессиональную консультацию:**
Опишите подробно состояние вашей кошки:
• Основные симптомы и их продолжительность
• Возраст, порода, вес кошки
• Изменения в поведении, аппетите, активности
• Когда началась проблема
• Что уже предпринимали

**Пример обращения:** 
"Британская кошка, 5 лет, 4 кг. Третий день жидкий стул, стала вялая, ест в два раза меньше обычного. Температура не мерили. Никаких лекарств не давали."

Поставлю диагноз и назначу конкретное лечение! 👨‍⚕️🐾"""
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"Пользователь {update.effective_user.id} запустил бота")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """🆘 **Справка по консультации**

**Команды:**
/start - Начать работу с ветеринаром
/help - Показать эту справку
/info - Информация о враче

**Как правильно описать проблему:**

**Обязательно укажите:**
✅ Возраст кошки (котенок/взрослая/пожилая)
✅ Породу или тип (беспородная/британец/мейн-кун и т.д.)
✅ Основные симптомы
✅ Как давно длится проблема
✅ Изменения в поведении

**Примеры хороших обращений:**
• "Персидский кот, 3 года, кашляет неделю, температура 39.2, вялый"
• "Котенок 5 месяцев, беспородный, понос с кровью 2 дня, не играет"
• "Мейн-кун, 7 лет, хромает на левую заднюю лапу, мяукает при движении"

**Дополнительная информация:**
• Вакцинации (когда последняя)
• Обработка от паразитов
• Чем кормите
• Есть ли другие животные

Чем подробнее описание - тем точнее диагноз и лечение! 🎯"""
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /info"""
        info_text = """ℹ️ **О враче-консультанте**

**Специализация:** Фелинолог (врач по кошкам)
**Стаж работы:** 15 лет в ветеринарной практике
**Опыт:** Более 10,000 пролеченных кошек

**Экспертиза:**
🔬 Диагностика заболеваний кошек
💊 Назначение эффективного лечения
🏥 Определение необходимости госпитализации
🐾 Особенности разных пород кошек
👶 Работа с котятами и пожилыми кошками

**Специализация по заболеваниям:**
• Инфекционные болезни кошек
• Паразитарные инвазии
• Болезни ЖКТ и мочеполовой системы
• Дерматологические проблемы
• Поведенческие нарушения

**Технологии:** Telegram Bot API + AI-ассистент
**Версия:** 2.0 (Профессиональная)

*Консультация не заменяет очного осмотра при серьезных состояниях*"""
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обращений владельцев"""
        user_text = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Получено обращение от {user_id}: {user_text[:50]}...")
        
        # Показываем что врач анализирует
        status_message = await update.message.reply_text(
            "🔍 Анализирую симптомы и ставлю диагноз... \nПожалуйста, подождите."
        )
        
        try:
            # Получаем профессиональную консультацию
            response = self.get_ai_response(user_text)
            
            # Удаляем статус и отправляем заключение врача
            await status_message.delete()
            await update.message.reply_text(response)
            logger.info(f"Консультация отправлена пользователю {user_id}")
                
        except Exception as e:
            logger.error(f"Ошибка при консультации для {user_id}: {e}")
            await status_message.edit_text(
                "😔 Произошла ошибка при анализе. Попробуйте еще раз или обратитесь в ветклинику."
            )
    
    def run(self):
        """Запуск ветеринарного консультанта"""
        logger.info("🚀 Запуск ветеринарного бота-фелинолога...")
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

