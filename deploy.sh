#!/bin/bash

# 🚀 Скрипт автоматического деплоя MVP

echo "═══════════════════════════════════════════════════════════"
echo "   🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ MVP"
echo "═══════════════════════════════════════════════════════════"
echo ""

cd /Users/user/Documents/Projects/Github/balt-set.ru

echo "📦 Добавление всех файлов в Git..."
git add .

echo ""
echo "💾 Создание коммита..."
git commit -m "🚀 MVP готов: home.html + 6 услуг с калькуляторами + документация"

echo ""
echo "📤 Отправка на GitHub..."
git push origin main

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   ✅ ДЕПЛОЙ ЗАВЕРШЁН!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "⏰ Timeweb автоматически обновит сайт через 3-5 минут"
echo ""
echo "🌐 Проверьте страницы:"
echo "   • https://app.balt-set.ru/home.html"
echo "   • https://app.balt-set.ru/services.html"
echo ""
echo "📊 Что создано:"
echo "   ✓ home.html - Главная страница"
echo "   ✓ services.html - 6 услуг с калькуляторами"
echo "   ✓ 4 файла документации"
echo ""
echo "💰 MVP готов зарабатывать деньги! 🚀"
echo ""
