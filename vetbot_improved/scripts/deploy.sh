#!/bin/bash

# Скрипт для развертывания улучшенной версии системы ветеринарных ботов
# Версия: 1.0

echo "🚀 РАЗВЕРТЫВАНИЕ УЛУЧШЕННОЙ СИСТЕМЫ ВЕТЕРИНАРНЫХ БОТОВ"
echo "======================================================"

# Проверка наличия Docker и Docker Compose
echo "🔍 Проверка окружения..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен!"
    echo "Установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не установлен!"
    echo "Установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте файл .env на основе .env.example"
    exit 1
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p data logs pids

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка и запуск контейнеров
echo "🏗️ Сборка и запуск контейнеров..."
docker-compose up -d --build

# Проверка статуса
echo "📊 Проверка статуса контейнеров..."
docker-compose ps

# Проверка логов
echo "📋 Проверка логов..."
docker-compose logs --tail=20

echo ""
echo "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "=========================="
echo "📱 Основной бот: @murzikpro_bot"
echo "👨‍⚕️ Бот врачей: @[имя_бота_врачей]"
echo "👨‍💼 Админ-панель: http://localhost:8501"
echo "🌐 Веб-приложение: http://localhost:5000"
echo ""
echo "📋 Логи:"
echo "   docker-compose logs -f"
echo ""
echo "🔧 Управление:"
echo "   Остановить: docker-compose down"
echo "   Перезапустить: docker-compose restart"
echo "   Статус: docker-compose ps"
echo ""
echo "⚠️ Важно: Убедитесь, что порты 5000 и 8501 открыты в брандмауэре"