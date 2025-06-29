#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Админ-панель на Streamlit для ветеринарного бота
"""

import streamlit as st
import sqlite3
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

class VetBotAdmin:
    def __init__(self, db_path='vetbot.db'):
        self.db_path = db_path
    
    def get_db_connection(self):
        """Получить соединение с базой данных"""
        return sqlite3.connect(self.db_path)
    
    def get_all_users(self):
        """Получить всех пользователей"""
        conn = self.get_db_connection()
        query = """
        SELECT u.user_id, u.username, u.first_name, u.last_name, u.created_at,
               COUNT(c.id) as consultations_count,
               COUNT(vc.id) as calls_count,
               MAX(c.created_at) as last_consultation
        FROM users u
        LEFT JOIN consultations c ON u.user_id = c.user_id
        LEFT JOIN vet_calls vc ON u.user_id = vc.user_id
        GROUP BY u.user_id
        ORDER BY last_consultation DESC NULLS LAST
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_user_consultations(self, user_id):
        """Получить консультации пользователя"""
        conn = self.get_db_connection()
        query = """
        SELECT id, question, response, created_at, admin_response, admin_username
        FROM consultations 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df
    
    def get_user_calls(self, user_id):
        """Получить заявки пользователя"""
        conn = self.get_db_connection()
        query = """
        SELECT * FROM vet_calls 
        WHERE user_id = ? 
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df
    
    def is_admin_session_active(self, user_id):
        """Проверить активную админскую сессию"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT admin_username FROM admin_sessions 
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def start_admin_session(self, user_id, admin_username):
        """Начать админскую сессию"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Завершаем все активные сессии для этого пользователя
        cursor.execute("""
            UPDATE admin_sessions 
            SET is_active = 0, ended_at = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        
        # Создаем новую сессию
        cursor.execute("""
            INSERT INTO admin_sessions (user_id, admin_username)
            VALUES (?, ?)
        """, (user_id, admin_username))
        
        conn.commit()
        conn.close()
    
    def end_admin_session(self, user_id):
        """Завершить админскую сессию"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE admin_sessions 
            SET is_active = 0, ended_at = CURRENT_TIMESTAMP 
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        conn.commit()
        conn.close()
    
    def add_admin_message_to_queue(self, user_id, message):
        """Добавить сообщение админа в очередь"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO admin_message_queue (user_id, message)
            VALUES (?, ?)
        """, (user_id, message))
        conn.commit()
        conn.close()
    
    def send_telegram_message(self, user_id, message):
        """Отправить сообщение через Telegram API"""
        try:
            url = f"{TELEGRAM_API_URL}/sendMessage"
            data = {
                'chat_id': user_id,
                'text': f"👨‍⚕️ Сообщение от ветеринара:\n\n{message}",
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    def get_statistics(self):
        """Получить статистику"""
        conn = self.get_db_connection()
        
        # Общая статистика
        stats = {}
        
        # Количество пользователей
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        # Количество консультаций
        cursor.execute("SELECT COUNT(*) FROM consultations")
        stats['total_consultations'] = cursor.fetchone()[0]
        
        # Количество заявок
        cursor.execute("SELECT COUNT(*) FROM vet_calls")
        stats['total_calls'] = cursor.fetchone()[0]
        
        # Активные сессии
        cursor.execute("SELECT COUNT(*) FROM admin_sessions WHERE is_active = 1")
        stats['active_sessions'] = cursor.fetchone()[0]
        
        # Консультации за последние 24 часа
        cursor.execute("""
            SELECT COUNT(*) FROM consultations 
            WHERE created_at > datetime('now', '-1 day')
        """)
        stats['consultations_24h'] = cursor.fetchone()[0]
        
        conn.close()
        return stats

def main():
    st.set_page_config(
        page_title="Админ-панель ветеринарного бота",
        page_icon="🩺",
        layout="wide"
    )
    
    # Инициализация админ-класса
    admin = VetBotAdmin()
    
    # Заголовок
    st.title("🩺 Админ-панель ветеринарного бота")
    st.markdown("---")
    
    # Боковая панель с навигацией
    st.sidebar.title("📋 Навигация")
    page = st.sidebar.selectbox(
        "Выберите раздел:",
        ["📊 Статистика", "👥 Пользователи", "💬 Активные диалоги", "📞 Заявки на вызов"]
    )
    
    # Статистика
    if page == "📊 Статистика":
        st.header("📊 Общая статистика")
        
        stats = admin.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Всего пользователей", stats['total_users'])
        
        with col2:
            st.metric("💬 Всего консультаций", stats['total_consultations'])
        
        with col3:
            st.metric("📞 Всего заявок", stats['total_calls'])
        
        with col4:
            st.metric("🔴 Активные сессии", stats['active_sessions'])
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📈 Консультации за 24ч", stats['consultations_24h'])
        
        # График активности (если есть данные)
        conn = admin.get_db_connection()
        activity_query = """
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM consultations 
        WHERE created_at > datetime('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        activity_df = pd.read_sql_query(activity_query, conn)
        conn.close()
        
        if not activity_df.empty:
            st.subheader("📈 Активность за последние 7 дней")
            st.line_chart(activity_df.set_index('date'))
    
    # Пользователи
    elif page == "👥 Пользователи":
        st.header("👥 Все пользователи")
        
        users_df = admin.get_all_users()
        
        if not users_df.empty:
            # Фильтры
            col1, col2 = st.columns(2)
            
            with col1:
                search_term = st.text_input("🔍 Поиск по имени/username:")
            
            with col2:
                min_consultations = st.number_input("Минимум консультаций:", min_value=0, value=0)
            
            # Применяем фильтры
            filtered_df = users_df.copy()
            
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['first_name'].str.contains(search_term, case=False, na=False) |
                    filtered_df['username'].str.contains(search_term, case=False, na=False)
                ]
            
            if min_consultations > 0:
                filtered_df = filtered_df[filtered_df['consultations_count'] >= min_consultations]
            
            # Отображаем таблицу
            st.dataframe(
                filtered_df,
                column_config={
                    "user_id": "ID",
                    "username": "Username",
                    "first_name": "Имя",
                    "last_name": "Фамилия",
                    "created_at": "Регистрация",
                    "consultations_count": "Консультации",
                    "calls_count": "Заявки",
                    "last_consultation": "Последняя консультация"
                },
                use_container_width=True
            )
            
            # Выбор пользователя для детального просмотра
            st.markdown("---")
            st.subheader("👤 Детальный просмотр пользователя")
            
            selected_user_id = st.selectbox(
                "Выберите пользователя:",
                options=filtered_df['user_id'].tolist(),
                format_func=lambda x: f"{filtered_df[filtered_df['user_id']==x]['first_name'].iloc[0]} ({x})"
            )
            
            if selected_user_id:
                user_info = filtered_df[filtered_df['user_id'] == selected_user_id].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**ID:** {user_info['user_id']}")
                    st.write(f"**Имя:** {user_info['first_name']} {user_info['last_name']}")
                    st.write(f"**Username:** @{user_info['username']}")
                
                with col2:
                    st.write(f"**Консультации:** {user_info['consultations_count']}")
                    st.write(f"**Заявки:** {user_info['calls_count']}")
                    st.write(f"**Регистрация:** {user_info['created_at']}")
                
                # Консультации пользователя
                consultations_df = admin.get_user_consultations(selected_user_id)
                
                if not consultations_df.empty:
                    st.subheader("💬 История консультаций")
                    
                    for _, consultation in consultations_df.iterrows():
                        with st.expander(f"Консультация от {consultation['created_at'][:16]}"):
                            st.write("**Вопрос:**")
                            st.write(consultation['question'])
                            st.write("**Ответ AI:**")
                            st.write(consultation['response'])
                            
                            if consultation['admin_response']:
                                st.write("**Ответ админа:**")
                                st.write(consultation['admin_response'])
                                st.write(f"*Ответил: {consultation['admin_username']}*")
        else:
            st.info("Пользователи не найдены")
    
    # Активные диалоги
    elif page == "💬 Активные диалоги":
        st.header("💬 Управление диалогами")
        
        users_df = admin.get_all_users()
        
        if not users_df.empty:
            # Выбор пользователя
            selected_user_id = st.selectbox(
                "Выберите пользователя для диалога:",
                options=users_df['user_id'].tolist(),
                format_func=lambda x: f"{users_df[users_df['user_id']==x]['first_name'].iloc[0]} ({x})"
            )
            
            if selected_user_id:
                user_info = users_df[users_df['user_id'] == selected_user_id].iloc[0]
                
                # Информация о пользователе
                st.write(f"**Пользователь:** {user_info['first_name']} (@{user_info['username']})")
                
                # Проверяем активную сессию
                active_admin = admin.is_admin_session_active(selected_user_id)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if active_admin:
                        st.success(f"🟢 Активная сессия с {active_admin}")
                        if st.button("🛑 Завершить сессию"):
                            admin.end_admin_session(selected_user_id)
                            st.rerun()
                    else:
                        st.info("🔴 Сессия не активна")
                        admin_name = st.text_input("Ваше имя:", value="Ветеринар")
                        if st.button("🚀 Начать сессию"):
                            admin.start_admin_session(selected_user_id, admin_name)
                            st.success("Сессия начата!")
                            st.rerun()
                
                # Отправка сообщения
                st.markdown("---")
                st.subheader("📤 Отправить сообщение")
                
                message_text = st.text_area("Введите сообщение:", height=100)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📨 Отправить через очередь"):
                        if message_text:
                            admin.add_admin_message_to_queue(selected_user_id, message_text)
                            st.success("Сообщение добавлено в очередь!")
                        else:
                            st.error("Введите сообщение!")
                
                with col2:
                    if st.button("⚡ Отправить немедленно"):
                        if message_text:
                            if admin.send_telegram_message(selected_user_id, message_text):
                                st.success("Сообщение отправлено!")
                            else:
                                st.error("Ошибка отправки!")
                        else:
                            st.error("Введите сообщение!")
                
                # История консультаций
                st.markdown("---")
                consultations_df = admin.get_user_consultations(selected_user_id)
                
                if not consultations_df.empty:
                    st.subheader("📜 История диалога")
                    
                    for _, consultation in consultations_df.head(5).iterrows():
                        with st.container():
                            st.markdown(f"**{consultation['created_at'][:16]}**")
                            
                            # Вопрос пользователя
                            st.markdown("👤 **Пользователь:**")
                            st.markdown(f"> {consultation['question']}")
                            
                            # Ответ AI
                            st.markdown("🤖 **AI-Ветеринар:**")
                            st.markdown(f"> {consultation['response'][:200]}...")
                            
                            # Ответ админа (если есть)
                            if consultation['admin_response']:
                                st.markdown("👨‍⚕️ **Ветеринар:**")
                                st.markdown(f"> {consultation['admin_response']}")
                            
                            st.markdown("---")
        else:
            st.info("Пользователи не найдены")
    
    # Заявки на вызов
    elif page == "📞 Заявки на вызов":
        st.header("📞 Заявки на вызов врача")
        
        conn = admin.get_db_connection()
        calls_query = """
        SELECT vc.*, u.first_name, u.username
        FROM vet_calls vc
        JOIN users u ON vc.user_id = u.user_id
        ORDER BY vc.created_at DESC
        """
        calls_df = pd.read_sql_query(calls_query, conn)
        conn.close()
        
        if not calls_df.empty:
            # Фильтры
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Статус:",
                    options=['Все'] + list(calls_df['status'].unique())
                )
            
            with col2:
                urgency_filter = st.selectbox(
                    "Срочность:",
                    options=['Все'] + list(calls_df['urgency'].unique())
                )
            
            with col3:
                days_filter = st.selectbox(
                    "Период:",
                    options=['Все', 'Сегодня', 'Неделя', 'Месяц']
                )
            
            # Применяем фильтры
            filtered_calls = calls_df.copy()
            
            if status_filter != 'Все':
                filtered_calls = filtered_calls[filtered_calls['status'] == status_filter]
            
            if urgency_filter != 'Все':
                filtered_calls = filtered_calls[filtered_calls['urgency'] == urgency_filter]
            
            # Отображаем заявки
            for _, call in filtered_calls.head(10).iterrows():
                with st.expander(f"Заявка #{call['id']} - {call['name']} ({call['status']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Клиент:** {call['name']}")
                        st.write(f"**Телефон:** {call['phone']}")
                        st.write(f"**Адрес:** {call['address']}")
                        st.write(f"**Питомец:** {call['pet_name']} ({call['pet_type']})")
                        st.write(f"**Возраст:** {call['pet_age']}")
                    
                    with col2:
                        st.write(f"**Срочность:** {call['urgency']}")
                        st.write(f"**Желаемое время:** {call['preferred_time']}")
                        st.write(f"**Статус:** {call['status']}")
                        st.write(f"**Создана:** {call['created_at']}")
                    
                    st.write(f"**Проблема:** {call['problem']}")
                    
                    if call['comments']:
                        st.write(f"**Комментарии:** {call['comments']}")
                    
                    # Кнопки управления статусом
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button(f"✅ Подтвердить #{call['id']}", key=f"confirm_{call['id']}"):
                            # Здесь можно добавить обновление статуса
                            st.success("Статус обновлен!")
                    
                    with col2:
                        if st.button(f"🚗 В пути #{call['id']}", key=f"progress_{call['id']}"):
                            st.success("Статус обновлен!")
                    
                    with col3:
                        if st.button(f"✅ Завершить #{call['id']}", key=f"complete_{call['id']}"):
                            st.success("Статус обновлен!")
                    
                    with col4:
                        if st.button(f"❌ Отменить #{call['id']}", key=f"cancel_{call['id']}"):
                            st.success("Статус обновлен!")
        else:
            st.info("Заявки не найдены")
    
    # Информация в боковой панели
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **🩺 Админ-панель v2.1.0**
    
    Функции:
    - 📊 Статистика использования
    - 👥 Управление пользователями  
    - 💬 Диалоги с пользователями
    - 📞 Заявки на вызов врача
    
    Для обновления данных перезагрузите страницу.
    """)

if __name__ == "__main__":
    main()

