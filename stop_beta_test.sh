#!/bin/bash
# Остановка бета-теста

echo ""
echo "🛑 Останавливаем бета-тест..."
echo ""

# Остановка ботов
pkill -f "telegram_client_bot.py" 2>/dev/null
pkill -f "telegram_master_bot.py" 2>/dev/null

sleep 2

# Проверка
if pgrep -f "telegram_client_bot.py" > /dev/null || pgrep -f "telegram_master_bot.py" > /dev/null; then
    echo "⚠️  Процессы всё ещё запущены, принудительная остановка..."
    pkill -9 -f "telegram_client_bot.py" 2>/dev/null
    pkill -9 -f "telegram_master_bot.py" 2>/dev/null
    sleep 1
fi

echo "✅ Бета-тест остановлен"
echo ""
echo "📊 Последние логи:"
echo ""
echo "=== Бот клиента ==="
tail -20 logs/client_bot.log 2>/dev/null || echo "Логи не найдены"
echo ""
echo "=== Бот мастера ==="
tail -20 logs/master_bot.log 2>/dev/null || echo "Логи не найдены"
echo ""
