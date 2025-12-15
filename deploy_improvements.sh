#!/bin/bash
# Автоматический деплой улучшений BALT-SET.RU

echo "🚀 ДЕПЛОЙ УЛУЧШЕНИЙ BALT-SET.RU"
echo "================================"
echo ""

# Переходим в папку проекта
cd /Users/user/Documents/Projects/Github/balt-set.ru/electric-service-automation-main

# Проверяем наличие node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 Устанавливаем зависимости..."
    npm install
fi

echo "🔨 Собираем проект..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Сборка успешна!"
    echo ""
    echo "📤 Копируем на VPS..."
    
    # Копируем файлы
    scp -r dist/* root@176.98.178.109:/var/www/app.balt-set.ru/
    
    if [ $? -eq 0 ]; then
        echo "✅ Файлы скопированы!"
        echo ""
        echo "🔐 Устанавливаем права доступа..."
        ssh root@176.98.178.109 "chmod -R 755 /var/www/app.balt-set.ru/"
        
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ ДЕПЛОЙ ЗАВЕРШЕН!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "🌐 Проверьте сайт: https://app.balt-set.ru/"
        echo ""
        echo "📋 Что изменилось:"
        echo "  ✓ 'Наши услуги' → 'Услуги электрика'"
        echo "  ✓ Добавлена система скидок за объем (3/5/6/11/21+ шт.)"
        echo "  ✓ Улучшена кнопка 'Редактировать' в корзине"
        echo "  ✓ Добавлена кнопка '← К услугам' для возврата"
        echo ""
        echo "🧪 Тестирование:"
        echo "  1. Откройте https://app.balt-set.ru/"
        echo "  2. Найдите 'Услуги электрика' на главной"
        echo "  3. Добавьте 3+ розетки - появится скидка 5%"
        echo "  4. В корзине нажмите 'Редактировать' - увидите кнопку '← К услугам'"
        echo ""
    else
        echo "❌ Ошибка копирования файлов"
        echo "Попробуйте вручную:"
        echo "scp -r dist/* root@176.98.178.109:/var/www/app.balt-set.ru/"
    fi
else
    echo "❌ Ошибка сборки проекта"
    echo "Проверьте логи выше для деталей"
fi
