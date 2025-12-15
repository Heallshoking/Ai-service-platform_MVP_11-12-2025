# 🚀 ПРОДАКШН-ДЕПЛОЙ БОТОВ

## ✅ Что настроено:

### 🤖 Telegram Боты:
1. **Бот для клиентов:** `@ai_service_client_bot`
   - Token: `8546494378:AAEXpAgazUGMSXi282M56uhnLBD7fwQ3UzU`

2. **Бот для мастеров:** `@ai_service_master_bot`
   - Token: `8558486884:AAFEAnfaAKlQtoQ0Qs9vAuJ9p0Pa-XLMsBg`

3. **Общий бот (лиды):** `@Baltset39_bot`
   - Token: `8594337620:AAEV59Hi-38xUjTKd70hRTkvcR6miWWWxls`

### 💰 Комиссия:
- **30%** (не афишируем публично!)
- Клиенту показываем только итоговую стоимость
- Мастеру показываем "после вычета комиссии сервиса"

---

## 🚀 ДЕПЛОЙ НА VPS (Вариант 1 - Автоматический)

### Выполните на вашем Mac:
```bash
cd /Users/user/Documents/Projects/Github/balt-set.ru
chmod +x deploy_production_bots.sh
./deploy_production_bots.sh
```

Скрипт автоматически:
- ✅ Скопирует боты на VPS (176.98.178.109)
- ✅ Установит зависимости
- ✅ Создаст systemd сервисы
- ✅ Запустит оба бота 24/7

---

## 🚀 ДЕПЛОЙ НА VPS (Вариант 2 - Ручной)

### Шаг 1: Скопируйте файлы на VPS
```bash
cd /Users/user/Documents/Projects/Github/balt-set.ru

# Копируем боты
scp telegram_client_bot.py root@176.98.178.109:/root/
scp telegram_master_bot.py root@176.98.178.109:/root/
scp .env root@176.98.178.109:/root/
scp ai_assistant.py root@176.98.178.109:/root/

# Пароль: pneDRE2K?Tz1k-
```

### Шаг 2: Подключитесь к VPS
```bash
ssh root@176.98.178.109
# Пароль: pneDRE2K?Tz1k-
```

### Шаг 3: Настройте окружение
```bash
# Создайте директорию
mkdir -p /root/ai_service_bots
cd /root/ai_service_bots

# Переместите файлы
mv /root/telegram_client_bot.py .
mv /root/telegram_master_bot.py .
mv /root/.env .
mv /root/ai_assistant.py . 2>/dev/null || true

# Установите зависимости
pip3 install python-telegram-bot httpx python-dotenv openai
```

### Шаг 4: Создайте systemd сервисы

#### Сервис для бота клиента:
```bash
cat > /etc/systemd/system/ai-client-bot.service << 'EOF'
[Unit]
Description=AI Service Platform - Client Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai_service_bots
ExecStart=/usr/bin/python3 /root/ai_service_bots/telegram_client_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Сервис для бота мастера:
```bash
cat > /etc/systemd/system/ai-master-bot.service << 'EOF'
[Unit]
Description=AI Service Platform - Master Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ai_service_bots
ExecStart=/usr/bin/python3 /root/ai_service_bots/telegram_master_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Шаг 5: Запустите боты
```bash
# Перезагрузите systemd
systemctl daemon-reload

# Остановите старые процессы
pkill -9 -f telegram_client_bot.py
pkill -9 -f telegram_master_bot.py

# Запустите новые сервисы
systemctl start ai-client-bot
systemctl start ai-master-bot

# Включите автозапуск
systemctl enable ai-client-bot
systemctl enable ai-master-bot
```

### Шаг 6: Проверьте статус
```bash
# Проверка статуса
systemctl status ai-client-bot
systemctl status ai-master-bot

# Логи в реальном времени
journalctl -u ai-client-bot -f
journalctl -u ai-master-bot -f
```

---

## ✅ ПРОВЕРКА РАБОТЫ

### 1. Проверьте бота клиента:
```
1. Откройте Telegram
2. Найдите: @ai_service_client_bot
3. Отправьте: /start
4. Должен ответить с приветствием
```

### 2. Проверьте бота мастера:
```
1. Откройте Telegram (другой аккаунт!)
2. Найдите: @ai_service_master_bot
3. Отправьте: /start
4. Должен предложить регистрацию
```

---

## 🔧 УПРАВЛЕНИЕ БОТАМИ

### Перезапуск:
```bash
ssh root@176.98.178.109
systemctl restart ai-client-bot
systemctl restart ai-master-bot
```

### Просмотр логов:
```bash
ssh root@176.98.178.109
journalctl -u ai-client-bot -n 50
journalctl -u ai-master-bot -n 50
```

### Остановка:
```bash
ssh root@176.98.178.109
systemctl stop ai-client-bot
systemctl stop ai-master-bot
```

---

## 📊 КОМИССИЯ 30%

### Как работает:
```
Пример: Работа стоит 10,000 ₽

Мастер видит:
💰 Стоимость работы: 10,000 ₽
💳 После вычета комиссии сервиса: 7,000 ₽

Клиент видит:
💰 К оплате: 10,000 ₽

Платформа получает:
💰 Комиссия: 3,000 ₽ (30%)
```

### ⚠️ ВАЖНО:
- НЕ афишируем процент комиссии публично
- Говорим "комиссия сервиса" без процентов
- В договорах указываем 30%

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

После успешного деплоя:

1. ✅ **Протестируйте полный цикл**
   - Создайте заявку через @ai_service_client_bot
   - Примите через @ai_service_master_bot
   - Проверьте расчёт комиссии 30%

2. 🎨 **Настройте описания ботов**
   - Откройте @BotFather
   - `/setdescription` для каждого бота
   - Добавьте красивые аватары

3. 👥 **Пригласите первых пользователей**
   - 5-10 мастеров для бета-теста
   - Дайте им тестовые заказы

4. 📢 **Запустите продвижение**
   - Реклама в соцсетях
   - SEO оптимизация
   - Контекстная реклама

---

## 🎉 Готово!

Оба бота работают на VPS 24/7 в продакшн-режиме!

**Тестируйте и запускайте!** 🚀
