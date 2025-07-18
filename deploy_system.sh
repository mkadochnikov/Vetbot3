#!/bin/bash

# Скрипт развертывания системы ветеринарных ботов
# Версия: 1.0

echo "🚀 РАЗВЕРТЫВАНИЕ СИСТЕМЫ ВЕТЕРИНАРНЫХ БОТОВ"
echo "=============================================="

# Проверка окружения
echo "🔍 Проверка окружения..."

if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

if [ ! -f "enhanced_bot.py" ]; then
    echo "❌ Основной бот не найден!"
    exit 1
fi

if [ ! -f "vet_doctor_bot.py" ]; then
    echo "❌ Бот врачей не найден!"
    exit 1
fi

echo "✅ Все файлы найдены"

# Остановка существующих процессов
echo "🛑 Остановка существующих процессов..."
pkill -f "enhanced_bot.py" || true
pkill -f "vet_doctor_bot.py" || true
pkill -f "admin_streamlit" || true

sleep 5

# Запуск основного бота
echo "🤖 Запуск основного бота..."
nohup python3 enhanced_bot.py > logs/main_bot.log 2>&1 &
MAIN_BOT_PID=$!
echo "✅ Основной бот запущен (PID: $MAIN_BOT_PID)"

sleep 3

# Запуск бота врачей
echo "👨‍⚕️ Запуск бота врачей..."
nohup python3 vet_doctor_bot.py > logs/doctor_bot.log 2>&1 &
DOCTOR_BOT_PID=$!
echo "✅ Бот врачей запущен (PID: $DOCTOR_BOT_PID)"

sleep 3

# Запуск админ-панели
echo "👨‍💼 Запуск админ-панели..."
mkdir -p logs
nohup streamlit run admin_streamlit_enhanced.py --server.port=8501 --server.address=0.0.0.0 > logs/admin_panel.log 2>&1 &
ADMIN_PANEL_PID=$!
echo "✅ Админ-панель запущена (PID: $ADMIN_PANEL_PID)"

sleep 5

# Проверка статуса
echo "📊 Проверка статуса сервисов..."

if ps -p $MAIN_BOT_PID > /dev/null; then
    echo "✅ Основной бот работает (PID: $MAIN_BOT_PID)"
else
    echo "❌ Основной бот не запустился"
fi

if ps -p $DOCTOR_BOT_PID > /dev/null; then
    echo "✅ Бот врачей работает (PID: $DOCTOR_BOT_PID)"
else
    echo "❌ Бот врачей не запустился"
fi

if ps -p $ADMIN_PANEL_PID > /dev/null; then
    echo "✅ Админ-панель работает (PID: $ADMIN_PANEL_PID)"
else
    echo "❌ Админ-панель не запустилась"
fi

# Сохранение PID файлов
echo $MAIN_BOT_PID > pids/main_bot.pid
echo $DOCTOR_BOT_PID > pids/doctor_bot.pid
echo $ADMIN_PANEL_PID > pids/admin_panel.pid

echo ""
echo "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "=========================="
echo "📱 Основной бот: @murzikpro_bot"
echo "👨‍⚕️ Бот врачей: @[имя_бота_врачей]"
echo "👨‍💼 Админ-панель: http://localhost:8501"
echo ""
echo "📋 Логи:"
echo "   Основной бот: logs/main_bot.log"
echo "   Бот врачей: logs/doctor_bot.log"
echo "   Админ-панель: logs/admin_panel.log"
echo ""
echo "🔧 Управление:"
echo "   Остановить все: ./stop_system.sh"
echo "   Перезапустить: ./restart_system.sh"
echo "   Статус: ./status_system.sh"

