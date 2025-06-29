# 🌐 Настройка Caddy для ветеринарного бота

Этот документ описывает настройку веб-сервера Caddy для проксирования доменов на соответствующие сервисы.

## 📋 Схема доменов

| Домен | Сервис | Порт | Описание |
|-------|--------|------|----------|
| `app.murzik.pro` | Веб-приложение | 5000 | Форма вызова врача |
| `admin.murzik.pro` | Админ-панель | 8501 | Streamlit админка |
| `murzik.pro` | Редирект | - | Перенаправление на app |
| `www.murzik.pro` | Редирект | - | Перенаправление на app |

## 🚀 Быстрая установка

### 1. Автоматическая установка
```bash
cd ~/Vetbot3
sudo ./caddy-setup.sh
```

### 2. Ручная установка

#### Установка Caddy:
```bash
# Добавляем репозиторий
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list

# Устанавливаем
sudo apt update
sudo apt install -y caddy
```

#### Настройка конфигурации:
```bash
# Копируем конфигурацию
sudo cp Caddyfile /etc/caddy/Caddyfile

# Создаем директории для логов
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy

# Проверяем конфигурацию
sudo caddy validate --config /etc/caddy/Caddyfile

# Запускаем
sudo systemctl enable caddy
sudo systemctl start caddy
```

## ⚙️ Конфигурация Caddyfile

### Основные блоки:

#### 1. Веб-приложение (`app.murzik.pro`)
```caddy
app.murzik.pro {
    reverse_proxy localhost:5000
    encode gzip
    log {
        output file /var/log/caddy/app.murzik.pro.log
    }
}
```

#### 2. Админ-панель (`admin.murzik.pro`)
```caddy
admin.murzik.pro {
    reverse_proxy localhost:8501
    encode gzip
    
    # Поддержка WebSocket для Streamlit
    @websocket {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    reverse_proxy @websocket localhost:8501
}
```

#### 3. Редиректы
```caddy
murzik.pro {
    redir https://app.murzik.pro{uri} permanent
}

www.murzik.pro {
    redir https://app.murzik.pro{uri} permanent
}
```

## 🔒 Безопасность

### Автоматические HTTPS сертификаты
Caddy автоматически получает и обновляет Let's Encrypt сертификаты для всех доменов.

### Заголовки безопасности
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` для HTTPS
- `Content-Security-Policy` для админ-панели

### Базовая аутентификация (опционально)
Для дополнительной защиты админ-панели можно включить HTTP Basic Auth:

```caddy
admin.murzik.pro {
    basicauth {
        admin $2a$14$hashed_password_here
    }
    reverse_proxy localhost:8501
}
```

Генерация хэша пароля:
```bash
caddy hash-password --plaintext "your_password"
```

## 📊 Мониторинг и логи

### Просмотр логов:
```bash
# Общие логи Caddy
sudo journalctl -u caddy -f

# Логи конкретного домена
sudo tail -f /var/log/caddy/app.murzik.pro.log
sudo tail -f /var/log/caddy/admin.murzik.pro.log
```

### Статус сервиса:
```bash
sudo systemctl status caddy
```

### Перезагрузка конфигурации:
```bash
sudo caddy reload --config /etc/caddy/Caddyfile
```

## 🔧 Управление

### Основные команды:
```bash
# Запуск
sudo systemctl start caddy

# Остановка
sudo systemctl stop caddy

# Перезапуск
sudo systemctl restart caddy

# Автозапуск
sudo systemctl enable caddy

# Проверка конфигурации
sudo caddy validate --config /etc/caddy/Caddyfile

# Перезагрузка без перезапуска
sudo caddy reload --config /etc/caddy/Caddyfile
```

## 🌐 DNS настройки

Убедитесь, что DNS записи указывают на ваш сервер:

```
A     murzik.pro          -> IP_ВАШЕГО_СЕРВЕРА
A     app.murzik.pro      -> IP_ВАШЕГО_СЕРВЕРА  
A     admin.murzik.pro    -> IP_ВАШЕГО_СЕРВЕРА
A     www.murzik.pro      -> IP_ВАШЕГО_СЕРВЕРА
```

Или используйте CNAME для поддоменов:
```
A     murzik.pro          -> IP_ВАШЕГО_СЕРВЕРА
CNAME app.murzik.pro      -> murzik.pro
CNAME admin.murzik.pro    -> murzik.pro
CNAME www.murzik.pro      -> murzik.pro
```

## 🚨 Устранение неполадок

### Проблема: Сертификат не получается
```bash
# Проверьте DNS
nslookup app.murzik.pro
nslookup admin.murzik.pro

# Проверьте порты 80 и 443
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Проверьте логи
sudo journalctl -u caddy -f
```

### Проблема: Сервис недоступен
```bash
# Проверьте, что сервисы запущены
ss -tlnp | grep :5000  # Веб-приложение
ss -tlnp | grep :8501  # Админ-панель

# Проверьте статус Caddy
sudo systemctl status caddy

# Проверьте конфигурацию
sudo caddy validate --config /etc/caddy/Caddyfile
```

### Проблема: WebSocket не работает в Streamlit
Убедитесь, что в конфигурации есть блок для WebSocket:
```caddy
@websocket {
    header Connection *Upgrade*
    header Upgrade websocket
}
reverse_proxy @websocket localhost:8501
```

## 📝 Примечания

1. **Автоматические сертификаты**: Caddy автоматически получает и обновляет SSL сертификаты
2. **Логирование**: Все запросы логируются в отдельные файлы по доменам
3. **Сжатие**: Включено gzip сжатие для всех ответов
4. **Безопасность**: Настроены заголовки безопасности
5. **WebSocket**: Поддержка WebSocket для Streamlit админ-панели

## 🔗 Полезные ссылки

- [Документация Caddy](https://caddyserver.com/docs/)
- [Caddyfile синтаксис](https://caddyserver.com/docs/caddyfile)
- [Let's Encrypt](https://letsencrypt.org/)
- [Streamlit deployment](https://docs.streamlit.io/knowledge-base/tutorials/deploy)

