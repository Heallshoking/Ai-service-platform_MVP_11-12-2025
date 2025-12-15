#!/bin/bash
# Деплой продакшн-ботов на VPS
# Запускает клиентского и мастерского ботов на 176.98.178.109

echo ""
echo "🚀 =========================================="
echo "   ДЕПЛОЙ ПРОДАКШН-БОТОВ НА VPS"
echo "   =========================================="
echo ""

VPS="176.98.178.109"
VPS_USER="root"
VPS_PASSWORD="pneDRE2K?Tz1k-"

echo "📋 Боты для деплоя:"
echo "   🙋 Клиент: @ai_service_client_bot"
echo "   👷 Мастер: @ai_service_master_bot"
echo "   💰 Комиссия: 30% (не афишируем)"
echo ""

# Проверка файлов
if [ ! -f "telegram_client_bot.py" ]; then
    echo "❌ Файл telegram_client_bot.py не найден!"
    exit 1
fi

if [ ! -f "telegram_master_bot.py" ]; then
    echo "❌ Файл telegram_master_bot.py не найден!"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

echo "📦 Копируем файлы на VPS..."

# Используем expect для автоматизации
expect << 'ENDEXPECT'
set timeout 120
set vps "176.98.178.109"
set password "pneDRE2K?Tz1k-"

# Копируем боты
puts "📤 Копируем telegram_client_bot.py..."
spawn scp telegram_client_bot.py root@$vps:/root/
expect "password:"
send "$password\r"
expect eof

puts "📤 Копируем telegram_master_bot.py..."
spawn scp telegram_master_bot.py root@$vps:/root/
expect "password:"
send "$password\r"
expect eof

puts "📤 Копируем .env..."
spawn scp .env root@$vps:/root/
expect "password:"
send "$password\r"
expect eof

puts "📤 Копируем зависимости (ai_assistant.py)..."
spawn scp ai_assistant.py root@$vps:/root/
expect "password:"
send "$password\r"
expect eof

puts "\n✅ Файлы скопированы"
ENDEXPECT

echo ""
echo "⚙️  Настройка окружения на VPS..."

# Настройка и запуск на VPS
expect << 'ENDSSH'
set timeout 120
set vps "176.98.178.109"
set password "pneDRE2K?Tz1k-"

spawn ssh root@$vps
expect "password:"
send "$password\r"
expect "#"

# Создаём директорию
send "mkdir -p /root/ai_service_bots\r"
expect "#"

# Перемещаем файлы
send "mv /root/telegram_client_bot.py /root/ai_service_bots/\r"
expect "#"
send "mv /root/telegram_master_bot.py /root/ai_service_bots/\r"
expect "#"
send "mv /root/.env /root/ai_service_bots/\r"
expect "#"
send "mv /root/ai_assistant.py /root/ai_service_bots/ 2>/dev/null || true\r"
expect "#"

puts "\n📦 Устанавливаем зависимости..."
send "cd /root/ai_service_bots\r"
expect "#"

send "pip3 install python-telegram-bot httpx python-dotenv openai -q\r"
expect "#"

puts "✅ Зависимости установлены"

# Останавливаем старые процессы
puts "\n🛑 Останавливаем старые процессы..."
send "pkill -9 -f telegram_client_bot.py\r"
expect "#"
send "pkill -9 -f telegram_master_bot.py\r"
expect "#"
send "sleep 2\r"
expect "#"

# Создаём systemd сервис для бота клиента
puts "\n📝 Создаём systemd сервис для бота клиента..."
send "cat > /etc/systemd/system/ai-client-bot.service << 'EOFCLIENT'\r"
send "\[Unit\]\r"
send "Description=AI Service Platform - Client Bot\r"
send "After=network.target\r"
send "\r"
send "\[Service\]\r"
send "Type=simple\r"
send "User=root\r"
send "WorkingDirectory=/root/ai_service_bots\r"
send "ExecStart=/usr/bin/python3 /root/ai_service_bots/telegram_client_bot.py\r"
send "Restart=always\r"
send "RestartSec=10\r"
send "\r"
send "\[Install\]\r"
send "WantedBy=multi-user.target\r"
send "EOFCLIENT\r"
expect "#"

# Создаём systemd сервис для бота мастера
puts "📝 Создаём systemd сервис для бота мастера..."
send "cat > /etc/systemd/system/ai-master-bot.service << 'EOFMASTER'\r"
send "\[Unit\]\r"
send "Description=AI Service Platform - Master Bot\r"
send "After=network.target\r"
send "\r"
send "\[Service\]\r"
send "Type=simple\r"
send "User=root\r"
send "WorkingDirectory=/root/ai_service_bots\r"
send "ExecStart=/usr/bin/python3 /root/ai_service_bots/telegram_master_bot.py\r"
send "Restart=always\r"
send "RestartSec=10\r"
send "\r"
send "\[Install\]\r"
send "WantedBy=multi-user.target\r"
send "EOFMASTER\r"
expect "#"

# Перезагружаем systemd
puts "\n🔄 Перезагружаем systemd..."
send "systemctl daemon-reload\r"
expect "#"

# Запускаем боты
puts "\n🚀 Запускаем ботов..."
send "systemctl start ai-client-bot\r"
expect "#"
send "systemctl start ai-master-bot\r"
expect "#"

# Включаем автозапуск
send "systemctl enable ai-client-bot\r"
expect "#"
send "systemctl enable ai-master-bot\r"
expect "#"

send "sleep 5\r"
expect "#"

# Проверяем статус
puts "\n📊 Проверка статуса ботов...\n"
send "systemctl status ai-client-bot --no-pager | head -10\r"
expect "#"
send "systemctl status ai-master-bot --no-pager | head -10\r"
expect "#"

send "exit\r"
expect eof

puts "\n✅ Деплой завершён!"
ENDSSH

echo ""
echo "=========================================="
echo "✅ ПРОДАКШН-БОТЫ ЗАПУЩЕНЫ!"
echo "=========================================="
echo ""
echo "📱 Боты:"
echo "   🙋 Клиент: @ai_service_client_bot"
echo "   👷 Мастер: @ai_service_master_bot"
echo ""
echo "🔍 Проверка:"
echo "   Клиент: ssh root@$VPS 'systemctl status ai-client-bot'"
echo "   Мастер: ssh root@$VPS 'systemctl status ai-master-bot'"
echo ""
echo "📋 Логи:"
echo "   Клиент: ssh root@$VPS 'journalctl -u ai-client-bot -f'"
echo "   Мастер: ssh root@$VPS 'journalctl -u ai-master-bot -f'"
echo ""
echo "🎉 Готово! Боты работают 24/7"
echo ""
