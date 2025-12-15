"""
Telegram бот для клиентов - BALT-SET.RU
Улучшенный UX по принципам Donald Norman
- Прогресс-бар
- Контроль пользователя
- Удобное редактирование
- Милые уведомления
"""
import os
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Google Sheets Integration
try:
    from google_sheets_integration import save_order_from_bot
    GOOGLE_SHEETS_ENABLED = True
except:
    print("⚠️ Google Sheets не подключен")
    GOOGLE_SHEETS_ENABLED = False

# Telegram Folders Integration
try:
    from telegram_folders_integration import get_client_folder_invite
    FOLDERS_ENABLED = True
except:
    print("⚠️ Telegram Folders не подключены")
    FOLDERS_ENABLED = False

# Master Notification Integration
try:
    from master_notification import notify_masters_about_new_order
    MASTER_NOTIFICATION_ENABLED = True
except:
    print("⚠️ Master Notification не подключен")
    MASTER_NOTIFICATION_ENABLED = False

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_CLIENT_BOT_TOKEN", "")
TELEGRAM_MASTER_BOT_TOKEN = os.getenv("TELEGRAM_MASTER_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "https://heallshoking-ai-service-platform-mvp-11-12-2025-2f94.twc1.net")

# Состояния диалога
START, PROBLEM, ADDRESS, NAME, PHONE, CONFIRM, EDIT = range(7)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_progress_bar(step: int, total: int = 5) -> str:
    """Прогресс-бар для визуальной обратной связи (Norman UX)"""
    filled = "🟢" * step
    empty = "⚪" * (total - step)
    percentage = int((step / total) * 100)
    return f"Шаг {step} из {total}\n{filled}{empty} {percentage}%"

def get_back_to_menu_button():
    """Кнопка возврата в меню (Norman UX: всегда доступный выход)"""
    keyboard = [["🏠 Вернуться в меню"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога - выбор направления"""
    # Очищаем данные
    context.user_data.clear()
    
    # Приветствие с картинкой и милым тоном
    try:
        await update.message.reply_photo(
            photo="https://bag4moms.balt-set.ru/tel.jpg",
            caption=(
                "👋 Привет! Я ваш помощник в поиске мастера 😊\n\n"
                "🔌 Помогу найти проверенного специалиста в Калининграде за 2 минуты!\n\n"
                "✨ Что вас ждёт:\n"
                "• Бесплатная консультация\n"
                "• Быстрый подбор мастера\n"
                "• Прозрачные цены\n\n"
                "Начнём? 🚀"
            )
        )
    except:
        await update.message.reply_text(
            "👋 Привет! Я ваш помощник в поиске мастера 😊\n\n"
            "🔌 Помогу найти проверенного специалиста в Калининграде за 2 минуты!\n\n"
            "✨ Что вас ждёт:\n"
            "• Бесплатная консультация\n"
            "• Быстрый подбор мастера\n"
            "• Прозрачные цены\n\n"
            "Начнём? 🚀"
        )
    
    # 2 кнопки выбора направления
    keyboard = [
        ["⚡ Услуги электрика"],
        ["🏠 Инженерные сети"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "🛠️ Выберите направление:",
        reply_markup=reply_markup
    )
    return START

async def handle_start_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора направления"""
    choice = update.message.text
    
    if choice == "⚡ Услуги электрика":
        # Сразу переходим к описанию проблемы (БЕЗ выбора подкатегории!)
        context.user_data['category'] = '⚡ Электрика'
        context.user_data['category_id'] = 'electrical'
        
        # Прогресс-бар + вопрос о проблеме
        await update.message.reply_text(
            f"{get_progress_bar(1)}\n\n"
            "⚡ Услуги электрика\n\n"
            "💬 Расскажите, что случилось? Опишите проблему своими словами.\n\n"
            "💡 Например:\n"
            "• 'Не работает розетка в гостиной'\n"
            "• 'Нужно установить люстру'\n"
            "• 'Выбивает автомат в щитке'\n\n"
            "✍️ Ваш ответ:",
            reply_markup=get_back_to_menu_button()
        )
        return PROBLEM
        
    elif choice == "🏠 Инженерные сети":
        # Переход на канал с кнопкой возврата
        keyboard = [["🏠 Вернуться в меню"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "🏠 Инженерные сети\n\n"
            "🔧 Для услуг по умному дому, отоплению и климату:\n\n"
            "👉 @konigkomfort\n"
            "https://t.me/konigkomfort",
            reply_markup=reply_markup
        )
        return START
    
    return START

async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение описания проблемы с ИНТЕЛЛЕКТУАЛЬНОЙ обработкой"""
    text = update.message.text.strip()
    
    # Проверка на возврат в меню
    if text == "🏠 Вернуться в меню":
        context.user_data.clear()
        return await start(update, context)
    
    # Проверка на вопросы - перенаправляем в ЛС админу
    question_words = ['сколько', 'что', 'как', 'где', 'когда', 'почему', 'можно ли', 'а если', '?']
    is_question = any(word in text.lower() for word in question_words) or text.endswith('?')
    
    if is_question and len(text.split()) < 6:
        # Это вопрос - милое перенаправление
        await update.message.reply_text(
            "💬 Вижу у вас есть вопрос! 😊\n\n"
            "📞 Напишите напрямую администратору:\n"
            "@admin_balt_set\n\n"
            "Он ответит вам быстрее, чем я! 😉\n\n"
            "🔄 Или продолжим оформление заявки?\n"
            "Опишите проблему для мастера:",
            reply_markup=get_back_to_menu_button()
        )
        return PROBLEM
    
    # Проверка минимальной длины (мягкая валидация)
    if len(text) < 10:
        await update.message.reply_text(
            "😊 Опишите чуть подробнее, пожалуйста!\n\n"
            "Это поможет мастеру лучше подготовиться к работе.\n\n"
            "💡 Например: 'Не работает розетка, искрит при включении'",
            reply_markup=get_back_to_menu_button()
        )
        return PROBLEM
    
    context.user_data['problem'] = text
    
    # Переход к адресу
    await update.message.reply_text(
        f"{get_progress_bar(2)}\n\n"
        f"✅ Понял: {text[:60]}{'...' if len(text) > 60 else ''}\n\n"
        "📍 Укажите адрес работ:\n\n"
        "💡 Например: 'Невского 50, кв. 12'\n\n"
        "✍️ Ваш адрес:",
        reply_markup=get_back_to_menu_button()
    )
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение адреса"""
    text = update.message.text.strip()
    
    # Проверка на возврат в меню
    if text == "🏠 Вернуться в меню":
        context.user_data.clear()
        return await start(update, context)
    
    if len(text) < 5:
        await update.message.reply_text(
            "😊 Укажите более точный адрес, пожалуйста!\n\n"
            "💡 Например: 'Невского 50' или 'Ленина 10, кв. 5'",
            reply_markup=get_back_to_menu_button()
        )
        return ADDRESS
    
    context.user_data['address'] = text
    
    # Переход к имени
    await update.message.reply_text(
        f"{get_progress_bar(3)}\n\n"
        f"✅ Адрес: {text}\n\n"
        "👤 Как вас зовут?\n\n"
        "💡 Просто имя, чтобы мастер знал как к вам обращаться\n\n"
        "✍️ Ваше имя:",
        reply_markup=get_back_to_menu_button()
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени"""
    text = update.message.text.strip()
    
    # Проверка на возврат в меню
    if text == "🏠 Вернуться в меню":
        context.user_data.clear()
        return await start(update, context)
    
    # Валидация имени
    if len(text) < 2 or len(text) > 30:
        await update.message.reply_text(
            "😊 Укажите ваше имя (2-30 символов)\n\n"
            "💡 Например: Алексей, Мария, Иван",
            reply_markup=get_back_to_menu_button()
        )
        return NAME
    
    # Проверка на попытку разговора
    if len(text.split()) > 4 or any(word in text.lower() for word in ['сколько', 'что', 'как', 'когда', 'где']):
        await update.message.reply_text(
            "😊 Похоже вы начали задавать вопрос!\n\n"
            "👤 Просто укажите ваше имя одним-двумя словами.\n\n"
            "💡 Например: Алексей, Мария Ивановна",
            reply_markup=get_back_to_menu_button()
        )
        return NAME
    
    context.user_data['name'] = text
    
    # Переход к телефону
    await update.message.reply_text(
        f"{get_progress_bar(4)}\n\n"
        f"✅ Приятно познакомиться, {text}! 😊\n\n"
        "📞 Укажите номер телефона:\n\n"
        "💡 Формат: +79001234567\n\n"
        "✍️ Ваш номер:",
        reply_markup=get_back_to_menu_button()
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение телефона и показ резюме с УДОБНЫМИ КНОПКАМИ"""
    text = update.message.text.strip()
    
    # Проверка на возврат в меню
    if text == "🏠 Вернуться в меню":
        context.user_data.clear()
        return await start(update, context)
    
    # Валидация телефона
    if not text.startswith('+7') or len(text) != 12:
        await update.message.reply_text(
            "😊 Пожалуйста, укажите номер в формате:\n"
            "+79001234567\n\n"
            "✍️ Попробуйте еще раз:",
            reply_markup=get_back_to_menu_button()
        )
        return PHONE
    
    context.user_data['phone'] = text
    
    # Показываем резюме с УДОБНЫМИ КНОПКАМИ (Donald Norman: ясность действий)
    data = context.user_data
    summary = (
        f"{get_progress_bar(5)}\n\n"
        "📋 <b>Проверьте вашу заявку:</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {text}\n"
        f"🛠️ Категория: {data['category']}\n"
        f"📝 Проблема: {data['problem'][:100]}{'...' if len(data['problem']) > 100 else ''}\n"
        f"📍 Адрес: {data['address']}\n\n"
        "✅ Всё верно?"
    )
    
    # INLINE кнопки для подтверждения (Donald Norman: четкие affordances)
    keyboard = [
        [InlineKeyboardButton("✅ Да, всё верно", callback_data="confirm_yes")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="confirm_edit")],
        [InlineKeyboardButton("❌ Отменить заявку", callback_data="confirm_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        summary,
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return CONFIRM

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения заявки"""
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    
    if choice == "confirm_no":
        # Отмена
        await query.edit_message_text(
            "❌ Заявка отменена.\n\n"
            "Для создания новой используйте /start"
        )
        return ConversationHandler.END
    
    elif choice == "confirm_edit":
        # Редактирование - показываем меню выбора поля
        keyboard = [
            [InlineKeyboardButton("📝 Изменить проблему", callback_data="edit_problem")],
            [InlineKeyboardButton("📍 Изменить адрес", callback_data="edit_address")],
            [InlineKeyboardButton("👤 Изменить имя", callback_data="edit_name")],
            [InlineKeyboardButton("📞 Изменить телефон", callback_data="edit_phone")],
            [InlineKeyboardButton("◀️ Назад к заявке", callback_data="edit_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✏️ <b>Что хотите изменить?</b>\n\n"
            "Выберите поле для редактирования:",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return EDIT
    
    elif choice == "confirm_yes":
        # Подтверждение - отправляем заявку
        await query.edit_message_text("⏳ Создаю заявку...")
        
        data = context.user_data
        
        # === GOOGLE SHEETS: Сохраняем заявку ===
        order_id = None
        if GOOGLE_SHEETS_ENABLED:
            try:
                order_id = save_order_from_bot(
                    name=data['name'],
                    phone=data['phone'],
                    category=data['category'],
                    problem=data['problem'],
                    address=data['address'],
                    source="telegram"
                )
                logger.info(f"✅ Заявка #{order_id} сохранена в Google Sheets")
            except Exception as e:
                logger.error(f"⚠️ Ошибка Google Sheets: {e}")
        
        # === УВЕДОМЛЕНИЕ МАСТЕРОВ ===
        await query.edit_message_text("🔍 Ищу подходящих мастеров...")
        
        if MASTER_NOTIFICATION_ENABLED:
            try:
                await notify_masters_about_new_order(
                    order_id=order_id or 0,
                    category=data['category'],
                    problem=data['problem'],
                    address=data['address'],
                    client_name=data['name'],
                    client_phone=data['phone']
                )
                logger.info(f"✅ Мастера уведомлены о заявке #{order_id}")
            except Exception as e:
                logger.error(f"⚠️ Ошибка уведомления мастеров: {e}")
        
        # Формируем итоговое сообщение
        message = (
            "✅ <b>Заявка создана!</b>\n\n"
            f"🎫 Номер: <b>#{order_id if order_id else 'XXXX'}</b>\n"
            f"📊 Статус: https://app.balt-set.ru/track.html?id={order_id if order_id else 'XXXX'}\n\n"
            "📞 <b>Мастер свяжется с вами в течение 15 минут!</b>\n\n"
            "💡 Отследить прогресс можно по ссылке выше"
        )
        
        # === TELEGRAM FOLDERS: Предлагаем папку ===
        if FOLDERS_ENABLED:
            try:
                folder_data = get_client_folder_invite()
                message += "\n\n💡 <b>Совет:</b> Добавьте папку в Telegram для удобства!"
                
                keyboard = [[
                    InlineKeyboardButton(
                        f"📁 Добавить папку \"{folder_data['folder_name']}\"",
                        url=folder_data['link']
                    )
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"Ошибка папки: {e}")
                await query.message.reply_text(message, parse_mode='HTML')
        else:
            await query.message.reply_text(message, parse_mode='HTML')
        
        return ConversationHandler.END

async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка редактирования конкретного поля"""
    query = update.callback_query
    await query.answer()
    
    field = query.data
    
    if field == "edit_back":
        # Возврат к резюме
        return await show_summary_again(query, context)
    
    elif field == "edit_problem":
        await query.edit_message_text(
            "✏️ Введите новое описание проблемы:",
            reply_markup=None
        )
        context.user_data['editing'] = 'problem'
        return PROBLEM
    
    elif field == "edit_address":
        await query.edit_message_text(
            "✏️ Введите новый адрес:",
            reply_markup=None
        )
        context.user_data['editing'] = 'address'
        return ADDRESS
    
    elif field == "edit_name":
        await query.edit_message_text(
            "✏️ Введите новое имя:",
            reply_markup=None
        )
        context.user_data['editing'] = 'name'
        return NAME
    
    elif field == "edit_phone":
        await query.edit_message_text(
            "✏️ Введите новый телефон:",
            reply_markup=None
        )
        context.user_data['editing'] = 'phone'
        return PHONE

async def show_summary_again(query, context):
    """Показать резюме снова после редактирования"""
    data = context.user_data
    summary = (
        f"{get_progress_bar(5)}\n\n"
        "📋 <b>Проверьте вашу заявку:</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🛠️ Категория: {data['category']}\n"
        f"📝 Проблема: {data['problem'][:100]}{'...' if len(data['problem']) > 100 else ''}\n"
        f"📍 Адрес: {data['address']}\n\n"
        "✅ Всё верно?"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Да, всё верно", callback_data="confirm_yes")],
        [InlineKeyboardButton("✏️ Редактировать", callback_data="confirm_edit")],
        [InlineKeyboardButton("❌ Отменить заявку", callback_data="confirm_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        summary,
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return CONFIRM

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    await update.message.reply_text(
        "❌ Операция отменена.\n\n"
        "Для создания новой заявки: /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ==================== ЗАПУСК БОТА ====================

def main():
    """Запуск бота"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_CLIENT_BOT_TOKEN не установлен!")
        return
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Conversation Handler с улучшенным UX
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_start_choice)],
            PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CONFIRM: [CallbackQueryHandler(handle_confirm)],
            EDIT: [CallbackQueryHandler(handle_edit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    logger.info("🤖 Telegram бот для клиентов (УЛУЧШЕННЫЙ) запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
