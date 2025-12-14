#!/usr/bin/env python3
"""
Telegram бот для сбора лидов с калькулятора
Автоматически обрабатывает контакты клиентов
"""

import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Конфигурация (можно вынести в .env)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '6789012345:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '-1001234567890')

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Проверяем, пришел ли пользователь из калькулятора
    if context.args and context.args[0] == 'estimate':
        # Показываем кнопку для отправки контакта
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
        # Обычный старт
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
    
    # Отправляем подтверждение клиенту
    update.message.reply_text(
        f"✅ Отлично! Ваш номер {phone} получен.\n\n"
        "📋 Детальная смета будет отправлена в течение 60 секунд!\n\n"
        "💬 Можете сразу написать дополнительные пожелания или вопросы — "
        "наш специалист учтёт их при подготовке сметы.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Отправляем уведомление админу
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
        context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

def message_received(update: Update, context: CallbackContext) -> None:
    """Обработчик текстовых сообщений (вопросы клиентов)"""
    user = update.effective_user
    text = update.message.text
    
    # Отправляем подтверждение клиенту
    update.message.reply_text(
        "✅ Ваш вопрос получен!\n\n"
        "Наш специалист ответит в течение 5 минут.\n\n"
        "📊 Пока ждёте, можете воспользоваться калькулятором:\n"
        "https://app.balt-set.ru/calculator-integrated"
    )
    
    # Пересылаем вопрос админу
    admin_message = (
        f"💬 <b>НОВЫЙ ВОПРОС</b>\n\n"
        f"👤 От: {user.first_name} {user.last_name or ''}\n"
        f"🆔 Username: @{user.username or 'не указан'}\n\n"
        f"<b>Вопрос:</b>\n{text}\n\n"
        f"🕐 {update.message.date.strftime('%d.%m.%Y %H:%M:%S')}"
    )
    
    try:
        context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

def help_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /help"""
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "💡 <b>Как пользоваться:</b>\n"
        "1️⃣ Откройте калькулятор на сайте\n"
        "2️⃣ Выберите нужные услуги\n"
        "3️⃣ Нажмите 'Использовать Telegram'\n"
        "4️⃣ Отправьте номер телефона\n"
        "5️⃣ Получите смету за 60 секунд!\n\n"
        "📞 Контакты:\n"
        "Телефон: +7 (4012) 52-07-25\n"
        "Сайт: https://app.balt-set.ru"
    )
    
    update.message.reply_text(help_text, parse_mode='HTML')

def main():
    """Запуск бота"""
    # Создаём updater и dispatcher
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    # Регистрируем обработчики
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.contact, contact_received))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_received))
    
    # Запускаем бота
    print("🤖 Telegram бот запущен!")
    print(f"📊 Admin Chat ID: {ADMIN_CHAT_ID}")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
