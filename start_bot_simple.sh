#!/bin/bash
# Запуск бота на VPS без systemd (простой вариант)

VPS="176.98.178.109"
echo "🚀 Запуск бота @Baltset39_bot на VPS $VPS"
echo ""
echo "Введите пароль VPS когда попросит: pneDRE2K?Tz1k-"
echo ""

# Копируем файл
echo "📦 Копируем бота..."
scp -o StrictHostKeyChecking=no telegram_lead_bot.py root@$VPS:/root/baltset_bot.py

echo ""
echo "🚀 Запускаем бота..."

# Подключаемся и запускаем
ssh -o StrictHostKeyChecking=no root@$VPS << 'ENDSSH'
# Останавливаем старый процесс
pkill -f baltset_bot.py || true
pkill -f telegram_lead_bot.py || true

# Устанавливаем зависимости (если нужно)
pip3 install python-telegram-bot==13.15 -q 2>/dev/null || \
    (apt-get update -qq && apt-get install -y python3-pip -qq && pip3 install python-telegram-bot==13.15 -q)

# Запускаем в фоне
cd /root
nohup python3 baltset_bot.py > baltset_bot.log 2>&1 &

echo ""
sleep 2

# Проверяем
if pgrep -f baltset_bot.py > /dev/null; then
    echo "================================"
    echo "✅ БОТ УСПЕШНО ЗАПУЩЕН!"
    echo "================================"
    echo ""
    echo "📱 Проверьте: https://t.me/Baltset39_bot"
    echo "💬 Напишите /start боту"
    echo ""
    echo "📋 PID процесса:"
    pgrep -f baltset_bot.py
    echo ""
    echo "📝 Логи в реальном времени:"
    echo "  ssh root@176.98.178.109 'tail -f /root/baltset_bot.log'"
else
    echo "❌ Ошибка запуска"
    echo "Логи:"
    tail -20 baltset_bot.log
fi
ENDSSH

echo ""
echo "🎉 Готово!"
echo ""
echo "💡 Полезные команды:"
echo "  Проверить статус: ssh root@$VPS 'pgrep -f baltset_bot.py'"
echo "  Посмотреть логи:  ssh root@$VPS 'tail -f /root/baltset_bot.log'"
echo "  Остановить бота:  ssh root@$VPS 'pkill -f baltset_bot.py'"
echo ""
