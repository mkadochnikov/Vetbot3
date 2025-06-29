#!/bin/bash

# Скрипт установки и настройки Caddy для ветеринарного бота
# Версия: 1.0

set -e

echo "🚀 Установка и настройка Caddy для ветеринарного бота"
echo "=================================================="

# Проверка прав root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Не запускайте этот скрипт от root!"
   echo "Используйте: sudo ./caddy-setup.sh"
   exit 1
fi

# Функция для проверки команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Установка Caddy
echo "📦 Установка Caddy..."

if command_exists caddy; then
    echo "✅ Caddy уже установлен"
    caddy version
else
    echo "📥 Загрузка и установка Caddy..."
    
    # Добавляем официальный репозиторий Caddy
    sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
    
    # Обновляем пакеты и устанавливаем Caddy
    sudo apt update
    sudo apt install -y caddy
    
    echo "✅ Caddy установлен"
fi

# 2. Создание директорий для логов
echo "📁 Создание директорий..."
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

# 3. Копирование конфигурации
echo "⚙️ Настройка конфигурации..."

# Бэкап существующего Caddyfile
if [ -f /etc/caddy/Caddyfile ]; then
    sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.backup.$(date +%Y%m%d_%H%M%S)
    echo "📋 Создан бэкап существующего Caddyfile"
fi

# Копируем наш Caddyfile
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo chown root:root /etc/caddy/Caddyfile
sudo chmod 644 /etc/caddy/Caddyfile

echo "✅ Конфигурация скопирована"

# 4. Проверка конфигурации
echo "🔍 Проверка конфигурации..."
if sudo caddy validate --config /etc/caddy/Caddyfile; then
    echo "✅ Конфигурация корректна"
else
    echo "❌ Ошибка в конфигурации!"
    exit 1
fi

# 5. Настройка systemd
echo "🔧 Настройка systemd..."

# Включаем автозапуск
sudo systemctl enable caddy

# Перезагружаем конфигурацию
sudo systemctl daemon-reload

echo "✅ Systemd настроен"

# 6. Проверка портов
echo "🔍 Проверка доступности портов..."

check_port() {
    local port=$1
    local service=$2
    
    if ss -tuln | grep -q ":$port "; then
        echo "✅ Порт $port ($service) доступен"
        return 0
    else
        echo "⚠️ Порт $port ($service) не прослушивается"
        return 1
    fi
}

# Проверяем порты сервисов
check_port 5000 "Веб-приложение"
check_port 8501 "Админ-панель"

# 7. Запуск Caddy
echo "🚀 Запуск Caddy..."

# Останавливаем если запущен
sudo systemctl stop caddy 2>/dev/null || true

# Запускаем
if sudo systemctl start caddy; then
    echo "✅ Caddy запущен"
else
    echo "❌ Ошибка запуска Caddy!"
    echo "Проверьте логи: sudo journalctl -u caddy -f"
    exit 1
fi

# Проверяем статус
sleep 2
if sudo systemctl is-active --quiet caddy; then
    echo "✅ Caddy работает корректно"
else
    echo "❌ Caddy не запустился!"
    echo "Статус: $(sudo systemctl is-active caddy)"
    exit 1
fi

# 8. Проверка HTTPS сертификатов
echo "🔒 Информация о HTTPS..."
echo "Caddy автоматически получит Let's Encrypt сертификаты для:"
echo "  - app.murzik.pro"
echo "  - admin.murzik.pro"
echo "  - murzik.pro"
echo "  - www.murzik.pro"
echo ""
echo "⚠️ Убедитесь, что DNS записи указывают на этот сервер!"

# 9. Финальная информация
echo ""
echo "🎉 Установка завершена!"
echo "======================"
echo ""
echo "📱 Доступные сервисы:"
echo "  🌐 Веб-приложение:    https://app.murzik.pro"
echo "  👨‍💼 Админ-панель:      https://admin.murzik.pro"
echo "  🏠 Главная страница:   https://murzik.pro"
echo ""
echo "📋 Полезные команды:"
echo "  sudo systemctl status caddy     # Статус"
echo "  sudo systemctl restart caddy    # Перезапуск"
echo "  sudo journalctl -u caddy -f     # Логи"
echo "  sudo caddy reload --config /etc/caddy/Caddyfile  # Перезагрузка конфига"
echo ""
echo "📁 Файлы конфигурации:"
echo "  /etc/caddy/Caddyfile            # Основная конфигурация"
echo "  /var/log/caddy/                 # Логи"
echo ""
echo "⚠️ Не забудьте:"
echo "  1. Настроить DNS записи A/AAAA для доменов"
echo "  2. Убедиться, что порты 80 и 443 открыты"
echo "  3. Запустить ваши сервисы (веб-приложение и админ-панель)"
echo ""
echo "✅ Готово! Caddy настроен и запущен."

