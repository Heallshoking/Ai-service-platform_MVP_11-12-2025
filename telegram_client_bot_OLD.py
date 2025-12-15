"""
Telegram бот для клиентов - AI Service Platform
Принимает заявки на вызов мастера через диалог
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
    ConversationHandler,
    ContextTypes,
    filters
)

# Google Sheets Integration
try:
    from google_sheets_integration import save_order_from_bot
    GOOGLE_SHEETS_ENABLED = True
except:
    print("⚠️ Google Sheets не подключен, заявки будут только на API")
    GOOGLE_SHEETS_ENABLED = False

# Telegram Folders Integration
try:
    from telegram_folders_integration import get_client_folder_invite
    FOLDERS_ENABLED = True
except:
    print("⚠️ Telegram Folders не подключены")
    FOLDERS_ENABLED = False

# Загрузка переменных окружения
load_dotenv()

# AI помощник (опционально - закомментировано)
# from ai_assistant import ai

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
CATEGORY, PROBLEM, ADDRESS, NAME, PHONE, CONFIRM = range(6)

# Категории услуг
CATEGORIES = {
    "⚡ Электрика": "electrical",
    "🚰 Сантехника": "plumbing", 
    "🔌 Бытовая техника": "appliance",
    "🔨 Общие работы": "general"
}

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога - СНАЧАЛА ПОЛЬЗА, ПОТОМ КОНТАКТЫ"""
    # Отправляем картинку с приветствием
    try:
        await update.message.reply_photo(
            photo="https://bag4moms.balt-set.ru/tel.jpg",
            caption=(
                "👋 Здравствуйте!\n\n"
                "🔌 Я помогу вам найти проверенного электрика/монтажника в Калининграде.\n\n"
                "✅ Бесплатная консультация\n"
                "💰 Предварительная оценка стоимости\n"
                "🔧 Подбор мастера за 2 минуты"
            )
        )
    except:
        # Если картинка не загрузилась - текстом
        await update.message.reply_text(
            "👋 Здравствуйте!\n\n"
            "🔌 Я помогу вам найти проверенного электрика/монтажника в Калининграде.\n\n"
            "✅ Бесплатная консультация\n"
            "💰 Предварительная оценка стоимости\n"
            "🔧 Подбор мастера за 2 минуты"
        )
    
    # Клавиатура с 2 кнопками
    keyboard = [
        ["⚡ Услуги электрика"],
        ["🏠 Инженерные сети (умный дом, отопление, климат)"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "🛠️ Выберите направление:",
        reply_markup=reply_markup
    )
    return CATEGORY

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить имя с ВАЛИДАЦИЕЙ (только имена, не разговор)"""
    name = update.message.text.strip()
    
    # Валидация: имя должно быть 2-30 символов, только буквы и пробелы
    if len(name) < 2 or len(name) > 30:
        await update.message.reply_text(
            "❌ Укажите ваше имя (2-30 символов)\n\n"
            "💡 Например: Алексей, Мария, Иван Иванович"
        )
        return NAME
    
    # Проверка на подозрительные фразы (разговор)
    suspicious_words = ['сколько', 'что', 'как', 'где', 'когда', 'почему', 'зачем', 'можно', 'нужно', 'хочу', 'сделать', 'стоит']
    if any(word in name.lower() for word in suspicious_words) or len(name.split()) > 4:
        await update.message.reply_text(
            "❌ Похоже, вы начали разговаривать 😊\n\n"
            "👤 Просто укажите ваше имя, чтобы мастер знал как к вам обращаться.\n\n"
            "💡 Например: Алексей, Мария, Иван"
        )
        return NAME
    
    context.user_data['name'] = name
    
    await update.message.reply_text(
        f"✅ Приятно познакомиться, {name}!\n\n"
        "📞 Укажите номер телефона:\n\n"
        "💡 Формат: +79001234567"
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить телефон и показать резюме"""
    phone = update.message.text.strip()
    
    # Простая валидация
    if not phone.startswith('+7') or len(phone) != 12:
        await update.message.reply_text(
            "❌ Пожалуйста, укажите корректный номер.\n\n"
            "💡 Формат: +79001234567"
        )
        return PHONE
    
    context.user_data['phone'] = phone
    
    # Показываем резюме заявки
    data = context.user_data
    summary = (
        "📋 Проверьте вашу заявку:\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {phone}\n"
        f"🛠️ Категория: {data['category_name']}\n"
        f"📝 Проблема: {data['problem']}\n"
        f"📍 Адрес: {data['address']}\n\n"
        "✅ Ответьте 'Да' для подтверждения\n"
        "❌ Или 'Нет' для отмены"
    )
    
    await update.message.reply_text(summary)
    return CONFIRM

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить категорию"""
    category_name = update.message.text
    
    # Проверяем выбор направления
    if category_name == "⚡ Услуги электрика":
        # Показываем подкатегории электрики
        keyboard = [[cat] for cat in CATEGORIES.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "⚡ Услуги электрика\n\n"
            "🛠️ Выберите тип работ:",
            reply_markup=reply_markup
        )
        return CATEGORY
    
    elif category_name == "🏠 Инженерные сети (умный дом, отопление, климат)":
        # Открываем канал @konigkomfort
        await update.message.reply_text(
            "🏠 Инженерные сети\n\n"
            "🔧 Для услуг по умному дому, отоплению и климату - \n"
            "переходите в наш канал:\n\n"
            "@konigkomfort\n\n"
            "👉 https://t.me/konigkomfort",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Если выбрали подкатегорию электрики
    if category_name not in CATEGORIES:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите категорию из списка:"
        )
        return CATEGORY
    
    category = CATEGORIES[category_name]
    context.user_data['category'] = category
    context.user_data['category_name'] = category_name
    
    await update.message.reply_text(
        f"✅ {category_name}\n\n"
        "📝 Опишите проблему подробно:\n\n"
        "💡 Например: 'Не работает розетка в гостиной, при включении искрит'",
        reply_markup=ReplyKeyboardRemove()
    )
    return PROBLEM

async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить описание проблемы"""
    problem = update.message.text
    
    if len(problem) < 10:
        await update.message.reply_text(
            "🔍 Опишите проблему подробнее, чтобы мастер понял что нужно сделать."
        )
        return PROBLEM
    
    context.user_data['problem'] = problem
    
    await update.message.reply_text(
        f"✅ Понял: {problem[:50]}{'...' if len(problem) > 50 else ''}\n\n"
        "📍 Укажите адрес:\n\n"
        "💡 Например: 'ул. Ленина, д. 10, кв. 5'"
    )
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить адрес - ТЕПЕРЬ СПРАШИВАЕМ ИМЯ"""
    address = update.message.text
    
    if len(address) < 5:
        await update.message.reply_text(
            "📍 Укажите более точный адрес (улица, дом)"
        )
        return ADDRESS
    
    context.user_data['address'] = address
    
    # ТЕПЕРЬ СПРАШИВАЕМ КОНТАКТЫ
    await update.message.reply_text(
        f"✅ Адрес: {address}\n\n"
        "📞 Теперь нужны ваши контакты, чтобы мастер смог с вами связаться.\n\n"
        "👤 Как вас зовут?"
    )
    return NAME

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
    search_msg = "Ищу подходящих мастеров..."
    await update.message.reply_text(search_msg)
    
    # Отправить заявку
    data = context.user_data
    
    # === GOOGLE SHEETS: Сохраняем заявку ===
    order_id = None
    if GOOGLE_SHEETS_ENABLED:
        try:
            order_id = save_order_from_bot(
                name=data['name'],
                phone=data['phone'],
                category=data.get('category_name', data.get('category', '')),
                problem=data['problem'],
                address=data['address'],
                source="telegram"
            )
            if order_id:
                print(f"✅ Заявка #{order_id} сохранена в Google Sheets")
        except Exception as e:
            print(f"⚠️ Ошибка сохранения в Google Sheets: {e}")
    
    # === API: Отправляем на API (если есть) ===
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
                
                message = "✅ Заявка создана!"
                
                # Добавляем номер заявки из Google Sheets
                if order_id:
                    message += f"\n\n🎫 Номер заявки: #{order_id}\n📋 Отследить: https://app.balt-set.ru/track.html"
                
                message += "\n\n📞 Мастер свяжется с вами в течение 15 минут!"
                
                # Добавляем цену
                price_msg = ""
                message = message.replace('</b>', f"</b>\n\n{price_msg}")
                
                # === TELEGRAM FOLDERS: Предлагаем добавить папку ===
                if FOLDERS_ENABLED:
                    try:
                        folder_data = get_client_folder_invite()
                        
                        # Добавляем информацию о папке в сообщение
                        message += "\n\n💡 <b>Совет:</b> Добавьте папку в Telegram, чтобы все уведомления были в одном месте!"
                        
                        # Создаем кнопку для добавления папки
                        keyboard = [
                            [InlineKeyboardButton(
                                f"📁 Добавить папку \"{folder_data['folder_name']}\"",
                                url=folder_data['link']
                            )]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
                    except Exception as e:
                        logger.error(f"Ошибка отправки папки: {e}")
                        await update.message.reply_text(message, parse_mode='HTML')
                else:
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
