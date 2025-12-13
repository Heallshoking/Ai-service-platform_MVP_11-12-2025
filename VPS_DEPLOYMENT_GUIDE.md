# 🖥️ VPS Setup Guide - Telegram Bots Production

## 📋 **Информация о сервере:**

### **Доступы:**
- **IP:** `176.98.178.109`
- **IPv6:** `2a03:6f00:a::1:b6f`
- **SSH:** `ssh root@176.98.178.109`
- **Пароль:** `pneDRE2K?Tz1k-`
- **Закрытые порты:** 389, 465, 3389, 587, 53413, 2525, 25

---

## 🎯 **Архитектура (рекомендуемая):**

```
┌─────────────────────────────────────────────┐
│ Timeweb App Platform (app.balt-set.ru)     │
│ ✅ FastAPI Backend                          │
│ ✅ Frontend (HTML/CSS/JS)                   │
│ ✅ API Endpoints                            │
│ ✅ Автодеплой из GitHub                     │
└─────────────────────────────────────────────┘
                    ▲
                    │ HTTPS API Calls
                    │
┌─────────────────────────────────────────────┐
│ VPS Server (176.98.178.109)                │
│ ✅ Telegram Client Bot (24/7)              │
│ ✅ Telegram Master Bot (24/7)              │
│ ✅ Systemd автозапуск                       │
│ ✅ Независимая работа                       │
└─────────────────────────────────────────────┘
```

---

## 🚀 **Автоматическая установка (рекомендуется):**

### **Шаг 1: Подключись к серверу**
```bash
ssh root@176.98.178.109
# Пароль: pneDRE2K?Tz1k-
```

### **Шаг 2: Скачай и запусти скрипт установки**
```bash
# Скачать скрипт с GitHub
curl -o setup_vps.sh https://raw.githubusercontent.com/Heallshoking/balt-set.ru/main/setup_vps.sh

# Сделать исполняемым
chmod +x setup_vps.sh

# Запустить установку
./setup_vps.sh
```

### **Что делает скрипт:**
1. ✅ Обновляет систему
2. ✅ Устанавливает Python 3.11
3. ✅ Создаёт пользователя `botuser` (безопасность)
4. ✅ Клонирует проект из GitHub
5. ✅ Устанавливает зависимости
6. ✅ Создаёт `.env` файл с токенами
7. ✅ Настраивает systemd сервисы
8. ✅ Запускает ботов

**Время установки: ~5 минут**

---

## 🔧 **Ручная установка (если нужен контроль):**

### **1. Подготовка сервера**
```bash
# Обновление
apt update && apt upgrade -y

# Установка зависимостей
apt install -y python3 python3-pip python3-venv git curl
```

### **2. Создание пользователя**
```bash
# Безопасность: отдельный пользователь для ботов
useradd -m -s /bin/bash botuser
```

### **3. Клонирование проекта**
```bash
mkdir -p /opt/ai-service-bots
cd /opt/ai-service-bots
git clone https://github.com/Heallshoking/balt-set.ru.git .
chown -R botuser:botuser /opt/ai-service-bots
```

### **4. Виртуальное окружение**
```bash
sudo -u botuser python3 -m venv venv
sudo -u botuser venv/bin/pip install -r requirements.txt
```

### **5. Создание .env файла**
```bash
cat > /opt/ai-service-bots/.env << 'EOF'
ENVIRONMENT=production
DEBUG=false
API_URL=https://app.balt-set.ru

TELEGRAM_CLIENT_BOT_TOKEN=8546494378:AAEXpAgazUGMSXi282M56uhnLBD7fwQ3UzU
TELEGRAM_MASTER_BOT_TOKEN=8558486884:AAFEAnfaAKlQtoQ0Qs9vAuJ9p0Pa-XLMsBg

PLATFORM_COMMISSION_PERCENT=25
SECRET_KEY=ai_service_platform_secret_production_2024
EOF

chmod 600 /opt/ai-service-bots/.env
```

### **6. Настройка systemd сервисов**

**Создай файлы сервисов:**
```bash
# Бот клиентов
nano /etc/systemd/system/telegram-client-bot.service
```

Вставь:
```ini
[Unit]
Description=AI Service Platform - Telegram Client Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/ai-service-bots
Environment="PATH=/opt/ai-service-bots/venv/bin:/usr/bin:/bin"
ExecStart=/opt/ai-service-bots/venv/bin/python telegram_client_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-client-bot.log
StandardError=append:/var/log/telegram-client-bot.error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Бот мастеров
nano /etc/systemd/system/telegram-master-bot.service
```

Вставь:
```ini
[Unit]
Description=AI Service Platform - Telegram Master Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/ai-service-bots
Environment="PATH=/opt/ai-service-bots/venv/bin:/usr/bin:/bin"
ExecStart=/opt/ai-service-bots/venv/bin/python telegram_master_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-master-bot.log
StandardError=append:/var/log/telegram-master-bot.error.log

[Install]
WantedBy=multi-user.target
```

### **7. Запуск сервисов**
```bash
# Перезагрузка systemd
systemctl daemon-reload

# Включение автозапуска
systemctl enable telegram-client-bot
systemctl enable telegram-master-bot

# Запуск
systemctl start telegram-client-bot
systemctl start telegram-master-bot

# Проверка статуса
systemctl status telegram-client-bot
systemctl status telegram-master-bot
```

---

## 📊 **Управление ботами на сервере:**

### **Проверка статуса:**
```bash
systemctl status telegram-client-bot
systemctl status telegram-master-bot
```

### **Просмотр логов:**
```bash
# Режим реального времени
tail -f /var/log/telegram-client-bot.log
tail -f /var/log/telegram-master-bot.log

# Последние 50 строк
tail -50 /var/log/telegram-client-bot.log
tail -50 /var/log/telegram-master-bot.log

# Поиск ошибок
grep ERROR /var/log/telegram-client-bot.log
grep ERROR /var/log/telegram-master-bot.log
```

### **Перезапуск ботов:**
```bash
# Оба бота
systemctl restart telegram-client-bot telegram-master-bot

# Отдельно
systemctl restart telegram-client-bot
systemctl restart telegram-master-bot
```

### **Остановка ботов:**
```bash
systemctl stop telegram-client-bot telegram-master-bot
```

### **Обновление кода:**
```bash
# Подключись к серверу
ssh root@176.98.178.109

# Перейди в директорию
cd /opt/ai-service-bots

# Обнови код из GitHub
sudo -u botuser git pull origin main

# Перезапусти ботов
systemctl restart telegram-client-bot telegram-master-bot

# Проверь логи
tail -f /var/log/telegram-client-bot.log
```

---

## 🔄 **Обновление кода через CI/CD (автоматически):**

### **GitHub Actions Workflow** (опционально):

Создай файл `.github/workflows/deploy-bots.yml`:

```yaml
name: Deploy Telegram Bots to VPS

on:
  push:
    branches: [main]
    paths:
      - 'telegram_client_bot.py'
      - 'telegram_master_bot.py'
      - 'ai_assistant.py'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: 176.98.178.109
          username: root
          password: ${{ secrets.VPS_PASSWORD }}
          script: |
            cd /opt/ai-service-bots
            sudo -u botuser git pull origin main
            systemctl restart telegram-client-bot telegram-master-bot
```

---

## ⚠️ **Типичные проблемы:**

### **1. "ModuleNotFoundError: No module named 'telegram'"**
**Решение:**
```bash
cd /opt/ai-service-bots
sudo -u botuser venv/bin/pip install -r requirements.txt
systemctl restart telegram-client-bot telegram-master-bot
```

### **2. "Conflict: terminated by other getUpdates request"**
**Решение:** Остановить локальные боты!
```bash
# На локальной машине
./stop_bots.sh

# Или убить процессы
pkill -f telegram_client_bot
pkill -f telegram_master_bot
```

### **3. Боты не запускаются**
**Проверь логи:**
```bash
journalctl -u telegram-client-bot -n 50
journalctl -u telegram-master-bot -n 50
```

---

## 📈 **Мониторинг (рекомендуется):**

### **Создай скрипт проверки:**
```bash
nano /opt/ai-service-bots/check_bots.sh
```

Вставь:
```bash
#!/bin/bash
if ! systemctl is-active --quiet telegram-client-bot; then
    echo "❌ Client bot is down! Restarting..."
    systemctl restart telegram-client-bot
fi

if ! systemctl is-active --quiet telegram-master-bot; then
    echo "❌ Master bot is down! Restarting..."
    systemctl restart telegram-master-bot
fi
```

Добавь в cron (каждые 5 минут):
```bash
chmod +x /opt/ai-service-bots/check_bots.sh
crontab -e

# Добавь строку:
*/5 * * * * /opt/ai-service-bots/check_bots.sh
```

---

## ✅ **Чеклист после установки:**

- [ ] Боты запущены: `systemctl status telegram-client-bot telegram-master-bot`
- [ ] Логи без ошибок: `tail /var/log/telegram-client-bot.log`
- [ ] Бот клиентов отвечает: открой @ai_service_client_bot → /start
- [ ] Бот мастеров отвечает: открой @ai_service_master_bot → /start
- [ ] Автозапуск включён: `systemctl is-enabled telegram-client-bot`
- [ ] Локальные боты остановлены: `./stop_bots.sh`

---

## 🎯 **Итоговая рекомендация:**

### **Используй гибридную архитектуру:**

1. **App Platform (app.balt-set.ru):**
   - ✅ FastAPI Backend
   - ✅ Frontend файлы
   - ✅ API endpoints
   - ✅ Автодеплой из GitHub

2. **VPS (176.98.178.109):**
   - ✅ Telegram боты 24/7
   - ✅ Независимая работа
   - ✅ Полный контроль

**Зачем нужен VPS:**
- Боты работают 24/7 без ограничений
- Быстрый перезапуск (секунды)
- Полный доступ к логам
- Не платишь за каждое приложение отдельно

**Frontend в GitHub:**
- ✅ Да! Храни в GitHub
- ✅ App Platform автоматически деплоит из GitHub
- ✅ Не нужно копировать файлы вручную

---

## 🚀 **Готов к запуску!**

**Подключись к серверу и запусти:**
```bash
ssh root@176.98.178.109
curl -o setup_vps.sh https://raw.githubusercontent.com/Heallshoking/balt-set.ru/main/setup_vps.sh
chmod +x setup_vps.sh
./setup_vps.sh
```

**Через 5 минут боты будут работать 24/7!** 🎉
