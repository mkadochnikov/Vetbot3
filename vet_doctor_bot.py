"""
Бот для ветеринарных врачей - регистрация и работа с клиентами
"""

import os
import json
import logging
import sqlite3
import requests
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
from notification_system import notification_system

# Загрузка переменных окружения
load_dotenv()

# Версия бота
VERSION = "1.0.0"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('./vet_doctor_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
VET_BOT_TOKEN = os.getenv('VET_BOT_TOKEN', 'YOUR_VET_BOT_TOKEN_HERE')
MAIN_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_MAIN_BOT_TOKEN_HERE')

class VetDoctorDatabase:
    """Класс для работы с базой данных врачей"""
    
    def __init__(self, db_path='vetbot.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'waiting', -- waiting, assigned, active, completed
                client_username TEXT,
                client_name TEXT,
                initial_message TEXT
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
        
        conn.commit()
        conn.close()
    
    def register_doctor(self, telegram_id, username, full_name, photo_path=None):
        """Регистрация нового врача"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO doctors (telegram_id, username, full_name, photo_path)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, full_name, photo_path))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error registering doctor: {e}")
            return None
        finally:
            conn.close()
    
    def get_doctor(self, telegram_id):
        """Получить информацию о враче"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM doctors WHERE telegram_id = ?
        ''', (telegram_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_approved_doctors(self):
        """Получить список одобренных врачей"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM doctors WHERE is_approved = 1 AND is_active = 1
        ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def create_consultation(self, client_id, client_username, client_name, initial_message):
        """Создать новую консультацию"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO active_consultations (client_id, client_username, client_name, initial_message)
                VALUES (?, ?, ?, ?)
            ''', (client_id, client_username, client_name, initial_message))
            
            consultation_id = cursor.lastrowid
            conn.commit()
            return consultation_id
        except Exception as e:
            logger.error(f"Error creating consultation: {e}")
            return None
        finally:
            conn.close()
    
    def assign_doctor_to_consultation(self, consultation_id, doctor_id):
        """Назначить врача на консультацию"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE active_consultations 
                SET doctor_id = ?, status = 'assigned'
                WHERE id = ? AND status = 'waiting'
            ''', (doctor_id, consultation_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error assigning doctor: {e}")
            return False
        finally:
            conn.close()
    
    def add_consultation_message(self, consultation_id, sender_type, sender_id, sender_name, message_text, telegram_message_id=None):
        """Добавить сообщение в консультацию"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO consultation_messages 
                (consultation_id, sender_type, sender_id, sender_name, message_text, telegram_message_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (consultation_id, sender_type, sender_id, sender_name, message_text, telegram_message_id))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding consultation message: {e}")
            return None
        finally:
            conn.close()

class VetDoctorBot:
    def __init__(self):
        self.application = Application.builder().token(VET_BOT_TOKEN).build()
        self.db = VetDoctorDatabase()
        self.setup_handlers()
        
        # Состояния регистрации
        self.registration_states = {}
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("profile", self.show_profile))
        self.application.add_handler(CommandHandler("consultations", self.show_consultations))
        
        # Обработчики кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Обработчик фотографий
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        doctor = self.db.get_doctor(user.id)
        
        if doctor:
            # Врач уже зарегистрирован
            if doctor[5]:  # is_approved
                await update.message.reply_text(
                    f"👨‍⚕️ Добро пожаловать, доктор {doctor[3]}!\n\n"
                    "✅ Ваш профиль одобрен администратором\n"
                    "🔔 Вы будете получать уведомления о новых клиентах\n\n"
                    "Команды:\n"
                    "/profile - Ваш профиль\n"
                    "/consultations - Активные консультации"
                )
            else:
                await update.message.reply_text(
                    f"👨‍⚕️ Здравствуйте, доктор {doctor[3]}!\n\n"
                    "⏳ Ваш профиль ожидает одобрения администратором\n"
                    "📧 Мы уведомим вас, когда профиль будет активирован"
                )
        else:
            # Новый врач - начинаем регистрацию
            keyboard = [
                [InlineKeyboardButton("📝 Зарегистрироваться как врач", callback_data="register_doctor")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "👋 Добро пожаловать в систему для ветеринарных врачей!\n\n"
                "🏥 Этот бот предназначен для врачей, которые хотят консультировать клиентов\n"
                "📋 Для работы необходимо пройти регистрацию и получить одобрение администратора\n\n"
                "Нажмите кнопку ниже для начала регистрации:",
                reply_markup=reply_markup
            )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "register_doctor":
            await self.start_registration(query, context)
        elif query.data.startswith("take_client_"):
            consultation_id = int(query.data.split("_")[2])
            await self.take_client(query, context, consultation_id)
    
    async def start_registration(self, query, context):
        """Начать регистрацию врача"""
        user = query.from_user
        self.registration_states[user.id] = {"step": "waiting_name"}
        
        await query.edit_message_text(
            "📝 Регистрация врача\n\n"
            "👤 Пожалуйста, введите ваше полное имя (ФИО):\n"
            "Например: Иванов Иван Иванович"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        
        # Проверяем, находится ли пользователь в процессе регистрации
        if user.id in self.registration_states:
            await self.handle_registration_step(update, context)
            return
        
        # Проверяем, ведет ли врач активную консультацию
        doctor = self.db.get_doctor(user.id)
        if doctor and doctor[5]:  # approved doctor
            # Ищем активную консультацию врача
            active_consultation = self.get_doctor_active_consultation(doctor[0])
            
            if active_consultation:
                # Врач ведет консультацию - пересылаем сообщение клиенту
                message_text = update.message.text
                client_id = active_consultation['client_id']
                
                # Отправляем сообщение клиенту
                success = await notification_system.send_message_to_client(
                    client_id, 
                    message_text, 
                    from_doctor=doctor[3]
                )
                
                if success:
                    # Сохраняем сообщение в историю консультации
                    notification_system.add_consultation_message(
                        active_consultation['id'], 
                        'doctor', 
                        user.id, 
                        doctor[3], 
                        message_text
                    )
                    
                    await update.message.reply_text("✅ Сообщение передано клиенту")
                else:
                    await update.message.reply_text("❌ Ошибка отправки сообщения клиенту")
                
                return
        
        await update.message.reply_text(
            "ℹ️ Используйте команды:\n"
            "/profile - Ваш профиль\n"
            "/consultations - Активные консультации"
        )
    
    def get_doctor_active_consultation(self, doctor_id):
        """Получить активную консультацию врача"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM active_consultations 
            WHERE doctor_id = ? AND status = 'active'
            ORDER BY started_at DESC LIMIT 1
        ''', (doctor_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['id', 'client_id', 'doctor_id', 'consultation_id', 'started_at', 
                      'status', 'client_username', 'client_name', 'initial_message']
            return dict(zip(columns, result))
        return None
    
    async def handle_registration_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка шагов регистрации"""
        user = update.effective_user
        state = self.registration_states.get(user.id, {})
        
        if state.get("step") == "waiting_name":
            full_name = update.message.text.strip()
            
            if len(full_name) < 5:
                await update.message.reply_text(
                    "❌ Пожалуйста, введите полное имя (минимум 5 символов)"
                )
                return
            
            self.registration_states[user.id] = {
                "step": "waiting_photo",
                "full_name": full_name
            }
            
            await update.message.reply_text(
                f"✅ Имя сохранено: {full_name}\n\n"
                "📸 Теперь отправьте вашу фотографию\n"
                "(это поможет клиентам узнать своего врача)"
            )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        user = update.effective_user
        state = self.registration_states.get(user.id, {})
        
        if state.get("step") == "waiting_photo":
            # Сохраняем фотографию
            photo = update.message.photo[-1]  # Берем фото наибольшего размера
            
            try:
                # Создаем директорию для фотографий врачей
                os.makedirs("doctor_photos", exist_ok=True)
                
                # Скачиваем фото
                file = await context.bot.get_file(photo.file_id)
                photo_path = f"doctor_photos/{user.id}_{photo.file_id}.jpg"
                await file.download_to_drive(photo_path)
                
                # Регистрируем врача в базе данных
                full_name = state["full_name"]
                doctor_id = self.db.register_doctor(
                    telegram_id=user.id,
                    username=user.username,
                    full_name=full_name,
                    photo_path=photo_path
                )
                
                if doctor_id:
                    # Удаляем состояние регистрации
                    del self.registration_states[user.id]
                    
                    await update.message.reply_text(
                        "🎉 Регистрация завершена!\n\n"
                        f"👤 Имя: {full_name}\n"
                        f"📸 Фотография: сохранена\n"
                        f"📧 Username: @{user.username or 'не указан'}\n\n"
                        "⏳ Ваш профиль отправлен на модерацию администратору\n"
                        "📧 Мы уведомим вас, когда профиль будет одобрен\n\n"
                        "Используйте /profile для просмотра статуса"
                    )
                    
                    # TODO: Уведомить администратора о новом враче
                    
                else:
                    await update.message.reply_text(
                        "❌ Произошла ошибка при регистрации. Попробуйте еще раз."
                    )
                    
            except Exception as e:
                logger.error(f"Error saving doctor photo: {e}")
                await update.message.reply_text(
                    "❌ Ошибка при сохранении фотографии. Попробуйте еще раз."
                )
        else:
            await update.message.reply_text(
                "ℹ️ Отправьте фотографию только во время регистрации"
            )
    
    async def show_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать профиль врача"""
        user = update.effective_user
        doctor = self.db.get_doctor(user.id)
        
        if not doctor:
            await update.message.reply_text(
                "❌ Вы не зарегистрированы как врач\n"
                "Используйте /start для регистрации"
            )
            return
        
        status = "✅ Одобрен" if doctor[5] else "⏳ На модерации"
        active = "🟢 Активен" if doctor[6] else "🔴 Неактивен"
        
        profile_text = f"""
👨‍⚕️ **Профиль врача**

👤 **Имя:** {doctor[3]}
📧 **Username:** @{doctor[2] or 'не указан'}
📊 **Статус:** {status}
🔄 **Активность:** {active}
📅 **Регистрация:** {doctor[7][:16]}
⏰ **Последняя активность:** {doctor[8][:16]}
        """
        
        if doctor[4]:  # photo_path
            try:
                with open(doctor[4], 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=profile_text,
                        parse_mode='Markdown'
                    )
            except:
                await update.message.reply_text(profile_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(profile_text, parse_mode='Markdown')
    
    async def show_consultations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать активные консультации"""
        user = update.effective_user
        doctor = self.db.get_doctor(user.id)
        
        if not doctor or not doctor[5]:  # not approved
            await update.message.reply_text(
                "❌ Ваш профиль не одобрен администратором"
            )
            return
        
        # TODO: Показать активные консультации врача
        await update.message.reply_text(
            "📋 Активные консультации\n\n"
            "🔄 Функция в разработке..."
        )
    
    async def take_client(self, query, context, consultation_id):
        """Взять клиента на консультацию"""
        user = query.from_user
        doctor = self.db.get_doctor(user.id)
        
        if not doctor or not doctor[5]:  # not approved
            await query.edit_message_text(
                "❌ Ваш профиль не одобрен для работы с клиентами"
            )
            return
        
        # Попытаться назначить врача на консультацию через систему уведомлений
        success, message = await notification_system.assign_doctor_to_consultation(consultation_id, user.id)
        
        if success:
            await query.edit_message_text(
                f"✅ Вы взяли клиента на консультацию!\n"
                f"👨‍⚕️ Врач: {doctor[3]}\n"
                f"📋 Консультация #{consultation_id}\n\n"
                "💬 Теперь вы можете общаться с клиентом. Все ваши сообщения будут переданы клиенту."
            )
            
            # Получаем информацию о консультации
            consultation_info = notification_system.get_consultation_info(consultation_id)
            if consultation_info:
                # Отправляем историю диалога врачу
                history = notification_system.get_consultation_history(consultation_id)
                if history:
                    history_text = "📖 **История диалога с клиентом:**\n\n"
                    for sender_type, sender_name, message_text, sent_at in history:
                        icon = {'client': '👤', 'ai': '🤖', 'admin': '👨‍💼'}.get(sender_type, '❓')
                        history_text += f"{icon} **{sender_name}:** {message_text}\n\n"
                    
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=history_text,
                        parse_mode='Markdown'
                    )
                
                # Уведомляем клиента о подключении врача
                client_id = consultation_info[1]  # client_id
                await notification_system.send_message_to_client(
                    client_id,
                    f"👨‍⚕️ К диалогу подключился врач **{doctor[3]}**!\n\n"
                    "Теперь вы можете задавать вопросы напрямую врачу. "
                    "Все ваши сообщения будут переданы врачу, а ответы врача - вам.",
                    from_doctor=doctor[3]
                )
                
                # Обновляем статус консультации на 'active'
                self.update_consultation_status(consultation_id, 'active')
            
        else:
            await query.edit_message_text(f"❌ {message}")
    
    def update_consultation_status(self, consultation_id, status):
        """Обновить статус консультации"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE active_consultations 
                SET status = ?
                WHERE id = ?
            ''', (status, consultation_id))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating consultation status: {e}")
        finally:
            conn.close()
    
    def run(self):
        """Запуск бота"""
        print(f"""
👨‍⚕️ Бот для ветеринарных врачей v{VERSION} запускается...
🔧 Функции: регистрация врачей, консультации
🏥 Специализация: ветеринария
        """)
        
        self.application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot = VetDoctorBot()
    bot.run()

