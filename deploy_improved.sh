#!/bin/bash

# Скрипт для развертывания улучшенной версии системы ветеринарных ботов на сервере
# Версия: 1.0

echo "🚀 РАЗВЕРТЫВАНИЕ УЛУЧШЕННОЙ СИСТЕМЫ ВЕТЕРИНАРНЫХ БОТОВ НА СЕРВЕРЕ"
echo "================================================================="

# Проверка аргументов
if [ $# -lt 1 ]; then
    echo "❌ Не указан адрес сервера!"
    echo "Использование: $0 user@server [port]"
    exit 1
fi

SERVER=$1
PORT=${2:-22}

echo "🔍 Проверка соединения с сервером..."
ssh -p $PORT $SERVER "echo '✅ Соединение установлено'" || {
    echo "❌ Не удалось подключиться к серверу!"
    exit 1
}

# Создание архива с улучшенной версией
echo "📦 Создание архива с улучшенной версией..."
cd vetbot_improved
tar -czf ../vetbot_improved.tar.gz .
cd ..

# Копирование архива на сервер
echo "📤 Копирование архива на сервер..."
scp -P $PORT vetbot_improved.tar.gz $SERVER:~/ || {
    echo "❌ Не удалось скопировать архив на сервер!"
    exit 1
}

# Создание директории и распаковка архива на сервере
echo "📂 Распаковка архива на сервере..."
ssh -p $PORT $SERVER "mkdir -p ~/vetbot_improved && tar -xzf ~/vetbot_improved.tar.gz -C ~/vetbot_improved" || {
    echo "❌ Не удалось распаковать архив на сервере!"
    exit 1
}

# Копирование .env файла, если он существует
if [ -f "vetbot_improved/.env" ]; then
    echo "📤 Копирование .env файла на сервер..."
    scp -P $PORT vetbot_improved/.env $SERVER:~/vetbot_improved/ || {
        echo "⚠️ Не удалось скопировать .env файл на сервер!"
        echo "Вам нужно будет создать его вручную на сервере."
    }
else
    echo "⚠️ Файл .env не найден!"
    echo "Вам нужно будет создать его на сервере на основе .env.example."
fi

# Установка зависимостей на сервере
echo "📦 Установка зависимостей на сервере..."
ssh -p $PORT $SERVER "cd ~/vetbot_improved && pip install -r requirements.txt" || {
    echo "⚠️ Не удалось установить зависимости на сервере!"
    echo "Вам нужно будет установить их вручную."
}

# Запуск миграции данных, если есть старая база
echo "🔄 Запуск миграции данных на сервере..."
ssh -p $PORT $SERVER "cd ~/vetbot_improved && python -m scripts.migrate_data" || {
    echo "⚠️ Не удалось выполнить миграцию данных на сервере!"
    echo "Вам нужно будет выполнить ее вручную."
}

# Запуск системы на сервере
echo "🚀 Запуск системы на сервере..."
ssh -p $PORT $SERVER "cd ~/vetbot_improved && python run.py start" || {
    echo "⚠️ Не удалось запустить систему на сервере!"
    echo "Вам нужно будет запустить ее вручную."
}

# Удаление временных файлов
echo "🧹 Удаление временных файлов..."
rm vetbot_improved.tar.gz

echo ""
echo "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "=========================="
echo "📱 Основной бот: @murzikpro_bot"
echo "👨‍⚕️ Бот врачей: @[имя_бота_врачей]"
echo "👨‍💼 Админ-панель: http://server:8501"
echo "🌐 Веб-приложение: http://server:5000"
echo ""
echo "📋 Логи:"
echo "   ssh $SERVER 'cd ~/vetbot_improved && tail -f logs/*.log'"
echo ""
echo "🔧 Управление:"
echo "   Остановить: ssh $SERVER 'cd ~/vetbot_improved && python run.py stop'"
echo "   Перезапустить: ssh $SERVER 'cd ~/vetbot_improved && python run.py restart'"
echo "   Статус: ssh $SERVER 'cd ~/vetbot_improved && python run.py status'"
echo ""
echo "⚠️ Важно: Убедитесь, что порты 5000 и 8501 открыты в брандмауэре сервера"