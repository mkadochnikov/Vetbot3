#!/bin/bash

# Простой скрипт для очистки всех процессов ботов
# Версия: 2.1.0

echo "🧹 Принудительная очистка всех процессов ботов..."

# Остановка всех процессов enhanced_bot.py
echo "🤖 Остановка всех экземпляров Telegram бота..."
pkill -f "enhanced_bot.py" 2>/dev/null && echo "✅ Старые боты остановлены" || echo "⚠️ Боты не найдены"

# Остановка всех процессов webapp_server.py
echo "🌐 Остановка всех экземпляров веб-приложения..."
pkill -f "webapp_server.py" 2>/dev/null && echo "✅ Старые веб-приложения остановлены" || echo "⚠️ Веб-приложения не найдены"

# Остановка всех процессов start_all.py
echo "🚀 Остановка всех лаунчеров..."
pkill -f "start_all.py" 2>/dev/null && echo "✅ Старые лаунчеры остановлены" || echo "⚠️ Лаунчеры не найдены"

# Остановка всех процессов bot.py (если есть старые версии)
echo "🤖 Остановка старых версий бота..."
pkill -f "bot.py" 2>/dev/null && echo "✅ Старые версии бота остановлены" || echo "⚠️ Старые версии не найдены"

# Ожидание завершения процессов
sleep 3

# Проверка что все процессы действительно остановлены
REMAINING=$(ps aux | grep -E "(enhanced_bot|webapp_server|start_all|bot\.py)" | grep -v grep | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo "⚠️ Найдены оставшиеся процессы, принудительное завершение..."
    pkill -9 -f "enhanced_bot.py" 2>/dev/null
    pkill -9 -f "webapp_server.py" 2>/dev/null
    pkill -9 -f "start_all.py" 2>/dev/null
    pkill -9 -f "bot.py" 2>/dev/null
    sleep 2
fi

# Очистка PID файлов
rm -f vet_services.pid 2>/dev/null

echo "✅ Принудительная очистка завершена"

# Проверка результата
FINAL_CHECK=$(ps aux | grep -E "(enhanced_bot|webapp_server|start_all|bot\.py)" | grep -v grep | wc -l)
if [ $FINAL_CHECK -eq 0 ]; then
    echo "🎉 Все процессы ботов успешно остановлены!"
else
    echo "⚠️ Остались процессы:"
    ps aux | grep -E "(enhanced_bot|webapp_server|start_all|bot\.py)" | grep -v grep
fi

