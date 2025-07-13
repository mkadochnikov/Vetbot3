#!/bin/bash
# Диагностический скрипт для выявления проблем с процессами и CPU
# Версия: 1.0

echo "=== ДИАГНОСТИКА СЕРВЕРА $(date) ==="
echo

# 1. Общая информация о системе
echo "1. ОБЩАЯ ИНФОРМАЦИЯ О СИСТЕМЕ:"
echo "Uptime: $(uptime)"
echo "Память: $(free -h | grep Mem)"
echo "Диск: $(df -h / | tail -1)"
echo

# 2. Загрузка CPU
echo "2. ЗАГРУЗКА CPU:"
echo "Текущая загрузка:"
top -bn1 | grep "Cpu(s)" | head -1
echo
echo "Топ процессов по CPU:"
ps aux --sort=-%cpu | head -10
echo

# 3. Анализ процессов
echo "3. АНАЛИЗ ПРОЦЕССОВ:"
echo "Общее количество процессов:"
ps aux | wc -l
echo
echo "Зомби-процессы:"
ps aux | awk '$8 ~ /^Z/ { print $2, $11 }' | wc -l
echo "Список зомби-процессов:"
ps aux | awk '$8 ~ /^Z/ { print $2, $11 }'
echo

# 4. Python процессы
echo "4. PYTHON ПРОЦЕССЫ:"
echo "Количество Python процессов:"
ps aux | grep python | grep -v grep | wc -l
echo
echo "Python процессы:"
ps aux | grep python | grep -v grep | head -20
echo

# 5. Streamlit процессы
echo "5. STREAMLIT ПРОЦЕССЫ:"
echo "Количество Streamlit процессов:"
ps aux | grep streamlit | grep -v grep | wc -l
echo
echo "Streamlit процессы:"
ps aux | grep streamlit | grep -v grep
echo

# 6. Процессы Telegram бота
echo "6. TELEGRAM BOT ПРОЦЕССЫ:"
echo "Процессы бота:"
ps aux | grep -E "(bot\.py|telegram)" | grep -v grep
echo

# 7. Анализ родительских процессов зомби
echo "7. АНАЛИЗ РОДИТЕЛЬСКИХ ПРОЦЕССОВ:"
echo "Процессы с наибольшим количеством дочерних:"
ps -eo pid,ppid,cmd --no-headers | awk '{print $2}' | sort | uniq -c | sort -nr | head -10
echo

# 8. Сетевые соединения
echo "8. СЕТЕВЫЕ СОЕДИНЕНИЯ:"
echo "Активные соединения на портах 8501, 5000:"
netstat -tulpn | grep -E ":8501|:5000" 2>/dev/null || ss -tulpn | grep -E ":8501|:5000"
echo

# 9. Системные ресурсы
echo "9. СИСТЕМНЫЕ РЕСУРСЫ:"
echo "Открытые файлы:"
lsof | wc -l 2>/dev/null || echo "lsof недоступен"
echo
echo "Лимиты процессов:"
ulimit -a | grep -E "(processes|files)"
echo

# 10. Логи системы (последние ошибки)
echo "10. СИСТЕМНЫЕ ЛОГИ:"
echo "Последние критические ошибки:"
dmesg | tail -10 | grep -i error 2>/dev/null || echo "Нет критических ошибок в dmesg"
echo

echo "=== ДИАГНОСТИКА ЗАВЕРШЕНА ==="

