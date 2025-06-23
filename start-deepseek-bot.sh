#!/bin/bash

echo "🤖 Запуск ветеринарного бота с DeepSeek API"

# Проверяем наличие файлов
check_files() {
    local missing_files=()
    
    if [ ! -f "vet_bot_deepseek.py" ]; then
        missing_files+=("vet_bot_deepseek.py")
    fi
    
    if [ ! -f "requirements.txt" ]; then
        echo "📦 Создание requirements.txt..."
        cat > requirements.txt << 'EOF'
python-telegram-bot==22.1
python-dotenv==1.1.0
requests==2.31.0
EOF
    fi
    
    if [ ! -f "Dockerfile" ]; then
        echo "🐳 Создание Dockerfile..."
        cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vet_bot_deepseek.py .

RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

ENV PYTHONUNBUFFERED=1

CMD ["python", "vet_bot_deepseek.py"]
EOF
    fi
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        echo "❌ Отсутствуют файлы:"
        printf '   %s\n' "${missing_files[@]}"
        echo ""
        echo "Скопируйте файлы из созданного проекта"
        exit 1
    fi
}

# Проверяем .env файл
check_env() {
    if [ ! -f ".env" ]; then
        echo "📝 Создание .env файла..."
        cat > .env << 'EOF'
# Telegram Bot Token (получите у @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# DeepSeek API Key
DEEPSEEK_API_KEY=sk-6c32104420624e3483ef173804d8abde
DEEPSEEK_MODEL=deepseek-chat

# Настройки
MAX_TOKENS=1500
TEMPERATURE=0.8
LOG_LEVEL=INFO
EOF
        echo "✅ Файл .env создан"
        echo ""
        echo "📝 ВАЖНО: Отредактируйте .env файл:"
        echo "   nano .env"
        echo ""
        echo "Заполните TELEGRAM_BOT_TOKEN (получите у @BotFather в Telegram)"
        echo "DeepSeek API ключ уже заполнен, но нужно пополнить баланс на platform.deepseek.com"
        exit 0
    fi
    
    # Проверяем заполнение токена
    if grep -q "your_telegram_bot_token_here" .env; then
        echo "❌ Заполните TELEGRAM_BOT_TOKEN в .env файле"
        echo "📝 Получите токен у @BotFather в Telegram"
        echo "   nano .env"
        exit 1
    fi
    
    echo "✅ Файл .env найден и настроен"
}

# Проверяем Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker не установлен!"
        echo "Установите Docker: curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
        exit 1
    fi
}

# Основная функция запуска
start_bot() {
    echo "🚀 Запуск ветеринарного бота с DeepSeek API..."
    
    # Проверки
    check_docker
    check_files
    check_env
    
    # Останавливаем старый контейнер
    echo "🛑 Остановка старого контейнера..."
    docker rm -f vet-telegram-bot-deepseek 2>/dev/null || true
    
    # Собираем образ
    echo "🔨 Сборка Docker образа..."
    if ! docker build -t vet-bot-deepseek .; then
        echo "❌ Ошибка сборки образа"
        exit 1
    fi
    
    # Запускаем контейнер
    echo "🚀 Запуск контейнера..."
    if docker run -d \
        --name vet-telegram-bot-deepseek \
        --env-file .env \
        --restart unless-stopped \
        vet-bot-deepseek; then
        
        echo "✅ Бот запущен!"
        echo ""
        echo "📊 Статус контейнера:"
        docker ps | grep deepseek
        echo ""
        echo "📋 Проверка логов через 3 секунды..."
        sleep 3
        docker logs --tail 10 vet-telegram-bot-deepseek
        echo ""
        echo "💰 ВАЖНО: Если видите ошибку 'Insufficient Balance':"
        echo "   1. Зайдите на https://platform.deepseek.com"
        echo "   2. Пополните баланс минимум на $5"
        echo "   3. Перезапустите бота: docker restart vet-telegram-bot-deepseek"
        echo ""
        echo "🔍 Команды управления:"
        echo "   docker logs -f vet-telegram-bot-deepseek  # Логи"
        echo "   docker restart vet-telegram-bot-deepseek  # Перезапуск"
        echo "   docker stop vet-telegram-bot-deepseek     # Остановка"
    else
        echo "❌ Ошибка запуска контейнера"
        echo "Проверьте логи: docker logs vet-telegram-bot-deepseek"
        exit 1
    fi
}

# Функция тестирования
test_bot() {
    echo "🧪 Тестирование бота..."
    
    if [ ! -f "test_vet_bot_deepseek.py" ]; then
        echo "❌ Файл test_vet_bot_deepseek.py не найден"
        exit 1
    fi
    
    python3 test_vet_bot_deepseek.py
}

# Функция просмотра логов
show_logs() {
    echo "📋 Логи бота (Ctrl+C для выхода):"
    docker logs -f vet-telegram-bot-deepseek
}

# Функция остановки
stop_bot() {
    echo "🛑 Остановка бота..."
    docker stop vet-telegram-bot-deepseek
    docker rm vet-telegram-bot-deepseek
    echo "✅ Бот остановлен"
}

# Обработка аргументов
case "${1:-start}" in
    "start")
        start_bot
        ;;
    "test")
        test_bot
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        stop_bot
        ;;
    "restart")
        stop_bot
        sleep 2
        start_bot
        ;;
    "help")
        echo "Использование: $0 [команда]"
        echo ""
        echo "Команды:"
        echo "  start    - Запустить бота (по умолчанию)"
        echo "  test     - Протестировать бота"
        echo "  logs     - Показать логи"
        echo "  stop     - Остановить бота"
        echo "  restart  - Перезапустить бота"
        echo "  help     - Показать эту справку"
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo "Используйте: $0 help"
        exit 1
        ;;
esac

