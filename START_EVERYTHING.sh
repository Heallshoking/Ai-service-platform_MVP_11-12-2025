#!/bin/bash
# АВТОМАТИЧЕСКИЙ ЗАПУСК ВСЕГО - ОДНА КОМАНДА
# Установит зависимости, запустит ботов локально и на VPS

clear
echo ""
echo "🚀 ================================================"
echo "   АВТОМАТИЧЕСКИЙ ЗАПУСК MVP ПЛАТФОРМЫ"
echo "   ================================================"
echo ""
echo "📋 Что будет сделано:"
echo "   1. Установка зависимостей"
echo "   2. Запуск ботов ЛОКАЛЬНО (для теста)"
echo "   3. Деплой ботов на VPS (продакшн)"
echo ""
read -p "Нажмите Enter для продолжения..."

# 1. УСТАНОВКА ЗАВИСИМОСТЕЙ
echo ""
echo "📦 Шаг 1/3: Установка зависимостей..."
python3 -m pip install --user python-telegram-bot==20.7 httpx python-dotenv --quiet
echo "✅ Зависимости установлены"

# 2. ЛОКАЛЬНЫЙ ЗАПУСК ДЛЯ ТЕСТА
echo ""
echo "🧪 Шаг 2/3: Запуск ботов локально..."
echo ""
echo "Останавливаю старые процессы..."
pkill -f telegram_client_bot.py 2>/dev/null
pkill -f telegram_master_bot.py 2>/dev/null
sleep 2

echo "Запускаю бота клиента..."
nohup python3 telegram_client_bot.py > logs/client_local.log 2>&1 &
sleep 3

echo "Запускаю бота мастера..."
nohup python3 telegram_master_bot.py > logs/master_local.log 2>&1 &
sleep 3

if pgrep -f telegram_client_bot.py > /dev/null; then
    echo "✅ Бот клиента запущен (PID: $(pgrep -f telegram_client_bot.py))"
else
    echo "❌ Бот клиента НЕ запустился! Смотрите: tail -f logs/client_local.log"
fi

if pgrep -f telegram_master_bot.py > /dev/null; then
    echo "✅ Бот мастера запущен (PID: $(pgrep -f telegram_master_bot.py))"
else
    echo "❌ Бот мастера НЕ запустился! Смотрите: tail -f logs/master_local.log"
fi

echo ""
echo "📱 ТЕСТИРУЙТЕ ПРЯМО СЕЙЧАС:"
echo "   Клиент: https://t.me/ai_service_client_bot"
echo "   Мастер: https://t.me/ai_service_master_bot"
echo ""
echo "Логи:"
echo "   tail -f logs/client_local.log"
echo "   tail -f logs/master_local.log"
echo ""

# 3. ДЕПЛОЙ НА VPS
echo ""
read -p "Задеплоить на VPS? (y/n): " deploy
if [ "$deploy" = "y" ] || [ "$deploy" = "Y" ]; then
    echo ""
    echo "🚀 Шаг 3/3: Деплой на VPS..."
    echo ""
    
    VPS="176.98.178.109"
    
    # Копируем файлы
    echo "📤 Копирование файлов..."
    scp telegram_client_bot.py telegram_master_bot.py .env root@$VPS:/root/
    
    # Настройка и запуск
    echo "⚙️  Настройка на VPS..."
    ssh root@$VPS << 'ENDSSH'
mkdir -p /root/ai_service_bots
mv /root/telegram_*.py /root/.env /root/ai_service_bots/ 2>/dev/null
cd /root/ai_service_bots

# Установка зависимостей
pip3 install python-telegram-bot==20.7 httpx python-dotenv -q

# Остановка старых
pkill -9 -f telegram_client_bot.py
pkill -9 -f telegram_master_bot.py
sleep 2

# Запуск в фоне
nohup python3 telegram_client_bot.py > client.log 2>&1 &
nohup python3 telegram_master_bot.py > master.log 2>&1 &
sleep 5

# Проверка
if pgrep -f telegram_client_bot.py > /dev/null; then
    echo "✅ Бот клиента на VPS работает"
else
    echo "❌ Бот клиента на VPS НЕ работает"
fi

if pgrep -f telegram_master_bot.py > /dev/null; then
    echo "✅ Бот мастера на VPS работает"
else
    echo "❌ Бот мастера на VPS НЕ работает"
fi
ENDSSH
    
    echo ""
    echo "✅ Деплой на VPS завершён!"
else
    echo ""
    echo "⏭️  Деплой на VPS пропущен"
fi

echo ""
echo "================================================"
echo "✅ ВСЁ ГОТОВО!"
echo "================================================"
echo ""
echo "📱 Боты:"
echo "   🙋 Клиент: @ai_service_client_bot"
echo "   👷 Мастер: @ai_service_master_bot"
echo ""
echo "💰 Комиссия: 30% (автоматически)"
echo ""
echo "🧪 Для тестирования:"
echo "   1. Откройте @ai_service_client_bot"
echo "   2. Отправьте /start"
echo "   3. Создайте заявку"
echo ""
echo "Остановить локальные боты:"
echo "   pkill -f telegram_client_bot.py"
echo "   pkill -f telegram_master_bot.py"
echo ""
