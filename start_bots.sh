#!/bin/bash
# Запуск всех Telegram ботов для AI Service Platform

cd "$(dirname "$0")"

echo "🤖 Запуск Telegram ботов..."
echo ""

# Создать директорию для логов
mkdir -p logs

# Остановить старые процессы (если есть)
echo "🛑 Останавливаю старые процессы..."
pkill -f "telegram_client_bot.py" 2>/dev/null
pkill -f "telegram_master_bot.py" 2>/dev/null
sleep 1

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "❌ Ошибка: .env файл не найден!"
    echo "   Создайте .env из .env.example и заполните токены ботов"
    exit 1
fi

# Запуск бота клиентов
echo "▶️ Запускаю бота для клиентов..."
nohup python3 telegram_client_bot.py > logs/client_bot.log 2>&1 &
CLIENT_PID=$!
echo $CLIENT_PID > logs/client_bot.pid
echo "   ✅ Бот клиентов запущен (PID: $CLIENT_PID)"
echo "   📋 Логи: logs/client_bot.log"
echo ""

# Запуск бота мастеров
echo "▶️ Запускаю бота для мастеров..."
nohup python3 telegram_master_bot.py > logs/master_bot.log 2>&1 &
MASTER_PID=$!
echo $MASTER_PID > logs/master_bot.pid
echo "   ✅ Бот мастеров запущен (PID: $MASTER_PID)"
echo "   📋 Логи: logs/master_bot.log"
echo ""

# Проверка через 3 секунды
sleep 3
echo "🔍 Проверка статуса..."
if ps -p $CLIENT_PID > /dev/null && ps -p $MASTER_PID > /dev/null; then
    echo "✅ Все боты работают!"
    echo ""
    echo "📱 Боты готовы принимать сообщения:"
    echo "   • @ai_service_client_bot - для клиентов"
    echo "   • @ai_service_master_bot - для мастеров"
    echo ""
    echo "📊 Для просмотра логов:"
    echo "   tail -f logs/client_bot.log"
    echo "   tail -f logs/master_bot.log"
    echo ""
    echo "🛑 Для остановки:"
    echo "   ./stop_bots.sh"
else
    echo "❌ Ошибка запуска! Проверьте логи:"
    echo "   cat logs/client_bot.log"
    echo "   cat logs/master_bot.log"
    exit 1
fi
