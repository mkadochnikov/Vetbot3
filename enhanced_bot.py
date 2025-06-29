#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Профессиональный ветеринарный бот с веб-приложением для вызова врача
Специализация: фелинология (лечение кошек)
"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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
BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-webapp-url.com')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
VET_SERVICE_PHONE = os.getenv('VET_SERVICE_PHONE', '+7-999-123-45-67')

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

class ProfessionalVetBot:
    """Профессиональный ветеринарный бот-фелинолог"""
    
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.db = VetBotDatabase()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("webapp", self.webapp_command))
        self.application.add_handler(CommandHandler("my_calls", self.my_calls_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        
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
            [InlineKeyboardButton("🩺 Консультация фелинолога", callback_data='consultation')],
            [InlineKeyboardButton("📱 Вызвать врача", web_app=WebAppInfo(url=WEBAPP_URL))],
            [InlineKeyboardButton("📋 Мои заявки", callback_data='my_calls')],
            [InlineKeyboardButton("📞 Контакты", callback_data='contact')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = f"""
🐾 Добро пожаловать, {user.first_name}!

Я ветеринарный врач-фелинолог с 15-летним стажем работы с кошками.

Мои услуги:
• Профессиональная консультация по здоровью кошек
• Вызов ветеринара на дом для осмотра
• Диагностика и лечение заболеваний кошек
• Рекомендации по уходу и содержанию

Выберите нужную услугу:
        """
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = f"""
🆘 Справка по работе с ветеринаром-фелинологом:

📋 Команды:
/start - Главное меню
/help - Эта справка
/webapp - Открыть форму вызова врача
/my_calls - Мои заявки на вызов врача
/contact - Контактная информация

🩺 Мои специализации:
• Диагностика заболеваний кошек всех пород
• Лечение инфекционных и паразитарных болезней
• Консультации по питанию и уходу за кошками
• Вакцинация и профилактические осмотры
• Помощь котятам и пожилым кошкам

⚠️ Экстренные случаи:
При критическом состоянии кошки звоните: {VET_SERVICE_PHONE}

Стаж работы: 15 лет специализации на кошках
        """
        await update.message.reply_text(help_text)
    
    async def webapp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для открытия веб-приложения"""
        keyboard = [[InlineKeyboardButton("📱 Вызвать ветеринара-фелинолога", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Нажмите кнопку ниже, чтобы вызвать ветеринара-фелинолога на дом:",
            reply_markup=reply_markup
        )
    
    async def my_calls_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для просмотра заявок пользователя"""
        user_id = update.effective_user.id
        calls = self.db.get_user_calls(user_id)
        
        if not calls:
            await update.message.reply_text("У вас пока нет заявок на вызов ветеринара.")
            return
        
        response = "📋 Ваши заявки на вызов ветеринара-фелинолога:\n\n"
        
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
📞 Контакты ветеринара-фелинолога:

👨‍⚕️ Врач-фелинолог
📱 Телефон: {VET_SERVICE_PHONE}
📧 Email: {os.getenv('VET_SERVICE_EMAIL', 'felinolog@vetservice.com')}

🕐 Режим работы:
• Консультации в боте: 8:00-22:00
• Экстренные вызовы: круглосуточно
• Плановые осмотры: 9:00-20:00

💰 Стоимость услуг:
• Консультация в боте: бесплатно
• Выезд на дом: от 2000 руб.
• Экстренный вызов: от 3500 руб.
• Комплексный осмотр кошки: от 1500 руб.

🎓 Квалификация: 15 лет специализации на кошках
        """
        
        await update.message.reply_text(contact_text)
    
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
    
    async def start_consultation(self, query):
        """Начать консультацию с фелинологом"""
        consultation_text = """
🩺 Консультация ветеринара-фелинолога

Как врач с 15-летним опытом работы с кошками, для качественной консультации мне нужна следующая информация:

1️⃣ **Порода и возраст кошки** (важно для диагностики)
2️⃣ **Вес кошки** (для расчета дозировок)
3️⃣ **Подробное описание симптомов**
4️⃣ **Длительность проблемы**
5️⃣ **Изменения в поведении, аппетите**
6️⃣ **Что уже предпринимали для лечения**
7️⃣ **Вакцинации и обработки от паразитов**

Опишите состояние вашей кошки в следующем сообщении.

⚠️ Помните: онлайн-консультация дает профессиональные рекомендации, но не заменяет очного осмотра при серьезных состояниях!
        """
        
        keyboard = [[InlineKeyboardButton("📱 Вызвать на дом для осмотра", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(consultation_text, reply_markup=reply_markup)
    
    async def show_help(self, query):
        """Показать помощь"""
        help_text = """
🆘 Помощь по работе с ветеринаром-фелинологом:

🔹 **Консультация** - получите профессиональную консультацию по здоровью кошки от врача с 15-летним стажем
🔹 **Вызвать врача** - закажите выезд ветеринара-фелинолога на дом
🔹 **Мои заявки** - отслеживайте статус ваших вызовов
🔹 **Контакты** - получите контактную информацию врача

🎓 **Моя специализация:**
• Все породы кошек (персы, британцы, мейн-куны и др.)
• Котята от рождения до года
• Взрослые и пожилые кошки
• Инфекционные заболевания кошек
• Паразитарные инвазии
• Проблемы ЖКТ и мочеполовой системы

⚠️ В экстренных случаях звоните напрямую!

Работаю 24/7 для здоровья ваших кошек.
        """
        await query.edit_message_text(help_text)
    
    async def show_my_calls(self, query):
        """Показать заявки пользователя"""
        user_id = query.from_user.id
        calls = self.db.get_user_calls(user_id)
        
        if not calls:
            await query.edit_message_text("У вас пока нет заявок на вызов ветеринара.")
            return
        
        response = "📋 Ваши заявки к ветеринару-фелинологу:\n\n"
        
        for call in calls[:3]:  # Показываем последние 3 заявки
            call_id, user_id, name, phone, address, pet_type, pet_name, pet_age, problem, urgency, preferred_time, comments, status, created_at = call
            
            status_emoji = {
                'pending': '⏳ Ожидает подтверждения',
                'confirmed': '✅ Подтверждена врачом',
                'in_progress': '🚗 Врач в пути',
                'completed': '✅ Осмотр завершен',
                'cancelled': '❌ Отменена'
            }.get(status, '❓ Неизвестно')
            
            response += f"#{call_id} - {status_emoji}\n"
            response += f"🐾 {pet_type}\n"
            response += f"📅 {created_at[:16]}\n\n"
        
        await query.edit_message_text(response)
    
    async def show_contact(self, query):
        """Показать контакты"""
        contact_text = f"""
📞 Контакты ветеринара-фелинолога:

👨‍⚕️ Врач-специалист по кошкам
📱 {VET_SERVICE_PHONE}
📧 {os.getenv('VET_SERVICE_EMAIL', 'felinolog@vetservice.com')}

🎓 Стаж: 15 лет работы с кошками
🏥 Специализация: фелинология

🕐 Режим работы:
Консультации: 8:00-22:00
Вызовы: круглосуточно
        """
        await query.edit_message_text(contact_text)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений - профессиональные консультации"""
        user_message = update.message.text.lower()
        
        # Профессиональный анализ сообщения
        if any(word in user_message for word in ['болит', 'боль', 'плохо', 'больной', 'температура', 'рвота', 'понос', 'кашель']):
            response = self.get_professional_symptom_advice(user_message)
        elif any(word in user_message for word in ['котенок', 'маленький', 'малыш']):
            response = self.get_kitten_advice()
        elif any(word in user_message for word in ['кормление', 'корм', 'еда', 'питание']):
            response = self.get_cat_feeding_advice()
        elif any(word in user_message for word in ['прививка', 'вакцинация', 'прививки']):
            response = self.get_cat_vaccination_advice()
        elif any(word in user_message for word in ['британец', 'перс', 'мейн-кун', 'сфинкс', 'порода']):
            response = self.get_breed_specific_advice()
        else:
            response = self.get_professional_general_advice()
        
        keyboard = [[InlineKeyboardButton("📱 Вызвать на дом", web_app=WebAppInfo(url=WEBAPP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(response, reply_markup=reply_markup)
    
    def get_professional_symptom_advice(self, message):
        """Профессиональные советы по симптомам у кошек"""
        return """
🩺 **Анализ симптомов (врач-фелинолог):**

На основе 15-летнего опыта работы с кошками рекомендую:

🔍 **Первичная диагностика:**
• Измерьте температуру (норма 38-39°C)
• Оцените аппетит и активность
• Проверьте слизистые (розовые = норма)
• Обратите внимание на дыхание

⚠️ **Тревожные симптомы у кошек:**
• Температура выше 39.5°C или ниже 37.5°C
• Отказ от еды более 24 часов
• Затрудненное дыхание
• Рвота более 2 раз в день
• Кровь в моче или кале

💊 **Первая помощь:**
• Обеспечьте покой и тепло
• Доступ к свежей воде
• НЕ давайте человеческие лекарства!
• Наблюдайте за динамикой

🚨 **Срочно вызывайте врача при ухудшении!**

Нужен осмотр на дому для точного диагноза?
        """
    
    def get_kitten_advice(self):
        """Советы по котятам"""
        return """
🐱 **Консультация по котятам (фелинолог):**

**Особенности ухода за котятами:**

🍼 **Кормление:**
• До 4 недель - только молоко матери
• 4-8 недель - постепенный переход на корм
• Специальный корм для котят до года
• Кормление 4-6 раз в день

💉 **Вакцинация котят:**
• Первая прививка: 8-9 недель
• Вторая прививка: 12 недель  
• Ревакцинация: ежегодно
• Обязательно от бешенства

🏥 **Здоровье:**
• Обработка от глистов с 3 недель
• Осмотр ветеринара в 6-8 недель
• Контроль веса и развития
• Социализация с 3-14 недель

⚠️ **Тревожные признаки:**
• Отказ от еды более 12 часов
• Вялость, постоянный сон
• Понос или рвота
• Затрудненное дыхание

Нужна консультация по вашему котенку?
        """
    
    def get_cat_feeding_advice(self):
        """Профессиональные советы по кормлению кошек"""
        return """
🍽️ **Рекомендации по питанию кошек (фелинолог):**

**Основы правильного питания:**

✅ **Качественный корм:**
• Премиум или супер-премиум класс
• Соответствие возрасту (котенок/взрослая/пожилая)
• Учет особенностей породы
• Баланс белков, жиров, углеводов

📊 **Режим кормления:**
• Котята: 4-6 раз в день
• Взрослые кошки: 2-3 раза в день
• Пожилые: 2-3 раза, меньшими порциями
• Всегда свежая вода в доступе

❌ **Запрещенные продукты:**
• Шоколад, лук, чеснок
• Виноград, изюм
• Кости птицы
• Молоко взрослым кошкам
• Жирная, соленая пища

🎯 **Породные особенности:**
• Персы: склонность к МКБ
• Британцы: контроль веса
• Мейн-куны: крупные порции
• Сфинксы: повышенный метаболизм

Нужна индивидуальная диета для вашей кошки?
        """
    
    def get_cat_vaccination_advice(self):
        """Профессиональные советы по вакцинации кошек"""
        return """
💉 **График вакцинации кошек (фелинолог):**

**Обязательные прививки:**

📅 **Котята:**
• 8-9 недель: комплексная вакцина
• 12 недель: ревакцинация + бешенство
• 1 год: ревакцинация всех прививок

🔄 **Взрослые кошки:**
• Ежегодная ревакцинация
• Бешенство - обязательно по закону
• Комплекс: панлейкопения, ринотрахеит, калицивироз

🛡️ **Защита от болезней:**
• Панлейкопения (кошачья чума)
• Ринотрахеит (герпес)
• Калицивироз
• Хламидиоз
• Бешенство

⚠️ **Противопоказания:**
• Болезнь кошки
• Беременность
• Недавний стресс
• Прием антибиотиков

📋 **Подготовка к вакцинации:**
• Обработка от глистов за 10-14 дней
• Осмотр ветеринара
• Измерение температуры
• Отсутствие симптомов болезни

Составлю индивидуальный график для вашей кошки!
        """
    
    def get_breed_specific_advice(self):
        """Советы по породным особенностям"""
        return """
🐾 **Породные особенности кошек (фелинолог):**

**Специфика разных пород:**

🇬🇧 **Британские кошки:**
• Склонность к ожирению
• Проблемы с сердцем (HCM)
• Особый уход за шерстью
• Спокойный характер

🇮🇷 **Персидские кошки:**
• Ежедневный уход за шерстью
• Проблемы с дыханием
• Склонность к МКБ
• Уход за глазами

🦁 **Мейн-куны:**
• Крупный размер - особое питание
• Склонность к HCM
• Дисплазия тазобедренных суставов
• Активный образ жизни

🏺 **Сфинксы:**
• Защита от солнца и холода
• Особый уход за кожей
• Повышенный аппетит
• Склонность к кожным проблемам

🎯 **Индивидуальный подход:**
Каждая порода требует специфического ухода, питания и профилактики заболеваний.

Расскажите о породе вашей кошки для персональных рекомендаций!
        """
    
    def get_professional_general_advice(self):
        """Общие профессиональные советы"""
        return """
🩺 **Консультация ветеринара-фелинолога:**

Спасибо за обращение! Как врач с 15-летним опытом работы с кошками, для качественной консультации мне важно знать:

📋 **Информация о кошке:**
• Порода, возраст, вес
• Конкретные симптомы или проблемы
• Длительность проблемы
• Изменения в поведении/аппетите
• История вакцинаций
• Что уже предпринимали

🎯 **Моя специализация:**
• Диагностика заболеваний кошек
• Породные особенности и генетика
• Инфекционные болезни кошек
• Паразитология
• Дерматология кошек
• Гериатрия (пожилые кошки)

💡 **Помните:** Онлайн-консультация дает профессиональные рекомендации, но точный диагноз требует очного осмотра.

Опишите подробнее состояние вашей кошки, и я дам конкретные рекомендации!
        """
    
    async def web_app_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик данных из веб-приложения"""
        try:
            data = json.loads(update.effective_message.web_app_data.data)
            data['user_id'] = update.effective_user.id
            
            # Сохраняем заявку в базу данных
            call_id = self.db.save_vet_call(data)
            
            # Формируем ответ пользователю
            response = f"""
✅ **Заявка на вызов ветеринара-фелинолога принята!**

📋 **Номер заявки:** #{call_id}
👤 **Владелец:** {data.get('name')}
📱 **Телефон:** {data.get('phone')}
📍 **Адрес:** {data.get('address')}
🐾 **Питомец:** {data.get('petType')} {data.get('petName', '')}
🎂 **Возраст:** {data.get('petAge')}
🚨 **Проблема:** {data.get('problem')}
⏰ **Желаемое время:** {data.get('preferredTime', 'Любое')}

Врач-фелинолог свяжется с вами в течение 30 минут для уточнения деталей и назначения времени визита.

📞 **Экстренная связь:** {VET_SERVICE_PHONE}
            """
            
            await update.effective_message.reply_text(response)
            
            # Уведомляем администратора
            if ADMIN_CHAT_ID:
                admin_message = f"""
🚨 **Новая заявка на вызов ветеринара-фелинолога**

📋 **ID:** #{call_id}
👤 **Клиент:** {data.get('name')} (@{update.effective_user.username or 'без username'})
📱 **Телефон:** {data.get('phone')}
📍 **Адрес:** {data.get('address')}
🐾 **Кошка:** {data.get('petName', 'Не указано')} ({data.get('petAge')})
🚨 **Проблема:** {data.get('problem')}
⚠️ **Срочность:** {data.get('urgency', 'Обычная')}
⏰ **Время:** {data.get('preferredTime', 'Любое')}
💬 **Комментарии:** {data.get('comments', 'Нет')}

📅 **Время заявки:** {datetime.now().strftime('%d.%m.%Y %H:%M')}
                """
                
                try:
                    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления администратору: {e}")
            
            logger.info(f"Заявка #{call_id} от пользователя {update.effective_user.id} сохранена")
            
        except json.JSONDecodeError:
            await update.effective_message.reply_text("❌ Ошибка обработки данных из формы")
        except Exception as e:
            logger.error(f"Ошибка обработки данных веб-приложения: {e}")
            await update.effective_message.reply_text("❌ Произошла ошибка при обработке заявки")
    
    def run(self):
        """Запуск бота"""
        logger.info("🚀 Запуск профессионального ветеринарного бота-фелинолога...")
        try:
            self.application.run_polling(drop_pending_updates=True)
        except KeyboardInterrupt:
            logger.info("🛑 Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")

def main():
    """Главная функция"""
    try:
        bot = ProfessionalVetBot()
        bot.run()
    except Exception as e:
        print(f"❌ Не удалось запустить бота: {e}")
        print("Проверьте конфигурацию в .env файле")

if __name__ == "__main__":
    main()

