#!/bin/bash
# Автоматический деплой Telegram бота на VPS
# Использование: ./deploy_telegram_bot.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем деплой Telegram бота на VPS${NC}"
echo ""

# Конфигурация
VPS_IP="176.98.178.109"
VPS_USER="root"
VPS_PASSWORD="pneDRE2K?Tz1k-"
BOT_DIR="/root/baltset_bot"
LOCAL_BOT_FILE="telegram_lead_bot.py"
LOCAL_ENV_FILE=".env"

# Проверка наличия файлов
if [ ! -f "$LOCAL_BOT_FILE" ]; then
    echo -e "${RED}❌ Файл $LOCAL_BOT_FILE не найден!${NC}"
    exit 1
fi

if [ ! -f "$LOCAL_ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден, создаём временный${NC}"
    cat > .env.tmp << 'EOF'
TELEGRAM_BOT_TOKEN=8594337620:AAEV59Hi-38xUjTKd70hRTkvcR6miWWWxls
ADMIN_CHAT_ID=-1002468635742
EOF
    LOCAL_ENV_FILE=".env.tmp"
fi

echo -e "${GREEN}📦 Шаг 1: Подключение к VPS${NC}"

# Создаём директорию на VPS
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'ENDSSH'
    mkdir -p /root/baltset_bot
    echo "✅ Директория создана"
ENDSSH

echo -e "${GREEN}📦 Шаг 2: Копирование файлов${NC}"

# Копируем бота
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no $LOCAL_BOT_FILE $VPS_USER@$VPS_IP:$BOT_DIR/

# Копируем .env
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no $LOCAL_ENV_FILE $VPS_USER@$VPS_IP:$BOT_DIR/.env

echo -e "${GREEN}📦 Шаг 3: Установка зависимостей${NC}"

# Устанавливаем Python и зависимости
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'ENDSSH'
    cd /root/baltset_bot
    
    # Обновляем систему
    apt-get update -qq
    
    # Устанавливаем Python3 и pip
    apt-get install -y python3 python3-pip -qq
    
    # Устанавливаем библиотеку для Telegram
    pip3 install python-telegram-bot==13.15 -q
    
    echo "✅ Зависимости установлены"
ENDSSH

echo -e "${GREEN}📦 Шаг 4: Создание systemd сервиса${NC}"

# Создаём systemd unit для автозапуска
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'ENDSSH'
    cat > /etc/systemd/system/baltset-bot.service << 'EOF'
[Unit]
Description=BALTSET Telegram Lead Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/baltset_bot
EnvironmentFile=/root/baltset_bot/.env
ExecStart=/usr/bin/python3 /root/baltset_bot/telegram_lead_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Перезагружаем systemd
    systemctl daemon-reload
    
    echo "✅ Systemd сервис создан"
ENDSSH

echo -e "${GREEN}📦 Шаг 5: Запуск бота${NC}"

# Останавливаем старый процесс (если есть)
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'ENDSSH'
    # Останавливаем сервис
    systemctl stop baltset-bot 2>/dev/null || true
    
    # Убиваем все процессы бота
    pkill -f telegram_lead_bot.py || true
    
    # Запускаем сервис
    systemctl start baltset-bot
    
    # Включаем автозапуск
    systemctl enable baltset-bot
    
    # Проверяем статус
    sleep 2
    systemctl status baltset-bot --no-pager -l
    
    echo ""
    echo "✅ Бот запущен!"
ENDSSH

echo ""
echo -e "${GREEN}🎉 ДЕПЛОЙ ЗАВЕРШЁН!${NC}"
echo ""
echo -e "${YELLOW}📊 Полезные команды:${NC}"
echo "  Статус бота:     ssh root@$VPS_IP 'systemctl status baltset-bot'"
echo "  Логи бота:       ssh root@$VPS_IP 'journalctl -u baltset-bot -f'"
echo "  Перезапуск:      ssh root@$VPS_IP 'systemctl restart baltset-bot'"
echo "  Остановка:       ssh root@$VPS_IP 'systemctl stop baltset-bot'"
echo ""
echo -e "${GREEN}✅ Бот работает 24/7 и будет автоматически перезапускаться при падении${NC}"
echo ""

# Удаляем временный .env если создавали
if [ -f ".env.tmp" ]; then
    rm .env.tmp
fi

# Проверяем что бот работает
echo -e "${YELLOW}🔍 Проверяем работу бота...${NC}"
sleep 3

sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP << 'ENDSSH'
    if systemctl is-active --quiet baltset-bot; then
        echo "✅ Бот активен и работает!"
        echo ""
        echo "📱 Попробуйте написать боту: https://t.me/Baltset39_bot"
    else
        echo "❌ Бот не запустился. Проверьте логи:"
        journalctl -u baltset-bot -n 50 --no-pager
    fi
ENDSSH

echo ""
echo -e "${GREEN}🎊 Готово! Бот задеплоен на VPS 176.98.178.109${NC}"
