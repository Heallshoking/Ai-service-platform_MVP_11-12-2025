#!/bin/bash
# Настройка VPS для Telegram ботов AI Service Platform
# Сервер: 176.98.178.109

echo "🚀 Начинаю настройку сервера для Telegram ботов..."
echo ""

# 1. Обновление системы
echo "📦 Шаг 1/8: Обновление системы..."
apt update && apt upgrade -y

# 2. Установка Python 3 и pip
echo "🐍 Шаг 2/8: Установка Python 3.11..."
apt install -y python3 python3-pip python3-venv git curl

# 3. Создание пользователя для ботов (безопасность)
echo "👤 Шаг 3/8: Создание пользователя 'botuser'..."
if ! id "botuser" &>/dev/null; then
    useradd -m -s /bin/bash botuser
    echo "✅ Пользователь botuser создан"
else
    echo "⚠️ Пользователь botuser уже существует"
fi

# 4. Создание директорий
echo "📁 Шаг 4/8: Создание рабочих директорий..."
mkdir -p /opt/ai-service-bots
chown -R botuser:botuser /opt/ai-service-bots

# 5. Клонирование репозитория
echo "📥 Шаг 5/8: Клонирование проекта из GitHub..."
cd /opt/ai-service-bots
sudo -u botuser git clone https://github.com/Heallshoking/balt-set.ru.git .

# 6. Создание виртуального окружения
echo "🔧 Шаг 6/8: Настройка виртуального окружения..."
sudo -u botuser python3 -m venv venv
sudo -u botuser venv/bin/pip install --upgrade pip
sudo -u botuser venv/bin/pip install -r requirements.txt

# 7. Создание .env файла
echo "⚙️ Шаг 7/8: Создание .env файла..."
cat > /opt/ai-service-bots/.env << 'EOF'
# AI Service Platform - Production Environment
ENVIRONMENT=production
DEBUG=false
DATABASE_PATH=./data/ai_service.db

# API URL (продакшн)
API_URL=https://app.balt-set.ru

# Telegram боты
TELEGRAM_CLIENT_BOT_TOKEN=8546494378:AAEXpAgazUGMSXi282M56uhnLBD7fwQ3UzU
TELEGRAM_MASTER_BOT_TOKEN=8558486884:AAFEAnfaAKlQtoQ0Qs9vAuJ9p0Pa-XLMsBg

# Комиссия
PLATFORM_COMMISSION_PERCENT=25

# Секретный ключ
SECRET_KEY=ai_service_platform_secret_production_2024

# Порт (не используется для ботов)
PORT=8000
EOF

chown botuser:botuser /opt/ai-service-bots/.env
chmod 600 /opt/ai-service-bots/.env

# 8. Создание systemd сервисов
echo "🔧 Шаг 8/8: Создание systemd сервисов..."

# Сервис для бота клиентов
cat > /etc/systemd/system/telegram-client-bot.service << 'EOF'
[Unit]
Description=AI Service Platform - Telegram Client Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/ai-service-bots
Environment="PATH=/opt/ai-service-bots/venv/bin:/usr/bin:/bin"
ExecStart=/opt/ai-service-bots/venv/bin/python telegram_client_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-client-bot.log
StandardError=append:/var/log/telegram-client-bot.error.log

[Install]
WantedBy=multi-user.target
EOF

# Сервис для бота мастеров
cat > /etc/systemd/system/telegram-master-bot.service << 'EOF'
[Unit]
Description=AI Service Platform - Telegram Master Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/ai-service-bots
Environment="PATH=/opt/ai-service-bots/venv/bin:/usr/bin:/bin"
ExecStart=/opt/ai-service-bots/venv/bin/python telegram_master_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-master-bot.log
StandardError=append:/var/log/telegram-master-bot.error.log

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
systemctl daemon-reload

# Включение автозапуска
systemctl enable telegram-client-bot
systemctl enable telegram-master-bot

# Запуск сервисов
systemctl start telegram-client-bot
systemctl start telegram-master-bot

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "📊 Проверка статуса:"
systemctl status telegram-client-bot --no-pager
echo ""
systemctl status telegram-master-bot --no-pager
echo ""
echo "📋 Логи:"
echo "  • Бот клиентов: tail -f /var/log/telegram-client-bot.log"
echo "  • Бот мастеров: tail -f /var/log/telegram-master-bot.log"
echo ""
echo "🔧 Управление:"
echo "  • Перезапуск: systemctl restart telegram-client-bot telegram-master-bot"
echo "  • Остановка: systemctl stop telegram-client-bot telegram-master-bot"
echo "  • Статус: systemctl status telegram-client-bot telegram-master-bot"
echo ""
echo "🚀 Боты запущены и работают 24/7!"
