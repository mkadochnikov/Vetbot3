# -*- coding: utf-8 -*-
"""
Улучшенная админ-панель на Streamlit для ветеринарного бота
"""
import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class VetBotAdmin:
    def __init__(self, db_path='vetbot.db'):
        self.db_path = db_path
    
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
                return {'total_users': 0, 'total_consultations': 0, 'total_calls': 0, 'today_consultations': 0}
            
            # Базовая статистика
            stats = {}
            
            # Общее количество пользователей
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            # Общее количество консультаций
            cursor = conn.execute("SELECT COUNT(*) FROM consultations")
            stats['total_consultations'] = cursor.fetchone()[0]
            
            # Общее количество вызовов
            cursor = conn.execute("SELECT COUNT(*) FROM vet_calls")
            stats['total_calls'] = cursor.fetchone()[0]
            
            # Консультации за сегодня
            today = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.execute("SELECT COUNT(*) FROM consultations WHERE DATE(created_at) = ?", (today,))
            stats['today_consultations'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            st.error(f"Ошибка получения статистики: {e}")
            return {'total_users': 0, 'total_consultations': 0, 'total_calls': 0, 'today_consultations': 0}
    
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

def main():
    st.set_page_config(
        page_title="Админ-панель ветеринарного бота",
        page_icon="🩺",
        layout="wide"
    )
    
    # Заголовок
    st.title("🩺 Админ-панель ветеринарного бота v2.1.0")
    st.markdown("---")
    
    # Проверка подключения к БД
    admin = VetBotAdmin()
    
    # Тест подключения
    try:
        conn = admin.get_db_connection()
        if conn:
            st.success("✅ Подключение к базе данных установлено")
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
        ["📊 Статистика", "👥 Пользователи", "💬 Консультации", "ℹ️ Информация"]
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
            st.metric("📞 Всего вызовов", stats['total_calls'])
        
        with col4:
            st.metric("📅 Консультаций сегодня", stats['today_consultations'])
        
        st.markdown("---")
        
        # График активности (заглушка)
        st.subheader("📈 Активность по дням")
        st.info("График активности будет добавлен в следующей версии")
    
    # Пользователи
    elif page == "👥 Пользователи":
        st.header("👥 Последние пользователи")
        
        users_df = admin.get_recent_users(20)
        
        if not users_df.empty:
            st.dataframe(users_df, use_container_width=True)
        else:
            st.info("Пользователи не найдены")
    
    # Консультации
    elif page == "💬 Консультации":
        st.header("💬 Последние консультации")
        
        consultations_df = admin.get_recent_consultations(20)
        
        if not consultations_df.empty:
            for _, row in consultations_df.iterrows():
                with st.expander(f"Консультация #{row['id']} - {row['username'] or 'Аноним'}"):
                    st.write(f"**Пользователь:** {row['user_id']}")
                    st.write(f"**Вопрос:** {row['question']}")
                    st.write(f"**Ответ AI:** {row['response'][:200]}...")
                    st.write(f"**Дата:** {row['created_at']}")
        else:
            st.info("Консультации не найдены")
    
    # Информация
    elif page == "ℹ️ Информация":
        st.header("ℹ️ Информация о системе")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤖 Telegram бот")
            st.write("- AI-консультации с DeepSeek")
            st.write("- Кликабельный номер экстренной связи")
            st.write("- Форма вызова ветеринара")
            
        with col2:
            st.subheader("🌐 Веб-приложение")
            st.write("- Порт: 5000")
            st.write("- Форма вызова врача")
            st.write("- Статические файлы")
        
        st.markdown("---")
        
        st.subheader("📊 Версия системы")
        st.code("Vetbot3 v2.1.0")
        
        st.subheader("🔧 Компоненты")
        st.write("- Python 3.x")
        st.write("- Streamlit")
        st.write("- SQLite")
        st.write("- Telegram Bot API")
        st.write("- DeepSeek AI API")
    
    # Информация в боковой панели
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **🩺 Админ-панель v2.1.0**
    
    Функции:
    - 📊 Статистика использования
    - 👥 Управление пользователями  
    - 💬 Просмотр консультаций
    - ℹ️ Информация о системе
    
    Для обновления данных перезагрузите страницу.
    """)

if __name__ == "__main__":
    main()
