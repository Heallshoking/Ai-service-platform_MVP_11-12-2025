#!/bin/bash
# Простой деплой бота через SCP и SSH
# Использование: ./deploy_bot_simple.sh

set -e

VPS_IP="176.98.178.109"
VPS_USER="root"

echo "🚀 Деплой Telegram бота на VPS $VPS_IP"
echo ""
echo "📦 Шаг 1: Копируем файлы..."

# Копируем бота и .env
scp -o StrictHostKeyChecking=no telegram_lead_bot.py .env $VPS_USER@$VPS_IP:/root/

echo ""
echo "📦 Шаг 2: Настраиваем и запускаем бота..."

# Подключаемся и настраиваем
ssh -o StrictHostKeyChecking=no $VPS_USER@$VPS_IP 'bash -s' << 'ENDSSH'
    # Создаём директорию
    mkdir -p /root/baltset_bot
    mv /root/telegram_lead_bot.py /root/baltset_bot/
    mv /root/.env /root/baltset_bot/
    cd /root/baltset_bot
    
    # Устанавливаем зависимости
    echo "⏳ Устанавливаем зависимости..."
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y python3 python3-pip -qq > /dev/null 2>&1
    pip3 install python-telegram-bot==13.15 -q > /dev/null 2>&1
    
    # Останавливаем старый процесс
    pkill -f telegram_lead_bot.py || true
    
    # Создаём systemd сервис
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
    
    # Перезагружаем systemd и запускаем
    systemctl daemon-reload
    systemctl stop baltset-bot 2>/dev/null || true
    systemctl start baltset-bot
    systemctl enable baltset-bot
    
    sleep 2
    
    # Проверяем статус
    if systemctl is-active --quiet baltset-bot; then
        echo ""
        echo "✅ Бот успешно запущен!"
        echo "📱 Проверьте: https://t.me/Baltset39_bot"
        echo ""
        systemctl status baltset-bot --no-pager -l | head -15
    else
        echo "❌ Ошибка запуска. Логи:"
        journalctl -u baltset-bot -n 20 --no-pager
    fi
ENDSSH

echo ""
echo "🎉 Деплой завершён!"
echo ""
echo "📊 Полезные команды:"
echo "  Логи:       ssh root@$VPS_IP 'journalctl -u baltset-bot -f'"
echo "  Перезапуск: ssh root@$VPS_IP 'systemctl restart baltset-bot'"
echo "  Статус:     ssh root@$VPS_IP 'systemctl status baltset-bot'"
echo ""
