#!/bin/bash
# Скрипт мониторинга и автоматической очистки процессов
# Для предотвращения накопления зомби-процессов
# Версия: 1.0

# Конфигурация
MAX_PYTHON_PROCESSES=10
MAX_STREAMLIT_PROCESSES=3
MAX_ZOMBIE_PROCESSES=5
MAX_CPU_LOAD=80
LOG_FILE="/var/log/process_monitor.log"

# Функция логирования
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Функция проверки и очистки
check_and_cleanup() {
    local current_time=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Подсчет процессов
    python_count=$(ps aux | grep python | grep -v grep | grep -v "process_monitor" | wc -l)
    streamlit_count=$(ps aux | grep streamlit | grep -v grep | wc -l)
    zombie_count=$(ps aux | awk '$8 ~ /^Z/' | wc -l)
    
    # Получение загрузки CPU
    cpu_load=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    cpu_load_int=$(echo "$cpu_load" | cut -d'.' -f1)
    
    log_message "Мониторинг: Python=$python_count, Streamlit=$streamlit_count, Zombies=$zombie_count, CPU=${cpu_load}%"
    
    # Проверка превышения лимитов
    cleanup_needed=false
    
    if [ "$python_count" -gt "$MAX_PYTHON_PROCESSES" ]; then
        log_message "ПРЕДУПРЕЖДЕНИЕ: Слишком много Python процессов ($python_count > $MAX_PYTHON_PROCESSES)"
        cleanup_needed=true
    fi
    
    if [ "$streamlit_count" -gt "$MAX_STREAMLIT_PROCESSES" ]; then
        log_message "ПРЕДУПРЕЖДЕНИЕ: Слишком много Streamlit процессов ($streamlit_count > $MAX_STREAMLIT_PROCESSES)"
        cleanup_needed=true
    fi
    
    if [ "$zombie_count" -gt "$MAX_ZOMBIE_PROCESSES" ]; then
        log_message "ПРЕДУПРЕЖДЕНИЕ: Слишком много зомби-процессов ($zombie_count > $MAX_ZOMBIE_PROCESSES)"
        cleanup_needed=true
    fi
    
    if [ "$cpu_load_int" -gt "$MAX_CPU_LOAD" ]; then
        log_message "ПРЕДУПРЕЖДЕНИЕ: Высокая загрузка CPU (${cpu_load}% > ${MAX_CPU_LOAD}%)"
        cleanup_needed=true
    fi
    
    # Выполнение очистки при необходимости
    if [ "$cleanup_needed" = true ]; then
        log_message "НАЧАЛО АВТОМАТИЧЕСКОЙ ОЧИСТКИ"
        
        # Очистка дублирующихся Streamlit процессов
        if [ "$streamlit_count" -gt "$MAX_STREAMLIT_PROCESSES" ]; then
            excess_streamlit=$(ps aux | grep streamlit | grep -v grep | tail -n +$(($MAX_STREAMLIT_PROCESSES + 1)) | awk '{print $2}' | tr '\n' ' ')
            if [ -n "$excess_streamlit" ]; then
                log_message "Завершение избыточных Streamlit процессов: $excess_streamlit"
                kill -TERM $excess_streamlit 2>/dev/null
                sleep 2
                kill -9 $excess_streamlit 2>/dev/null
            fi
        fi
        
        # Очистка дублирующихся Python процессов (кроме основного бота)
        if [ "$python_count" -gt "$MAX_PYTHON_PROCESSES" ]; then
            # Сохраняем основной процесс бота
            main_bot_pid=$(ps aux | grep "bot\.py" | grep -v grep | head -1 | awk '{print $2}')
            excess_python=$(ps aux | grep python | grep -v grep | grep -v "bot\.py" | grep -v "process_monitor" | grep -v "/usr/bin/python" | tail -n +$(($MAX_PYTHON_PROCESSES - 2)) | awk '{print $2}' | tr '\n' ' ')
            if [ -n "$excess_python" ]; then
                log_message "Завершение избыточных Python процессов: $excess_python (сохраняем бот PID: $main_bot_pid)"
                kill -TERM $excess_python 2>/dev/null
                sleep 2
                kill -9 $excess_python 2>/dev/null
            fi
        fi
        
        # Очистка зомби-процессов
        if [ "$zombie_count" -gt "$MAX_ZOMBIE_PROCESSES" ]; then
            zombie_pids=$(ps aux | awk '$8 ~ /^Z/ {print $2}' | tr '\n' ' ')
            log_message "Обработка зомби-процессов: $zombie_pids"
            for zpid in $zombie_pids; do
                parent_pid=$(ps -o ppid= -p $zpid 2>/dev/null | tr -d ' ')
                if [ -n "$parent_pid" ] && [ "$parent_pid" != "1" ]; then
                    kill -CHLD $parent_pid 2>/dev/null
                fi
            done
        fi
        
        log_message "АВТОМАТИЧЕСКАЯ ОЧИСТКА ЗАВЕРШЕНА"
        
        # Проверка после очистки
        sleep 5
        new_python_count=$(ps aux | grep python | grep -v grep | grep -v "process_monitor" | wc -l)
        new_streamlit_count=$(ps aux | grep streamlit | grep -v grep | wc -l)
        new_zombie_count=$(ps aux | awk '$8 ~ /^Z/' | wc -l)
        
        log_message "После очистки: Python=$new_python_count, Streamlit=$new_streamlit_count, Zombies=$new_zombie_count"
    fi
}

# Функция проверки основных сервисов
check_services() {
    # Проверка бота
    bot_running=$(ps aux | grep "bot\.py" | grep -v grep | wc -l)
    if [ "$bot_running" -eq 0 ]; then
        log_message "КРИТИЧНО: Telegram бот не работает, перезапуск..."
        cd /root/Vetbot3
        nohup python3 bot.py > /dev/null 2>&1 &
        log_message "Telegram бот перезапущен"
    fi
    
    # Проверка админ-панели
    admin_running=$(ps aux | grep "admin_streamlit" | grep -v grep | wc -l)
    if [ "$admin_running" -eq 0 ]; then
        log_message "ПРЕДУПРЕЖДЕНИЕ: Админ-панель не работает, перезапуск..."
        cd /root/Vetbot3
        nohup streamlit run admin_streamlit_enhanced.py --server.port 8501 --server.address 0.0.0.0 > /dev/null 2>&1 &
        log_message "Админ-панель перезапущена"
    fi
    
    # Проверка веб-приложения
    webapp_running=$(ps aux | grep "webapp_server" | grep -v grep | wc -l)
    if [ "$webapp_running" -eq 0 ]; then
        log_message "ПРЕДУПРЕЖДЕНИЕ: Веб-приложение не работает, перезапуск..."
        cd /root
        nohup python3 webapp_server_fixed.py > /dev/null 2>&1 &
        log_message "Веб-приложение перезапущено"
    fi
}

# Основная функция
main() {
    log_message "=== ЗАПУСК МОНИТОРИНГА ПРОЦЕССОВ ==="
    
    # Создание лог-файла если не существует
    touch "$LOG_FILE"
    
    # Основной цикл мониторинга
    while true; do
        check_and_cleanup
        check_services
        
        # Ожидание 2 минуты перед следующей проверкой
        sleep 120
    done
}

# Обработка сигналов для корректного завершения
trap 'log_message "Мониторинг процессов остановлен"; exit 0' SIGTERM SIGINT

# Запуск в зависимости от аргументов
case "${1:-daemon}" in
    "daemon")
        main
        ;;
    "once")
        log_message "=== РАЗОВАЯ ПРОВЕРКА ==="
        check_and_cleanup
        check_services
        ;;
    "status")
        echo "Статус процессов:"
        echo "Python: $(ps aux | grep python | grep -v grep | wc -l)"
        echo "Streamlit: $(ps aux | grep streamlit | grep -v grep | wc -l)"
        echo "Zombies: $(ps aux | awk '$8 ~ /^Z/' | wc -l)"
        echo "CPU Load: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')"
        ;;
    *)
        echo "Использование: $0 [daemon|once|status]"
        echo "  daemon - запуск в режиме демона (по умолчанию)"
        echo "  once   - разовая проверка и очистка"
        echo "  status - показать текущий статус"
        exit 1
        ;;
esac

