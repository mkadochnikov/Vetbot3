#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask сервер для хостинга веб-приложения вызова ветеринара
"""

import os
from flask import Flask, render_template_string, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешить CORS для всех доменов

# Путь к файлам веб-приложения
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), 'webapp')

@app.route('/')
def index():
    """Главная страница веб-приложения"""
    try:
        with open(os.path.join(WEBAPP_DIR, 'index.html'), 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Веб-приложение не найдено", 404

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

