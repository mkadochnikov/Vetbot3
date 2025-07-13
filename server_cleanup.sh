#!/bin/bash
# Скрипт для очистки зомби-процессов и исправления высокой загрузки CPU
# Версия: 1.0

echo "=== ОЧИСТКА СЕРВЕРА $(date) ==="
echo

# Функция для безопасного завершения процессов
safe_kill() {
    local pids="$1"
    local signal="$2"
    local description="$3"
    
    if [ -n "$pids" ]; then
        echo "Завершение $description..."
        echo "PIDs: $pids"
        kill $signal $pids 2>/dev/null
        sleep 2
        # Проверяем, завершились ли процессы
        for pid in $pids; do
            if kill -0 $pid 2>/dev/null; then
                echo "Принудительное завершение PID $pid"
                kill -9 $pid 2>/dev/null
            fi
        done
        echo "Завершено: $description"
    else
        echo "Нет процессов для завершения: $description"
    fi
    echo
}

# 1. Сохранение текущего состояния
echo "1. СОХРАНЕНИЕ СОСТОЯНИЯ:"
ps aux > /tmp/processes_before_cleanup.txt
echo "Состояние процессов сохранено в /tmp/processes_before_cleanup.txt"
echo

# 2. Анализ проблемных процессов
echo "2. АНАЛИЗ ПРОБЛЕМНЫХ ПРОЦЕССОВ:"
zombie_count=$(ps aux | awk '$8 ~ /^Z/' | wc -l)
python_count=$(ps aux | grep python | grep -v grep | wc -l)
streamlit_count=$(ps aux | grep streamlit | grep -v grep | wc -l)

echo "Зомби-процессов: $zombie_count"
echo "Python процессов: $python_count"
echo "Streamlit процессов: $streamlit_count"
echo

# 3. Остановка дублирующихся Streamlit процессов
echo "3. ОЧИСТКА STREAMLIT ПРОЦЕССОВ:"
streamlit_pids=$(ps aux | grep streamlit | grep -v grep | awk '{print $2}' | tr '\n' ' ')
if [ -n "$streamlit_pids" ]; then
    echo "Найдены Streamlit процессы: $streamlit_pids"
    safe_kill "$streamlit_pids" "-TERM" "Streamlit процессов"
else
    echo "Streamlit процессы не найдены"
fi

# 4. Очистка дублирующихся Python процессов (кроме основного бота)
echo "4. ОЧИСТКА ДУБЛИРУЮЩИХСЯ PYTHON ПРОЦЕССОВ:"
# Находим основной процесс бота
main_bot_pid=$(ps aux | grep "bot\.py" | grep -v grep | head -1 | awk '{print $2}')
echo "Основной процесс бота PID: $main_bot_pid"

# Находим все Python процессы кроме основного бота и системных
duplicate_python_pids=$(ps aux | grep python | grep -v grep | grep -v "bot\.py" | grep -v "/usr/bin/python" | awk '{print $2}' | tr '\n' ' ')
if [ -n "$duplicate_python_pids" ]; then
    echo "Дублирующиеся Python процессы: $duplicate_python_pids"
    safe_kill "$duplicate_python_pids" "-TERM" "дублирующихся Python процессов"
else
    echo "Дублирующиеся Python процессы не найдены"
fi

# 5. Очистка зомби-процессов через родительские процессы
echo "5. ОЧИСТКА ЗОМБИ-ПРОЦЕССОВ:"
zombie_pids=$(ps aux | awk '$8 ~ /^Z/ {print $2}' | tr '\n' ' ')
if [ -n "$zombie_pids" ]; then
    echo "Зомби-процессы: $zombie_pids"
    # Находим родительские процессы зомби
    for zpid in $zombie_pids; do
        parent_pid=$(ps -o ppid= -p $zpid 2>/dev/null | tr -d ' ')
        if [ -n "$parent_pid" ] && [ "$parent_pid" != "1" ]; then
            echo "Перезапуск родительского процесса $parent_pid для зомби $zpid"
            kill -CHLD $parent_pid 2>/dev/null
        fi
    done
else
    echo "Зомби-процессы не найдены"
fi

# 6. Очистка временных файлов
echo "6. ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ:"
echo "Очистка /tmp..."
find /tmp -type f -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
find /tmp -type f -name "streamlit*" -delete 2>/dev/null || true
echo "Временные файлы очищены"
echo

# 7. Проверка системных лимитов
echo "7. ПРОВЕРКА СИСТЕМНЫХ ЛИМИТОВ:"
echo "Текущие лимиты процессов:"
ulimit -u
echo "Текущие лимиты файлов:"
ulimit -n
echo

# 8. Перезапуск основных сервисов
echo "8. ПЕРЕЗАПУСК ОСНОВНЫХ СЕРВИСОВ:"

# Проверяем, работает ли основной бот
if [ -n "$main_bot_pid" ] && kill -0 $main_bot_pid 2>/dev/null; then
    echo "Основной бот работает (PID: $main_bot_pid)"
else
    echo "Основной бот не работает, перезапуск..."
    cd /root/Vetbot3
    nohup python3 bot.py > /dev/null 2>&1 &
    echo "Бот перезапущен"
fi

# Перезапуск админ-панели
echo "Перезапуск админ-панели..."
cd /root/Vetbot3
nohup streamlit run admin_streamlit_enhanced.py --server.port 8501 --server.address 0.0.0.0 > /dev/null 2>&1 &
echo "Админ-панель перезапущена"

# Перезапуск веб-приложения
echo "Перезапуск веб-приложения..."
cd /root
nohup python3 webapp_server_fixed.py > /dev/null 2>&1 &
echo "Веб-приложение перезапущено"

# 9. Финальная проверка
echo "9. ФИНАЛЬНАЯ ПРОВЕРКА:"
sleep 5
echo "Активные процессы после очистки:"
echo "Python процессов: $(ps aux | grep python | grep -v grep | wc -l)"
echo "Streamlit процессов: $(ps aux | grep streamlit | grep -v grep | wc -l)"
echo "Зомби-процессов: $(ps aux | awk '$8 ~ /^Z/' | wc -l)"
echo

# 10. Сохранение результата
ps aux > /tmp/processes_after_cleanup.txt
echo "Состояние после очистки сохранено в /tmp/processes_after_cleanup.txt"

echo "=== ОЧИСТКА ЗАВЕРШЕНА ==="
echo "Рекомендуется мониторить систему в течение 10-15 минут"

