# 🚀 Инструкция по деплою на сервер

## Быстрый деплой (автоматический)

```bash
# Из локальной директории проекта
cd /Users/user/Documents/Проекты/vinil_bot_kld
./deploy.sh
```

Скрипт автоматически:
- Создаст пакет для деплоя
- Загрузит файлы на сервер
- Установит зависимости
- Перезапустит сервисы

---

## Ручной деплой (шаг за шагом)

### Шаг 1: Подключение к серверу

```bash
ssh root@176.98.178.109
# Пароль: b4aosWDARJY,rE
```

### Шаг 2: Переход в директорию проекта

```bash
cd /root/vinyl_marketplace_RU
```

### Шаг 3: Обновление .env файла

Создайте правильный `.env` файл с нужными переменными:

```bash
cat > .env << 'EOF'
# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
GOOGLE_SPREADSHEET_ID=1FlMqkV4qRQibJj5UOJ4Q4OMCAu0MtzDLpTkINI9HjuU

# Telegram
TELEGRAM_BOT_TOKEN=8571382458:AAHQKir0yVDPTom93x2PGzgM1o9PLov-918
ADMIN_TELEGRAM_ID=1668456209

# API
API_HOST=0.0.0.0
API_PORT=8000

# LLM (DeepSeek)
LLM_PROVIDER=custom
CUSTOM_LLM_ENDPOINT=https://api.deepseek.com/v1/chat/completions
CUSTOM_API_KEY=sk-570160dff40c40a090cb75304f68c6e6
OPENAI_API_KEY=sk-570160dff40c40a090cb75304f68c6e6

# Google Drive
DRIVE_FOLDER_ID=1FlMqkV4qRQibJj5UOJ4Q4OMCAu0MtzDLpTkINI9HjuU
EOF
```

### Шаг 4: Загрузка обновлённых файлов

Скопируйте файлы с локального компьютера на сервер:

```bash
# На локальном компьютере в другом терминале:
cd /Users/user/Documents/Проекты/vinil_bot_kld

# Загрузка основных файлов
scp vinyl_bot.py root@176.98.178.109:/root/vinyl_marketplace_RU/
scp main.py root@176.98.178.109:/root/vinyl_marketplace_RU/
scp migrate_sheets.py root@176.98.178.109:/root/vinyl_marketplace_RU/
scp verify_system.py root@176.98.178.109:/root/vinyl_marketplace_RU/
scp server.env root@176.98.178.109:/root/vinyl_marketplace_RU/.env

# Загрузка utils директории
scp -r utils root@176.98.178.109:/root/vinyl_marketplace_RU/
```

### Шаг 5: Запуск миграции

На сервере:

```bash
cd /root/vinyl_marketplace_RU
python3 migrate_sheets.py
```

### Шаг 6: Проверка системы

```bash
python3 verify_system.py
```

### Шаг 7: Перезапуск сервисов

```bash
# Остановить старые процессы
pkill -f "python.*vinyl_bot.py"
pkill -f "python.*main.py"

# Запустить заново
nohup python3 main.py > /tmp/vinyl_api.log 2>&1 &
nohup python3 vinyl_bot.py > /tmp/vinyl_bot.log 2>&1 &

# Проверить, что запустились
ps aux | grep python | grep -v grep
```

### Шаг 8: Проверка логов

```bash
# Логи API
tail -f /tmp/vinyl_api.log

# Логи бота
tail -f /tmp/vinyl_bot.log

# Или через journalctl (если используются systemd сервисы)
journalctl -u vinyl_bot.service -f
```

---

## Создание systemd сервисов (опционально)

Для автоматического запуска при перезагрузке сервера:

### Сервис для API

```bash
cat > /etc/systemd/system/vinyl-api.service << 'EOF'
[Unit]
Description=Vinyl Marketplace API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/vinyl_marketplace_RU
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/python3 /root/vinyl_marketplace_RU/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Сервис для бота

```bash
cat > /etc/systemd/system/vinyl-bot.service << 'EOF'
[Unit]
Description=Vinyl Marketplace Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/vinyl_marketplace_RU
Environment="PATH=/usr/bin"
ExecStart=/usr/bin/python3 /root/vinyl_marketplace_RU/vinyl_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Активация сервисов

```bash
systemctl daemon-reload
systemctl enable vinyl-api vinyl-bot
systemctl start vinyl-api vinyl-bot
systemctl status vinyl-api vinyl-bot
```

---

## Проверка работы

### Проверка процессов

```bash
ps aux | grep python | grep -v grep
```

Должны быть видны процессы:
- `python3 main.py`
- `python3 vinyl_bot.py`

### Проверка портов

```bash
netstat -tlnp | grep 8000
```

Должен быть открыт порт 8000 (FastAPI).

### Проверка API

```bash
curl http://localhost:8000/api/records
```

### Тестирование бота

Откройте Telegram и отправьте боту:
- `/start` — должно показать главное меню
- `1` или `VIN-00001` — поиск по артикулу

---

## Устранение неполадок

### Бот не отвечает

```bash
# Проверить логи
tail -100 /tmp/vinyl_bot.log

# Проверить, запущен ли
ps aux | grep vinyl_bot

# Перезапустить
pkill -f vinyl_bot.py
nohup python3 vinyl_bot.py > /tmp/vinyl_bot.log 2>&1 &
```

### API не работает

```bash
# Проверить логи
tail -100 /tmp/vinyl_api.log

# Проверить порт
netstat -tlnp | grep 8000

# Перезапустить
pkill -f main.py
nohup python3 main.py > /tmp/vinyl_api.log 2>&1 &
```

### Ошибки в миграции

```bash
# Проверить .env
cat .env | grep GOOGLE_SPREADSHEET_ID

# Проверить credentials.json
ls -la credentials.json

# Запустить с подробными логами
python3 migrate_sheets.py
```

---

## Полезные команды

```bash
# Мониторинг логов в реальном времени
tail -f /tmp/vinyl_bot.log /tmp/vinyl_api.log

# Очистка логов
> /tmp/vinyl_bot.log
> /tmp/vinyl_api.log

# Перезапуск всего
pkill -f "python.*vinyl"
cd /root/vinyl_marketplace_RU
nohup python3 main.py > /tmp/vinyl_api.log 2>&1 &
nohup python3 vinyl_bot.py > /tmp/vinyl_bot.log 2>&1 &

# Проверка использования ресурсов
htop
```

---

## Контрольный чеклист

- [ ] `.env` файл создан с правильными переменными
- [ ] `credentials.json` существует на сервере
- [ ] Миграция `migrate_sheets.py` выполнена успешно
- [ ] Проверка `verify_system.py` прошла
- [ ] API процесс запущен (порт 8000)
- [ ] Бот процесс запущен
- [ ] Бот отвечает в Telegram
- [ ] Поиск по артикулу работает
- [ ] Админ-кнопки видны в карточках

---

**Готово!** Система должна работать на сервере.
