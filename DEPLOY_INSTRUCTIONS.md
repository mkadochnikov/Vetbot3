# 🚀 Инструкция по развертыванию улучшенной версии Vetbot3

## 📋 Что было сделано

✅ **Создан Pull Request** с улучшенной версией: https://github.com/mkadochnikov/Vetbot3/pull/1

✅ **Улучшенная версия** находится в ветке `improved-version-v3`

✅ **Модульная архитектура** с разделением на компоненты

✅ **SQLAlchemy ORM** для безопасной работы с базой данных

✅ **Docker контейнеризация** для простого развертывания

✅ **Система управления** всеми компонентами

## 🖥️ Развертывание на вашем сервере

### Шаг 1: Подключитесь к серверу
```bash
ssh -p 4828 user@46.252.251.117
```

### Шаг 2: Остановите старые процессы (если есть)
```bash
# Остановка всех процессов бота
pkill -f 'python.*bot' || true
pkill -f 'python.*admin' || true
pkill -f 'python.*webapp' || true
```

### Шаг 3: Создайте резервную копию (если есть старая версия)
```bash
# Если у вас уже есть Vetbot3
if [ -d ~/Vetbot3 ]; then
    mv ~/Vetbot3 ~/Vetbot3_backup_$(date +%Y%m%d_%H%M%S)
fi
```

### Шаг 4: Клонируйте улучшенную версию
```bash
# Клонирование репозитория
git clone https://github.com/mkadochnikov/Vetbot3.git ~/Vetbot3

# Переход в директорию
cd ~/Vetbot3

# Переключение на улучшенную ветку
git checkout improved-version-v3

# Переход в директорию улучшенной версии
cd ~/Vetbot3/vetbot_improved
```

### Шаг 5: Установите зависимости
```bash
# Обновление pip
pip3 install --upgrade pip

# Установка зависимостей
pip3 install -r requirements.txt
```

### Шаг 6: Настройте конфигурацию
```bash
# Копирование примера конфигурации
cp .env.example .env

# Редактирование конфигурации
nano .env
```

**Настройте следующие параметры в .env файле:**
```env
# Токен основного бота (от @BotFather)
TELEGRAM_BOT_TOKEN=your_main_bot_token

# Токен бота врачей (от @BotFather) 
VET_BOT_TOKEN=your_doctor_bot_token

# API ключ DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key

# ID чата администратора (ваш Telegram ID)
ADMIN_CHAT_ID=your_telegram_id

# Остальные параметры можно оставить по умолчанию
```

### Шаг 7: Создайте необходимые директории
```bash
# Создание директорий для данных и логов
mkdir -p data logs pids
```

### Шаг 8: Мигрируйте данные (если есть старая база)
```bash
# Если у вас есть старая база данных vetbot.db
if [ -f ~/vetbot.db ]; then
    cp ~/vetbot.db data/vetbot_old.db
    python3 -m scripts.migrate_data
fi
```

### Шаг 9: Запустите систему
```bash
# Запуск всех компонентов
python3 run.py start
```

### Шаг 10: Проверьте статус
```bash
# Проверка статуса всех компонентов
python3 run.py status

# Просмотр логов
tail -f logs/*.log
```

## 🌐 Доступ к компонентам

После успешного запуска будут доступны:

- **🤖 Основной бот**: @murzikpro_bot (или ваш бот)
- **👨‍⚕️ Бот врачей**: настроенный в .env файле
- **🌐 Веб-приложение**: http://46.252.251.117:5000
- **👨‍💼 Админ-панель**: http://46.252.251.117:8501

## 🔧 Управление системой

```bash
cd ~/Vetbot3/vetbot_improved

# Запуск всех компонентов
python3 run.py start

# Остановка всех компонентов  
python3 run.py stop

# Перезапуск всех компонентов
python3 run.py restart

# Проверка статуса
python3 run.py status

# Миграция данных
python3 run.py migrate
```

## 📋 Просмотр логов

```bash
cd ~/Vetbot3/vetbot_improved

# Все логи
tail -f logs/*.log

# Основной бот
tail -f logs/main_bot.log

# Бот врачей  
tail -f logs/doctor_bot.log

# Веб-приложение
tail -f logs/webapp.log

# Админ-панель
tail -f logs/admin_panel.log
```

## 🔙 Откат к старой версии

Если что-то пошло не так, можно легко откатиться:

```bash
cd ~/Vetbot3

# Остановка улучшенной версии
cd vetbot_improved && python3 run.py stop

# Переключение на основную ветку
cd ~/Vetbot3 && git checkout main

# Запуск старой версии (если нужно)
# Используйте ваши старые скрипты запуска
```

## 🐳 Альтернатива: Docker развертывание

Если у вас установлен Docker:

```bash
cd ~/Vetbot3/vetbot_improved

# Настройка .env файла
cp .env.example .env
nano .env

# Запуск с Docker Compose
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

## ⚠️ Важные моменты

1. **Порты**: Убедитесь, что порты 5000 и 8501 открыты в брандмауэре
2. **Токены**: Обязательно настройте все токены в .env файле
3. **Права**: Убедитесь, что у пользователя есть права на запись в домашнюю директорию
4. **Python**: Требуется Python 3.8 или выше

## 🆘 Помощь

Если возникли проблемы:

1. **Проверьте логи**: `tail -f ~/Vetbot3/vetbot_improved/logs/*.log`
2. **Проверьте статус**: `cd ~/Vetbot3/vetbot_improved && python3 run.py status`
3. **Проверьте .env файл**: убедитесь, что все токены настроены правильно
4. **Проверьте порты**: `netstat -tlnp | grep -E ':(5000|8501)'`

## 🔗 Полезные ссылки

- **Pull Request**: https://github.com/mkadochnikov/Vetbot3/pull/1
- **Репозиторий**: https://github.com/mkadochnikov/Vetbot3
- **Ветка с улучшениями**: improved-version-v3

---

**🎉 Удачного развертывания!**