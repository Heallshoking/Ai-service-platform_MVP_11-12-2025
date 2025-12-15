#!/bin/bash
# Быстрый запуск бета-теста MVP
# Запускает оба бота для клиента и мастера

echo ""
echo "🧪 =================================="
echo "   ЗАПУСК БЕТА-ТЕСТА MVP"
echo "   =================================="
echo ""

# Проверка .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo ""
    echo "Создайте файл .env:"
    echo "  cp .env.example .env"
    echo ""
    echo "Заполните токены ботов в .env:"
    echo "  TELEGRAM_CLIENT_BOT_TOKEN=..."
    echo "  TELEGRAM_MASTER_BOT_TOKEN=..."
    echo ""
    exit 1
fi

# Проверка токенов
source .env

if [ -z "$TELEGRAM_CLIENT_BOT_TOKEN" ] || [ "$TELEGRAM_CLIENT_BOT_TOKEN" = "your_client_bot_token_here" ]; then
    echo "❌ Токен бота клиента не настроен!"
    echo ""
    echo "Получите токен:"
    echo "  1. Откройте @BotFather в Telegram"
    echo "  2. /newbot → создайте бота для клиентов"
    echo "  3. Скопируйте токен в .env"
    echo ""
    exit 1
fi

if [ -z "$TELEGRAM_MASTER_BOT_TOKEN" ] || [ "$TELEGRAM_MASTER_BOT_TOKEN" = "your_master_bot_token_here" ]; then
    echo "❌ Токен бота мастера не настроен!"
    echo ""
    echo "Получите токен:"
    echo "  1. Откройте @BotFather в Telegram"
    echo "  2. /newbot → создайте бота для мастеров"
    echo "  3. Скопируйте токен в .env"
    echo ""
    exit 1
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p data
mkdir -p logs

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
python3 -c "import telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Устанавливаем зависимости..."
    pip3 install python-telegram-bot httpx python-dotenv openai -q
fi

echo "✅ Зависимости установлены"
echo ""

# Остановка старых процессов
echo "🛑 Останавливаем старые процессы..."
pkill -f "telegram_client_bot.py" 2>/dev/null
pkill -f "telegram_master_bot.py" 2>/dev/null
sleep 2

# Запуск бота клиента
echo "🤖 Запуск бота для клиентов..."
nohup python3 telegram_client_bot.py > logs/client_bot.log 2>&1 &
CLIENT_PID=$!
echo "   PID: $CLIENT_PID"

sleep 3

# Запуск бота мастера
echo "👷 Запуск бота для мастеров..."
nohup python3 telegram_master_bot.py > logs/master_bot.log 2>&1 &
MASTER_PID=$!
echo "   PID: $MASTER_PID"

sleep 3

echo ""
echo "=================================="
echo "✅ БЕТА-ТЕСТ ЗАПУЩЕН!"
echo "=================================="
echo ""

# Проверка статуса
if pgrep -f "telegram_client_bot.py" > /dev/null; then
    echo "✅ Бот клиента работает (PID: $(pgrep -f telegram_client_bot.py))"
else
    echo "❌ Бот клиента НЕ запустился!"
    echo "   Логи: tail -f logs/client_bot.log"
fi

if pgrep -f "telegram_master_bot.py" > /dev/null; then
    echo "✅ Бот мастера работает (PID: $(pgrep -f telegram_master_bot.py))"
else
    echo "❌ Бот мастера НЕ запустился!"
    echo "   Логи: tail -f logs/master_bot.log"
fi

echo ""
echo "=================================="
echo "📱 НАЧНИТЕ ТЕСТИРОВАНИЕ:"
echo "=================================="
echo ""
echo "1️⃣  Откройте бота клиента в Telegram"
echo "    Найдите по username (см. @BotFather)"
echo ""
echo "2️⃣  Отправьте: /start"
echo "    Создайте тестовую заявку"
echo ""
echo "3️⃣  Откройте бота мастера (другой аккаунт)"
echo "    Примите заявку"
echo ""
echo "📋 Подробная инструкция:"
echo "    cat BETA_TEST_GUIDE.md"
echo ""
echo "=================================="
echo "🔍 УПРАВЛЕНИЕ:"
echo "=================================="
echo ""
echo "Логи клиента:  tail -f logs/client_bot.log"
echo "Логи мастера:  tail -f logs/master_bot.log"
echo ""
echo "Остановить:    ./stop_beta_test.sh"
echo "Перезапустить: ./start_beta_test.sh"
echo ""
echo "=================================="
echo ""
