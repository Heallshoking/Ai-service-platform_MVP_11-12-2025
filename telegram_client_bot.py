"""
Telegram бот для клиентов - AI Service Platform
Принимает заявки на вызов мастера через диалог
"""
import os
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Загрузка переменных окружения
load_dotenv()

# Импорт AI помощника
from ai_assistant import ai

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_CLIENT_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "https://heallshoking-ai-service-platform-mvp-11-12-2025-2f94.twc1.net")

# Состояния диалога
NAME, PHONE, CATEGORY, PROBLEM, ADDRESS, CONFIRM = range(6)

# Категории услуг
CATEGORIES = {
    "⚡ Электрика": "electrical",
    "🚰 Сантехника": "plumbing", 
    "🔌 Бытовая техника": "appliance",
    "🔨 Общие работы": "general"
}

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога с AI-приветствием"""
    greeting = ai.get_greeting()
    await update.message.reply_text(greeting)
    
    await update.message.reply_text("Как вас зовут?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить имя с AI-подтверждением"""
    name = update.message.text
    context.user_data['name'] = name
    
    # AI подтверждение
    ack = ai.get_acknowledgment('name', name)
    await update.message.reply_text(ack)
    
    await update.message.reply_text(
        "Укажите ваш номер телефона в формате:\n"
        "+79001234567"
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить телефон с AI-валидацией"""
    phone = update.message.text
    
    # Простая валидация
    if not phone.startswith('+7') or len(phone) != 12:
        error = ai.get_validation_error('phone')
        await update.message.reply_text(error)
        return PHONE
    
    context.user_data['phone'] = phone
    
    # AI подтверждение
    ack = ai.get_acknowledgment('phone')
    await update.message.reply_text(ack)
    
    # Клавиатура с категориями
    keyboard = [[cat] for cat in CATEGORIES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "Выберите категорию услуги:",
        reply_markup=reply_markup
    )
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить категорию с AI-советом"""
    category_name = update.message.text
    
    if category_name not in CATEGORIES:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите категорию из списка:"
        )
        return CATEGORY
    
    category = CATEGORIES[category_name]
    context.user_data['category'] = category
    context.user_data['category_name'] = category_name
    
    # AI подтверждение
    ack = ai.get_acknowledgment('category', category_name)
    await update.message.reply_text(ack)
    
    # AI совет по категории
    tip = ai.get_category_tip(category)
    if tip:
        await update.message.reply_text(tip)
    
    await update.message.reply_text(
        "Опишите вашу проблему максимально подробно:\n"
        "(Например: 'Не работает розетка в гостиной, при включении искрит')",
        reply_markup=ReplyKeyboardRemove()
    )
    return PROBLEM

async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить описание проблемы с AI-валидацией"""
    problem = update.message.text
    
    if len(problem) < 10:
        error = ai.get_validation_error('problem_short')
        await update.message.reply_text(error)
        return PROBLEM
    
    context.user_data['problem'] = problem
    
    # AI подтверждение
    ack = ai.get_acknowledgment('problem')
    await update.message.reply_text(ack)
    
    await update.message.reply_text(
        "Укажите адрес, куда нужно выехать мастеру:\n"
        "(Например: 'ул. Ленина, д. 10, кв. 5')"
    )
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить адрес с AI-резюме"""
    address = update.message.text
    
    if len(address) < 5:
        error = ai.get_validation_error('address_short')
        await update.message.reply_text(error)
        return ADDRESS
    
    context.user_data['address'] = address
    
    # AI подтверждение
    ack = ai.get_acknowledgment('address')
    await update.message.reply_text(ack)
    
    # AI генерирует резюме
    summary = ai.generate_summary(context.user_data)
    await update.message.reply_text(summary, parse_mode='HTML')
    
    await update.message.reply_text(
        "Ответьте 'Да' для подтверждения или 'Нет' для отмены."
    )
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и отправка заявки с AI-ответом"""
    answer = update.message.text.lower()
    
    if answer not in ['да', 'yes', 'lf']:
        await update.message.reply_text(
            "❌ Заявка отменена.\n"
            "Для создания новой заявки используйте /start"
        )
        return ConversationHandler.END
    
    # AI сообщение о поиске мастера
    search_msg = ai.get_master_search_message()
    await update.message.reply_text(search_msg)
    
    # Отправить заявку на API
    data = context.user_data
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/api/v1/ai/web-form",
                json={
                    "name": data['name'],
                    "phone": data['phone'],
                    "category": data['category'],
                    "problem_description": data['problem'],
                    "address": data['address']
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # AI генерирует финальное подтверждение
                confirmation_data = {
                    'job_id': result.get('job_id'),
                    'master_assigned': result.get('master_assigned', False),
                    'master_name': f"Мастер #{result.get('master_id')}" if result.get('master_id') else "специалист"
                }
                
                message = ai.generate_confirmation(confirmation_data)
                
                # Добавляем цену
                price_msg = ai.get_price_estimate(result.get('estimated_price', 0))
                message = message.replace('</b>', f"</b>\n\n{price_msg}")
                
                await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text(
                    f"❌ Ошибка при создании заявки: {response.text}\n"
                    "Попробуйте позже или свяжитесь с поддержкой."
                )
    
    except Exception as e:
        logger.error(f"Ошибка отправки заявки: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при отправке заявки.\n"
            "Попробуйте позже или свяжитесь с поддержкой."
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text(
        "❌ Операция отменена.\n"
        "Для создания новой заявки используйте /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ==================== ЗАПУСК БОТА ====================

def main():
    """Запуск бота"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_CLIENT_BOT_TOKEN не установлен!")
        return
    
    # Создать приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Диалоговый обработчик
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Запуск бота
    logger.info("🤖 Telegram бот для клиентов запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
