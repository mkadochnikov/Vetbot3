# 🚀 Инструкции по развертыванию

Данный документ содержит подробные инструкции по развертыванию ветеринарного бота в различных средах.

## 📋 Предварительные требования

### 1. Создание Telegram бота

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot` и следуйте инструкциям
3. Сохраните полученный токен
4. Настройте веб-приложение командой `/setmenubutton`

### 2. Подготовка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```env
BOT_TOKEN=your_bot_token_here
WEBAPP_URL=https://your-domain.com
ADMIN_CHAT_ID=your_admin_chat_id
VET_SERVICE_PHONE=+7-999-123-45-67
VET_SERVICE_EMAIL=info@vetservice.com
PORT=5000
```

## 🌐 Развертывание на Heroku

### Шаг 1: Подготовка

```bash
# Установите Heroku CLI
# Войдите в аккаунт
heroku login

# Создайте приложение
heroku create your-vet-bot-app
```

### Шаг 2: Настройка переменных окружения

```bash
heroku config:set BOT_TOKEN=your_bot_token_here
heroku config:set WEBAPP_URL=https://your-vet-bot-app.herokuapp.com
heroku config:set ADMIN_CHAT_ID=your_admin_chat_id
heroku config:set VET_SERVICE_PHONE=+7-999-123-45-67
heroku config:set VET_SERVICE_EMAIL=info@vetservice.com
```

### Шаг 3: Развертывание

```bash
git add .
git commit -m "Deploy vet bot to Heroku"
git push heroku main

# Запуск процессов
heroku ps:scale web=1 worker=1
```

### Шаг 4: Настройка веб-приложения в боте

1. Перейдите к [@BotFather](https://t.me/BotFather)
2. Выберите команду `/setmenubutton`
3. Выберите вашего бота
4. Укажите URL: `https://your-vet-bot-app.herokuapp.com`
5. Установите текст: "Вызвать врача"

## 🐳 Развертывание с Docker

### Локальное развертывание

```bash
# Сборка образа
docker build -t vet-bot .

# Запуск веб-приложения
docker run -d -p 5000:5000 --env-file .env --name vet-webapp vet-bot python webapp_server.py

# Запуск бота
docker run -d --env-file .env --name vet-bot-worker vet-bot python enhanced_bot.py
```

### Использование Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## ☁️ Развертывание на VPS

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
sudo apt install python3 python3-pip python3-venv git -y

# Установка Nginx (для проксирования)
sudo apt install nginx -y
```

### Шаг 2: Клонирование и настройка

```bash
# Клонирование репозитория
git clone <your-repo-url>
cd Vetbot3

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
nano .env  # Отредактируйте файл
```

### Шаг 3: Настройка systemd сервисов

Создайте файл `/etc/systemd/system/vet-bot.service`:

```ini
[Unit]
Description=Vet Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Vetbot3
Environment=PATH=/home/ubuntu/Vetbot3/venv/bin
ExecStart=/home/ubuntu/Vetbot3/venv/bin/python enhanced_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Создайте файл `/etc/systemd/system/vet-webapp.service`:

```ini
[Unit]
Description=Vet WebApp
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Vetbot3
Environment=PATH=/home/ubuntu/Vetbot3/venv/bin
ExecStart=/home/ubuntu/Vetbot3/venv/bin/python webapp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Шаг 4: Запуск сервисов

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable vet-bot vet-webapp

# Запуск сервисов
sudo systemctl start vet-bot vet-webapp

# Проверка статуса
sudo systemctl status vet-bot vet-webapp
```

### Шаг 5: Настройка Nginx

Создайте файл `/etc/nginx/sites-available/vet-bot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/vet-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Шаг 6: Настройка SSL (опционально)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автообновление сертификата
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Мониторинг и логи

### Просмотр логов

```bash
# Логи бота
sudo journalctl -u vet-bot -f

# Логи веб-приложения
sudo journalctl -u vet-webapp -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Мониторинг ресурсов

```bash
# Использование CPU и памяти
htop

# Дисковое пространство
df -h

# Статус сервисов
sudo systemctl status vet-bot vet-webapp nginx
```

## 🔧 Обслуживание

### Обновление кода

```bash
cd /home/ubuntu/Vetbot3
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vet-bot vet-webapp
```

### Резервное копирование базы данных

```bash
# Создание резервной копии
cp vetbot.db vetbot_backup_$(date +%Y%m%d_%H%M%S).db

# Автоматическое резервное копирование (добавить в crontab)
0 2 * * * cd /home/ubuntu/Vetbot3 && cp vetbot.db backups/vetbot_backup_$(date +\%Y\%m\%d_\%H\%M\%S).db
```

## 🚨 Устранение неполадок

### Общие проблемы

1. **Бот не отвечает:**
   - Проверьте токен бота
   - Убедитесь, что сервис запущен
   - Проверьте логи на ошибки

2. **Веб-приложение недоступно:**
   - Проверьте статус веб-сервера
   - Убедитесь, что порт открыт
   - Проверьте конфигурацию Nginx

3. **Ошибки базы данных:**
   - Проверьте права доступа к файлу БД
   - Убедитесь в наличии свободного места
   - Проверьте целостность БД

### Полезные команды

```bash
# Перезапуск всех сервисов
sudo systemctl restart vet-bot vet-webapp nginx

# Проверка портов
sudo netstat -tlnp | grep :5000

# Проверка процессов
ps aux | grep python

# Очистка логов
sudo journalctl --vacuum-time=7d
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи сервисов
2. Убедитесь в правильности конфигурации
3. Проверьте доступность внешних сервисов
4. Обратитесь к документации Telegram Bot API

---

**Успешного развертывания!** 🚀

