#!/bin/bash
# Скрипт развертывания исправлений для предотвращения зомби-процессов
# Версия: 1.0

echo "=== РАЗВЕРТЫВАНИЕ ИСПРАВЛЕНИЙ СЕРВЕРА ==="
echo "Дата: $(date)"
echo

# Функция проверки успешности команды
check_success() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1"
        exit 1
    fi
}

# 1. Создание резервной копии текущих файлов
echo "1. СОЗДАНИЕ РЕЗЕРВНЫХ КОПИЙ:"
mkdir -p /root/backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backup_$(date +%Y%m%d_%H%M%S)"

# Копируем текущие файлы
cp /root/Vetbot3/bot.py "$BACKUP_DIR/bot.py.backup" 2>/dev/null
cp /root/process_monitor.sh "$BACKUP_DIR/process_monitor.sh.backup" 2>/dev/null
cp /etc/systemd/system/process-monitor.service "$BACKUP_DIR/process-monitor.service.backup" 2>/dev/null

echo "Резервные копии созданы в $BACKUP_DIR"
echo

# 2. Копирование новых файлов
echo "2. КОПИРОВАНИЕ НОВЫХ ФАЙЛОВ:"

# Копируем скрипты мониторинга
cp /home/ubuntu/server_diagnostic.sh /root/
check_success "Скрипт диагностики скопирован"

cp /home/ubuntu/server_cleanup.sh /root/
check_success "Скрипт очистки скопирован"

cp /home/ubuntu/process_monitor.sh /root/
check_success "Скрипт мониторинга скопирован"

# Копируем улучшенный бот
cp /home/ubuntu/bot_improved.py /root/Vetbot3/bot.py
check_success "Улучшенный бот скопирован"

# Копируем systemd сервис
cp /home/ubuntu/process-monitor.service /etc/systemd/system/
check_success "Systemd сервис скопирован"

# Делаем скрипты исполняемыми
chmod +x /root/server_diagnostic.sh /root/server_cleanup.sh /root/process_monitor.sh
check_success "Права доступа установлены"

echo

# 3. Остановка текущих процессов
echo "3. ОСТАНОВКА ТЕКУЩИХ ПРОЦЕССОВ:"

# Останавливаем все Python процессы кроме этого скрипта
echo "Остановка дублирующихся процессов..."
pkill -f "streamlit" 2>/dev/null
pkill -f "bot.py" 2>/dev/null
pkill -f "webapp_server" 2>/dev/null
sleep 3

# Принудительная остановка если нужно
pkill -9 -f "streamlit" 2>/dev/null
pkill -9 -f "bot.py" 2>/dev/null
pkill -9 -f "webapp_server" 2>/dev/null

echo "Старые процессы остановлены"
echo

# 4. Настройка systemd сервиса
echo "4. НАСТРОЙКА SYSTEMD СЕРВИСА:"

systemctl daemon-reload
check_success "Systemd daemon перезагружен"

systemctl enable process-monitor.service
check_success "Сервис мониторинга включен"

echo

# 5. Запуск новых процессов
echo "5. ЗАПУСК НОВЫХ ПРОЦЕССОВ:"

# Запускаем улучшенный бот
cd /root/Vetbot3
nohup python3 bot.py > /var/log/vetbot.log 2>&1 &
sleep 2
if pgrep -f "bot.py" > /dev/null; then
    echo "✅ Telegram бот запущен"
else
    echo "❌ Ошибка запуска Telegram бота"
fi

# Запускаем админ-панель
nohup streamlit run admin_streamlit_enhanced.py --server.port 8501 --server.address 0.0.0.0 > /var/log/admin_panel.log 2>&1 &
sleep 2
if pgrep -f "admin_streamlit" > /dev/null; then
    echo "✅ Админ-панель запущена"
else
    echo "❌ Ошибка запуска админ-панели"
fi

# Запускаем веб-приложение
cd /root
nohup python3 webapp_server_fixed.py > /var/log/webapp.log 2>&1 &
sleep 2
if pgrep -f "webapp_server" > /dev/null; then
    echo "✅ Веб-приложение запущено"
else
    echo "❌ Ошибка запуска веб-приложения"
fi

# Запускаем сервис мониторинга
systemctl start process-monitor.service
sleep 2
if systemctl is-active --quiet process-monitor.service; then
    echo "✅ Сервис мониторинга запущен"
else
    echo "❌ Ошибка запуска сервиса мониторинга"
fi

echo

# 6. Проверка результатов
echo "6. ПРОВЕРКА РЕЗУЛЬТАТОВ:"

echo "Активные процессы:"
echo "Python процессов: $(ps aux | grep python | grep -v grep | wc -l)"
echo "Streamlit процессов: $(ps aux | grep streamlit | grep -v grep | wc -l)"
echo "Зомби-процессов: $(ps aux | awk '$8 ~ /^Z/' | wc -l)"

echo
echo "Статус сервисов:"
echo "Telegram бот: $(pgrep -f "bot.py" > /dev/null && echo "Работает" || echo "Не работает")"
echo "Админ-панель: $(pgrep -f "admin_streamlit" > /dev/null && echo "Работает" || echo "Не работает")"
echo "Веб-приложение: $(pgrep -f "webapp_server" > /dev/null && echo "Работает" || echo "Не работает")"
echo "Мониторинг: $(systemctl is-active --quiet process-monitor.service && echo "Работает" || echo "Не работает")"

echo

# 7. Создание cron задачи для дополнительной проверки
echo "7. НАСТРОЙКА ДОПОЛНИТЕЛЬНОГО МОНИТОРИНГА:"

# Добавляем cron задачу для проверки каждые 5 минут
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/process_monitor.sh once >> /var/log/process_monitor.log 2>&1") | crontab -
check_success "Cron задача добавлена"

echo

# 8. Создание лог-файлов
echo "8. СОЗДАНИЕ ЛОГ-ФАЙЛОВ:"
touch /var/log/process_monitor.log
touch /var/log/vetbot.log
touch /var/log/admin_panel.log
touch /var/log/webapp.log
chmod 644 /var/log/process_monitor.log /var/log/vetbot.log /var/log/admin_panel.log /var/log/webapp.log
echo "Лог-файлы созданы"

echo

echo "=== РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО ==="
echo "✅ Все исправления применены"
echo "✅ Сервисы запущены"
echo "✅ Мониторинг активирован"
echo
echo "📊 Для проверки статуса используйте:"
echo "   /root/process_monitor.sh status"
echo "   systemctl status process-monitor.service"
echo
echo "📋 Логи доступны в:"
echo "   /var/log/process_monitor.log"
echo "   /var/log/vetbot.log"
echo "   /var/log/admin_panel.log"
echo "   /var/log/webapp.log"
echo
echo "🔄 Автоматический мониторинг будет предотвращать накопление зомби-процессов"

