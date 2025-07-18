# -*- coding: utf-8 -*-
"""
Улучшенный ветеринарный бот с веб-приложением для вызова врача и админ-панелью
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
from notification_system import notification_system

# Загрузка переменных окружения
load_dotenv()

# Версия бота
VERSION = "2.1.0"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('./enhanced_bot.log'),
        logging.StreamHandler()
    ]
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
                admin_response TEXT,
                admin_username TEXT,
                consultation_status TEXT DEFAULT 'ai', -- ai, waiting_doctor, with_doctor, completed
                assigned_doctor_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица врачей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                photo_path TEXT,
                is_approved BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица активных консультаций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                doctor_id INTEGER,
                consultation_id INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'waiting', -- waiting, assigned, active, completed
                client_username TEXT,
                client_name TEXT,
                initial_message TEXT,
                FOREIGN KEY (consultation_id) REFERENCES consultations (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        
        # Таблица сообщений консультаций
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultation_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consultation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL, -- client, doctor, admin, ai
                sender_id INTEGER,
                sender_name TEXT,
                message_text TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                telegram_message_id INTEGER,
                FOREIGN KEY (consultation_id) REFERENCES active_consultations (id)
            )
        ''')
        
        # Таблица уведомлений врачам
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctor_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consultation_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                message_id INTEGER,
                is_responded BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (consultation_id) REFERENCES active_consultations (id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        
        # Таблица для админских сессий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_username TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Таблица для сообщений админов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_username TEXT NOT NULL,
                message TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                telegram_message_id INTEGER
            )
        ''')
        
        # Таблица для очереди сообщений от админов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_message_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def is_admin_session_active(self, user_id):
        """Проверить, активна ли админская сессия"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT admin_username FROM admin_sessions 
            WHERE user_id = ? AND is_active = 1
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_pending_admin_messages(self, user_id):
        """Получить неотправленные сообщения от админов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, message FROM admin_message_queue 
            WHERE user_id = ? AND sent = 0
            ORDER BY created_at ASC
        ''', (user_id,))
        
        messages = cursor.fetchall()
        conn.close()
        return messages
    
    def mark_admin_message_sent(self, message_id):
        """Отметить сообщение как отправленное"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE admin_message_queue 
            SET sent = 1 
            WHERE id = ?
        ''', (message_id,))
        
        conn.commit()
        conn.close()
    
    def add_admin_message_to_queue(self, user_id, message):
        """Добавить сообщение админа в очередь"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO admin_message_queue (user_id, message)
            VALUES (?, ?)
        ''', (user_id, message))
        
        conn.commit()
        conn.close()
    
    def save_user(self, user_data):
        """Сохранение данных пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_data['user_id'], user_data.get('username'), 
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
        ''', (call_data['user_id'], call_data['name'], call_data['phone'],
              call_data['address'], call_data['pet_type'], call_data['pet_name'],
              call_data['pet_age'], call_data['problem'], call_data['urgency'],
              call_data['preferred_time'], call_data['comments']))
        
        conn.commit()
        conn.close()
    
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
    
    def save_consultation(self, user_id, question, response):
        """Сохранение консультации"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO consultations (user_id, question, response)
            VALUES (?, ?, ?)
        ''', (user_id, question, response))
        
        consultation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return consultation_id
    
    def get_active_consultation_by_client(self, client_id):
        """Получить активную консультацию клиента"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM active_consultations 
            WHERE client_id = ? AND status IN ('waiting', 'assigned', 'active')
            ORDER BY started_at DESC LIMIT 1
        ''', (client_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'client_id', 'doctor_id', 'consultation_id', 'started_at', 
                      'status', 'client_username', 'client_name', 'initial_message']
            return dict(zip(columns, result))
        return None
    
    def get_doctor_by_id(self, doctor_id):
        """Получить информацию о враче по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM doctors WHERE id = ?
        ''', (doctor_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'telegram_id', 'username', 'full_name', 'photo_path', 
                      'is_approved', 'is_active', 'registered_at', 'last_activity']
            return dict(zip(columns, result))
        return None

class EnhancedVetBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db = VetBotDatabase()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("version", self.version_command))
        
        # Обработчики кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Обработчик веб-приложения
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.web_app_data))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def get_ai_consultation(self, user_message, user_name):
        """Получение AI-консультации от DeepSeek"""
        try:
            system_prompt = """Ты опытный ветеринар-фелинолог с 15+ летним стажем, специализирующийся исключительно на лечении кошек.

Важные правила ответа:
- НЕ используй символы ### в ответах
- НЕ используй форматирование **текст**
- Используй простой текст с эмодзи
- Структурируй ответ с помощью номеров и эмодзи

Дай профессиональную консультацию по здоровью кошки, включая:
1. Анализ симптомов
2. Возможные причины
3. Рекомендации по первой помощи
4. Когда обязательно нужен осмотр врача

Помни: ты консультируешь только по кошкам!"""
            
            headers = {
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Пользователь {user_name} спрашивает: {user_message}"}
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            }
            
            # Асинхронный запрос с таймаутом
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    requests.post, 
                    DEEPSEEK_API_URL, 
                    headers=headers, 
                    json=data, 
                    timeout=30
                ),
                timeout=35.0
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Очистка форматирования
                ai_response = ai_response.replace('###', '').replace('**', '')
                
                # Добавляем информацию о версии
                ai_response += f"\n\n🤖 Консультация предоставлена ветеринарным ботом v{VERSION}"
                ai_response += "\n⚠️ Для точного диагноза рекомендуется очный осмотр"
                
                return ai_response
            else:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return self.get_fallback_response()
                
        except Exception as e:
            logger.error(f"Error getting AI consultation: {e}")
            return self.get_fallback_response()
    
    def get_fallback_response(self):
        """Резервный ответ при недоступности AI"""
        return f"""🐱 Извините, AI-консультант временно недоступен.

📞 Для получения консультации обратитесь к ветеринару:
Телефон: {VET_SERVICE_PHONE}

🚨 При экстренных ситуациях звоните немедленно!

🤖 Консультация предоставлена ветеринарным ботом v{VERSION}"""
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Сохраняем данные пользователя
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        self.db.save_user(user_data)
        
        welcome_text = f"""🐱 Добро пожаловать в ветеринарную службу!

Я помогу вам:
• Получить AI-консультацию по здоровью кошки
• Вызвать ветеринара на дом

📱 Версия бота: {VERSION}

Выберите нужную опцию:"""
        
        keyboard = [
            [InlineKeyboardButton("🤖 AI Консультация", callback_data='consultation')],
            [InlineKeyboardButton("📱 Вызвать врача", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def version_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для показа версии"""
        version_text = f"""🤖 Ветеринарный бот

📱 Версия: {VERSION}
🔧 Функции: AI-консультации, вызов врача
🐱 Специализация: кошки"""
        
        await update.message.reply_text(version_text)
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'consultation':
            await self.start_consultation(query)
        elif query.data == 'emergency_contact':
            await self.emergency_contact(query)
    
    async def start_consultation(self, query):
        """Начать консультацию"""
        consultation_text = """🩺 AI-Ветеринарная консультация

🤖 Наш AI-ветеринар с 15+ летним опытом готов помочь!

Для получения качественной консультации, пожалуйста, опишите:

1️⃣ Порода кошки
2️⃣ Возраст питомца
3️⃣ Подробное описание симптомов
4️⃣ Как давно наблюдаются симптомы
5️⃣ Что предпринимали для лечения

Просто напишите ваш вопрос в следующем сообщении, и AI-ветеринар проанализирует ситуацию.

⚠️ Помните: AI-консультация не заменяет очного осмотра врача!"""
        
        await query.edit_message_text(consultation_text)
    
    async def emergency_contact(self, query):
        """Экстренные контакты"""
        emergency_text = f"""🚨 Экстренные контакты

📞 Телефон службы: {VET_SERVICE_PHONE}

⚠️ При критических состояниях:
• Отравление
• Травмы
• Затрудненное дыхание
• Потеря сознания

Звоните НЕМЕДЛЕННО!"""
        
        # Создаем кнопку для прямого звонка
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [InlineKeyboardButton(f"📞 Позвонить {VET_SERVICE_PHONE}", url=f"tel:{VET_SERVICE_PHONE}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(emergency_text, reply_markup=reply_markup)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений с AI-консультацией"""
        user_id = update.effective_user.id
        user_message = update.message.text
        user_name = update.effective_user.first_name or "Пользователь"
        username = update.effective_user.username
        
        # Сначала проверяем и отправляем сообщения от админов
        await self.check_and_send_admin_messages(update, context)
        
        # Проверяем, активна ли админская сессия
        active_admin = self.db.is_admin_session_active(user_id)
        
        # Проверяем, есть ли активная консультация с врачом
        active_consultation = self.db.get_active_consultation_by_client(user_id)
        
        # Отправляем сообщение о том, что обрабатываем запрос
        try:
            if active_consultation and active_consultation['status'] == 'active':
                # Клиент уже в диалоге с врачом - пересылаем сообщение врачу
                doctor_info = self.db.get_doctor_by_id(active_consultation['doctor_id'])
                if doctor_info:
                    processing_msg = await update.message.reply_text(f"👨‍⚕️ Сообщение передано врачу {doctor_info['full_name']}...")
                    
                    # Отправляем сообщение врачу
                    client_display_name = f"{user_name} (@{username})" if username else user_name
                    await notification_system.send_message_to_doctor(
                        doctor_info['telegram_id'], 
                        user_message, 
                        from_client=client_display_name
                    )
                    
                    # Сохраняем сообщение в историю консультации
                    notification_system.add_consultation_message(
                        active_consultation['id'], 
                        'client', 
                        user_id, 
                        client_display_name, 
                        user_message
                    )
                    
                    await processing_msg.edit_text("✅ Сообщение передано врачу. Ожидайте ответа.")
                    return
                    
            elif active_admin:
                processing_msg = await update.message.reply_text(f"👨‍⚕️ Ветеринар {active_admin} анализирует ваш вопрос...")
            else:
                processing_msg = await update.message.reply_text("🤔 Анализирую ваш вопрос, подождите немного...")
        except Exception as e:
            logger.error(f"Error sending processing message: {e}")
            return
        
        try:
            # Получаем AI-консультацию с таймаутом
            ai_response = await asyncio.wait_for(
                self.get_ai_consultation(user_message, user_name),
                timeout=60.0  # 45 секунд таймаут
            )
            
            # Если активна админская сессия, добавляем уведомление
            if active_admin:
                ai_response += f"\n\n👨‍⚕️ К диалогу подключен ветеринар {active_admin}. Вы можете получить дополнительную персональную консультацию!"
            
            # Сохраняем консультацию в базу данных
            consultation_id = self.db.save_consultation(user_id, user_message, ai_response)
            
            # Создаем запрос на консультацию с врачом (если нет активной консультации)
            if not active_consultation and consultation_id:
                client_display_name = f"{user_name} (@{username})" if username else user_name
                active_consultation_id = notification_system.create_consultation_request(
                    user_id, username, client_display_name, user_message
                )
                
                if active_consultation_id:
                    # Уведомляем врачей о новом клиенте
                    await notification_system.notify_doctors_about_client(
                        active_consultation_id, client_display_name, user_message
                    )
                    
                    # Добавляем кнопку для прямого обращения к врачу
                    ai_response += "\n\n🔔 Врачи уведомлены о вашем вопросе. Если кто-то из врачей будет свободен, он сможет подключиться к диалогу для персональной консультации."
            
            # Удаляем сообщение о обработке
            try:
                await processing_msg.delete()
            except:
                pass  # Игнорируем ошибки удаления
            
            # Отправляем ответ с кнопками
            keyboard = [
                [InlineKeyboardButton("📱 Вызвать врача на дом", web_app=WebAppInfo(url=WEBAPP_URL))],
                [InlineKeyboardButton("📞 Экстренная связь", callback_data='emergency_contact')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Разбиваем длинные сообщения
            if len(ai_response) > 4000:
                # Отправляем по частям
                parts = [ai_response[i:i+4000] for i in range(0, len(ai_response), 4000)]
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Последняя часть с кнопками
                        await update.message.reply_text(part, reply_markup=reply_markup)
                    else:
                        await update.message.reply_text(part)
            else:
                await update.message.reply_text(ai_response, reply_markup=reply_markup)
            
        except asyncio.TimeoutError:
            logger.error("AI consultation timeout")
            try:
                await processing_msg.edit_text(
                    "⏰ Извините, AI-консультант не отвечает. Попробуйте позже или обратитесь к врачу напрямую.\n\n"
                    f"📞 Телефон: {VET_SERVICE_PHONE}"
                )
            except:
                pass
        except Exception as e:
            logger.error(f"Error in handle_message: {e}", exc_info=True)
            try:
                await processing_msg.edit_text(
                    "❌ Произошла ошибка при обработке запроса. Попробуйте позже или обратитесь к врачу напрямую.\n\n"
                    f"📞 Телефон: {VET_SERVICE_PHONE}\n\n"
                    f"🔧 Детали ошибки: {str(e)[:100]}"
                )
            except:
                pass
    
    async def check_and_send_admin_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверить и отправить сообщения от админов"""
        user_id = update.effective_user.id
        pending_messages = self.db.get_pending_admin_messages(user_id)
        
        for message_id, message in pending_messages:
            try:
                await update.message.reply_text(f"👨‍⚕️ Сообщение от ветеринара:\n\n{message}")
                self.db.mark_admin_message_sent(message_id)
            except Exception as e:
                logger.error(f"Error sending admin message: {e}")
    
    async def web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик данных из веб-приложения"""
        try:
            data = json.loads(update.effective_message.web_app_data.data)
            
            # Добавляем user_id к данным
            data['user_id'] = update.effective_user.id
            
            # Сохраняем заявку в базу данных
            self.db.save_vet_call(data)
            
            # Отправляем подтверждение пользователю
            confirmation_text = f"""✅ Заявка на вызов врача принята!

👤 Имя: {data.get('name', 'Не указано')}
📞 Телефон: {data.get('phone', 'Не указан')}
📍 Адрес: {data.get('address', 'Не указан')}
🐱 Питомец: {data.get('pet_name', 'Не указано')} ({data.get('pet_type', 'кошка')})
⏰ Желаемое время: {data.get('preferred_time', 'Не указано')}

📋 Проблема: {data.get('problem', 'Не указана')}

🔔 Мы свяжемся с вами в ближайшее время для подтверждения визита.

📞 Контактный телефон: {VET_SERVICE_PHONE}"""
            
            await update.effective_message.reply_text(confirmation_text)
            
            # Уведомляем администратора (если настроен)
            if ADMIN_CHAT_ID:
                admin_text = f"""🆕 Новая заявка на вызов врача!

👤 От: {update.effective_user.first_name} (@{update.effective_user.username})
📞 Телефон: {data.get('phone')}
📍 Адрес: {data.get('address')}
🐱 Питомец: {data.get('pet_name')} ({data.get('pet_age')})
🚨 Срочность: {data.get('urgency')}
⏰ Время: {data.get('preferred_time')}

📋 Проблема: {data.get('problem')}
💬 Комментарии: {data.get('comments', 'Нет')}"""
                
                try:
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)
                except Exception as e:
                    logger.error(f"Error sending admin notification: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing web app data: {e}")
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке заявки. Попробуйте еще раз или свяжитесь с нами напрямую."
            )
    
    def run(self):
        """Запуск бота"""
        print(f"""
🤖 Ветеринарный бот v{VERSION} запускается...
🔧 Функции: AI-консультации, вызов врача, админ-панель
🐱 Специализация: кошки
📱 WebApp URL: {WEBAPP_URL}
        """)
        
        self.application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot = EnhancedVetBot()
    bot.run()

