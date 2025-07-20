"""
Улучшенная админ-панель на Streamlit для ветеринарного бота
Версия 3.1 с исправлениями отображения пользователей и диалогов
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
            cursor = conn.execute("SELECT COUNT(*) FROM vet_calls")
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
        """Получить последних пользователей с информацией о закрепленных врачах"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT 
                u.user_id, 
                u.username, 
                u.first_name, 
                u.last_name, 
                u.created_at,
                CASE 
                    WHEN ac.doctor_id IS NOT NULL THEN 
                        COALESCE(d.full_name, 'Врач ID: ' || ac.doctor_id)
                    ELSE 'Не закреплен'
                END as assigned_doctor,
                ac.doctor_id,
                CASE 
                    WHEN ac.consultation_id IS NOT NULL THEN 1
                    ELSE 0
                END as has_active_consultation
            FROM users u
            LEFT JOIN active_consultations ac ON u.user_id = ac.user_id
            LEFT JOIN doctors d ON ac.doctor_id = d.user_id
            ORDER BY u.created_at DESC 
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
            
            query = f"""
            SELECT id, name, phone, address, created_at 
            FROM vet_calls 
            ORDER BY created_at DESC 
            LIMIT {limit}
            """
            df = pd.read_sql_query(query, conn)
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
    
    def get_doctors(self):
        """Получить список всех врачей"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT id, telegram_id, username, full_name, is_approved, is_active, 
                   registered_at, last_activity, photo_path
            FROM doctors 
            ORDER BY registered_at DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Ошибка получения врачей: {e}")
            return pd.DataFrame()
    
    def update_doctor_approval(self, doctor_id, is_approved):
        """Обновить статус одобрения врача"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE doctors 
                SET is_approved = ? 
                WHERE id = ?
            """, (is_approved, doctor_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            st.error(f"Ошибка обновления статуса врача: {e}")
            return False
    
    def update_doctor_activity(self, doctor_id, is_active):
        """Обновить статус активности врача"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE doctors 
                SET is_active = ? 
                WHERE id = ?
            """, (is_active, doctor_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            st.error(f"Ошибка обновления активности врача: {e}")
            return False
    
    def get_doctor_consultations(self, doctor_id):
        """Получить консультации врача"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT ac.id, ac.client_id, ac.client_name, ac.status, ac.started_at,
                   COUNT(cm.id) as message_count
            FROM active_consultations ac
            LEFT JOIN consultation_messages cm ON ac.id = cm.consultation_id
            WHERE ac.doctor_id = ?
            GROUP BY ac.id
            ORDER BY ac.started_at DESC
            """
            df = pd.read_sql_query(query, conn, params=(doctor_id,))
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Ошибка получения консультаций врача: {e}")
            return pd.DataFrame()
    
    def get_active_consultations(self):
        """Получить активные консультации"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT 
                ac.id,
                ac.user_id as client_id,
                COALESCE(u.first_name || ' ' || u.last_name, u.username, 'ID: ' || u.user_id) as client_name,
                COALESCE(d.full_name, 'ID: ' || ac.doctor_id) as doctor_name,
                ac.status,
                ac.started_at,
                ac.doctor_id
            FROM active_consultations ac
            LEFT JOIN users u ON ac.user_id = u.user_id
            LEFT JOIN doctors d ON ac.doctor_id = d.id
            WHERE ac.status = 'active'
            ORDER BY ac.started_at DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Ошибка получения активных консультаций: {e}")
            return pd.DataFrame()
    
    def get_available_doctors(self):
        """Получить доступных врачей"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return pd.DataFrame()
            
            query = """
            SELECT id, full_name, telegram_id
            FROM doctors 
            WHERE is_approved = 1 AND is_active = 1
            ORDER BY full_name
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
            
        except Exception as e:
            st.error(f"Ошибка получения доступных врачей: {e}")
            return pd.DataFrame()
    
    def reassign_doctor(self, consultation_id, new_doctor_id):
        """Переназначить врача для консультации"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Обновляем консультацию
            cursor.execute("""
                UPDATE active_consultations 
                SET doctor_id = ? 
                WHERE id = ?
            """, (new_doctor_id, consultation_id))
            
            # Добавляем системное сообщение о переназначении
            cursor.execute("""
                INSERT INTO consultation_messages (consultation_id, sender_type, message, sent_at)
                VALUES (?, 'system', 'Консультация переназначена новому врачу', ?)
            """, (consultation_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            st.error(f"Ошибка переназначения врача: {e}")
            return False
    
    def save_admin_message(self, user_id, message):
        """Сохранить сообщение админа в БД"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admin_messages (user_id, message, sent_at)
                VALUES (?, ?, ?)
            """, (user_id, message, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Ошибка сохранения сообщения: {e}")
            return False
    
    def format_user_display_name(self, user_row):
        """Форматировать отображаемое имя пользователя"""
        try:
            # Проверяем наличие имени и фамилии
            first_name = user_row.get('first_name', '') or ''
            last_name = user_row.get('last_name', '') or ''
            username = user_row.get('username', '') or ''
            user_id = user_row.get('user_id', '')
            
            # Формируем отображаемое имя
            if first_name and last_name:
                return f"{first_name} {last_name}"
            elif first_name:
                return first_name
            elif username:
                return f"@{username}"
            else:
                return f"Пользователь {user_id}"
                
        except Exception as e:
            return f"Пользователь {user_row.get('user_id', 'Unknown')}"
    
    def send_doctor_message(self, doctor_id, message):
        """Отправить сообщение врачу"""
        try:
            # Получаем telegram_id врача
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.execute("SELECT telegram_id FROM doctors WHERE id = ?", (doctor_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                st.error("Врач не найден")
                return False
            
            telegram_id = result[0]
            
            # Отправляем сообщение через Telegram API
            if not self.bot_token:
                st.error("Токен бота не найден")
                return False
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': telegram_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data)
            return response.status_code == 200
            
        except Exception as e:
            st.error(f"Ошибка отправки сообщения врачу: {e}")
            return False

def main():
    st.set_page_config(
        page_title="Админ-панель VetBot",
        page_icon="🐱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Инициализация админ-класса
    admin = VetBotAdmin()
    
    # Заголовок
    st.title("🐱 Админ-панель VetBot v3.1")
    st.markdown("---")
    
    # Боковая панель с навигацией
    st.sidebar.title("📋 Навигация")
    
    # Используем radio buttons вместо selectbox
    page = st.sidebar.radio(
        "Выберите раздел:",
        [
            "📊 Статистика",
            "👥 Пользователи", 
            "💬 Консультации",
            "🚑 Вызовы врача",
            "👨‍⚕️ Врачи",
            "💬 Диалоги",
            "ℹ️ Информация"
        ]
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
            # Создаем улучшенную таблицу с отформатированными именами
            display_users = users.copy()
            display_users['Отображаемое имя'] = display_users.apply(admin.format_user_display_name, axis=1)
            
            # Переупорядочиваем колонки для лучшего отображения
            columns_order = ['user_id', 'Отображаемое имя', 'username', 'first_name', 'last_name', 'assigned_doctor', 'created_at']
            display_users = display_users[columns_order]
            
            # Переименовываем колонки для лучшего отображения
            display_users = display_users.rename(columns={
                'user_id': 'ID пользователя',
                'username': 'Username',
                'first_name': 'Имя',
                'last_name': 'Фамилия',
                'assigned_doctor': 'Закрепленный врач',
                'created_at': 'Дата регистрации'
            })
            
            st.dataframe(display_users, use_container_width=True)
            
            # Добавляем кнопки для каждого пользователя
            st.subheader("🔧 Действия с пользователями")
            
            for index, user in users.iterrows():
                user_display_name = admin.format_user_display_name(user)
                
                with st.expander(f"👤 {user_display_name} (ID: {user['user_id']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button(f"💬 Перейти к диалогу", key=f"dialog_{user['user_id']}"):
                            st.session_state['selected_user_id'] = user['user_id']
                            st.session_state['selected_username'] = user_display_name
                            st.session_state['show_dialog'] = True
                            st.rerun()
                    
                    with col2:
                        if st.button(f"📤 Быстрое сообщение", key=f"quick_{user['user_id']}"):
                            st.session_state['quick_message_user_id'] = user['user_id']
                            st.session_state['quick_message_username'] = user_display_name
                            st.rerun()
                    
                    with col3:
                        st.write(f"**Врач:** {user['assigned_doctor']}")
                        if user['has_active_consultation']:
                            st.success("🟢 Активная консультация")
                        else:
                            st.info("⚪ Нет активной консультации")
            
            # Быстрое сообщение
            if 'quick_message_user_id' in st.session_state:
                st.subheader("⚡ Быстрое сообщение")
                user_id = st.session_state['quick_message_user_id']
                username = st.session_state['quick_message_username']
                
                st.info(f"Отправка сообщения пользователю: {username}")
                
                quick_message = st.text_area("💬 Сообщение:", height=100, 
                                           placeholder="Введите быстрое сообщение...")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("📤 Отправить быстрое сообщение", type="primary"):
                        if quick_message.strip():
                            admin_name = st.session_state.get('admin_username', 'Консультант')
                            full_message = f"👨‍💼 **{admin_name}:**\n\n{quick_message}"
                            
                            if admin.send_telegram_message(user_id, full_message):
                                st.success("✅ Сообщение отправлено!")
                                del st.session_state['quick_message_user_id']
                                del st.session_state['quick_message_username']
                                st.rerun()
                            else:
                                st.error("❌ Ошибка отправки сообщения")
                        else:
                            st.warning("⚠️ Введите текст сообщения")
                
                with col2:
                    if st.button("❌ Отмена"):
                        del st.session_state['quick_message_user_id']
                        del st.session_state['quick_message_username']
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
    
    # Врачи
    elif page == "👨‍⚕️ Врачи":
        st.header("👨‍⚕️ Управление врачами")
        
        doctors = admin.get_doctors()
        if not doctors.empty:
            st.subheader("📋 Список врачей")
            
            # Фильтры
            col1, col2, col3 = st.columns(3)
            with col1:
                approval_filter = st.selectbox("Статус одобрения:", ["Все", "Одобренные", "Ожидают одобрения"])
            with col2:
                activity_filter = st.selectbox("Активность:", ["Все", "Активные", "Неактивные"])
            with col3:
                st.write("")  # Пустая колонка для выравнивания
            
            # Применяем фильтры
            filtered_doctors = doctors.copy()
            if approval_filter == "Одобренные":
                filtered_doctors = filtered_doctors[filtered_doctors['is_approved'] == 1]
            elif approval_filter == "Ожидают одобрения":
                filtered_doctors = filtered_doctors[filtered_doctors['is_approved'] == 0]
            
            if activity_filter == "Активные":
                filtered_doctors = filtered_doctors[filtered_doctors['is_active'] == 1]
            elif activity_filter == "Неактивные":
                filtered_doctors = filtered_doctors[filtered_doctors['is_active'] == 0]
            
            # Отображаем таблицу врачей
            st.dataframe(filtered_doctors, use_container_width=True)
            
            # Управление врачами
            if not filtered_doctors.empty:
                st.subheader("🔧 Управление врачами")
                
                for _, doctor in filtered_doctors.iterrows():
                    with st.expander(f"👨‍⚕️ {doctor['full_name']} (ID: {doctor['id']})"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.write(f"**Username:** @{doctor['username']}")
                            st.write(f"**Telegram ID:** {doctor['telegram_id']}")
                        
                        with col2:
                            st.write(f"**Одобрен:** {'✅' if doctor['is_approved'] else '❌'}")
                            st.write(f"**Активен:** {'✅' if doctor['is_active'] else '❌'}")
                        
                        with col3:
                            st.write(f"**Регистрация:** {doctor['registered_at']}")
                            if doctor['last_activity']:
                                st.write(f"**Последняя активность:** {doctor['last_activity']}")
                        
                        with col4:
                            # Кнопки управления
                            if not doctor['is_approved']:
                                if st.button(f"✅ Одобрить", key=f"approve_{doctor['id']}"):
                                    if admin.update_doctor_approval(doctor['id'], 1):
                                        st.success("Врач одобрен!")
                                        st.rerun()
                            else:
                                if st.button(f"❌ Отклонить", key=f"reject_{doctor['id']}"):
                                    if admin.update_doctor_approval(doctor['id'], 0):
                                        st.success("Одобрение отозвано!")
                                        st.rerun()
                            
                            if doctor['is_active']:
                                if st.button(f"🔴 Деактивировать", key=f"deactivate_{doctor['id']}"):
                                    if admin.update_doctor_activity(doctor['id'], 0):
                                        st.success("Врач деактивирован!")
                                        st.rerun()
                            else:
                                if st.button(f"🟢 Активировать", key=f"activate_{doctor['id']}"):
                                    if admin.update_doctor_activity(doctor['id'], 1):
                                        st.success("Врач активирован!")
                                        st.rerun()
                        
                        # Просмотр консультаций врача
                        doctor_consultations = admin.get_doctor_consultations(doctor['id'])
                        if not doctor_consultations.empty:
                            st.write("**Консультации врача:**")
                            st.dataframe(doctor_consultations, use_container_width=True)
                        else:
                            st.info("У врача пока нет консультаций")
                        
                        # Отправка сообщения врачу
                        if st.button(f"💬 Отправить сообщение", key=f"message_{doctor['id']}"):
                            st.session_state['message_doctor_id'] = doctor['id']
                            st.session_state['message_doctor_name'] = doctor['full_name']
                            st.rerun()
            
            # Форма отправки сообщения врачу
            if 'message_doctor_id' in st.session_state:
                st.subheader("💬 Отправить сообщение врачу")
                doctor_id = st.session_state['message_doctor_id']
                doctor_name = st.session_state['message_doctor_name']
                
                st.info(f"Отправка сообщения врачу: {doctor_name}")
                
                message_text = st.text_area("💬 Сообщение:", height=100, 
                                          placeholder="Введите сообщение для врача...")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("📤 Отправить сообщение врачу", type="primary"):
                        if message_text.strip():
                            admin_message = f"👨‍💼 **Сообщение от администратора:**\n\n{message_text}"
                            
                            if admin.send_doctor_message(doctor_id, admin_message):
                                st.success("✅ Сообщение отправлено врачу!")
                                del st.session_state['message_doctor_id']
                                del st.session_state['message_doctor_name']
                                st.rerun()
                            else:
                                st.error("❌ Ошибка отправки сообщения")
                        else:
                            st.warning("⚠️ Введите текст сообщения")
                
                with col2:
                    if st.button("❌ Отмена"):
                        del st.session_state['message_doctor_id']
                        del st.session_state['message_doctor_name']
                        st.rerun()
        else:
            st.info("👨‍⚕️ Врачи не найдены")
            st.markdown("""
            **Как добавить врачей:**
            1. Врачи должны зарегистрироваться через бота для врачей
            2. После регистрации они появятся в этом разделе
            3. Администратор может одобрить или отклонить заявки врачей
            """)
    
    # Диалоги
    elif page == "💬 Диалоги":
        st.header("💬 Управление консультациями")
        
        # Вкладки для разных функций
        tab1, tab2 = st.tabs(["🔄 Активные консультации", "💬 Диалоги с пользователями"])
        
        with tab1:
            st.subheader("🔄 Переназначение врачей")
            
            # Получаем активные консультации
            active_consultations = admin.get_active_consultations()
            
            if not active_consultations.empty:
                st.dataframe(active_consultations, use_container_width=True)
                
                # Форма переназначения
                st.markdown("---")
                st.subheader("👨‍⚕️ Переназначить врача")
                
                # Выбор консультации
                consultation_options = {}
                for _, row in active_consultations.iterrows():
                    key = f"ID: {row['id']} - {row['client_name']} → {row['doctor_name']}"
                    consultation_options[key] = row['id']
                
                selected_consultation = st.selectbox(
                    "Выберите консультацию:",
                    options=list(consultation_options.keys())
                )
                
                # Выбор нового врача
                available_doctors = admin.get_available_doctors()
                if not available_doctors.empty:
                    doctor_options = {}
                    for _, row in available_doctors.iterrows():
                        doctor_options[row['full_name']] = row['id']
                    
                    selected_doctor = st.selectbox(
                        "Выберите нового врача:",
                        options=list(doctor_options.keys())
                    )
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("🔄 Переназначить", type="primary"):
                            consultation_id = consultation_options[selected_consultation]
                            new_doctor_id = doctor_options[selected_doctor]
                            
                            if admin.reassign_doctor(consultation_id, new_doctor_id):
                                st.success(f"✅ Консультация переназначена врачу {selected_doctor}")
                                st.rerun()
                            else:
                                st.error("❌ Ошибка переназначения")
                else:
                    st.warning("⚠️ Нет доступных врачей для переназначения")
            else:
                st.info("📭 Нет активных консультаций")
        
        with tab2:
            st.subheader("💬 Диалоги с пользователями")
            
            # Проверяем, выбран ли пользователь или нужно показать диалог
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
                else:
                    st.info("📭 История диалога пуста")
                
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
                        display_name = admin.format_user_display_name(user)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"👤 {display_name} (ID: {user['user_id']})")
                        with col2:
                            if st.button(f"💬 Диалог", key=f"dialog_{user['user_id']}"):
                                st.session_state['selected_user_id'] = user['user_id']
                                st.session_state['selected_username'] = f"{display_name} (ID: {user['user_id']})"
                                st.rerun()
    
    # Информация
    elif page == "ℹ️ Информация":
        st.header("ℹ️ Информация о системе")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Версия системы")
            st.info("**Админ-панель:** v3.1 (исправленная)")
            st.info("**База данных:** SQLite")
            st.info("**Фреймворк:** Streamlit")
            
        with col2:
            st.subheader("📊 Статус компонентов")
            st.success("✅ База данных")
            st.success("✅ Telegram API")
            st.success("✅ Веб-интерфейс")
        
        st.subheader("🆕 Исправления v3.1")
        st.markdown("""
        - 🔧 **Исправлено отображение пользователей без username**
        - 💬 **Улучшена обработка диалогов с любыми пользователями**
        - ⚡ **Добавлена функция быстрых сообщений**
        - 🎯 **Улучшена навигация между разделами**
        - 🛡️ **Безопасная обработка NULL значений**
        - 👨‍⚕️ **Добавлен раздел управления врачами**
        - 🔄 **Функция переназначения врачей**
        - 💬 **Кнопки перехода к диалогам пользователей**
        """)
        
        st.subheader("🚀 Возможности v3.0")
        st.markdown("""
        - 🚑 **Просмотр заявок на вызов врача**
        - 💬 **Полная история диалогов с пользователями**
        - ✉️ **Отправка сообщений пользователям через Telegram**
        - 👨‍💼 **Персонализированные ответы от консультантов**
        - 📊 **Расширенная статистика**
        """)

if __name__ == "__main__":
    main()

