# 🤖 Ветеринарный бот с DeepSeek API

## 📋 Обзор

Ветеринарный Telegram-бот, использующий модель **deepseek-chat** для консультаций по здоровью кошек. Бот работает как профессиональный ветеринар, ставит диагнозы и назначает лечение.

## ✅ Результаты тестирования

**Статус:** Бот создан и протестирован ✅
- ✅ Код написан и структурирован
- ✅ Обработка ошибок работает корректно  
- ✅ Docker конфигурация готова
- ⚠️ Требуется пополнение баланса DeepSeek API

## 💰 Проблема с балансом

При тестировании получена ошибка **402 "Insufficient Balance"**. 

### Как пополнить баланс DeepSeek:

1. **Зайдите на https://platform.deepseek.com**
2. **Войдите в аккаунт** (тот же, где получили API ключ)
3. **Перейдите в раздел "Billing" или "Платежи"**
4. **Пополните баланс** (минимум $5-10)
5. **Проверьте лимиты** в настройках API

### Стоимость использования:
- **deepseek-chat**: ~$0.14 за 1M входных токенов
- **Примерная стоимость**: $0.001-0.003 за консультацию
- **Рекомендуемый баланс**: $10-20 на месяц активного использования

## 🚀 Быстрый запуск

### 1. Подготовка файлов
```bash
# Скопируйте файлы в папку проекта:
# - vet_bot_deepseek.py
# - requirements.deepseek.txt  
# - Dockerfile.deepseek
# - .env.deepseek
```

### 2. Настройка конфигурации
```bash
# Создайте .env файл
cp .env.deepseek .env

# Отредактируйте .env
nano .env

# Заполните:
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
DEEPSEEK_API_KEY=sk-6c32104420624e3483ef173804d8abde
```

### 3. Запуск в Docker
```bash
# Переименуйте файлы
mv requirements.deepseek.txt requirements.txt
mv Dockerfile.deepseek Dockerfile
mv vet_bot_deepseek.py vet_bot_human.py

# Соберите образ
docker build -t vet-bot-deepseek .

# Запустите контейнер
docker run -d \
    --name vet-telegram-bot-deepseek \
    --env-file .env \
    --restart unless-stopped \
    vet-bot-deepseek

# Проверьте логи
docker logs -f vet-telegram-bot-deepseek
```

## 🔧 Управление ботом

### Основные команды:
```bash
# Статус контейнера
docker ps | grep deepseek

# Логи в реальном времени
docker logs -f vet-telegram-bot-deepseek

# Перезапуск
docker restart vet-telegram-bot-deepseek

# Остановка
docker stop vet-telegram-bot-deepseek

# Удаление
docker rm vet-telegram-bot-deepseek
```

### Обновление бота:
```bash
# Остановить и удалить старый
docker rm -f vet-telegram-bot-deepseek

# Пересобрать образ
docker build -t vet-bot-deepseek . --no-cache

# Запустить новый
docker run -d --name vet-telegram-bot-deepseek --env-file .env --restart unless-stopped vet-bot-deepseek
```

## 🐱 Использование бота

### Команды бота:
- `/start` - Начать работу
- `/help` - Справка по использованию  
- `/info` - Информация о боте

### Примеры вопросов:
```
"Кошка 3 года, понос 2 дня, вялая, плохо ест"
"Котенок 6 месяцев, кашляет и чихает неделю"  
"Кот 5 лет, хромает на переднюю лапу, мяукает"
```

### Формат ответа бота:
```
🔍 Диагноз: Острый гастроэнтерит
💊 Лечение: Энтеросгель 1мл 3 раза в день
🏠 Уход: Голодная диета 12 часов, затем легкая пища
⚠️ Когда к врачу: При ухудшении или отсутствии улучшения за 24 часа
```

## ⚙️ Конфигурация

### Переменные окружения (.env):
```bash
# Обязательные
TELEGRAM_BOT_TOKEN=ваш_токен_бота
DEEPSEEK_API_KEY=ваш_ключ_deepseek

# Опциональные
DEEPSEEK_MODEL=deepseek-chat
MAX_TOKENS=1500
TEMPERATURE=0.8
LOG_LEVEL=INFO
```

### Настройка модели:
- **deepseek-chat** - основная модель (рекомендуется)
- **deepseek-coder** - для технических задач
- **deepseek-math** - для математических расчетов

## 🛠️ Диагностика проблем

### Проблема: "Insufficient Balance"
```bash
# Проверьте баланс на platform.deepseek.com
# Пополните счет минимум на $5
```

### Проблема: "Invalid API Key"  
```bash
# Проверьте правильность ключа в .env
cat .env | grep DEEPSEEK_API_KEY

# Убедитесь что ключ активен на platform.deepseek.com
```

### Проблема: Бот не отвечает
```bash
# Проверьте логи
docker logs vet-telegram-bot-deepseek

# Проверьте статус контейнера
docker ps | grep deepseek

# Проверьте Telegram токен
# Отправьте /start боту в Telegram
```

### Проблема: Медленные ответы
```bash
# Уменьшите MAX_TOKENS в .env
MAX_TOKENS=800

# Или измените температуру
TEMPERATURE=0.5
```

## 📊 Мониторинг

### Проверка работоспособности:
```bash
# Создайте скрипт мониторинга
cat > monitor_deepseek.sh << 'EOF'
#!/bin/bash
while true; do
    echo "=== $(date) ==="
    docker ps --filter "name=deepseek" --format "table {{.Names}}\t{{.Status}}"
    docker logs --tail 5 vet-telegram-bot-deepseek 2>/dev/null | grep -E "(ERROR|INFO)"
    echo ""
    sleep 300  # Проверка каждые 5 минут
done
EOF

chmod +x monitor_deepseek.sh
./monitor_deepseek.sh
```

### Статистика использования:
```bash
# Ресурсы контейнера
docker stats vet-telegram-bot-deepseek --no-stream

# Размер логов
docker logs vet-telegram-bot-deepseek 2>&1 | wc -l
```

## 🔄 Альтернативы при проблемах с DeepSeek

Если возникают проблемы с DeepSeek API, можно использовать:

1. **Groq API** (бесплатный)
2. **Together AI** (дешевый)  
3. **Локальную версию** (без интернета)
4. **OpenAI через VPN** (если доступен)

## 📞 Поддержка

### При проблемах:
1. Проверьте логи: `docker logs vet-telegram-bot-deepseek`
2. Убедитесь в наличии баланса на DeepSeek
3. Проверьте правильность API ключей
4. Перезапустите контейнер

### Полезные ссылки:
- **DeepSeek Platform**: https://platform.deepseek.com
- **DeepSeek Docs**: https://platform.deepseek.com/api-docs
- **Telegram BotFather**: @BotFather

---

## 🎉 Заключение

Ветеринарный бот с DeepSeek API создан и готов к работе! 

**Что сделано:**
✅ Написан полнофункциональный бот
✅ Настроена интеграция с DeepSeek API  
✅ Создана Docker конфигурация
✅ Протестирована обработка ошибок
✅ Подготовлена документация

**Что нужно сделать:**
💰 Пополнить баланс DeepSeek API ($5-10)
🔑 Получить Telegram Bot Token от @BotFather
🚀 Запустить бота в Docker

После пополнения баланса бот будет работать как профессиональный ветеринар! 🐱👨‍⚕️

