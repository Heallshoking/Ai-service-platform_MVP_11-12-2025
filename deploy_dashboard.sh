#!/bin/bash
# Деплой Dashboard на веб-сервер

echo "📊 Деплой Dashboard на сайт..."

# Копируем dashboard.html на сервер
scp static/dashboard.html root@176.98.178.109:/var/www/bag4moms/data/www/bag4moms.balt-set.ru/

if [ $? -eq 0 ]; then
    echo "✅ Dashboard успешно загружен!"
    echo ""
    echo "🌐 Доступен по адресу:"
    echo "   https://bag4moms.balt-set.ru/dashboard.html"
    echo ""
    echo "⚠️  НЕ ЗАБУДЬТЕ:"
    echo "1. Вставить SPREADSHEET_ID в dashboard.html (строка 410)"
    echo "2. Настроить Google Sheets по инструкции БЫСТРЫЙ_СТАРТ_GOOGLE_SHEETS.md"
else
    echo "❌ Ошибка загрузки"
fi
