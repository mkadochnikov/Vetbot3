# 🚀 Инструкция по миграции на улучшенную версию

Данный документ содержит инструкции по миграции с оригинальной версии Vetbot3 на улучшенную версию.

## 📋 Содержание

1. [Подготовка](#подготовка)
2. [Развертывание на том же сервере](#развертывание-на-том-же-сервере)
3. [Развертывание на новом сервере](#развертывание-на-новом-сервере)
4. [Миграция данных](#миграция-данных)
5. [Проверка работоспособности](#проверка-работоспособности)
6. [Откат в случае проблем](#откат-в-случае-проблем)

## 🔧 Подготовка

1. **Резервное копирование**
   ```bash
   # Создание резервной копии базы данных
   cp /path/to/vetbot.db /path/to/vetbot.db.backup
   
   # Архивирование всего проекта
   tar -czf vetbot3_backup.tar.gz /path/to/Vetbot3
   ```

2. **Проверка зависимостей**
   ```bash
   # Установка необходимых пакетов
   pip install -r vetbot_improved/requirements.txt
   ```

## 🚀 Развертывание на том же сервере

1. **Остановка текущей версии**
   ```bash
   # Остановка всех компонентов
   cd /path/to/Vetbot3
   ./stop_system.sh
   ```

2. **Копирование улучшенной версии**
   ```bash
   # Создание директории для улучшенной версии
   mkdir -p /path/to/Vetbot3_improved
   
   # Копирование файлов
   cp -r vetbot_improved/* /path/to/Vetbot3_improved/
   ```

3. **Настройка переменных окружения**
   ```bash
   # Копирование существующего .env файла
   cp /path/to/Vetbot3/.env /path/to/Vetbot3_improved/
   
   # Редактирование при необходимости
   nano /path/to/Vetbot3_improved/.env
   ```

4. **Запуск миграции данных**
   ```bash
   cd /path/to/Vetbot3_improved
   python -m scripts.migrate_data
   ```

5. **Запуск улучшенной версии**
   ```bash
   cd /path/to/Vetbot3_improved
   python run.py start
   ```

## 🌐 Развертывание на новом сервере

1. **Использование скрипта развертывания**
   ```bash
   # Запуск скрипта развертывания
   ./deploy_improved.sh user@server [port]
   ```

2. **Ручное развертывание**
   ```bash
   # Копирование архива на сервер
   scp vetbot_improved.tar.gz user@server:~/
   
   # Распаковка архива
   ssh user@server "mkdir -p ~/vetbot_improved && tar -xzf ~/vetbot_improved.tar.gz -C ~/vetbot_improved"
   
   # Копирование .env файла
   scp vetbot_improved/.env user@server:~/vetbot_improved/
   
   # Установка зависимостей
   ssh user@server "cd ~/vetbot_improved && pip install -r requirements.txt"
   
   # Запуск системы
   ssh user@server "cd ~/vetbot_improved && python run.py start"
   ```

## 📊 Миграция данных

1. **Автоматическая миграция**
   ```bash
   # Запуск скрипта миграции
   cd /path/to/Vetbot3_improved
   python -m scripts.migrate_data
   ```

2. **Ручная миграция (если автоматическая не сработала)**
   ```bash
   # Копирование базы данных
   cp /path/to/Vetbot3/vetbot.db /path/to/Vetbot3_improved/data/
   
   # Инициализация новой базы данных
   cd /path/to/Vetbot3_improved
   python -m database.init_db
   ```

## ✅ Проверка работоспособности

1. **Проверка статуса компонентов**
   ```bash
   cd /path/to/Vetbot3_improved
   python run.py status
   ```

2. **Проверка логов**
   ```bash
   # Просмотр логов основного бота
   tail -f /path/to/Vetbot3_improved/logs/main_bot.log
   
   # Просмотр логов бота врачей
   tail -f /path/to/Vetbot3_improved/logs/doctor_bot.log
   
   # Просмотр логов веб-приложения
   tail -f /path/to/Vetbot3_improved/logs/webapp.log
   
   # Просмотр логов админ-панели
   tail -f /path/to/Vetbot3_improved/logs/admin_panel.log
   ```

3. **Тестирование функциональности**
   - Отправьте сообщение основному боту
   - Проверьте работу веб-приложения
   - Проверьте работу админ-панели
   - Проверьте работу бота врачей

## 🔄 Откат в случае проблем

1. **Остановка улучшенной версии**
   ```bash
   cd /path/to/Vetbot3_improved
   python run.py stop
   ```

2. **Восстановление оригинальной версии**
   ```bash
   # Восстановление базы данных
   cp /path/to/vetbot.db.backup /path/to/Vetbot3/vetbot.db
   
   # Запуск оригинальной версии
   cd /path/to/Vetbot3
   ./start_system.sh
   ```

## 📞 Поддержка

Если у вас возникли проблемы с миграцией, обратитесь за помощью:
- GitHub Issues: https://github.com/mkadochnikov/Vetbot3/issues
- Email: support@murzik.pro