"""
Система уведомлений между основным ботом и ботом врачей
"""

import os
import json
import logging
import sqlite3
import asyncio
import requests
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
MAIN_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
VET_BOT_TOKEN = os.getenv('VET_BOT_TOKEN')

class NotificationSystem:
    """Система уведомлений между ботами"""
    
    def __init__(self, db_path='vetbot.db'):
        self.db_path = db_path
        self.main_bot = Bot(token=MAIN_BOT_TOKEN) if MAIN_BOT_TOKEN else None
        self.vet_bot = Bot(token=VET_BOT_TOKEN) if VET_BOT_TOKEN else None
    
    def get_approved_doctors(self):
        """Получить список одобренных врачей"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, full_name FROM doctors 
            WHERE is_approved = 1 AND is_active = 1
        ''')
        
        result = cursor.fetchall()
        conn.close()
        return result
    
    def create_consultation_request(self, client_id, client_username, client_name, initial_message):
        """Создать запрос на консультацию"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Создаем активную консультацию
            cursor.execute('''
                INSERT INTO active_consultations 
                (client_id, client_username, client_name, initial_message)
                VALUES (?, ?, ?, ?)
            ''', (client_id, client_username, client_name, initial_message))
            
            consultation_id = cursor.lastrowid
            conn.commit()
            return consultation_id
        except Exception as e:
            logger.error(f"Error creating consultation request: {e}")
            return None
        finally:
            conn.close()
    
    async def notify_doctors_about_client(self, consultation_id, client_name, initial_message):
        """Уведомить всех врачей о новом клиенте"""
        if not self.vet_bot:
            logger.error("VET_BOT_TOKEN not configured")
            return False
        
        doctors = self.get_approved_doctors()
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
                self.save_doctor_notification(consultation_id, doctor_telegram_id, message.message_id)
                successful_notifications += 1
                
                logger.info(f"Notification sent to doctor {doctor_name} ({doctor_telegram_id})")
                
            except Exception as e:
                logger.error(f"Failed to send notification to doctor {doctor_name}: {e}")
        
        return successful_notifications > 0
    
    def save_doctor_notification(self, consultation_id, doctor_telegram_id, message_id):
        """Сохранить уведомление врача в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Получаем ID врача по telegram_id
            cursor.execute('SELECT id FROM doctors WHERE telegram_id = ?', (doctor_telegram_id,))
            doctor_row = cursor.fetchone()
            
            if doctor_row:
                doctor_id = doctor_row[0]
                cursor.execute('''
                    INSERT INTO doctor_notifications 
                    (consultation_id, doctor_id, message_id)
                    VALUES (?, ?, ?)
                ''', (consultation_id, doctor_id, message_id))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving doctor notification: {e}")
        finally:
            conn.close()
    
    async def assign_doctor_to_consultation(self, consultation_id, doctor_telegram_id):
        """Назначить врача на консультацию"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Получаем ID врача
            cursor.execute('SELECT id, full_name FROM doctors WHERE telegram_id = ?', (doctor_telegram_id,))
            doctor_row = cursor.fetchone()
            
            if not doctor_row:
                return False, "Врач не найден"
            
            doctor_id, doctor_name = doctor_row
            
            # Проверяем, что консультация еще не назначена
            cursor.execute('''
                SELECT status FROM active_consultations WHERE id = ?
            ''', (consultation_id,))
            
            consultation_row = cursor.fetchone()
            if not consultation_row:
                return False, "Консультация не найдена"
            
            if consultation_row[0] != 'waiting':
                return False, "Консультация уже назначена другому врачу"
            
            # Назначаем врача
            cursor.execute('''
                UPDATE active_consultations 
                SET doctor_id = ?, status = 'assigned'
                WHERE id = ? AND status = 'waiting'
            ''', (doctor_id, consultation_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                
                # Отмечаем уведомление как отвеченное
                cursor.execute('''
                    UPDATE doctor_notifications 
                    SET is_responded = 1
                    WHERE consultation_id = ? AND doctor_id = ?
                ''', (consultation_id, doctor_id))
                
                conn.commit()
                
                # Уведомляем других врачей, что клиент занят
                await self.notify_other_doctors_client_taken(consultation_id, doctor_name, doctor_telegram_id)
                
                return True, f"Консультация назначена врачу {doctor_name}"
            else:
                return False, "Не удалось назначить консультацию"
                
        except Exception as e:
            logger.error(f"Error assigning doctor to consultation: {e}")
            return False, f"Ошибка: {e}"
        finally:
            conn.close()
    
    async def notify_other_doctors_client_taken(self, consultation_id, assigned_doctor_name, assigned_doctor_telegram_id):
        """Уведомить других врачей, что клиент уже взят"""
        if not self.vet_bot:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Получаем всех врачей, которым было отправлено уведомление
            cursor.execute('''
                SELECT dn.doctor_id, dn.message_id, d.telegram_id, d.full_name
                FROM doctor_notifications dn
                JOIN doctors d ON dn.doctor_id = d.id
                WHERE dn.consultation_id = ? AND dn.is_responded = 0 AND d.telegram_id != ?
            ''', (consultation_id, assigned_doctor_telegram_id))
            
            notifications = cursor.fetchall()
            
            for doctor_id, message_id, doctor_telegram_id, doctor_name in notifications:
                try:
                    # Редактируем сообщение
                    await self.vet_bot.edit_message_text(
                        chat_id=doctor_telegram_id,
                        message_id=message_id,
                        text=f"❌ **Клиент уже взят**\n\n👨‍⚕️ Врач: {assigned_doctor_name}\n⏰ Время: {datetime.now().strftime('%H:%M')}",
                        parse_mode='Markdown'
                    )
                    
                    # Отмечаем уведомление как отвеченное
                    cursor.execute('''
                        UPDATE doctor_notifications 
                        SET is_responded = 1
                        WHERE id = (SELECT id FROM doctor_notifications WHERE consultation_id = ? AND doctor_id = ? LIMIT 1)
                    ''', (consultation_id, doctor_id))
                    
                except Exception as e:
                    logger.error(f"Failed to update notification for doctor {doctor_name}: {e}")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error notifying other doctors: {e}")
        finally:
            conn.close()
    
    async def send_message_to_client(self, client_id, message_text, from_doctor=None):
        """Отправить сообщение клиенту от врача"""
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
    
    async def send_message_to_doctor(self, doctor_telegram_id, message_text, from_client=None):
        """Отправить сообщение врачу от клиента"""
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
    
    def get_consultation_info(self, consultation_id):
        """Получить информацию о консультации"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ac.*, d.telegram_id, d.full_name
            FROM active_consultations ac
            LEFT JOIN doctors d ON ac.doctor_id = d.id
            WHERE ac.id = ?
        ''', (consultation_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result
    
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
    
    def get_consultation_history(self, consultation_id):
        """Получить историю сообщений консультации"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sender_type, sender_name, message_text, sent_at
            FROM consultation_messages
            WHERE consultation_id = ?
            ORDER BY sent_at ASC
        ''', (consultation_id,))
        
        result = cursor.fetchall()
        conn.close()
        return result

# Глобальный экземпляр системы уведомлений
notification_system = NotificationSystem()

