#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Улучшенный ветеринарный бот с веб-приложением для вызова врача
"""

import os
import json
import logging
import sqlite3
import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Версия бота
VERSION = "2.1.0"
BUILD_DATE = "2025-01-06"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-webapp-url.com')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
VET_SERVICE_PHONE = os.getenv('VET_SERVICE_PHONE', '+7-999-123-45-67')

# DeepSeek API конфигурация
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-your-api-key-here')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class VetBotDatabase:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path='vetbot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заявок на вызов врача
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vet_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                phone TEXT,
                address TEXT,
                pet_type TEXT,
                pet_name TEXT,
                pet_age TEXT,
                problem TEXT,
                urgency TEXT,
                preferred_time TEXT,
                comments TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица консультаций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question TEXT,
                response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_user(self, user_data):
        """Сохранение данных пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_data['id'], user_data.get('username'), 
              user_data.get('first_name'), user_data.get('last_name')))
        
        conn.commit()
        conn.close()
    
    def save_vet_call(self, call_data):
        """Сохранение заявки на вызов врача"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vet_calls 
            (user_id, name, phone, address, pet_type, pet_name, pet_age, 
             problem, urgency, preferred_time, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            call_data.get('user_id'),
            call_data.get('name'),
            call_data.get('phone'),
            call_data.get('address'),
            call_data.get('petType'),
            call_data.get('petName'),
            call_data.get('petAge'),
            call_data.get('problem'),
            call_data.get('urgency', 'normal'),
            call_data.get('preferredTime'),
            call_data.get('comments')
        ))
        
        call_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return call_id
    
    def get_user_calls(self, user_id):
        """Получение заявок пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vet_calls 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        calls = cursor.fetchall()
        conn.close()
        
        return calls

class EnhancedVetBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db = VetBotDatabase()
        self.setup_handlers()
    
    async def get_ai_consultation(self, user_message, user_name=""):
        """Получение AI-консультации от DeepSeek"""
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            system_prompt = """Ты - опытный ветеринар-фелинолог с 15+ летним стажем. 
            Специализируешься на лечении кошек, но также консультируешь по другим домашним животным.
            
            Твоя задача:
            1. Проанализировать симптомы и дать профессиональную консультацию
            2. Предложить первичные рекомендации по уходу
            3. Определить степень срочности ситуации
            4. При необходимости рекомендовать очный осмотр
            
            Отвечай на русском языке, используй эмодзи для лучшего восприятия.
            Всегда подчеркивай, что онлайн-консультация не заменяет очного осмотра.
            Будь внимательным, профессиональным и сочувствующим."""
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Пользователь {user_name} спрашивает: {user_message}"}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # Асинхронный запрос к API
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=30)
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Добавляем информацию о боте в конец ответа
                ai_response += f"\n\n🤖 Консультация предоставлена ветеринарным ботом v{VERSION}"
                ai_response += f"\n⚠️ Для точного диагноза рекомендуется очный осмотр"
                
                return ai_response
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return self.get_fallback_response()
                
        except Exception as e:
            logger.error(f"Error getting AI consultation: {e}")
            return self.get_fallback_response()
    
    def get_fallback_response(self):
        """Резервный ответ при недоступности AI"""
        return """
🩺 Извините, AI-консультант временно недоступен.

📋 Общие рекомендации:
• При острых симптомах - срочно к врачу
• Обеспечьте покой животному
• Следите за температурой и аппетитом
• Не давайте человеческие лекарства

📞 Для экстренной помощи звоните: """ + VET_SERVICE_PHONE + """

🤖 Попробуйте задать вопрос позже, когда AI-консультант будет доступен.
        """
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("webapp", self.webapp_command))
        self.application.add_handler(CommandHandler("my_calls", self.my_calls_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        self.application.add_handler(CommandHandler("version", self.version_command))
        
        # Обработчики callback'ов
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик данных из веб-приложения
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.web_app_data))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        self.db.save_user(user.to_dict())
        
        keyboard = [
            [InlineKeyboardButton("🩺 Консультация", callback_data='consultation')],
            [InlineKeyboardButton("📱 Вызвать врача", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton("📋 Мои заявки", callback_data='my_calls')],
            [InlineKeyboardButton("📞 Контакты", callback_data='contact')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🐾 Добро пожаловать, {user.first_name}!

🩺 Профессиональный ветеринарный консультант-фелинолог
👨‍⚕️ Специализация: лечение кошек (стаж 15+ лет)

Я помогу вам:
• Получить консультацию по здоровью питомца
• Вызвать ветеринара на дом
• Отследить статус ваших заявок
• Найти контакты ветслужбы

📱 Версия бота: {VERSION} (сборка {BUILD_DATE})

Выберите нужную опцию:
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = f"""
🆘 Помощь по использованию бота:

🩺 Профессиональный ветеринарный консультант-фелинолог
👨‍⚕️ Специализация: лечение кошек (стаж 15+ лет)
📱 Версия: {VERSION} (сборка {BUILD_DATE})

📋 Команды:
/start - Главное меню
/help - Эта справка
/webapp - Открыть веб-приложение
/my_calls - Мои заявки на вызов врача
/contact - Контактная информация
/version - Показать версию бота

🩺 Функции:
• Консультация - получить совет по здоровью питомца
• Вызвать врача - заказать выезд ветеринара на дом
• Отслеживание заявок - проверить статус вызова

⚠️ Важно:
В экстренных случаях звоните напрямую: {VET_SERVICE_PHONE}
        """
        await update.message.reply_text(help_text)
    
    async def webapp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для открытия веб-приложения"""
        keyboard = [[InlineKeyboardButton("📱 Открыть веб-приложение", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Нажмите кнопку ниже, чтобы открыть веб-приложение для вызова врача:",
            reply_markup=reply_markup
        )
    
    async def my_calls_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для просмотра заявок пользователя"""
        user_id = update.effective_user.id
        calls = self.db.get_user_calls(user_id)
        
        if not calls:
            await update.message.reply_text("У вас пока нет заявок на вызов врача.")
            return
        
        response = "📋 Ваши заявки на вызов врача:\n\n"
        
        for call in calls[:5]:  # Показываем последние 5 заявок
            call_id, user_id, name, phone, address, pet_type, pet_name, pet_age, problem, urgency, preferred_time, comments, status, created_at = call
            
            status_emoji = {
                'pending': '⏳',
                'confirmed': '✅',
                'in_progress': '🚗',
                'completed': '✅',
                'cancelled': '❌'
            }.get(status, '❓')
            
            response += f"{status_emoji} Заявка #{call_id}\n"
            response += f"📅 {created_at}\n"
            response += f"🐾 {pet_type} {pet_name or ''}\n"
            response += f"📍 {address[:50]}...\n"
            response += f"📊 Статус: {status}\n\n"
        
        await update.message.reply_text(response)
    
    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для показа контактов"""
        contact_text = f"""
📞 Контактная информация:

🏥 Ветеринарная служба
📱 Телефон: {VET_SERVICE_PHONE}
📧 Email: {os.getenv('VET_SERVICE_EMAIL', 'info@vetservice.com')}

🕐 Режим работы:
• Консультации: 8:00-22:00
• Экстренные вызовы: круглосуточно
• Плановые вызовы: 9:00-20:00

💰 Стоимость услуг:
• Консультация в боте: бесплатно
• Выезд врача: от 1500 руб.
• Экстренный вызов: от 3000 руб.
        """
        
        await update.message.reply_text(contact_text)
    
    async def version_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для показа версии бота"""
        version_text = f"""
📱 Информация о версии:

🤖 Ветеринарный бот-фелинолог
📊 Версия: {VERSION}
📅 Дата сборки: {BUILD_DATE}
👨‍⚕️ Специализация: лечение кошек (стаж 15+ лет)

🔧 Возможности:
• Профессиональные консультации
• Веб-приложение для вызова врача
• База данных заявок
• Отслеживание статуса вызовов
        """
        await update.message.reply_text(version_text)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на inline кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'consultation':
            await self.start_consultation(query)
        elif query.data == 'help':
            await self.show_help(query)
        elif query.data == 'my_calls':
            await self.show_my_calls(query)
        elif query.data == 'contact':
            await self.show_contact(query)
        elif query.data == 'emergency_contact':
            await self.show_emergency_contact(query)
    
    async def show_emergency_contact(self, query):
        """Показать экстренные контакты"""
        emergency_text = f"""
🚨 ЭКСТРЕННАЯ ВЕТЕРИНАРНАЯ ПОМОЩЬ

📞 Круглосуточная служба: {VET_SERVICE_PHONE}

⚠️ Звоните немедленно при:
• Потере сознания животного
• Сильном кровотечении
• Затрудненном дыхании
• Судорогах
• Отравлении
• Травмах

🚗 Выезд экстренной бригады: 24/7
💰 Стоимость экстренного вызова: от 3000 руб.

Не теряйте время - звоните прямо сейчас!
        """
        await query.edit_message_text(emergency_text)
    
    async def start_consultation(self, query):
        """Начать консультацию"""
        consultation_text = """
🩺 AI-Ветеринарная консультация

🤖 Наш AI-ветеринар с 15+ летним опытом готов помочь!

Для получения качественной консультации, пожалуйста, опишите:

1️⃣ Вид животного (кошка, собака, птица и т.д.)
2️⃣ Возраст питомца
3️⃣ Подробное описание симптомов
4️⃣ Как давно наблюдаются симптомы
5️⃣ Что предпринимали для лечения

Просто напишите ваш вопрос в следующем сообщении, и AI-ветеринар проанализирует ситуацию.

⚠️ Помните: AI-консультация не заменяет очного осмотра врача!
        """
        
        keyboard = [[InlineKeyboardButton("📱 Вызвать врача на дом", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(consultation_text, reply_markup=reply_markup)
    
    async def show_help(self, query):
        """Показать помощь"""
        help_text = """
🆘 Помощь по использованию бота:

🔹 Консультация - получите первичную консультацию по здоровью питомца
🔹 Вызвать врача - закажите выезд ветеринара на дом через удобную форму
🔹 Мои заявки - отслеживайте статус ваших вызовов
🔹 Контакты - получите контактную информацию службы

⚠️ В экстренных случаях звоните напрямую!

Бот работает 24/7 для вашего удобства.
        """
        await query.edit_message_text(help_text)
    
    async def show_my_calls(self, query):
        """Показать заявки пользователя"""
        user_id = query.from_user.id
        calls = self.db.get_user_calls(user_id)
        
        if not calls:
            await query.edit_message_text("У вас пока нет заявок на вызов врача.")
            return
        
        response = "📋 Ваши заявки:\n\n"
        
        for call in calls[:3]:  # Показываем последние 3 заявки
            call_id, user_id, name, phone, address, pet_type, pet_name, pet_age, problem, urgency, preferred_time, comments, status, created_at = call
            
            status_emoji = {
                'pending': '⏳ Ожидает',
                'confirmed': '✅ Подтверждена',
                'in_progress': '🚗 Врач в пути',
                'completed': '✅ Завершена',
                'cancelled': '❌ Отменена'
            }.get(status, '❓ Неизвестно')
            
            response += f"#{call_id} - {status_emoji}\n"
            response += f"🐾 {pet_type}\n"
            response += f"📅 {created_at[:16]}\n\n"
        
        await query.edit_message_text(response)
    
    async def show_contact(self, query):
        """Показать контакты"""
        contact_text = f"""
📞 Контакты ветслужбы:

📱 {VET_SERVICE_PHONE}
📧 {os.getenv('VET_SERVICE_EMAIL', 'info@vetservice.com')}

🕐 Режим работы:
Консультации: 8:00-22:00
Вызовы: круглосуточно
        """
        await query.edit_message_text(contact_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений с AI-консультацией"""
        user_message = update.message.text
        user_name = update.effective_user.first_name or "Пользователь"
        
        # Отправляем сообщение о том, что обрабатываем запрос
        processing_msg = await update.message.reply_text("🤔 Анализирую ваш вопрос, подождите немного...")
        
        try:
            # Получаем AI-консультацию
            ai_response = await self.get_ai_consultation(user_message, user_name)
            
            # Сохраняем консультацию в базу данных
            self.save_consultation(update.effective_user.id, user_message, ai_response)
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Отправляем ответ с кнопками
            keyboard = [
                [InlineKeyboardButton("📱 Вызвать врача на дом", web_app=WebAppInfo(url=WEBAPP_URL))],
                [InlineKeyboardButton("📞 Экстренная связь", callback_data='emergency_contact')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(ai_response, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
            await processing_msg.edit_text("❌ Произошла ошибка при обработке запроса. Попробуйте позже.")
    
    def save_consultation(self, user_id, question, response):
        """Сохранение консультации в базу данных"""
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO consultations (user_id, question, response)
                VALUES (?, ?, ?)
            ''', (user_id, question, response))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving consultation: {e}")
    
    async def web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик данных из веб-приложения"""
        data = update.effective_message.web_app_data.data
        user = update.effective_user
        
        try:
            call_data = json.loads(data)
            call_data['user_id'] = user.id
            
            # Сохранение заявки в базу данных
            call_id = self.db.save_vet_call(call_data)
            
            # Определение срочности
            urgency_text = {
                'normal': 'Обычная',
                'urgent': 'Срочная', 
                'emergency': 'Экстренная'
            }.get(call_data.get('urgency', 'normal'), 'Обычная')
            
            # Ответ пользователю
            response = f"""
✅ Заявка #{call_id} принята!

📋 Детали заявки:
• Имя: {call_data.get('name', 'Не указано')}
• Телефон: {call_data.get('phone', 'Не указан')}
• Адрес: {call_data.get('address', 'Не указан')}
• Питомец: {call_data.get('petType', 'Не указан')} {call_data.get('petName', '')}
• Возраст: {call_data.get('petAge', 'Не указан')}
• Проблема: {call_data.get('problem', 'Не указана')}
• Срочность: {urgency_text}

🕐 Ожидаемое время прибытия: 
{self.get_arrival_time(call_data.get('urgency', 'normal'))}

📞 С вами свяжется врач для уточнения деталей в течение 15 минут.
            """
            
            await update.effective_message.reply_text(response)
            
            # Уведомление администратора
            if ADMIN_CHAT_ID:
                admin_message = f"""
🚨 НОВАЯ ЗАЯВКА #{call_id}

👤 Пользователь: {user.first_name} {user.last_name or ''} (@{user.username or 'нет'})
📱 Телефон: {call_data.get('phone')}
📍 Адрес: {call_data.get('address')}
🐾 Питомец: {call_data.get('petType')} {call_data.get('petName', '')} ({call_data.get('petAge', 'возраст не указан')})
🚨 Срочность: {urgency_text}
📝 Проблема: {call_data.get('problem')}
⏰ Предпочтительное время: {call_data.get('preferredTime', 'Не указано')}
💬 Комментарии: {call_data.get('comments', 'Нет')}
                """
                
                try:
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления админу: {e}")
            
            # Логирование
            logger.info(f"Получена заявка #{call_id} от пользователя {user.id}: {call_data}")
            
        except json.JSONDecodeError:
            await update.effective_message.reply_text(
                "❌ Ошибка обработки данных. Попробуйте еще раз."
            )
        except Exception as e:
            logger.error(f"Ошибка обработки заявки: {e}")
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке заявки. Попробуйте еще раз или свяжитесь с нами по телефону."
            )
    
    def get_arrival_time(self, urgency):
        """Получение времени прибытия в зависимости от срочности"""
        times = {
            'emergency': '30-60 минут',
            'urgent': '1-2 часа',
            'normal': '2-4 часа'
        }
        return times.get(urgency, '2-4 часа')
    
    def run(self):
        """Запуск бота"""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  ВЕТЕРИНАРНЫЙ БОТ-ФЕЛИНОЛОГ                 ║
╠══════════════════════════════════════════════════════════════╣
║ 📊 Версия: {VERSION:<47} ║
║ 📅 Дата сборки: {BUILD_DATE:<42} ║
║ 👨‍⚕️ Специализация: лечение кошек (стаж 15+ лет)           ║
║ 🔧 Возможности: консультации, веб-приложение, база данных   ║
╚══════════════════════════════════════════════════════════════╝
        """)
        logger.info(f"Запуск профессионального ветеринарного бота-фелинолога v{VERSION}")
        logger.info(f"Дата сборки: {BUILD_DATE}")
        logger.info("Бот готов к работе!")
        
        # Простой запуск бота
        self.application.run_polling()

if __name__ == '__main__':
    bot = EnhancedVetBot()
    bot.run()

