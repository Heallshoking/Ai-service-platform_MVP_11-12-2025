#!/bin/bash
# Быстрый деплой обновлённого бота

SERVER="root@176.98.178.109"
REMOTE_DIR="/root/vinyl_marketplace_RU"

echo "🚀 Загрузка обновлённого бота на сервер..."

# Загрузка файла
scp vinyl_bot.py $SERVER:$REMOTE_DIR/

echo ""
echo "🔄 Перезапуск бота на сервере..."

# Перезапуск бота
ssh $SERVER << 'ENDSSH'
cd /root/vinyl_marketplace_RU

# Остановка старого процесса
echo "⏹️  Останавливаю старый процесс..."
pkill -f "python.*vinyl_bot.py" || true
sleep 2

# Запуск нового
echo "▶️  Запускаю обновлённого бота..."
nohup python3 vinyl_bot.py > /tmp/vinyl_bot.log 2>&1 &

sleep 3

# Проверка
if pgrep -f "python.*vinyl_bot.py" > /dev/null; then
    echo "✅ Бот запущен успешно"
    echo ""
    echo "📱 Теперь в Telegram отправьте боту: /start"
    echo ""
    tail -20 /tmp/vinyl_bot.log
else
    echo "❌ Ошибка запуска бота"
    echo ""
    echo "Логи:"
    tail -50 /tmp/vinyl_bot.log
fi
ENDSSH

echo ""
echo "✅ Готово! Проверьте бота в Telegram."
