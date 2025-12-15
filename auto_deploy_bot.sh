#!/bin/bash
# Автоматический деплой бота на VPS 176.98.178.109
set -e

echo "🚀 Деплой Telegram бота @Baltset39_bot на VPS"
echo ""

VPS="176.98.178.109"

# Шаг 1: Копируем файлы
echo "📦 Копируем файлы на VPS..."
scp telegram_lead_bot.py root@$VPS:/root/
scp .env root@$VPS:/root/

echo ""
echo "📦 Настраиваем и запускаем бота..."

# Шаг 2: Настройка и запуск
ssh root@$VPS 'bash -s' << 'ENDSSH'
    echo "📁 Создаём директорию..."
    mkdir -p /root/baltset_bot
    mv /root/telegram_lead_bot.py /root/baltset_bot/ 2>/dev/null || true
    mv /root/.env /root/baltset_bot/ 2>/dev/null || true
    cd /root/baltset_bot
    
    echo "📦 Устанавливаем Python и зависимости..."
    apt-get update -qq > /dev/null 2>&1
    apt-get install -y python3 python3-pip -qq > /dev/null 2>&1
    pip3 install python-telegram-bot==13.15 -q > /dev/null 2>&1
    
    echo "🛑 Останавливаем старый процесс..."
    systemctl stop baltset-bot 2>/dev/null || true
    pkill -f telegram_lead_bot.py || true
    
    echo "⚙️  Создаём systemd сервис..."
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
    
    echo "🚀 Запускаем бота..."
    systemctl daemon-reload
    systemctl start baltset-bot
    systemctl enable baltset-bot
    
    sleep 3
    
    echo ""
    echo "================================"
    if systemctl is-active --quiet baltset-bot; then
        echo "✅ БОТ УСПЕШНО ЗАПУЩЕН!"
        echo "================================"
        echo ""
        echo "📱 Проверьте: https://t.me/Baltset39_bot"
        echo "💬 Напишите /start боту"
        echo ""
        systemctl status baltset-bot --no-pager -l | head -15
    else
        echo "❌ ОШИБКА ЗАПУСКА"
        echo "================================"
        journalctl -u baltset-bot -n 30 --no-pager
    fi
ENDSSH

echo ""
echo "🎉 Деплой завершён!"
echo ""
echo "📊 Полезные команды:"
echo "  Логи:       ssh root@$VPS 'journalctl -u baltset-bot -f'"
echo "  Статус:     ssh root@$VPS 'systemctl status baltset-bot'"
echo "  Перезапуск: ssh root@$VPS 'systemctl restart baltset-bot'"
echo ""
