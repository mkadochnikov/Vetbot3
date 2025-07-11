"""
Улучшенная админ-панель на Streamlit для ветеринарного бота
Версия 3.0 с поддержкой вызовов врача и диалогов
"""
import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class VetBotAdmin:
    def __init__(self, db_path='vetbot.db'):
        self.db_path = db_path
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    def get_db_connection(self):
        """Получить соединение с базой данных"""
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            st.error(f"Ошибка подключения к БД: {e}")
            return None
    
    def get_statistics(self):
        """Получить общую статистику"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return {'total_users': 0, 'total_consultations': 0, 'total_calls': 0, 'today_consultations': 0, 'vet_requests': 0}
            
            stats = {}
            
            # Общее количество пользователей
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Общее количество консультаций
            cursor = conn.execute("SELECT COUNT(*) FROM consultations")
            stats['total_consultations'] = cursor.fetchone()[0]
            
            # Общее количество вызовов врача
            cursor = conn.execute("SELECT COUNT(*) FROM vet_calls")
            stats['total_calls'] = cursor.fetchone()[0]
            
            # Заявки на вызов врача (новая таблица)
            cursor = conn.execute("SELECT COUNT(*) FROM vet_requests")
            stats['vet_requests'] = cursor.fetchone()[0]
            
            # Консультации за сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.execute("SELECT COUNT(*) FROM consultations WHERE DATE(created_at) = ?", (today,))
            stats['today_consultations'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"Ошибка получения статистики: {e}")
            return {'total_users': 0, 'total_consultations': 0, 'total_calls': 0, 'today_consultations': 0, 'vet_requests': 0}
    
    def get_recent_users(self, limit=10):
        """Получить последних пользователей"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT user_id, username, first_name, last_name, created_at
            FROM users 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Ошибка получения пользователей: {e}")
            return pd.DataFrame()
    
    def get_recent_consultations(self, limit=10):
        """Получить последние консультации"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT c.id, c.user_id, u.username, c.question, c.response, c.created_at
            FROM consultations c
            LEFT JOIN users u ON c.user_id = u.user_id
            ORDER BY c.created_at DESC 
            LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Ошибка получения консультаций: {e}")
            return pd.DataFrame()
    
    def get_vet_requests(self, limit=20):
        """Получить заявки на вызов врача"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT id, name, phone, address, created_at
            FROM vet_requests 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(limit,))
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Ошибка получения заявок: {e}")
            return pd.DataFrame()
    
    def get_user_dialog(self, user_id):
        """Получить весь диалог пользователя"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            # Получаем консультации пользователя
            query = """
            SELECT 'consultation' as type, question as message, response, created_at
            FROM consultations 
            WHERE user_id = ?
            ORDER BY created_at ASC
            """
            consultations = pd.read_sql_query(query, conn, params=(user_id,))
            
            # Получаем сообщения от админа
            query_admin = """
            SELECT 'admin_message' as type, message, NULL as response, sent_at as created_at
            FROM admin_messages 
            WHERE user_id = ?
            ORDER BY sent_at ASC
            """
            admin_messages = pd.read_sql_query(query_admin, conn, params=(user_id,))
            
            conn.close()
            
            # Объединяем и сортируем по времени
            if not consultations.empty and not admin_messages.empty:
                all_messages = pd.concat([consultations, admin_messages], ignore_index=True)
                all_messages = all_messages.sort_values('created_at').reset_index(drop=True)
                return all_messages
            elif not consultations.empty:
                return consultations
            elif not admin_messages.empty:
                return admin_messages
            else:
                return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Ошибка получения диалога: {e}")
            return pd.DataFrame()
    
    def send_telegram_message(self, user_id, message):
        """Отправить сообщение пользователю в Telegram"""
        try:
            if not self.bot_token:
                st.error("Токен бота не найден в переменных окружения")
                return False
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': user_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                # Сохраняем сообщение в БД
                self.save_admin_message(user_id, message)
                return True
            else:
                st.error(f"Ошибка отправки: {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Ошибка отправки сообщения: {e}")
            return False
    
    def save_admin_message(self, user_id, message):
        """Сохранить сообщение админа в БД"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            admin_username = st.session_state.get('admin_username', 'admin')
            
            cursor = conn.execute("""
                INSERT INTO admin_messages (user_id, admin_username, message, sent_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, admin_username, message, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Ошибка сохранения сообщения: {e}")
            return False

def main():
    st.set_page_config(
        page_title="Админ-панель ветеринарного бота",
        page_icon="🩺",
        layout="wide"
    )
    
    # Заголовок
    st.title("🩺 Админ-панель ветеринарного бота v3.0")
    st.markdown("---")
    
    # Проверка подключения к БД
    admin = VetBotAdmin()
    
    # Тест подключения
    try:
        conn = admin.get_db_connection()
        if conn:
            # Проверяем количество таблиц
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            table_count = cursor.fetchone()[0]
            st.sidebar.success(f"✅ БД подключена ({table_count} таблиц)")
            conn.close()
        else:
            st.error("❌ Не удалось подключиться к базе данных")
            return
    except Exception as e:
        st.error(f"❌ Ошибка подключения: {e}")
        return
    
    # Боковая панель с навигацией
    st.sidebar.title("📋 Навигация")
    page = st.sidebar.selectbox(
        "Выберите раздел:",
        ["📊 Статистика", "👥 Пользователи", "💬 Консультации", "🚑 Вызовы врача", "💬 Диалоги", "ℹ️ Информация"]
    )
    
    # Статистика
    if page == "📊 Статистика":
        st.header("📊 Общая статистика")
        
        stats = admin.get_statistics()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("👥 Всего пользователей", stats['total_users'])
        
        with col2:
            st.metric("💬 Всего консультаций", stats['total_consultations'])
        
        with col3:
            st.metric("🚑 Вызовы врача", stats['total_calls'])
        
        with col4:
            st.metric("📋 Заявки на вызов", stats['vet_requests'])
        
        with col5:
            st.metric("📅 Консультации сегодня", stats['today_consultations'])
        
        st.markdown("---")
        
        # Последние консультации
        st.subheader("💬 Последние консультации")
        consultations = admin.get_recent_consultations(5)
        if not consultations.empty:
            st.dataframe(consultations, use_container_width=True)
        else:
            st.info("Консультации не найдены")
    
    # Пользователи
    elif page == "👥 Пользователи":
        st.header("👥 Управление пользователями")
        
        users = admin.get_recent_users(20)
        if not users.empty:
            st.dataframe(users, use_container_width=True)
            
            # Выбор пользователя для просмотра диалога
            st.subheader("🔍 Выбрать пользователя для диалога")
            user_options = {f"{row['username']} ({row['user_id']})": row['user_id'] 
                          for _, row in users.iterrows() if row['username']}
            
            if user_options:
                selected_user = st.selectbox("Выберите пользователя:", list(user_options.keys()))
                if selected_user:
                    user_id = user_options[selected_user]
                    if st.button("📖 Открыть диалог"):
                        st.session_state['selected_user_id'] = user_id
                        st.session_state['selected_username'] = selected_user
                        st.rerun()
        else:
            st.info("Пользователи не найдены")
    
    # Консультации
    elif page == "💬 Консультации":
        st.header("💬 История консультаций")
        
        consultations = admin.get_recent_consultations(50)
        if not consultations.empty:
            # Фильтр по пользователю
            users = consultations['username'].dropna().unique()
            selected_user_filter = st.selectbox("Фильтр по пользователю:", ['Все'] + list(users))
            
            if selected_user_filter != 'Все':
                consultations = consultations[consultations['username'] == selected_user_filter]
            
            st.dataframe(consultations, use_container_width=True)
            
            # Детальный просмотр консультации
            if not consultations.empty:
                st.subheader("🔍 Детальный просмотр")
                consultation_ids = consultations['id'].tolist()
                selected_consultation = st.selectbox("Выберите консультацию:", consultation_ids)
                
                if selected_consultation:
                    consultation = consultations[consultations['id'] == selected_consultation].iloc[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_area("❓ Вопрос:", consultation['question'], height=100, disabled=True)
                    with col2:
                        st.text_area("💡 Ответ:", consultation['response'], height=100, disabled=True)
                    
                    st.caption(f"📅 Дата: {consultation['created_at']} | 👤 Пользователь: {consultation['username']}")
        else:
            st.info("Консультации не найдены")
    
    # Вызовы врача
    elif page == "🚑 Вызовы врача":
        st.header("🚑 Заявки на вызов врача")
        
        vet_requests = admin.get_vet_requests(50)
        if not vet_requests.empty:
            st.dataframe(vet_requests, use_container_width=True)
            
            # Детальный просмотр заявки
            st.subheader("🔍 Детальный просмотр заявки")
            request_ids = vet_requests['id'].tolist()
            selected_request = st.selectbox("Выберите заявку:", request_ids)
            
            if selected_request:
                request = vet_requests[vet_requests['id'] == selected_request].iloc[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("👤 Имя:", request['name'], disabled=True)
                with col2:
                    st.text_input("📞 Телефон:", request['phone'], disabled=True)
                with col3:
                    st.text_input("📍 Адрес:", request['address'], disabled=True)
                
                st.caption(f"📅 Дата заявки: {request['created_at']}")
        else:
            st.info("Заявки на вызов врача не найдены")
    
    # Диалоги
    elif page == "💬 Диалоги":
        st.header("💬 Диалоги с пользователями")
        
        # Проверяем, выбран ли пользователь
        if 'selected_user_id' in st.session_state:
            user_id = st.session_state['selected_user_id']
            username = st.session_state['selected_username']
            
            st.subheader(f"💬 Диалог с {username}")
            
            # Получаем диалог
            dialog = admin.get_user_dialog(user_id)
            
            if not dialog.empty:
                # Отображаем диалог
                st.subheader("📖 История диалога")
                for _, message in dialog.iterrows():
                    if message['type'] == 'consultation':
                        # Вопрос пользователя
                        st.chat_message("user").write(f"❓ **Вопрос:** {message['message']}")
                        if message['response']:
                            st.chat_message("assistant").write(f"🤖 **AI-ответ:** {message['response']}")
                    elif message['type'] == 'admin_message':
                        # Сообщение от админа
                        st.chat_message("assistant").write(f"👨‍💼 **Консультант:** {message['message']}")
                
                st.markdown("---")
            
            # Форма для отправки сообщения
            st.subheader("✉️ Отправить сообщение пользователю")
            
            # Инициализация имени админа
            if 'admin_username' not in st.session_state:
                st.session_state['admin_username'] = 'Консультант'
            
            admin_name = st.text_input("👨‍💼 Ваше имя:", st.session_state['admin_username'])
            st.session_state['admin_username'] = admin_name
            
            message_text = st.text_area("💬 Сообщение:", height=100, 
                                      placeholder="Введите ваше сообщение пользователю...")
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📤 Отправить", type="primary"):
                    if message_text.strip():
                        # Добавляем подпись консультанта
                        full_message = f"👨‍💼 **{admin_name}:**\n\n{message_text}"
                        
                        if admin.send_telegram_message(user_id, full_message):
                            st.success("✅ Сообщение отправлено!")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка отправки сообщения")
                    else:
                        st.warning("⚠️ Введите текст сообщения")
            
            with col2:
                if st.button("🔙 Назад к списку пользователей"):
                    if 'selected_user_id' in st.session_state:
                        del st.session_state['selected_user_id']
                    if 'selected_username' in st.session_state:
                        del st.session_state['selected_username']
                    st.rerun()
        
        else:
            st.info("👆 Выберите пользователя в разделе 'Пользователи' для начала диалога")
            
            # Показываем список пользователей для быстрого доступа
            st.subheader("👥 Быстрый выбор пользователя")
            users = admin.get_recent_users(10)
            if not users.empty:
                for _, user in users.iterrows():
                    if user['username']:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"👤 {user['username']} ({user['first_name']} {user['last_name']})")
                        with col2:
                            if st.button(f"💬 Диалог", key=f"dialog_{user['user_id']}"):
                                st.session_state['selected_user_id'] = user['user_id']
                                st.session_state['selected_username'] = f"{user['username']} ({user['user_id']})"
                                st.rerun()
    
    # Информация
    elif page == "ℹ️ Информация":
        st.header("ℹ️ Информация о системе")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Версия системы")
            st.info("**Админ-панель:** v3.0")
            st.info("**База данных:** SQLite")
            st.info("**Фреймворк:** Streamlit")
            
        with col2:
            st.subheader("📊 Статус компонентов")
            st.success("✅ База данных")
            st.success("✅ Telegram API")
            st.success("✅ Веб-интерфейс")
        
        st.subheader("🆕 Новые возможности v3.0")
        st.markdown("""
        - 🚑 **Просмотр заявок на вызов врача**
        - 💬 **Полная история диалогов с пользователями**
        - ✉️ **Отправка сообщений пользователям через Telegram**
        - 👨‍💼 **Персонализированные ответы от консультантов**
        - 📊 **Расширенная статистика**
        """)

if __name__ == "__main__":
    main()

