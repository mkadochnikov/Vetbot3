#!/bin/bash

# Скрипт для развертывания улучшенной версии Vetbot3 с GitHub на сервер
# Версия: 1.0

echo "🚀 РАЗВЕРТЫВАНИЕ VETBOT3 УЛУЧШЕННОЙ ВЕРСИИ С GITHUB"
echo "=================================================="

# Проверка аргументов
if [ $# -lt 1 ]; then
    echo "❌ Не указан адрес сервера!"
    echo "Использование: $0 user@server [port] [branch]"
    echo "Пример: $0 user@46.252.251.117 4828 improved-version-v3"
    exit 1
fi

SERVER=$1
PORT=${2:-22}
BRANCH=${3:-improved-version-v3}
REPO_URL="https://github.com/mkadochnikov/Vetbot3.git"

echo "📋 Параметры развертывания:"
echo "   Сервер: $SERVER"
echo "   Порт: $PORT"
echo "   Ветка: $BRANCH"
echo "   Репозиторий: $REPO_URL"
echo ""

# Проверка соединения с сервером
echo "🔍 Проверка соединения с сервером..."
ssh -p $PORT -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER "echo '✅ Соединение установлено'" || {
    echo "❌ Не удалось подключиться к серверу!"
    echo "Проверьте:"
    echo "  - Правильность адреса сервера"
    echo "  - Доступность порта $PORT"
    echo "  - SSH ключи или пароль"
    exit 1
}

# Создание скрипта развертывания на сервере
echo "📝 Создание скрипта развертывания на сервере..."
ssh -p $PORT $SERVER "cat > ~/deploy_vetbot.sh << 'EOF'
#!/bin/bash

echo '🚀 Развертывание Vetbot3 на сервере...'

# Остановка старых процессов
echo '🛑 Остановка старых процессов...'
pkill -f 'python.*bot' || true
pkill -f 'python.*admin' || true
pkill -f 'python.*webapp' || true

# Создание резервной копии, если существует
if [ -d ~/Vetbot3 ]; then
    echo '💾 Создание резервной копии...'
    mv ~/Vetbot3 ~/Vetbot3_backup_\$(date +%Y%m%d_%H%M%S) || true
fi

# Клонирование репозитория
echo '📥 Клонирование репозитория...'
git clone $REPO_URL ~/Vetbot3 || {
    echo '❌ Не удалось клонировать репозиторий!'
    exit 1
}

cd ~/Vetbot3

# Переключение на нужную ветку
echo '🔄 Переключение на ветку $BRANCH...'
git checkout $BRANCH || {
    echo '❌ Не удалось переключиться на ветку $BRANCH!'
    exit 1
}

# Переход в директорию улучшенной версии
cd ~/Vetbot3/vetbot_improved

# Проверка наличия Python и pip
echo '🔍 Проверка Python и pip...'
python3 --version || {
    echo '❌ Python3 не установлен!'
    exit 1
}

pip3 --version || {
    echo '❌ pip3 не установлен!'
    exit 1
}

# Установка зависимостей
echo '📦 Установка зависимостей...'
pip3 install -r requirements.txt || {
    echo '❌ Не удалось установить зависимости!'
    exit 1
}

# Создание необходимых директорий
echo '📁 Создание директорий...'
mkdir -p data logs pids

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo '⚠️ Файл .env не найден!'
    echo 'Создание .env файла из примера...'
    cp .env.example .env
    echo ''
    echo '❗ ВАЖНО: Отредактируйте файл .env с вашими настройками:'
    echo '   nano ~/Vetbot3/vetbot_improved/.env'
    echo ''
    echo 'Необходимо указать:'
    echo '  - TELEGRAM_BOT_TOKEN (токен основного бота)'
    echo '  - VET_BOT_TOKEN (токен бота врачей)'
    echo '  - DEEPSEEK_API_KEY (API ключ DeepSeek)'
    echo '  - ADMIN_CHAT_ID (ваш Telegram ID)'
    echo ''
    read -p 'Нажмите Enter после настройки .env файла...'
fi

# Миграция данных из старой версии (если есть)
if [ -f ~/vetbot.db ]; then
    echo '🔄 Миграция данных из старой версии...'
    cp ~/vetbot.db data/vetbot_old.db
    python3 -m scripts.migrate_data || {
        echo '⚠️ Не удалось выполнить миграцию данных автоматически'
        echo 'Вы можете выполнить ее позже вручную'
    }
fi

# Запуск системы
echo '🚀 Запуск системы...'
python3 run.py start || {
    echo '❌ Не удалось запустить систему!'
    echo 'Проверьте логи: tail -f logs/*.log'
    exit 1
}

echo ''
echo '🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО УСПЕШНО!'
echo '=================================='
echo '📱 Основной бот: @murzikpro_bot'
echo '👨‍⚕️ Бот врачей: настройте в .env файле'
echo '🌐 Веб-приложение: http://$(hostname -I | awk "{print \$1}"):5000'
echo '👨‍💼 Админ-панель: http://$(hostname -I | awk "{print \$1}"):8501'
echo ''
echo '📋 Полезные команды:'
echo '   Статус: cd ~/Vetbot3/vetbot_improved && python3 run.py status'
echo '   Остановка: cd ~/Vetbot3/vetbot_improved && python3 run.py stop'
echo '   Перезапуск: cd ~/Vetbot3/vetbot_improved && python3 run.py restart'
echo '   Логи: tail -f ~/Vetbot3/vetbot_improved/logs/*.log'
echo ''
echo '⚠️ Не забудьте:'
echo '   1. Настроить .env файл с вашими токенами'
echo '   2. Открыть порты 5000 и 8501 в брандмауэре'
echo '   3. Настроить домены или использовать IP адреса'

EOF

chmod +x ~/deploy_vetbot.sh"

# Запуск скрипта развертывания на сервере
echo "🚀 Запуск развертывания на сервере..."
ssh -p $PORT $SERVER "~/deploy_vetbot.sh"

echo ""
echo "🎉 РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo "=========================="
echo ""
echo "🔗 Pull Request с улучшениями:"
echo "   https://github.com/mkadochnikov/Vetbot3/pull/1"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Настройте .env файл на сервере:"
echo "      ssh -p $PORT $SERVER 'nano ~/Vetbot3/vetbot_improved/.env'"
echo ""
echo "   2. Проверьте статус системы:"
echo "      ssh -p $PORT $SERVER 'cd ~/Vetbot3/vetbot_improved && python3 run.py status'"
echo ""
echo "   3. Просмотрите логи:"
echo "      ssh -p $PORT $SERVER 'tail -f ~/Vetbot3/vetbot_improved/logs/*.log'"
echo ""
echo "🔄 Управление системой:"
echo "   Остановка: ssh -p $PORT $SERVER 'cd ~/Vetbot3/vetbot_improved && python3 run.py stop'"
echo "   Запуск: ssh -p $PORT $SERVER 'cd ~/Vetbot3/vetbot_improved && python3 run.py start'"
echo "   Перезапуск: ssh -p $PORT $SERVER 'cd ~/Vetbot3/vetbot_improved && python3 run.py restart'"
echo ""
echo "🔙 Откат к старой версии (если нужно):"
echo "   ssh -p $PORT $SERVER 'cd ~/Vetbot3 && git checkout main'"