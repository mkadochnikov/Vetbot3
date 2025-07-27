"""
Flask сервер для хостинга веб-приложения вызова ветеринара
"""

import os
import logging
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session

from vetbot_improved.config import WEBAPP_PORT, BASE_DIR
from vetbot_improved.database.base import get_db
from vetbot_improved.models import VetCall

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('./logs/webapp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создание Flask приложения
app = Flask(__name__)
CORS(app)  # Разрешить CORS для всех доменов

# Путь к файлам веб-приложения
WEBAPP_DIR = os.path.join(BASE_DIR, 'web', 'static')

@app.route('/')
def index():
    """Главная страница веб-приложения"""
    try:
        return send_from_directory(WEBAPP_DIR, 'index.html')
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
        db = next(get_db())
        try:
            vet_call = VetCall(
                user_id=data.get('user_id'),
                name=name,
                phone=phone,
                address=address,
                pet_type=data.get('pet_type'),
                pet_name=data.get('pet_name'),
                pet_age=data.get('pet_age'),
                problem=data.get('problem'),
                urgency=data.get('urgency'),
                preferred_time=data.get('preferred_time'),
                comments=data.get('comments')
            )
            db.add(vet_call)
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'Заявка успешно отправлена! Врач свяжется с вами в ближайшее время.',
                'request_id': vet_call.id
            })
            
        except Exception as e:
            db.rollback()
            logger.error(f"Ошибка при обработке заявки: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Произошла ошибка при отправке заявки. Попробуйте позже.'
            }), 500
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Ошибка при обработке заявки: {str(e)}")
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
    return jsonify({"status": "ok", "service": "vet-webapp"})

@app.route('/api/requests')
def get_requests():
    """API для получения заявок (для админ-панели)"""
    try:
        db = next(get_db())
        try:
            vet_calls = db.query(VetCall).order_by(VetCall.created_at.desc()).all()
            
            requests = []
            for call in vet_calls:
                requests.append({
                    'id': call.id,
                    'name': call.name,
                    'phone': call.phone,
                    'address': call.address,
                    'created_at': call.created_at.isoformat(),
                    'status': call.status
                })
            
            return jsonify(requests)
            
        except Exception as e:
            logger.error(f"Ошибка при получении заявок: {str(e)}")
            return jsonify([]), 500
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Ошибка при получении заявок: {str(e)}")
        return jsonify([]), 500

def main():
    """Основная функция для запуска веб-сервера"""
    # Создание директории для статических файлов, если она не существует
    os.makedirs(WEBAPP_DIR, exist_ok=True)
    
    # Копирование файлов веб-приложения из оригинального проекта
    original_webapp_dir = os.path.join(BASE_DIR.parent, 'webapp')
    if os.path.exists(original_webapp_dir):
        import shutil
        for file_name in ['index.html', 'styles.css', 'script.js']:
            src_file = os.path.join(original_webapp_dir, file_name)
            dst_file = os.path.join(WEBAPP_DIR, file_name)
            if os.path.exists(src_file):
                shutil.copy2(src_file, dst_file)
                logger.info(f"Copied {file_name} to {WEBAPP_DIR}")
    
    # Запуск веб-сервера
    app.run(host='0.0.0.0', port=WEBAPP_PORT, debug=False)

if __name__ == '__main__':
    main()