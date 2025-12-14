#!/bin/bash

echo "🚀 Деплой навигации и редиректов..."

cd /Users/user/Documents/Projects/Github/balt-set.ru

git add README_NAVIGATION.md static/products.html

git commit -m "🔧 Настройка навигации: добавлен редирект /products → /catalog.html"

git push origin main

echo "✅ Деплой завершён! Сайт обновится через 3-5 минут"
