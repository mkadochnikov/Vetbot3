#!/bin/bash

# Управление ветеринарными сервисами
# Версия: 2.1.0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
PYTHON_PATH="$VENV_PATH/bin/python"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода заголовка
print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              ВЕТЕРИНАРНЫЙ СЕРВИС - УПРАВЛЕНИЕ               ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║ 🤖 Telegram бот с AI-консультациями                        ║"
    echo "║ 🌐 Веб-приложение для вызова врача                         ║"
    echo "║ 📊 Версия: 2.1.0                                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Проверка виртуального окружения
check_venv() {
    if [ ! -f "$PYTHON_PATH" ]; then
        echo -e "${RED}❌ Виртуальное окружение не найдено: $VENV_PATH${NC}"
        echo -e "${YELLOW}💡 Создайте виртуальное окружение: python3 -m venv venv${NC}"
        exit 1
    fi
}

# Проверка зависимостей
check_dependencies() {
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        echo -e "${RED}❌ Файл .env не найден${NC}"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/enhanced_bot.py" ]; then
        echo -e "${RED}❌ Файл enhanced_bot.py не найден${NC}"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/webapp_server.py" ]; then
        echo -e "${RED}❌ Файл webapp_server.py не найден${NC}"
        exit 1
    fi
}

# Запуск всех сервисов
start_services() {
    print_header
    echo -e "${GREEN}🚀 Запуск всех сервисов...${NC}"
    
    check_venv
    check_dependencies
    
    cd "$SCRIPT_DIR"
    source "$VENV_PATH/bin/activate"
    
    echo -e "${BLUE}📋 Запуск в фоновом режиме...${NC}"
    nohup python start_all.py > vet_services.log 2>&1 &
    
    echo $! > vet_services.pid
    
    sleep 3
    
    if ps -p $(cat vet_services.pid) > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Сервисы запущены успешно!${NC}"
        echo -e "${BLUE}📱 Веб-приложение: http://localhost:5000${NC}"
        echo -e "${BLUE}🤖 Telegram бот: активен${NC}"
        echo -e "${YELLOW}📋 Логи: tail -f vet_services.log${NC}"
    else
        echo -e "${RED}❌ Ошибка запуска сервисов${NC}"
        echo -e "${YELLOW}📋 Проверьте логи: cat vet_services.log${NC}"
    fi
}

# Остановка всех сервисов
stop_services() {
    echo -e "${YELLOW}🛑 Остановка сервисов...${NC}"
    
    if [ -f "$SCRIPT_DIR/vet_services.pid" ]; then
        PID=$(cat "$SCRIPT_DIR/vet_services.pid")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            sleep 2
            
            # Принудительная остановка если процесс все еще работает
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
                echo -e "${YELLOW}⚠️ Принудительная остановка${NC}"
            fi
            
            echo -e "${GREEN}✅ Сервисы остановлены${NC}"
        else
            echo -e "${YELLOW}⚠️ Процесс уже не запущен${NC}"
        fi
        rm -f "$SCRIPT_DIR/vet_services.pid"
    else
        echo -e "${YELLOW}⚠️ PID файл не найден${NC}"
    fi
    
    # Дополнительная очистка процессов
    pkill -f "enhanced_bot.py" 2>/dev/null
    pkill -f "webapp_server.py" 2>/dev/null
    pkill -f "start_all.py" 2>/dev/null
}

# Перезапуск сервисов
restart_services() {
    echo -e "${BLUE}🔄 Перезапуск сервисов...${NC}"
    stop_services
    sleep 2
    start_services
}

# Статус сервисов
status_services() {
    print_header
    echo -e "${BLUE}📊 Статус сервисов:${NC}"
    
    if [ -f "$SCRIPT_DIR/vet_services.pid" ]; then
        PID=$(cat "$SCRIPT_DIR/vet_services.pid")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Основной процесс запущен (PID: $PID)${NC}"
            
            # Проверка отдельных компонентов
            if pgrep -f "enhanced_bot.py" > /dev/null; then
                echo -e "${GREEN}✅ Telegram бот: работает${NC}"
            else
                echo -e "${RED}❌ Telegram бот: не работает${NC}"
            fi
            
            if pgrep -f "webapp_server.py" > /dev/null; then
                echo -e "${GREEN}✅ Веб-приложение: работает${NC}"
            else
                echo -e "${RED}❌ Веб-приложение: не работает${NC}"
            fi
            
            # Проверка портов
            if netstat -tlnp 2>/dev/null | grep ":5000" > /dev/null; then
                echo -e "${GREEN}✅ Порт 5000: открыт${NC}"
            else
                echo -e "${YELLOW}⚠️ Порт 5000: не открыт${NC}"
            fi
            
        else
            echo -e "${RED}❌ Сервисы не запущены${NC}"
        fi
    else
        echo -e "${RED}❌ Сервисы не запущены (PID файл не найден)${NC}"
    fi
}

# Просмотр логов
show_logs() {
    if [ -f "$SCRIPT_DIR/vet_services.log" ]; then
        echo -e "${BLUE}📋 Последние логи:${NC}"
        tail -n 50 "$SCRIPT_DIR/vet_services.log"
    else
        echo -e "${YELLOW}⚠️ Файл логов не найден${NC}"
    fi
}

# Обновление из репозитория
update_services() {
    echo -e "${BLUE}🔄 Обновление из репозитория...${NC}"
    
    cd "$SCRIPT_DIR"
    
    if [ -d ".git" ]; then
        git pull origin main
        echo -e "${GREEN}✅ Код обновлен${NC}"
        
        # Перезапуск после обновления
        if [ -f "$SCRIPT_DIR/vet_services.pid" ]; then
            echo -e "${BLUE}🔄 Перезапуск сервисов с новым кодом...${NC}"
            restart_services
        fi
    else
        echo -e "${YELLOW}⚠️ Git репозиторий не найден${NC}"
    fi
}

# Главное меню
show_menu() {
    print_header
    echo -e "${BLUE}Выберите действие:${NC}"
    echo "1) 🚀 Запустить сервисы"
    echo "2) 🛑 Остановить сервисы"
    echo "3) 🔄 Перезапустить сервисы"
    echo "4) 📊 Статус сервисов"
    echo "5) 📋 Показать логи"
    echo "6) 🔄 Обновить из репозитория"
    echo "7) 🚪 Выход"
    echo
    read -p "Введите номер (1-7): " choice
    
    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) status_services ;;
        5) show_logs ;;
        6) update_services ;;
        7) echo -e "${GREEN}👋 До свидания!${NC}"; exit 0 ;;
        *) echo -e "${RED}❌ Неверный выбор${NC}" ;;
    esac
}

# Обработка аргументов командной строки
case "${1:-menu}" in
    start) start_services ;;
    stop) stop_services ;;
    restart) restart_services ;;
    status) status_services ;;
    logs) show_logs ;;
    update) update_services ;;
    menu) 
        while true; do
            show_menu
            echo
            read -p "Нажмите Enter для продолжения..."
            clear
        done
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|update|menu}"
        echo "Или запустите без параметров для интерактивного меню"
        exit 1
        ;;
esac

