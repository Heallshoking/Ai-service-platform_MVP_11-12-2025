# 🤖 Telegram Боты - Быстрый Старт

## ✅ **СТАТУС: БОТЫ ЗАПУЩЕНЫ И РАБОТАЮТ!**

### 📱 **Ссылки на ботов:**
- **Для клиентов:** https://t.me/ai_service_client_bot
- **Для мастеров:** https://t.me/ai_service_master_bot

---

## 🚀 **Быстрый запуск (локально):**

### **Запустить ботов:**
```bash
./start_bots.sh
```

### **Остановить ботов:**
```bash
./stop_bots.sh
```

### **Просмотр логов:**
```bash
# Бот клиентов
tail -f logs/client_bot.log

# Бот мастеров
tail -f logs/master_bot.log
```

---

## 📋 **Первое тестирование:**

### **Шаг 1: Регистрация мастера**
1. Открой https://t.me/ai_service_master_bot
2. Напиши `/start`
3. Нажми "✅ Зарегистрироваться"
4. Заполни данные:
   - **Имя:** Иван Тестовый
   - **Телефон:** +79001234567
   - **Город:** Калининград
   - **Специализации:** Электрика (напиши "Электрика")

### **Шаг 2: Создание тестового заказа**
1. Открой https://t.me/ai_service_client_bot
2. Напиши `/start`
3. Создай заказ:
   - **Имя:** Тест
   - **Телефон:** +79009876543
   - **Категория:** ⚡ Электрика
   - **Проблема:** Не работает розетка в гостиной
   - **Адрес:** ул. Ленина, д. 1

### **Шаг 3: Проверка работы**
1. Вернись в бота мастера
2. Нажми "🆕 Новые заказы"
3. **Должен появиться** тестовый заказ!
4. Прими заказ → Завершить → Проверь комиссию

---

## 🔧 **Настройка для продакшена:**

### **На сервере Timeweb:**

#### **Вариант 1: Через systemd (рекомендуется)**

1. Создай файлы сервисов:
```bash
# /etc/systemd/system/telegram-client-bot.service
[Unit]
Description=AI Service Platform - Client Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/balt-set.ru
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 telegram_client_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/systemd/system/telegram-master-bot.service
[Unit]
Description=AI Service Platform - Master Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/balt-set.ru
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 telegram_master_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Запусти сервисы:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-client-bot
sudo systemctl enable telegram-master-bot
sudo systemctl start telegram-client-bot
sudo systemctl start telegram-master-bot
```

3. Проверка:
```bash
sudo systemctl status telegram-client-bot
sudo systemctl status telegram-master-bot
```

#### **Вариант 2: Через screen (простой способ)**

```bash
# Клиентский бот
screen -S client-bot
cd /path/to/balt-set.ru
python3 telegram_client_bot.py
# Нажми Ctrl+A, затем D (detach)

# Бот мастеров
screen -S master-bot
cd /path/to/balt-set.ru
python3 telegram_master_bot.py
# Нажми Ctrl+A, затем D

# Вернуться к сессии:
screen -r client-bot
screen -r master-bot

# Список сессий:
screen -ls
```

---

## 📊 **Логи и мониторинг:**

### **Проверка работы ботов:**
```bash
# Процессы
ps aux | grep telegram

# Логи
tail -f logs/client_bot.log
tail -f logs/master_bot.log

# Поиск ошибок
grep ERROR logs/client_bot.log
grep ERROR logs/master_bot.log
```

---

## ⚠️ **Типичные проблемы:**

### **1. "Conflict: terminated by other getUpdates request"**
**Причина:** Запущено несколько экземпляров бота
**Решение:**
```bash
./stop_bots.sh
./start_bots.sh
```

### **2. "TELEGRAM_CLIENT_BOT_TOKEN not found"**
**Причина:** .env файл не настроен
**Решение:**
```bash
cp .env.example .env
# Заполни токены в .env
```

### **3. "Module 'telegram' not found"**
**Причина:** Не установлены зависимости
**Решение:**
```bash
pip install -r requirements.txt
```

---

## 🎯 **Следующие шаги:**

### **1. Добавь настоящих мастеров** (минимум 3)
- Зарегистрируй их через бота мастера
- Или добавь через API:
```bash
curl -X POST https://app.balt-set.ru/api/v1/masters \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Иван Электриков",
    "phone": "+79001234567",
    "specializations": "electrical",
    "city": "Калининград"
  }'
```

### **2. Протестируй весь флоу**
- Клиент создаёт заказ
- Мастер получает уведомление
- Мастер принимает заказ
- Мастер завершает работу
- Проверь комиссию (25% платформе, 75% мастеру)

### **3. Запусти ботов на сервере 24/7**
- Используй systemd или screen
- Настрой автозапуск при перезагрузке

### **4. Запусти маркетинг**
- Размести ссылки на ботов в VK
- Добавь в объявления на Авито
- Создай QR-коды для визиток

---

## 🔗 **Полезные ссылки:**

- **Документация:** MVP_LAUNCH_CHECKLIST.md
- **SEO план:** SEO_ROADMAP.md
- **GitHub:** https://github.com/Heallshoking/balt-set.ru
- **Сайт:** https://app.balt-set.ru

---

## ✅ **MVP ГОТОВ К ЗАПУСКУ!**

**Telegram боты работают локально.**
**Для продакшена — настрой systemd или screen на сервере.**

**Удачи с первыми заказами! 🚀**
