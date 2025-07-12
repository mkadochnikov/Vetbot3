#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask сервер для хостинга веб-приложения вызова ветеринара
"""

import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template_string, send_from_directory, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешить CORS для всех доменов

# Путь к файлам веб-приложения
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), 'webapp')
DB_PATH = os.path.join(os.path.dirname(__file__), 'vetbot.db')

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создание таблицы для заявок на вызов врача
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vet_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new'
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Главная страница веб-приложения"""
    try:
        with open(os.path.join(WEBAPP_DIR, 'index.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Веб-приложение не найдено", 404

@app.route('/submit_request', methods=['POST'])
def submit_request():
    """Обработка заявки на вызов врача"""
    try:
        # Получение данных из JSON
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False, 
                'message': 'Не получены данные'
            }), 400
        
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        address = data.get('address', '').strip()
        
        # Валидация данных
        if not name or not phone or not address:
            return jsonify({
                'success': False,
                'message': 'Все поля обязательны для заполнения'
            }), 400
        
        # Сохранение в базу данных
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vet_requests (name, phone, address, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, phone, address, datetime.now()))
        
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Заявка успешно отправлена! Врач свяжется с вами в ближайшее время.',
            'request_id': request_id
        })
        
    except Exception as e:
        app.logger.error(f"Ошибка при обработке заявки: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Произошла ошибка при отправке заявки. Попробуйте позже.'
        }), 500

@app.route('/styles.css')
def styles():
    """CSS стили"""
    return send_from_directory(WEBAPP_DIR, 'styles.css', mimetype='text/css')

@app.route('/script.js')
def script():
    """JavaScript файл"""
    return send_from_directory(WEBAPP_DIR, 'script.js', mimetype='application/javascript')

@app.route('/health')
def health():
    """Проверка здоровья сервиса"""
    return {"status": "ok", "service": "vet-webapp"}

@app.route('/api/requests')
def get_requests():
    """API для получения заявок (для админ-панели)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, phone, address, created_at, status
            FROM vet_requests
            ORDER BY created_at DESC
        ''')
        
        requests = []
        for row in cursor.fetchall():
            requests.append({
                'id': row[0],
                'name': row[1],
                'phone': row[2],
                'address': row[3],
                'created_at': row[4],
                'status': row[5]
            })
        
        conn.close()
        return jsonify(requests)
        
    except Exception as e:
        app.logger.error(f"Ошибка при получении заявок: {str(e)}")
        return jsonify([]), 500

if __name__ == '__main__':
    # Инициализация базы данных при запуске
    init_db()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

