# 🚀 Деплой Telegram бота на VPS - Простая инструкция

## ✅ Всё готово к деплою!

### Бот настроен:
- ✅ Токен: `8594337620:AAEV59Hi-38xUjTKd70hRTkvcR6miWWWxls`
- ✅ Chat ID: `-1002468635742`  
- ✅ Username: `@Baltset39_bot`
- ✅ Калькулятор интегрирован

---

## 📋 Быстрый деплой (5 минут):

### Вариант 1: Автоматический (рекомендуется)

```bash
cd /Users/user/Documents/Projects/Github/balt-set.ru
./deploy_bot_simple.sh
```

**Введите пароль VPS:** `pneDRE2K?Tz1k-`

### Вариант 2: Ручной (если автоматический не сработал)

#### Шаг 1: Подключитесь к VPS
```bash
ssh root@176.98.178.109
# Пароль: pneDRE2K?Tz1k-
```

#### Шаг 2: Создайте директорию
```bash
mkdir -p /root/baltset_bot
cd /root/baltset_bot
```

#### Шаг 3: Создайте файл бота
```bash
cat > telegram_lead_bot.py << 'EOF'
#!/usr/bin/env python3
"""
Telegram бот для сбора лидов с калькулятора
Автоматически обрабатывает контакты клиентов
"""

import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Конфигурация
TELEGRAM_BOT_TOKEN = '8594337620:AAEV59Hi-38xUjTKd70hRTkvcR6miWWWxls'
ADMIN_CHAT_ID = '-1002468635742'

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    if context.args and context.args[0] == 'estimate':
        button = KeyboardButton("📱 Отправить номер телефона", request_contact=True)
        keyboard = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
        
        update.message.reply_text(
            f"👋 Здравствуйте, {user.first_name}!\n\n"
            "🎯 Вы запросили смету на электромонтажные работы.\n\n"
            "Для получения точного расчёта и консультации электрика "
            "поделитесь своим номером телефона — это займёт всего 1 секунду!",
            reply_markup=keyboard
        )
    else:
        update.message.reply_text(
            f"👋 Привет, {user.first_name}!\n\n"
            "Я бот компании БАЛТСЕТЬ — помогаю с расчётом стоимости электромонтажных работ.\n\n"
            "📊 Используйте наш калькулятор:\n"
            "https://app.balt-set.ru/calculator-integrated\n\n"
            "Или задайте вопрос напрямую — я передам его нашим специалистам!"
        )

def contact_received(update: Update, context: CallbackContext) -> None:
    """Обработчик получения контакта"""
    contact = update.message.contact
    user = update.effective_user
    phone = contact.phone_number
    
    update.message.reply_text(
        f"✅ Отлично! Ваш номер {phone} получен.\n\n"
        "📋 Детальная смета будет отправлена в течение 60 секунд!\n\n"
        "💬 Можете сразу написать дополнительные пожелания или вопросы — "
        "наш специалист учтёт их при подготовке сметы.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    admin_message = (
        f"📞 <b>НОВЫЙ ЛИД ИЗ TELEGRAM!</b>\n\n"
        f"👤 Имя: {user.first_name} {user.last_name or ''}\n"
        f"📱 Телефон: <code>{phone}</code>\n"
        f"🆔 Telegram ID: <code>{user.id}</code>\n"
        f"👤 Username: @{user.username or 'не указан'}\n"
        f"📊 Источник: Калькулятор → Telegram бот\n"
        f"🕐 Время: {update.message.date.strftime('%d.%m.%Y %H:%M:%S')}"
    )
    
    try:
        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

def message_received(update: Update, context: CallbackContext) -> None:
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    text = update.message.text
    
    update.message.reply_text(
        "✅ Ваш вопрос получен!\n\n"
        "Наш специалист ответит в течение 5 минут.\n\n"
        "📊 Пока ждёте, можете воспользоваться калькулятором:\n"
        "https://app.balt-set.ru/calculator-integrated"
    )
    
    admin_message = (
        f"💬 <b>НОВЫЙ ВОПРОС</b>\n\n"
        f"👤 От: {user.first_name} {user.last_name or ''}\n"
        f"🆔 Username: @{user.username or 'не указан'}\n\n"
        f"<b>Вопрос:</b>\n{text}\n\n"
        f"🕐 {update.message.date.strftime('%d.%m.%Y %H:%M:%S')}"
    )
    
    try:
        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode='HTML')
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "📞 Контакты:\n"
        "Телефон: +7 (4012) 52-07-25\n"
        "Сайт: https://app.balt-set.ru"
    )
    
    update.message.reply_text(help_text, parse_mode='HTML')

def main():
    """Запуск бота"""
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.contact, contact_received))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_received))
    
    print("🤖 Telegram бот запущен!")
    print(f"📊 Admin Chat ID: {ADMIN_CHAT_ID}")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
EOF
```

#### Шаг 4: Установите зависимости
```bash
apt-get update
apt-get install -y python3 python3-pip
pip3 install python-telegram-bot==13.15
```

#### Шаг 5: Создайте systemd сервис
```bash
cat > /etc/systemd/system/baltset-bot.service << 'EOF'
[Unit]
Description=BALTSET Telegram Lead Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/baltset_bot
ExecStart=/usr/bin/python3 /root/baltset_bot/telegram_lead_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Шаг 6: Запустите бота
```bash
systemctl daemon-reload
systemctl start baltset-bot
systemctl enable baltset-bot
systemctl status baltset-bot
```

---

## ✅ Проверка работы

### Проверьте статус:
```bash
ssh root@176.98.178.109 'systemctl status baltset-bot'
```

### Посмотрите логи:
```bash
ssh root@176.98.178.109 'journalctl -u baltset-bot -f'
```

### Протестируйте бота:
Откройте: **https://t.me/Baltset39_bot**

Напишите `/start` - должен ответить!

---

## 🔧 Управление ботом

### Перезапуск:
```bash
ssh root@176.98.178.109 'systemctl restart baltset-bot'
```

### Остановка:
```bash
ssh root@176.98.178.109 'systemctl stop baltset-bot'
```

### Просмотр логов:
```bash
ssh root@176.98.178.109 'journalctl -u baltset-bot -n 100'
```

---

## 📱 Тестирование полной воронки:

1. ✅ Откройте https://app.balt-set.ru/calculator-integrated
2. ✅ Выберите тип помещения
3. ✅ Нажмите "Рассчитать стоимость"
4. ✅ В модалке нажмите "Использовать Telegram"
5. ✅ Откроется бот @Baltset39_bot
6. ✅ Нажмите "Отправить номер телефона"
7. ✅ Вы получите уведомление в чат `-1002468635742`!

---

## 🎊 Готово!

**Бот работает 24/7 и автоматически:**
- ✅ Принимает контакты клиентов
- ✅ Отправляет уведомления в ваш Telegram чат
- ✅ Пересылает вопросы клиентов
- ✅ Перезапускается при падении
- ✅ Запускается после перезагрузки VPS

**VPS:** 176.98.178.109  
**Бот:** @Baltset39_bot  
**Чат для уведомлений:** -1002468635742

---

**Автор:** Qoder AI  
**Дата:** 15 декабря 2025  
**Статус:** ✅ Готово к запуску
