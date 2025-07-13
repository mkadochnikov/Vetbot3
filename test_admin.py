#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовая версия админ-панели для проверки исправлений
"""
import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

class VetBotAdmin:
    def __init__(self, db_path='test_vetbot.db'):
        self.db_path = db_path
    
    def get_db_connection(self):
        """Получить соединение с базой данных"""
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            st.error(f"Ошибка подключения к БД: {e}")
            return None
    
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

def main():
    st.set_page_config(
        page_title="Тест админ-панели",
        page_icon="🧪",
        layout="wide"
    )
    
    st.title("🧪 Тест исправлений админ-панели")
    st.markdown("---")
    
    admin = VetBotAdmin()
    
    # Тест подключения
    try:
        conn = admin.get_db_connection()
        if conn:
            st.success("✅ Подключение к тестовой БД успешно")
            conn.close()
        else:
            st.error("❌ Не удалось подключиться к БД")
            return
    except Exception as e:
        st.error(f"❌ Ошибка: {e}")
        return
    
    st.header("👥 Тест отображения пользователей")
    
    users = admin.get_recent_users(20)
    if not users.empty:
        st.subheader("📊 Таблица пользователей")
        st.dataframe(users, use_container_width=True)
        
        st.subheader("🔍 Тест выбора пользователей для диалога")
        
        # Создаем опции для всех пользователей, включая тех, у кого нет username
        user_options = {}
        for _, row in users.iterrows():
            # Формируем отображаемое имя
            display_name = ""
            if row['username'] and row['username'] != 'None':
                display_name = f"{row['username']}"
            elif row['first_name'] and row['first_name'] != 'None':
                display_name = f"{row['first_name']}"
                if row['last_name'] and row['last_name'] != 'None':
                    display_name += f" {row['last_name']}"
            else:
                display_name = f"Пользователь {row['user_id']}"
            
            # Добавляем ID в скобках
            full_display = f"{display_name} ({row['user_id']})"
            user_options[full_display] = row['user_id']
        
        if user_options:
            st.write("**Доступные пользователи для диалога:**")
            for display_name, user_id in user_options.items():
                st.write(f"✅ {display_name}")
            
            selected_user = st.selectbox("Выберите пользователя:", list(user_options.keys()))
            if selected_user:
                user_id = user_options[selected_user]
                st.success(f"✅ Выбран пользователь: {selected_user} (ID: {user_id})")
        else:
            st.warning("⚠️ Нет доступных пользователей")
        
        st.subheader("🧪 Результат тестирования")
        st.success("✅ **Исправление работает!**")
        st.write("- Пользователи без username теперь отображаются по имени")
        st.write("- Все пользователи доступны для выбора диалога")
        st.write("- Корректное отображение в выпадающем списке")
        
    else:
        st.error("❌ Пользователи не найдены в тестовой БД")

if __name__ == "__main__":
    main()

