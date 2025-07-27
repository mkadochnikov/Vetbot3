"""
Сервис уведомлений между ботами
"""

import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from vetbot_improved.config import TELEGRAM_BOT_TOKEN, VET_BOT_TOKEN
from vetbot_improved.models import (
    Doctor, ActiveConsultation, DoctorNotification
)

logger = logging.getLogger(__name__)

class NotificationService:
    """Сервис уведомлений между ботами"""
    
    def __init__(self):
        """Инициализация сервиса уведомлений"""
        self.main_bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None
        self.vet_bot = Bot(token=VET_BOT_TOKEN) if VET_BOT_TOKEN else None
    
    def get_approved_doctors(self, db: Session) -> List[Tuple[int, str]]:
        """
        Получить список одобренных врачей
        
        Args:
            db: Сессия базы данных
            
        Returns:
            List[Tuple[int, str]]: Список кортежей (telegram_id, full_name)
        """
        doctors = db.query(Doctor).filter(
            Doctor.is_approved == True,
            Doctor.is_active == True
        ).all()
        
        return [(doctor.telegram_id, doctor.full_name) for doctor in doctors]
    
    async def notify_doctors_about_client(
        self, 
        db: Session,
        consultation_id: int, 
        client_name: str, 
        initial_message: str
    ) -> bool:
        """
        Уведомить всех врачей о новом клиенте
        
        Args:
            db: Сессия базы данных
            consultation_id: ID консультации
            client_name: Имя клиента
            initial_message: Начальное сообщение
            
        Returns:
            bool: Успешность отправки уведомлений
        """
        if not self.vet_bot:
            logger.error("VET_BOT_TOKEN not configured")
            return False
        
        doctors = self.get_approved_doctors(db)
        if not doctors:
            logger.warning("No approved doctors found")
            return False
        
        # Создаем кнопку для взятия клиента
        keyboard = [
            [InlineKeyboardButton("👨‍⚕️ Взять клиента", callback_data=f"take_client_{consultation_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        notification_text = f"""
🔔 **Новый клиент ждет консультации!**

👤 **Клиент:** {client_name}
💬 **Вопрос:** {initial_message[:200]}{'...' if len(initial_message) > 200 else ''}
⏰ **Время:** {datetime.now().strftime('%H:%M')}

Кто первый нажмет кнопку - за тем закрепится клиент.
        """
        
        successful_notifications = 0
        
        # Отправляем уведомления всем врачам
        for doctor_telegram_id, doctor_name in doctors:
            try:
                message = await self.vet_bot.send_message(
                    chat_id=doctor_telegram_id,
                    text=notification_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
                # Сохраняем уведомление в базу данных
                self._save_doctor_notification(db, consultation_id, doctor_telegram_id, message.message_id)
                successful_notifications += 1
                
                logger.info(f"Notification sent to doctor {doctor_name} ({doctor_telegram_id})")
                
            except Exception as e:
                logger.error(f"Failed to send notification to doctor {doctor_name}: {e}")
        
        return successful_notifications > 0
    
    def _save_doctor_notification(
        self, 
        db: Session,
        consultation_id: int, 
        doctor_telegram_id: int, 
        message_id: int
    ) -> None:
        """
        Сохранить уведомление врача в базу данных
        
        Args:
            db: Сессия базы данных
            consultation_id: ID консультации
            doctor_telegram_id: Telegram ID врача
            message_id: ID сообщения
        """
        try:
            # Получаем ID врача по telegram_id
            doctor = db.query(Doctor).filter(Doctor.telegram_id == doctor_telegram_id).first()
            
            if doctor:
                notification = DoctorNotification(
                    consultation_id=consultation_id,
                    doctor_id=doctor.id,
                    message_id=message_id
                )
                db.add(notification)
                db.commit()
        except Exception as e:
            logger.error(f"Error saving doctor notification: {e}")
            db.rollback()
    
    async def assign_doctor_to_consultation(
        self, 
        db: Session,
        consultation_id: int, 
        doctor_telegram_id: int
    ) -> Tuple[bool, str]:
        """
        Назначить врача на консультацию
        
        Args:
            db: Сессия базы данных
            consultation_id: ID консультации
            doctor_telegram_id: Telegram ID врача
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            # Получаем ID врача
            doctor = db.query(Doctor).filter(Doctor.telegram_id == doctor_telegram_id).first()
            
            if not doctor:
                return False, "Врач не найден"
            
            # Проверяем, что консультация еще не назначена
            consultation = db.query(ActiveConsultation).filter(ActiveConsultation.id == consultation_id).first()
            
            if not consultation:
                return False, "Консультация не найдена"
            
            if consultation.status != 'waiting':
                return False, "Консультация уже назначена другому врачу"
            
            # Назначаем врача
            consultation.doctor_id = doctor.id
            consultation.status = 'assigned'
            db.commit()
            
            # Отмечаем уведомление как отвеченное
            notifications = db.query(DoctorNotification).filter(
                DoctorNotification.consultation_id == consultation_id,
                DoctorNotification.doctor_id == doctor.id
            ).all()
            
            for notification in notifications:
                notification.is_responded = True
            
            db.commit()
            
            # Уведомляем других врачей, что клиент занят
            await self._notify_other_doctors_client_taken(db, consultation_id, doctor.full_name, doctor_telegram_id)
            
            return True, f"Консультация назначена врачу {doctor.full_name}"
                
        except Exception as e:
            logger.error(f"Error assigning doctor to consultation: {e}")
            db.rollback()
            return False, f"Ошибка: {e}"
    
    async def _notify_other_doctors_client_taken(
        self, 
        db: Session,
        consultation_id: int, 
        assigned_doctor_name: str, 
        assigned_doctor_telegram_id: int
    ) -> None:
        """
        Уведомить других врачей, что клиент уже взят
        
        Args:
            db: Сессия базы данных
            consultation_id: ID консультации
            assigned_doctor_name: Имя назначенного врача
            assigned_doctor_telegram_id: Telegram ID назначенного врача
        """
        if not self.vet_bot:
            return
        
        try:
            # Получаем всех врачей, которым было отправлено уведомление
            notifications = db.query(DoctorNotification, Doctor).join(
                Doctor, DoctorNotification.doctor_id == Doctor.id
            ).filter(
                DoctorNotification.consultation_id == consultation_id,
                DoctorNotification.is_responded == False,
                Doctor.telegram_id != assigned_doctor_telegram_id
            ).all()
            
            for notification, doctor in notifications:
                try:
                    # Редактируем сообщение
                    await self.vet_bot.edit_message_text(
                        chat_id=doctor.telegram_id,
                        message_id=notification.message_id,
                        text=f"❌ **Клиент уже взят**\n\n👨‍⚕️ Врач: {assigned_doctor_name}\n⏰ Время: {datetime.now().strftime('%H:%M')}",
                        parse_mode='Markdown'
                    )
                    
                    # Отмечаем уведомление как отвеченное
                    notification.is_responded = True
                    
                except Exception as e:
                    logger.error(f"Failed to update notification for doctor {doctor.full_name}: {e}")
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error notifying other doctors: {e}")
            db.rollback()
    
    async def send_message_to_client(
        self, 
        client_id: int, 
        message_text: str, 
        from_doctor: Optional[str] = None
    ) -> bool:
        """
        Отправить сообщение клиенту от врача
        
        Args:
            client_id: ID клиента
            message_text: Текст сообщения
            from_doctor: Имя врача (опционально)
            
        Returns:
            bool: Успешность отправки
        """
        if not self.main_bot:
            logger.error("MAIN_BOT_TOKEN not configured")
            return False
        
        try:
            prefix = f"👨‍⚕️ **Врач {from_doctor}:**\n\n" if from_doctor else ""
            
            await self.main_bot.send_message(
                chat_id=client_id,
                text=f"{prefix}{message_text}",
                parse_mode='Markdown'
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            return False
    
    async def send_message_to_doctor(
        self, 
        doctor_telegram_id: int, 
        message_text: str, 
        from_client: Optional[str] = None
    ) -> bool:
        """
        Отправить сообщение врачу от клиента
        
        Args:
            doctor_telegram_id: Telegram ID врача
            message_text: Текст сообщения
            from_client: Имя клиента (опционально)
            
        Returns:
            bool: Успешность отправки
        """
        if not self.vet_bot:
            logger.error("VET_BOT_TOKEN not configured")
            return False
        
        try:
            prefix = f"👤 **Клиент {from_client}:**\n\n" if from_client else ""
            
            await self.vet_bot.send_message(
                chat_id=doctor_telegram_id,
                text=f"{prefix}{message_text}",
                parse_mode='Markdown'
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to send message to doctor {doctor_telegram_id}: {e}")
            return False