#!/bin/bash
# Деплой Telegram Folders Integration на VPS

echo "📁 Деплой Telegram Folders Integration..."
echo ""

# Проверка наличия файлов
if [ ! -f "telegram_folders_integration.py" ]; then
    echo "❌ Ошибка: telegram_folders_integration.py не найден"
    exit 1
fi

if [ ! -f "telegram_client_bot.py" ]; then
    echo "❌ Ошибка: telegram_client_bot.py не найден"
    exit 1
fi

echo "✅ Файлы найдены"
echo ""

# 1. Копируем telegram_folders_integration.py
echo "📤 Копирование telegram_folders_integration.py..."
scp telegram_folders_integration.py root@176.98.178.109:/root/ai_service_bots/

if [ $? -eq 0 ]; then
    echo "✅ telegram_folders_integration.py скопирован"
else
    echo "❌ Ошибка копирования telegram_folders_integration.py"
    exit 1
fi

# 2. Копируем обновленный telegram_client_bot.py
echo "📤 Копирование обновленного telegram_client_bot.py..."
scp telegram_client_bot.py root@176.98.178.109:/root/ai_service_bots/

if [ $? -eq 0 ]; then
    echo "✅ telegram_client_bot.py скопирован"
else
    echo "❌ Ошибка копирования telegram_client_bot.py"
    exit 1
fi

echo ""
echo "🔄 Перезапуск клиентского бота..."

# 3. Перезапускаем бота через SSH
ssh root@176.98.178.109 << 'EOF'
cd /root/ai_service_bots/

# Останавливаем бота
echo "🛑 Останавливаем telegram_client_bot.py..."
pkill -f telegram_client_bot.py

# Ждем 2 секунды
sleep 2

# Запускаем бота
echo "🚀 Запускаем telegram_client_bot.py..."
nohup python3 telegram_client_bot.py > client_bot.log 2>&1 &

# Ждем 1 секунду для запуска
sleep 1

# Проверяем статус
echo ""
echo "📊 Проверка статуса:"
ps aux | grep telegram_client_bot.py | grep -v grep

echo ""
echo "📋 Последние строки лога:"
tail -n 10 client_bot.log

EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Деплой завершен успешно!"
    echo ""
    echo "🧪 Тестирование:"
    echo "1. Откройте Telegram: @ai_service_client_bot"
    echo "2. Выполните /start"
    echo "3. Создайте заявку"
    echo "4. После подтверждения должна появиться кнопка '📁 Добавить папку'"
    echo ""
    echo "📖 Подробная инструкция: TELEGRAM_FOLDERS_GUIDE.md"
else
    echo ""
    echo "❌ Ошибка при перезапуске бота"
    echo "Проверьте логи: ssh root@176.98.178.109 'tail -f /root/ai_service_bots/client_bot.log'"
fi
