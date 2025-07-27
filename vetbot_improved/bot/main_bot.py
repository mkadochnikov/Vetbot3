"""
Основной бот для ветеринарных консультаций
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable
from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, CallbackQueryHandler
)

from vetbot_improved.config import TELEGRAM_BOT_TOKEN, WEBAPP_URL, VERSION
from vetbot_improved.database.base import get_db
from vetbot_improved.models import (
    User, Consultation, ActiveConsultation, 
    ConsultationMessage, VetCall
)
from vetbot_improved.services.ai_service import AIService
from vetbot_improved.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class MainBot:
    """Основной бот для ветеринарных консультаций"""
    
    def __init__(self):
        """Инициализация бота"""
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.notification_service = NotificationService()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("version", self.version_command))
        
        # Обработчики кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Обработчик веб-приложения
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.web_app_data))
        
        # Обработчик текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Обработчик ошибок
        self.application.add_error_handler(self.error_handler)
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Сохраняем пользователя в базу данных
        db = next(get_db())
        try:
            db_user = db.query(User).filter(User.user_id == user.id).first()
            
            if not db_user:
                db_user = User(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                db.add(db_user)
                db.commit()
                logger.info(f"New user registered: {user.id} - {user.username or user.first_name}")
            
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [
                InlineKeyboardButton("🏥 Вызвать врача", web_app=WebAppInfo(url=WEBAPP_URL))
            ],
            [
                InlineKeyboardButton("❓ Задать вопрос", callback_data="ask_question"),
                InlineKeyboardButton("ℹ️ О сервисе", callback_data="about")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение
        await update.message.reply_html(
            f"Привет, <b>{user.first_name}</b>! 👋\n\n"
            f"Я ветеринарный бот для консультаций по здоровью кошек. "
            f"Вы можете задать мне вопрос или вызвать врача на дом.\n\n"
            f"🤖 <b>Версия:</b> {VERSION}",
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
🐱 <b>Ветеринарный бот - Помощь</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать это сообщение
/version - Показать версию бота

<b>Возможности:</b>
• 🤖 <b>AI-консультация</b> - Задайте вопрос о здоровье кошки
• 🏥 <b>Вызов врача</b> - Оформите заявку на вызов ветеринара
• 👨‍⚕️ <b>Консультация с врачом</b> - После AI-ответа ваш вопрос будет передан живым врачам

<b>Как пользоваться:</b>
1. Просто напишите свой вопрос о здоровье кошки
2. Получите ответ от AI
3. Дождитесь, когда живой врач подключится к диалогу
4. Для вызова врача на дом нажмите кнопку "Вызвать врача"

⚠️ <b>Важно:</b> Бот не заменяет визит к ветеринару. При серьезных проблемах обязательно обратитесь в клинику!
        """
        
        await update.message.reply_html(help_text)
    
    async def version_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /version"""
        await update.message.reply_text(f"🤖 Ветеринарный бот v{VERSION}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "ask_question":
            await query.message.reply_text(
                "🐱 Пожалуйста, опишите проблему или задайте вопрос о здоровье вашей кошки.\n\n"
                "Например:\n"
                "- Кошка не ест второй день, что делать?\n"
                "- У кота слезятся глаза и чихает\n"
                "- Какие прививки нужны котенку?"
            )
        
        elif query.data == "about":
            about_text = f"""
🐱 <b>О сервисе "Ветеринарный бот"</b>

Наш сервис предоставляет:
• 🤖 <b>AI-консультации</b> по здоровью кошек
• 👨‍⚕️ <b>Консультации с живыми ветеринарами</b>
• 🏥 <b>Вызов ветеринара на дом</b>

<b>Как это работает:</b>
1. Вы задаете вопрос о здоровье кошки
2. AI дает первичную консультацию
3. Ваш вопрос передается команде ветеринаров
4. Врач подключается к диалогу для более детальной консультации

<b>Наши преимущества:</b>
• Быстрый ответ 24/7
• Профессиональные ветеринары
• Удобный интерфейс
• Конфиденциальность данных

<b>Версия:</b> {VERSION}
            """
            
            await query.message.reply_html(about_text)
    
    async def web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик данных из веб-приложения"""
        data = update.effective_message.web_app_data.data
        user = update.effective_user
        
        try:
            import json
            call_data = json.loads(data)
            
            # Добавляем ID пользователя
            call_data["user_id"] = user.id
            
            # Сохраняем заявку в базу данных
            db = next(get_db())
            try:
                vet_call = VetCall(
                    user_id=user.id,
                    name=call_data.get("name", ""),
                    phone=call_data.get("phone", ""),
                    address=call_data.get("address", ""),
                    pet_type=call_data.get("pet_type", ""),
                    pet_name=call_data.get("pet_name", ""),
                    pet_age=call_data.get("pet_age", ""),
                    problem=call_data.get("problem", ""),
                    urgency=call_data.get("urgency", ""),
                    preferred_time=call_data.get("preferred_time", ""),
                    comments=call_data.get("comments", "")
                )
                db.add(vet_call)
                db.commit()
                
                # Отправляем подтверждение
                await update.message.reply_html(
                    f"✅ <b>Заявка на вызов ветеринара успешно отправлена!</b>\n\n"
                    f"📋 <b>Номер заявки:</b> {vet_call.id}\n"
                    f"👤 <b>Имя:</b> {call_data.get('name')}\n"
                    f"📞 <b>Телефон:</b> {call_data.get('phone')}\n"
                    f"🏠 <b>Адрес:</b> {call_data.get('address')}\n\n"
                    f"Наш оператор свяжется с вами в ближайшее время для подтверждения заявки."
                )
                
                logger.info(f"New vet call request: {vet_call.id} from user {user.id}")
                
            except Exception as e:
                logger.error(f"Error saving vet call: {e}")
                db.rollback()
                await update.message.reply_text(
                    "❌ Произошла ошибка при сохранении заявки. Пожалуйста, попробуйте еще раз."
                )
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error processing web app data: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке данных. Пожалуйста, попробуйте еще раз."
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user = update.effective_user
        message_text = update.message.text
        
        # Проверяем, есть ли активная консультация с врачом
        db = next(get_db())
        try:
            active_consultation = db.query(ActiveConsultation).filter(
                ActiveConsultation.client_id == user.id,
                ActiveConsultation.status.in_(["assigned", "active"])
            ).first()
            
            if active_consultation and active_consultation.doctor_id:
                # Получаем информацию о враче
                doctor = db.query(Doctor).filter(Doctor.id == active_consultation.doctor_id).first()
                
                if doctor:
                    # Сохраняем сообщение в базу данных
                    message = ConsultationMessage(
                        consultation_id=active_consultation.id,
                        sender_type="client",
                        sender_id=user.id,
                        sender_name=user.username or user.first_name,
                        message_text=message_text,
                        telegram_message_id=update.message.message_id
                    )
                    db.add(message)
                    db.commit()
                    
                    # Отправляем сообщение врачу
                    await self.notification_service.send_message_to_doctor(
                        doctor.telegram_id,
                        message_text,
                        from_client=user.username or user.first_name
                    )
                    
                    return
            
            # Если нет активной консультации, обрабатываем как новый вопрос
            await update.message.reply_text(
                "🤔 Анализирую ваш вопрос... Пожалуйста, подождите."
            )
            
            # Получаем ответ от AI
            ai_response = await AIService.get_consultation(
                message_text, 
                user.username or user.first_name
            )
            
            # Отправляем ответ пользователю
            await update.message.reply_text(ai_response)
            
            # Сохраняем консультацию в базу данных
            consultation = Consultation(
                user_id=user.id,
                question=message_text,
                response=ai_response,
                consultation_status="waiting_doctor"
            )
            db.add(consultation)
            db.commit()
            
            # Создаем активную консультацию
            active_consultation = ActiveConsultation(
                client_id=user.id,
                consultation_id=consultation.id,
                client_username=user.username,
                client_name=user.first_name,
                initial_message=message_text,
                status="waiting"
            )
            db.add(active_consultation)
            db.commit()
            
            # Сохраняем сообщения в историю консультации
            client_message = ConsultationMessage(
                consultation_id=active_consultation.id,
                sender_type="client",
                sender_id=user.id,
                sender_name=user.username or user.first_name,
                message_text=message_text,
                telegram_message_id=update.message.message_id
            )
            db.add(client_message)
            
            ai_message = ConsultationMessage(
                consultation_id=active_consultation.id,
                sender_type="ai",
                sender_id=None,
                sender_name="AI",
                message_text=ai_response
            )
            db.add(ai_message)
            db.commit()
            
            # Уведомляем врачей о новом клиенте
            await self.notification_service.notify_doctors_about_client(
                db,
                active_consultation.id,
                user.username or user.first_name,
                message_text
            )
            
            # Отправляем сообщение о том, что вопрос передан врачам
            await update.message.reply_text(
                "👨‍⚕️ Ваш вопрос передан нашим ветеринарам. "
                "Как только один из них освободится, он подключится к диалогу."
            )
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            db.rollback()
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке сообщения. Пожалуйста, попробуйте еще раз."
            )
        finally:
            db.close()
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик ошибок"""
        logger.error(f"Exception while handling an update: {context.error}")
    
    async def run(self):
        """Запуск бота"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info(f"Bot started. Version: {VERSION}")
        
        try:
            # Держим бота запущенным до прерывания
            await self.application.updater.stop_on_signal()
        finally:
            await self.application.stop()
            await self.application.shutdown()
            
            logger.info("Bot stopped")

def main():
    """Основная функция для запуска бота"""
    # Настройка логирования
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler('./logs/main_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    # Создание и запуск бота
    bot = MainBot()
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()