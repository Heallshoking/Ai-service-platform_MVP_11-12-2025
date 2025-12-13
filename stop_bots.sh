#!/bin/bash
# Остановка всех Telegram ботов

cd "$(dirname "$0")"

echo "🛑 Останавливаю Telegram ботов..."

# Остановить процессы
pkill -f "telegram_client_bot.py"
pkill -f "telegram_master_bot.py"

# Удалить PID файлы
rm -f logs/client_bot.pid logs/master_bot.pid

sleep 1

# Проверка
if ! pgrep -f "telegram.*bot.py" > /dev/null; then
    echo "✅ Все боты остановлены"
else
    echo "⚠️ Некоторые процессы всё ещё работают. Пробую принудительно..."
    pkill -9 -f "telegram.*bot.py"
    sleep 1
    echo "✅ Боты остановлены принудительно"
fi
