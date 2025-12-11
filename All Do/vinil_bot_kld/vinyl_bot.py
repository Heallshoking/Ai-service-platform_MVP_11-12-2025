# -*- coding: utf-8 -*-
"""
Telegram бот для винилового маркетплейса
Админка и интерфейс для продавцов и покупателей
"""

import os
import logging
import asyncio
import httpx
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from telegram.error import Conflict
from dotenv import load_dotenv

from utils.sheets_client import SheetsClient
from utils.drive_client import DriveClient
from utils.photo_hash import calculate_photo_hash, compare_hashes

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация клиентов
sheets_client = SheetsClient()
drive_client = DriveClient()

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', '0'))
API_BASE_URL = f"http://{os.getenv('API_HOST', 'localhost')}:{os.getenv('API_PORT', '8000')}"

# Состояния разговора для добавления записи
(TITLE, ARTIST, GENRE, YEAR, LABEL, COUNTRY, CONDITION, PRICE, PHOTO) = range(9)

# Состояния для бронирования
(BUYER_NAME, BUYER_ADDRESS, BUYER_CONTACT) = range(9, 12)

# Состояния для админ-действий
(ADMIN_PRICE_INPUT, ADMIN_STOCK_INPUT) = range(12, 14)


def get_progress_bar(current: int, total: int) -> str:
    """
    Создание визуального прогресс-бара
    
    Args:
        current: Текущий шаг
        total: Всего шагов
    
    Returns:
        Строка с прогресс-баром
    """
    filled = int((current / total) * 10)
    empty = 10 - filled
    bar = '▓' * filled + '░' * empty
    percentage = int((current / total) * 100)
    return f"[{bar}] {percentage}%"

# Предопределённые опции
GENRES = [
    ["Рок", "Прогрессивный рок"],
    ["Психоделический рок", "Джаз"],
    ["Блюз", "Соул"],
    ["Фанк", "Классика"],
    ["Опера", "Электронная музыка"],
    ["Диско", "Поп"],
    ["Шансон", "Фолк"],
    ["Мировая музыка"]
]

COUNTRIES = [
    ["СССР", "Россия"],
    ["США", "Великобритания"],
    ["Германия", "Франция"],
    ["Италия", "Япония"],
    ["Польша", "Чехословакия"]
]

CONDITIONS = [
    ["Идеальное (Mint)", "Почти идеальное (Near Mint)"],
    ["Очень хорошее плюс (VG+)", "Очень хорошее (VG)"],
    ["Хорошее плюс (G+)", "Хорошее (G)"]
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с улучшенным UX"""
    user = update.effective_user
    
    # Loading индикатор
    loading_msg = await update.message.reply_text("⏳ Загрузка...")
    
    # Регистрация пользователя
    try:
        sheets_client.register_user(user.id, user.full_name)
    except Exception as e:
        logger.error(f"Ошибка регистрации пользователя: {e}")
    
    # Проверка на deep link для бронирования
    if context.args and context.args[0].startswith('vinyl_'):
        await loading_msg.delete()
        record_id = context.args[0].replace('vinyl_', '')
        await show_record_for_booking(update, context, record_id)
        return
    
    # Удаляем loading
    await loading_msg.delete()
    
    # Постоянная клавиатура с двумя кнопками
    permanent_keyboard = ReplyKeyboardMarkup(
        [["➕ Добавить", "📋 Меню"]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    
    # Главная страница = Поиск на складе для админа
    search_message = f"""
👋 Привет, {user.first_name}!

🏢 <b>Админ-панель винилового магазина</b>

💡 <b>Как искать пластинки:</b>

1️⃣ По артикулу: <code>VIN-00001</code> или <code>1</code>
2️⃣ По названию: <code>The Dark Side of the Moon</code>
3️⃣ По исполнителю: <code>Pink Floyd</code>

⌨️ Напиши в чат, и я найду пластинку!

👇 <b>Используй кнопки:</b>
• <b>➕ Добавить</b> - добавить новую пластинку
• <b>📋 Меню</b> - управление и статистика
"""
    
    # Отправляем картинку с текстом
    photo_url = "https://drive.google.com/uc?export=view&id=1UF9Wn5MtL4OgzHoET_cu1w2nde-ILqXK"
    
    try:
        await update.message.reply_photo(
            photo=photo_url,
            caption=search_message,
            reply_markup=permanent_keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.warning(f"Не удалось загрузить картинку: {e}")
        await update.message.reply_text(
            search_message,
            reply_markup=permanent_keyboard,
            parse_mode='HTML'
        )
async def show_record_card(update: Update, context: ContextTypes.DEFAULT_TYPE, record: dict):
    """Показ карточки пластинки по записи справочника"""
    row_number = record.get('_row_number', 0)
    coll = sheets_client.get_collective_status(row_number)
    price = record.get('Цена', 0)
    stock = record.get('Stock_Count', 1)
    format_type = record.get('Формат', 'LP')
    status = record.get('Статус', '')
    
    # Определяем эмодзи статуса
    if '🟢' in status:
        status_emoji = '🟢 Доступна'
    elif '🟡' in status:
        status_emoji = '🟡 Резерв'
    elif '🔴' in status:
        status_emoji = '🔴 Продана'
    else:
        status_emoji = status

    message = (
        f"📀 <b>{record.get('Название','')}</b>\n"
        f"🎤 <i>{record.get('Исполнитель','')}</i>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔖 Артикул: <code>{record.get('Артикул','')}</code>\n"
        f"🎵 Формат: {format_type}\n"
        f"📀 Жанр: {record.get('Жанр','')}\n"
        f"📅 Год: {record.get('Год','')}\n"
        f"🏭 Лейбл: {record.get('Лейбл', 'Не указан')}\n"
        f"🌍 Страна: {record.get('Страна','')}\n"
        f"💿 Состояние: {record.get('Состояние','')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Цена: {price:,.0f} ₽</b>\n"
        f"📦 Остаток: {stock} шт.\n"
        f"📍 Статус: {status_emoji}"
    )

    # Админ-кнопки (только для админа)
    keyboard = [
        [
            InlineKeyboardButton("✏️ Цена", callback_data=f"admin_edit_price_{row_number}"),
            InlineKeyboardButton("🔄 Статус", callback_data=f"admin_edit_status_{row_number}")
        ],
        [
            InlineKeyboardButton("📦 Остаток", callback_data=f"admin_edit_stock_{row_number}"),
            InlineKeyboardButton("🌐 Обновить сайт", callback_data="admin_export_site")
        ],
        [
            InlineKeyboardButton("📖 AI-описание", callback_data=f"ai_description_{row_number}")
        ]
    ]

    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
☎️ <b>Контакты и помощь</b>

<b>Администратор:</b>
👤 @admin_username

<b>По вопросам:</b>
• Покупка/продажа пластинок
• Складчины и предзаказы
• Технические проблемы
• Сотрудничество

<b>Как пользоваться:</b>
🔍 <i>Поиск по исполнителю</i> — найти пластинку
📂 <i>Личный кабинет</i> — мои объявления, продать, история

<b>Просто напишите название:</b>
Например: "Кино Группа крови" — и я найду или создам заявку!
"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')


async def add_record_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления записи с прогресс-баром"""
    # Инициализация прогресса
    context.user_data['progress'] = 0
    context.user_data['total_steps'] = 9
    
    progress_text = get_progress_bar(0, 9)
    
    # Сообщение для ответа из message или callback
    message = update.message if update.message else update.callback_query.message
    
    await message.reply_text(
        f"📀 <b>Добавление виниловой пластинки</b>\n\n"
        f"{progress_text}\n\n"
        f"<b>Шаг 1/9: Название альбома</b>\n\n"
        f"Введите название пластинки:\n"
        f"<i>Например: The Dark Side of the Moon</i>\n\n"
        f"💡 <i>Совет: Используйте оригинальное название</i>",
        parse_mode='HTML'
    )
    return TITLE


async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия"""
    title = update.message.text.strip()
    
    if len(title) < 3 or len(title) > 200:
        await update.message.reply_text(
            "❌ Название должно быть от 3 до 200 символов.\n"
            "Попробуйте ещё раз:"
        )
        return TITLE
    
    context.user_data['title'] = title
    await update.message.reply_text(
        f"✅ Название: {title}\n\n"
        "Введите имя исполнителя:"
    )
    return ARTIST


async def get_artist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение исполнителя"""
    artist = update.message.text.strip()
    
    if len(artist) < 2 or len(artist) > 100:
        await update.message.reply_text(
            "❌ Имя исполнителя: от 2 до 100 символов.\n"
            "Попробуйте ещё раз:"
        )
        return ARTIST
    
    context.user_data['artist'] = artist
    
    # Показываем клавиатуру с жанрами
    reply_markup = ReplyKeyboardMarkup(GENRES, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Исполнитель: {artist}\n\n"
        "Выберите жанр:",
        reply_markup=reply_markup
    )
    return GENRE


async def get_genre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение жанра"""
    genre = update.message.text.strip()
    context.user_data['genre'] = genre
    
    await update.message.reply_text(
        f"✅ Жанр: {genre}\n\n"
        "Введите год выпуска (1900-2025) или нажмите 'Пропустить':",
        reply_markup=ReplyKeyboardMarkup([["Пропустить"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return YEAR


async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение года"""
    # Поддержка 'Пропустить'
    if update.message.text.strip().lower() in ['пропустить', '/skip']:
        context.user_data['year'] = ''
        await update.message.reply_text(
            "✅ Год: пропущено\n\n"
            "Введите название лейбла (или нажмите 'Пропустить'):",
            reply_markup=ReplyKeyboardMarkup([["Пропустить"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return LABEL
    try:
        year = int(update.message.text.strip())
        if year < 1900 or year > 2025:
            await update.message.reply_text(
                "❌ Введите год от 1900 до 2025.\n"
                "Попробуйте ещё раз:"
            )
            return YEAR
        context.user_data['year'] = year
        await update.message.reply_text(
            f"✅ Год: {year}\n\n"
            "Введите название лейбла (или нажмите 'Пропустить'):",
            reply_markup=ReplyKeyboardMarkup([["Пропустить"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return LABEL
    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректный год (число).\n"
            "Попробуйте ещё раз:"
        )
        return YEAR
        
        if year < 1900 or year > 2025:
            await update.message.reply_text(
                "❌ Введите год от 1900 до 2025.\n"
                "Попробуйте ещё раз:"
            )
            return YEAR
        
        context.user_data['year'] = year
        await update.message.reply_text(
            f"✅ Год: {year}\n\n"
            "Введите название лейбла (или /skip чтобы пропустить):"
        )
        return LABEL
        
    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректный год (число).\n"
            "Попробуйте ещё раз:"
        )
        return YEAR


async def get_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение лейбла"""
    if update.message.text.strip().lower() in ['пропустить', '/skip']:
        context.user_data['label'] = ''
        label_text = "пропущено"
    else:
        label = update.message.text.strip()
        if len(label) > 100:
            await update.message.reply_text(
                "❌ Название лейбла: максимум 100 символов.\n"
                "Попробуйте ещё раз (или нажмите 'Пропустить'):"
            )
            return LABEL
        context.user_data['label'] = label
        label_text = label
    
    # Показываем клавиатуру со странами
    reply_markup = ReplyKeyboardMarkup(COUNTRIES + [["Пропустить"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Лейбл: {label_text}\n\n"
        "Выберите страну производства (или нажмите 'Пропустить'):",
        reply_markup=reply_markup
    )
    return COUNTRY


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение страны"""
    country_text = update.message.text.strip()
    if country_text.lower() in ['пропустить', '/skip']:
        context.user_data['country'] = ''
        country = 'пропущено'
    else:
        country = country_text
        context.user_data['country'] = country
    
    # Показываем клавиатуру с состояниями
    reply_markup = ReplyKeyboardMarkup(CONDITIONS + [["Пропустить"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        f"✅ Страна: {country}\n\n"
        "Выберите состояние пластинки (или нажмите 'Пропустить'):",
        reply_markup=reply_markup
    )
    return CONDITION


async def get_condition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение состояния"""
    condition_text = update.message.text.strip()
    if condition_text.lower() in ['пропустить', '/skip']:
        context.user_data['condition'] = ''
        condition = 'пропущено'
    else:
        condition = condition_text
        context.user_data['condition'] = condition
    
    await update.message.reply_text(
        f"✅ Состояние: {condition}\n\n"
        "Введите цену в рублях:",
        reply_markup=ReplyKeyboardRemove()
    )
    return PRICE


async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение цены"""
    try:
        price = float(update.message.text.strip())
        
        if price <= 0:
            await update.message.reply_text(
                "❌ Цена должна быть больше 0.\n"
                "Попробуйте ещё раз:"
            )
            return PRICE
        
        context.user_data['price'] = price
        await update.message.reply_text(
            f"✅ Цена: {price} руб.\n\n"
            "📸 Загрузите фото пластинки (JPG/PNG, максимум 10 МБ):"
        )
        return PHOTO
        
    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректную цену (число).\n"
            "Попробуйте ещё раз:"
        )
        return PRICE


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение фото с детальными статусами"""
    if not update.message.photo:
        await update.message.reply_text(
            "❌ <b>Ошибка формата</b>\n\n"
            "Пожалуйста, загрузите фото в формате JPG или PNG.\n\n"
            "📸 <i>Совет: Сделайте четкое фото обложки</i>",
            parse_mode='HTML'
        )
        return PHOTO
    
    try:
        # Получение фото
        photo = update.message.photo[-1]  # Самый большой размер
        
        # Проверка размера (10 МБ)
        if photo.file_size > 10 * 1024 * 1024:
            size_mb = photo.file_size / (1024 * 1024)
            await update.message.reply_text(
                f"📸 <b>Файл слишком большой</b>\n\n"
                f"Размер: {size_mb:.1f} МБ\n"
                f"Максимум: 10 МБ\n\n"
                f"Пожалуйста, сожмите фото и попробуйте снова.",
                parse_mode='HTML'
            )
            return PHOTO
        
        # Многошаговый процесс с обратной связью
        status_msg = await update.message.reply_text(
            "⏳ <b>Обработка фото...</b>\n\n"
            "├─ 📥 Загрузка... ⏳\n"
            "├─ 🔍 Проверка дубликатов... ⏹\n"
            "├─ ☁️ Сохранение в облако... ⏹\n"
            "└─ ✨ Генерация описания... ⏹",
            parse_mode='HTML'
        )
        
        # Скачивание фото
        file = await context.bot.get_file(photo.file_id)
        photo_path = f"/tmp/vinyl_{update.effective_user.id}_{datetime.now().timestamp()}.jpg"
        await file.download_to_drive(photo_path)
        
        await status_msg.edit_text(
            "⏳ <b>Обработка фото...</b>\n\n"
            "├─ 📥 Загрузка... ✅\n"
            "├─ 🔍 Проверка дубликатов... ⏳\n"
            "├─ ☁️ Сохранение в облако... ⏹\n"
            "└─ ✨ Генерация описания... ⏹",
            parse_mode='HTML'
        )
        
        # Вычисление хеша фото
        photo_hash = calculate_photo_hash(photo_path)
        
        # Проверка на дубликат
        duplicate_id = sheets_client.check_photo_duplicate(photo_hash)
        if duplicate_id:
            await status_msg.delete()
            
            keyboard = [
                [InlineKeyboardButton("✅ Это другая пластинка", callback_data="confirm_not_duplicate")],
                [InlineKeyboardButton("❌ Да, это дубликат", callback_data="cancel_duplicate")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "⚠️ <b>Обнаружен похожий винил</b>\n\n"
                f"Найдена запись #{duplicate_id} с похожим фото.\n\n"
                "Это действительно другая пластинка?",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            os.remove(photo_path)
            return PHOTO
        
        await status_msg.edit_text(
            "⏳ <b>Обработка фото...</b>\n\n"
            "├─ 📥 Загрузка... ✅\n"
            "├─ 🔍 Проверка дубликатов... ✅\n"
            "├─ ☁️ Сохранение в облако... ⏳\n"
            "└─ ✨ Генерация описания... ⏹",
            parse_mode='HTML'
        )
        
        # Добавление записи в Google Sheets
        record_data = {
            'title': context.user_data['title'],
            'artist': context.user_data['artist'],
            'genre': context.user_data['genre'],
            'year': context.user_data['year'],
            'label': context.user_data.get('label', ''),
            'country': context.user_data['country'],
            'condition': context.user_data['condition'],
            'price': context.user_data['price'],
            'seller_tg_id': update.effective_user.id
        }
        
        # Сохранение в Sheets (без фото пока)
        row_number = sheets_client.add_record(record_data)
        
        # Загрузка фото в Google Drive
        photo_url = drive_client.upload_photo(photo_path, row_number)
        
        # Обновление URL фото в Sheets
        worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        worksheet.update_cell(row_number, 9, photo_url)  # Колонка I - ФОТО_URL
        
        # Сохранение хеша фото
        sheets_client.add_photo_hash(photo_hash, row_number)
        
        # Добавление отчёта
        sheets_client.add_report('Добавлена', row_number, update.effective_user.id)
        
        # Удаление временного файла
        os.remove(photo_path)
        
        await update.message.reply_text(
            "✅ Запись успешно добавлена!\n\n"
            "⏳ Генерация AI-описания... Это займёт 10-30 секунд."
        )
        
        # Фоновая генерация описания
        asyncio.create_task(generate_description_async(
            update, context, row_number, record_data
        ))
        
        # Очистка данных
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка сохранения записи: {e}")
        await update.message.reply_text(
            "🔧 Техническая ошибка. Администратор уведомлён.\n"
            "Попробуйте позже."
        )
        return ConversationHandler.END


async def generate_description_async(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     row_number: int, record_data: dict):
    """Асинхронная генерация описания через API с fallback"""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/generate-description",
                json={
                    'record_id': f'row_{row_number}',
                    'title': record_data['title'],
                    'artist': record_data['artist'],
                    'year': record_data['year'],
                    'genre': record_data['genre'],
                    'label': record_data.get('label'),
                    'country': record_data.get('country')
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✨ Описание готово!\n\n{result['description'][:200]}..."
                )
            else:
                logger.warning(f"API генерации недоступен: {response.status_code}. Используется заглушка.")
                # Fallback: простое описание
                fallback = f"📀 {record_data['title']} — культовая пластинка!\n\nОписание будет добавлено позже."
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=fallback
                )
                
    except Exception as e:
        logger.info(f"Фоновая генерация пропущена (API недоступен): {e}")
        # Не показываем ошибку пользователю — это не критично


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущей операции"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Операция отменена.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def my_records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр своих записей"""
    user_id = update.effective_user.id
    
    try:
        worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        all_records = worksheet.get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес'])
        
        user_records = [r for r in all_records if r.get('Продавец_TG_ID') == user_id]
        
        if not user_records:
            await update.message.reply_text(
                "У вас пока нет добавленных пластинок.\n"
                "Используйте /add_record чтобы добавить."
            )
            return
        
        message = f"📀 Ваши пластинки ({len(user_records)}):\n\n"
        
        for idx, record in enumerate(user_records[:10], 1):  # Первые 10
            status_emoji = record.get('Статус', '')[:2]
            message += (
                f"{idx}. {status_emoji} {record.get('Название')} - {record.get('Исполнитель')}\n"
                f"   {record.get('Цена')} руб., {record.get('Год')}\n\n"
            )
        
        if len(user_records) > 10:
            message += f"... и ещё {len(user_records) - 10}"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Ошибка получения записей пользователя: {e}")
        await update.message.reply_text("Ошибка получения данных")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик inline кнопок
    """
    query = update.callback_query
    await query.answer()
    
    # Обработка кнопки МЕНЮ
    if query.data == "show_main_menu":
        keyboard = [
            [
                InlineKeyboardButton("➕ Добавить пластинку", callback_data="start_add_record"),
            ],
            [
                InlineKeyboardButton("📊 Статистика", callback_data="statistics"),
                InlineKeyboardButton("🌐 Обновить сайт", callback_data="admin_export_site"),
            ],
        ]
        await query.message.reply_text(
            "📋 <b>Меню управления</b>\n\n"
            "🔍 Поиск: напиши артикул или название в чате\n"
            "👇 Выбери действие:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return

    # Поиск на складе (удаленная кнопка, оставлено для совместимости)
    elif query.data == "warehouse_search" or query.data == "main_buy":
        # Удаляем сообщение меню
        try:
            await query.message.delete()
        except:
            pass
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🔍 <b>Поиск</b>\n\n"
                 "Просто напиши в чате:\n\n"
                 "• Артикул: <code>VIN-00001</code> или <code>1</code>\n"
                 "• Название: <code>Dark Side</code>\n"
                 "• Исполнитель: <code>Pink Floyd</code>",
            parse_mode='HTML'
        )
        return

    # Статистика
    elif query.data == "statistics":
        # Удаляем сообщение меню
        try:
            await query.message.delete()
        except:
            pass
        
        try:
            worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
            all_records = worksheet.get_all_records()
            
            total = len(all_records)
            available = len([r for r in all_records if '🟢' in str(r.get('Статус', ''))])
            sold = len([r for r in all_records if '🔴' in str(r.get('Статус', ''))])
            reserved = len([r for r in all_records if '🟡' in str(r.get('Статус', ''))])
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"📊 <b>Статистика склада</b>\n\n"
                     f"📦 Всего пластинок: <b>{total}</b>\n\n"
                     f"🟢 Доступно: {available}\n"
                     f"🟡 Зарезервировано: {reserved}\n"
                     f"🔴 Продано: {sold}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка загрузки статистики: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Ошибка загрузки статистики"
            )
        return

    # Главное меню (старые кнопки для совместимости)
    if query.data == "main_buy":
        await query.message.reply_text(
            "🛒 <b>Режим покупателя</b>\n\n"
            "Как искать пластинки:\n\n"
            "1️⃣ По артикулу: <code>VIN-00001</code> или просто <code>1</code>\n"
            "2️⃣ По названию: <code>The Dark Side of the Moon</code>\n"
            "3️⃣ По исполнителю: <code>Pink Floyd</code>\n\n"
            "💡 Просто отправь сообщение в чат, и я найду пластинку!\n\n"
            "🎯 Если пластинки нет — создам заявку на поиск с возможностью складчины.",
            parse_mode='HTML'
        )
        return

    elif query.data == "main_sell":
        context.user_data["mode"] = "sell"
        await query.message.reply_text(
            "💼 <b>Режим продажи</b>\n\n"
            "Отправь артикул пластинки, которую хочешь продать или списать.\n\n"
            "📋 Пример: <code>VIN-00042</code> или просто <code>42</code>\n\n"
            "ℹ️ Я найду её в каталоге и покажу карточку с опциями управления.",
            parse_mode='HTML'
        )
        return

    elif query.data == "main_add_record" or query.data == "start_add_record":
        # Очищаем context.user_data перед началом добавления
        context.user_data.clear()
        await add_record_start(update, context)
        return
    
    # Админ: изменение цены
    elif query.data.startswith("admin_edit_price_"):
        if query.from_user.id != ADMIN_TELEGRAM_ID:
            await query.message.reply_text("❌ Недоступно")
            return
        row_number = int(query.data.replace("admin_edit_price_", ""))
        context.user_data['admin_edit_price_row'] = row_number
        await query.message.reply_text(
            "✏️ <b>Изменение цены</b>\n\n"
            "Введите новую цену в рублях:\n"
            "Например: <code>5000</code> или <code>12500</code>\n\n"
            "💡 Можно использовать разделители: 5 000 или 12,500",
            parse_mode='HTML'
        )
        return
    
    # Админ: изменение статуса
    elif query.data.startswith("admin_edit_status_"):
        if query.from_user.id != ADMIN_TELEGRAM_ID:
            await query.message.reply_text("❌ Недоступно")
            return
        row_number = int(query.data.replace("admin_edit_status_", ""))
        keyboard = [
            [InlineKeyboardButton("🟢 Доступна", callback_data=f"admin_set_status_{row_number}_available")],
            [InlineKeyboardButton("🟡 Резерв", callback_data=f"admin_set_status_{row_number}_reserved")],
            [InlineKeyboardButton("🔴 Продана", callback_data=f"admin_set_status_{row_number}_sold")]
        ]
        await query.message.reply_text(
            "🔄 <b>Изменение статуса</b>\n\n"
            "Выберите новый статус:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return
    
    # Админ: установка статуса
    elif query.data.startswith("admin_set_status_"):
        if query.from_user.id != ADMIN_TELEGRAM_ID:
            await query.message.reply_text("❌ Недоступно")
            return
        parts = query.data.split("_")
        row_number = int(parts[3])
        status_type = parts[4]
        
        status_map = {
            'available': '🟢 Доступна',
            'reserved': '🟡 Зарезервирована',
            'sold': '🔴 Продана'
        }
        new_status = status_map.get(status_type, '🟢 Доступна')
        
        try:
            sheets_client.update_status(row_number, new_status)
            await query.message.reply_text(f"✅ Статус обновлён: {new_status}")
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
            await query.message.reply_text("❌ Ошибка обновления статуса")
        return
    
    # Админ: изменение остатка
    elif query.data.startswith("admin_edit_stock_"):
        if query.from_user.id != ADMIN_TELEGRAM_ID:
            await query.message.reply_text("❌ Недоступно")
            return
        row_number = int(query.data.replace("admin_edit_stock_", ""))
        context.user_data['admin_edit_stock_row'] = row_number
        await query.message.reply_text(
            "📦 <b>Изменение остатка</b>\n\n"
            "Введите количество на складе:\n"
            "Например: <code>5</code>, <code>10</code> или <code>0</code>\n\n"
            "⚠️ <b>Важно:</b> При установке 0 статус автоматически изменится на '🔴 Продана'\n"
            "При увеличении с 0 до любого числа — статус вернётся на '🟢 Доступна'",
            parse_mode='HTML'
        )
        return
    
    # Админ: обновление сайта
    elif query.data == "admin_export_site":
        if query.from_user.id != ADMIN_TELEGRAM_ID:
            await query.message.reply_text("❌ Недоступно")
            return
        
        status_msg = await query.message.reply_text(
            "⏳ <b>Генерация статического каталога...</b>\n\n"
            "📊 Собираю данные из Google Sheets...\n"
            "🔄 Это может занять 10-30 секунд",
            parse_mode='HTML'
        )
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{API_BASE_URL}/admin/export-static",
                    params={"output_dir": "./static_export"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    await status_msg.edit_text(
                        f"✅ <b>Сайт успешно обновлён!</b>\n\n"
                        f"📊 Экспортировано записей: <b>{result.get('exported_records', 0)}</b>\n"
                        f"📁 Путь: <code>{result.get('catalog_path', '')}</code>\n\n"
                        f"⏱ Время генерации: {result.get('generation_time_seconds', 0):.2f} сек.\n\n"
                        f"🌐 Файлы готовы для загрузки на Vercel/Netlify",
                        parse_mode='HTML'
                    )
                else:
                    await status_msg.edit_text(
                        f"❌ <b>Ошибка экспорта</b>\n\n"
                        f"Код ошибки: {response.status_code}\n\n"
                        f"Проверьте:\n"
                        f"• Запущен ли FastAPI сервер\n"
                        f"• Доступ к Google Sheets\n"
                        f"• Логи: <code>tail -f /tmp/vinyl_api.log</code>",
                        parse_mode='HTML'
                    )
        except httpx.TimeoutException:
            await status_msg.edit_text(
                "⏱ <b>Превышено время ожидания</b>\n\n"
                "Генерация занимает больше времени, чем ожидалось.\n"
                "Скорее всего, процесс всё ещё выполняется на сервере.\n\n"
                "Подождите 1-2 минуты и проверьте файлы вручную.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка экспорта сайта: {e}")
            await status_msg.edit_text(
                f"❌ <b>Ошибка обновления сайта</b>\n\n"
                f"<code>{str(e)[:150]}</code>\n\n"
                f"💡 Попробуйте:\n"
                f"• Перезапустить FastAPI: <code>pkill -f main.py && python3 main.py &</code>\n"
                f"• Проверить .env файл\n"
                f"• Посмотреть логи API",
                parse_mode='HTML'
            )
        return

    # AI-описание для существующей карточки
    elif query.data.startswith("ai_description_"):
        row_number = int(query.data.replace("ai_description_", ""))
        
        status_msg = await query.message.reply_text(
            "🤖 <b>AI-музыковед пишет описание...</b>\n\n"
            "⏳ Это займёт 10-30 секунд",
            parse_mode='HTML'
        )
        
        try:
            # Получаем данные записи
            worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
            record = worksheet.row_values(row_number)
            headers = worksheet.row_values(1)
            record_dict = dict(zip(headers, record))
            
            record_data = {
                'title': record_dict.get('Название', ''),
                'artist': record_dict.get('Исполнитель', ''),
                'year': int(record_dict.get('Год', 0) or 0),
                'genre': record_dict.get('Жанр', ''),
                'label': record_dict.get('Лейбл', ''),
                'country': record_dict.get('Страна', '')
            }
            
            # Вызываем API для генерации описания
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/generate-description",
                    json={
                        "record_id": str(row_number),
                        "title": record_data['title'],
                        "artist": record_data['artist'],
                        "year": record_data['year'],
                        "genre": record_data['genre'],
                        "label": record_data['label'],
                        "country": record_data['country']
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    description = result.get('description', '')
                    
                    # Сохраняем описание в Google Sheets
                    desc_col = headers.index('Описание') + 1 if 'Описание' in headers else None
                    if desc_col:
                        worksheet.update_cell(row_number, desc_col, description)
                    
                    await status_msg.edit_text(
                        f"✅ <b>AI-описание создано!</b>\n\n"
                        f"{description[:500]}{'...' if len(description) > 500 else ''}",
                        parse_mode='HTML'
                    )
                else:
                    await status_msg.edit_text(
                        f"❌ Ошибка генерации: {response.status_code}",
                        parse_mode='HTML'
                    )
        except Exception as e:
            logger.error(f"Ошибка AI-описания: {e}")
            await status_msg.edit_text(
                f"❌ Ошибка: {str(e)[:100]}",
                parse_mode='HTML'
            )
        return
    
    # AI-создание новой карточки
    elif query.data.startswith("ai_create_card_"):
        search_query = query.data.replace("ai_create_card_", "")
        
        status_msg = await query.message.reply_text(
            f"🤖 <b>AI-музыковед ищет информацию...</b>\n\n"
            f"🔍 Запрос: {search_query}\n"
            f"⏳ Это займёт 15-60 секунд",
            parse_mode='HTML'
        )
        
        try:
            # Создаём запись в Google Sheets
            record_data = {
                'title': search_query,
                'artist': '',
                'genre': '',
                'year': '',
                'label': '',
                'country': '',
                'condition': '',
                'price': 0,
                'photo_url': '',
                'seller_tg_id': query.from_user.id
            }
            
            # Добавляем запись
            row_number = sheets_client.add_record(record_data)
            
            await status_msg.edit_text(
                f"✅ <b>Карточка создана!</b>\n\n"
                f"📀 {search_query}\n"
                f"🔖 Артикул: <code>VIN-{row_number-1:05d}</code>\n\n"
                f"🤖 AI-музыковед генерирует описание в фоновом режиме...",
                parse_mode='HTML'
            )
            
            # Фоновая генерация описания
            record_data_ai = {
                'title': search_query,
                'artist': '',
                'year': 0,
                'genre': '',
                'label': '',
                'country': ''
            }
            asyncio.create_task(generate_description_async(update, context, row_number, record_data_ai))
            
        except Exception as e:
            logger.error(f"Ошибка AI-создания карточки: {e}")
            await status_msg.edit_text(
                f"❌ Ошибка: {str(e)[:100]}",
                parse_mode='HTML'
            )
        return

    if query.data == "browse_catalog":
        await browse_catalog(update, context)
    elif query.data == "start_add_record":
        # Обработка через ConversationHandler (entry_points содержит CallbackQueryHandler)
        return
    elif query.data == "my_records":
        # Личный кабинет
        kb = [
            [InlineKeyboardButton("💼 Мои объявления", callback_data="my_listings")],
            [InlineKeyboardButton("🛍️ Продать пластинку", callback_data="start_add_record")],
            [InlineKeyboardButton("📊 История просмотра", callback_data="history")]
        ]
        await query.message.reply_text("📂 <b>Личный кабинет</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')
    elif query.data == "favorites":
        try:
            ws = sheets_client.spreadsheet.worksheet("Избранное")
        except Exception:
            ws = sheets_client.spreadsheet.add_worksheet(title="Избранное", rows=100, cols=5)
            ws.update([["Дата/Время","Пользователь TG","Название","Исполнитель","Ссылка"]], 'A1:E1')
        favs = ws.get_all_records(expected_headers=["Дата/Время","Пользователь TG","Название","Исполнитель","Ссылка"])
        user_id = query.from_user.id
        fav_user = [f for f in favs if int(f.get("Пользователь TG", 0) or 0) == user_id]
        if not fav_user:
            await query.message.reply_text("⭐ Избранное пусто. На карточке нажмите '🔔 Следить за появлением'.")
        else:
            msg = "⭐ <b>Избранное</b>\n\n"
            for f in fav_user[:5]:
                msg += f"• <b>{f.get('Название')}</b> — {f.get('Исполнитель')}\n"
            await query.message.reply_text(msg, parse_mode='HTML')
    elif query.data == "my_listings":
        await show_my_records_inline(update, context)
    elif query.data == "history":
        try:
            ws = sheets_client.spreadsheet.worksheet("Предзаказы")
            rows = ws.get_all_records(expected_headers=["Дата/Время","Название","Исполнитель","Пользователь TG","Контакт","Тип","Комментарий","Статус"])
            user_id = query.from_user.id
            my_rows = [r for r in rows if int(r.get("Пользователь TG", 0) or 0) == user_id]
            if not my_rows:
                await query.message.reply_text("💸 История пуста.")
            else:
                msg = "💸 <b>История</b>\n\n"
                for r in my_rows[:5]:
                    msg += f"• {r.get('Тип')} — <b>{r.get('Название')}</b> ({r.get('Исполнитель')}) — {r.get('Статус')}\n"
                await query.message.reply_text(msg, parse_mode='HTML')
        except Exception as e:
            logger.error(f"history error: {e}")
            await query.message.reply_text("❌ Не удалось загрузить историю.")
    elif query.data == "music_trending":
        picks = sheets_client.get_trending_records(limit=3)
        if not picks:
            await query.message.reply_text("Пока нет трендов — попробуйте поиск или эпохи.")
        else:
            for r in picks:
                row_number = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG).get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес']).index(r) + 2
                price = r.get('Цена', 0)
                msg = (
                    f"🎵 <b>{r.get('Название','')}</b>\n"
                    f"🎤 {r.get('Исполнитель','')}\n\n"
                    f"💰 <b>Цена: {price} ₽</b>\n"
                    f"👥 Складчина: {r.get('Складчина_участников',0)} из {r.get('Минимум_складчиков',10)}"
                )
                keyboard = [
                    [InlineKeyboardButton("🤝 Складчина", callback_data=f"collect_join_row_{row_number}")],
                    [InlineKeyboardButton("🛒 Купить сейчас", callback_data=f"buy_row_{row_number}")]
                ]
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    elif query.data == "music_epoch":
        kb = [
            [InlineKeyboardButton("60-е", callback_data="music_epoch_choice_1960_1969"), InlineKeyboardButton("70-е", callback_data="music_epoch_choice_1970_1979")],
            [InlineKeyboardButton("80-е", callback_data="music_epoch_choice_1980_1989"), InlineKeyboardButton("90-е", callback_data="music_epoch_choice_1990_1999")],
            [InlineKeyboardButton("2000-е", callback_data="music_epoch_choice_2000_2009"), InlineKeyboardButton("2010-е", callback_data="music_epoch_choice_2010_2019")]
        ]
        await query.message.reply_text("Выберите эпоху:", reply_markup=InlineKeyboardMarkup(kb))
    elif query.data.startswith("music_epoch_choice_"):
        _, start, end = query.data.split("_")[3:]
        start_year = int(start)
        end_year = int(end)
        picks = sheets_client.get_records_by_epoch(start_year, end_year, limit=3)
        if not picks:
            await query.message.reply_text("Пока нет записей для выбранной эпохи.")
        else:
            for r in picks:
                row_number = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG).get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес']).index(r) + 2
                price = r.get('Цена', 0)
                msg = (
                    f"🎵 <b>{r.get('Название','')}</b>\n"
                    f"🎤 {r.get('Исполнитель','')}\n\n"
                    f"💰 <b>Цена: {price} ₽</b>"
                )
                keyboard = [
                    [InlineKeyboardButton("🤝 Складчина", callback_data=f"collect_join_row_{row_number}")],
                    [InlineKeyboardButton("🛒 Купить сейчас", callback_data=f"buy_row_{row_number}")]
                ]
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    elif query.data == "music_mood":
        kb = [
            [InlineKeyboardButton("⚡ Энергично", callback_data="music_mood_choice_energetic")],
            [InlineKeyboardButton("🌙 Спокойно", callback_data="music_mood_choice_calm")],
            [InlineKeyboardButton("🕰️ Ностальгия", callback_data="music_mood_choice_nostalgia")]
        ]
        await query.message.reply_text("Выберите настроение:", reply_markup=InlineKeyboardMarkup(kb))
    elif query.data == "music_classics":
        try:
            worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
            recs = worksheet.get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес'])
            classics = [r for r in recs if 'Классика' in str(r.get('Жанр',''))]
            picks = classics[:3] if classics else recs[:3]
            for r in picks:
                row_number = recs.index(r) + 2
                price = r.get('Цена', 0)
                msg = (
                    f"🎵 <b>{r.get('Название','')}</b>\n"
                    f"🎤 {r.get('Исполнитель','')}\n\n"
                    f"💰 <b>Цена: {price} ₽</b>"
                )
                keyboard = [
                    [InlineKeyboardButton("🤝 Складчина", callback_data=f"collect_join_row_{row_number}")],
                    [InlineKeyboardButton("🛒 Купить сейчас", callback_data=f"buy_row_{row_number}")]
                ]
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        except Exception as e:
            logger.error(f"music_classics error: {e}")
            await query.message.reply_text("❌ Не удалось получить рекомендации.")
    elif query.data.startswith("music_mood_choice_"):
        mood = query.data.replace("music_mood_choice_", "")
        genre_map = {
            'energetic': ['Рок', 'Хип-хоп', 'Электронная музыка'],
            'calm': ['Джаз', 'Соул', 'Классика'],
            'nostalgia': ['Рок', 'Фолк', 'Шансон']
        }
        try:
            worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
            recs = worksheet.get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес'])
            want = genre_map.get(mood, [])
            filtered = [r for r in recs if any(g in str(r.get('Жанр','')) for g in want)]
            picks = filtered[:3] if filtered else recs[:3]
            await query.message.reply_text("Вот что вам может понравиться:")
            for r in picks:
                row_number = recs.index(r) + 2
                price = r.get('Цена', 0)
                msg = (
                    f"🎵 <b>{r.get('Название','')}</b>\n"
                    f"🎤 {r.get('Исполнитель','')}\n\n"
                    f"💰 <b>Цена: {price} ₽</b>"
                )
                keyboard = [
                    [InlineKeyboardButton("🤝 Складчина", callback_data=f"collect_join_row_{row_number}")],
                    [InlineKeyboardButton("🛒 Купить сейчас", callback_data=f"buy_row_{row_number}")]
                ]
                await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        except Exception as e:
            logger.error(f"music_mood_choice error: {e}")
            await query.message.reply_text("❌ Не удалось получить рекомендации.")
    elif query.data.startswith("collect_join_row_"):
        row_number = int(query.data.replace("collect_join_row_", ""))
        status = sheets_client.get_collective_status(row_number)
        res = sheets_client.increment_collective_participation(row_number)
        worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        row_vals = worksheet.row_values(row_number)
        title = row_vals[0] if len(row_vals) >= 1 else ''
        artist = row_vals[1] if len(row_vals) >= 2 else ''
        if res["participants"] >= res["minimum"]:
            sheets_client.log_admin_event("Складчина набрана", title, artist, details=f"{res['participants']}/{res['minimum']}")
            await query.message.reply_text(
                f"🎉 Группа набрана: {res['participants']} из {res['minimum']}\nАдмин скоро пришлёт спецпредложение."
            )
        else:
            await query.message.reply_text(
                f"🤝 Вы участвуете в складчине. Сейчас: {res['participants']} из {res['minimum']}."
            )
    elif query.data.startswith("preorder_row_"):
        row_number = int(query.data.replace("preorder_row_", ""))
        worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        row_vals = worksheet.row_values(row_number)
        title = row_vals[0] if len(row_vals) >= 1 else ''
        artist = row_vals[1] if len(row_vals) >= 2 else ''
        user = query.from_user
        contact = f"@{user.username}" if user.username else str(user.id)
        sheets_client.create_preorder(title, artist, user.id, contact, order_type='Предзаказ', comment='Из бота')
        sheets_client.log_admin_event("Новый предзаказ", title, artist, details=contact)
        await query.message.reply_text("🛒 Предзаказ оформлен! Админ свяжется для деталей.")
    elif query.data.startswith("details_row_"):
        row_number = int(query.data.replace("details_row_", ""))
        worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        rec = worksheet.get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес'])[row_number-2]
        record_data = {
            'title': rec.get('Название',''),
            'artist': rec.get('Исполнитель',''),
            'year': rec.get('Год',0),
            'genre': rec.get('Жанр',''),
            'label': rec.get('Лейбл','неизвестен'),
            'country': rec.get('Страна','неизвестна')
        }
        await query.message.reply_text("⏳ Генерирую историю...")
        asyncio.create_task(generate_description_async(update, context, row_number, record_data))
    elif query.data.startswith("follow_row_"):
        row_number = int(query.data.replace("follow_row_", ""))
        ws = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        row_vals = ws.row_values(row_number)
        title = row_vals[0] if len(row_vals) >= 1 else ''
        artist = row_vals[1] if len(row_vals) >= 2 else ''
        try:
            fav = sheets_client.spreadsheet.worksheet("Избранное")
        except Exception:
            fav = sheets_client.spreadsheet.add_worksheet(title="Избранное", rows=100, cols=5)
            fav.update([["Дата/Время","Пользователь TG","Название","Исполнитель","Ссылка"]], 'A1:E1')
        fav.append_row([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            query.from_user.id,
            title,
            artist,
            ''
        ])
        await query.message.reply_text("🔔 Буду держать вас в курсе!")
        if query.from_user.id != ADMIN_TELEGRAM_ID:
            await query.message.reply_text("❌ Недоступно")
            return
        row_number = int(query.data.replace("admin_edit_min_row_", ""))
        kb = [
            [InlineKeyboardButton("5", callback_data=f"admin_set_min_row_{row_number}_5"), InlineKeyboardButton("10", callback_data=f"admin_set_min_row_{row_number}_10")],
            [InlineKeyboardButton("15", callback_data=f"admin_set_min_row_{row_number}_15"), InlineKeyboardButton("20", callback_data=f"admin_set_min_row_{row_number}_20")],
        ]
        await query.message.reply_text("Выберите новый порог складчины:", reply_markup=InlineKeyboardMarkup(kb))
    elif query.data.startswith("admin_set_min_row_"):
        if query.from_user.id != ADMIN_TELEGRAM_ID:
            await query.message.reply_text("❌ Недоступно")
            return
        parts = query.data.split("_")
        row_number = int(parts[4])
        minimum = int(parts[5])
        sheets_client.set_collective_minimum(row_number, minimum)
        await query.message.reply_text(f"✅ Порог складчины обновлён: {minimum}")


async def browse_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Просмотр каталога с фильтрами
    """
    query = update.callback_query
    
    loading_msg = await query.message.reply_text("⏳ Загрузка каталога...")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{API_BASE_URL}/api/records?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])
                
                await loading_msg.delete()
                
                if not records:
                    await query.message.reply_text(
                        "📭 <b>Каталог пуст</b>\n\n"
                        "Пока нет доступных пластинок.\n"
                        "Станьте первым - добавьте свою!",
                        parse_mode='HTML'
                    )
                    return
                
                # Показываем первые 5 записей
                for idx, record in enumerate(records, 1):
                    keyboard = [
                        [InlineKeyboardButton("📖 Подробнее", callback_data=f"view_{record['id']}")],
                        [InlineKeyboardButton("🛒 Забронировать", callback_data=f"book_{record['id']}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    price_rub = record['price']
                    
                    message = f"""
🎵 <b>{record['title']}</b>
🎤 {record['artist']}

📀 <b>Детали:</b>
• Жанр: {record['genre']}
• Год: {record['year']}
• Страна: {record['country']}
• Состояние: {record['condition']}

💰 <b>Цена: {price_rub} ₽</b>
"""
                    
                    await query.message.reply_text(
                        message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                
                # Кнопка "Показать ещё"
                keyboard = [[InlineKeyboardButton("➡️ Показать ещё", callback_data="load_more")]]
                await query.message.reply_text(
                    f"Показано: {len(records)} из {data.get('total', 0)}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # Fallback: показать каталог из Google Sheets
                try:
                    worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
                    records = worksheet.get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес'])
                    await loading_msg.delete()
                    if not records:
                        await query.message.reply_text(
                            "📭 <b>Каталог пуст</b>\n\n"
                            "Добавьте первую запись через кнопку.",
                            parse_mode='HTML'
                        )
                        return
                    for idx, rec in enumerate(records[:5], 1):
                        row_number = idx + 1  # данные начинаются со 2 строки
                        price = rec.get('Цена', 0)
                        msg = (
                            f"🎵 <b>{rec.get('Название','')}</b>\n"
                            f"🎤 {rec.get('Исполнитель','')}\n\n"
                            f"💰 <b>Цена: {price} ₽</b>"
                        )
                        keyboard = [
                            [InlineKeyboardButton("🤝 Участвовать в складчине", callback_data=f"collect_join_row_{row_number}")],
                            [InlineKeyboardButton("🛒 Купить сейчас по рыночной цене", callback_data=f"buy_row_{row_number}")],
                            [InlineKeyboardButton("📖 История и подробности", callback_data=f"details_row_{row_number}")]
                        ]
                        await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
                except Exception as e:
                    logger.error(f"Каталог fallback из Sheets: {e}")
                    await loading_msg.edit_text("❌ Ошибка загрузки каталога.\nПопробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка загрузки каталога: {e}")
        # Fallback: открыть данные из Google Sheets
        try:
            worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
            records = worksheet.get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес'])
            await loading_msg.delete()
            if not records:
                await query.message.reply_text(
                    "📭 <b>Каталог пуст</b>\n\n"
                    "Добавьте первую запись через кнопку.",
                    parse_mode='HTML'
                )
            else:
                for idx, rec in enumerate(records[:5], 1):
                    row_number = idx + 1
                    price = rec.get('Цена', 0)
                    msg = (
                        f"🎵 <b>{rec.get('Название','')}</b>\n"
                        f"🎤 {rec.get('Исполнитель','')}\n\n"
                        f"💰 <b>Цена: {price} ₽</b>"
                    )
                    keyboard = [
                        [InlineKeyboardButton("🤝 Участвовать в складчине", callback_data=f"collect_join_row_{row_number}")],
                        [InlineKeyboardButton("🛒 Купить сейчас по рыночной цене", callback_data=f"buy_row_{row_number}")],
                        [InlineKeyboardButton("📖 История и подробности", callback_data=f"details_row_{row_number}")]
                    ]
                    await query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        except Exception as e2:
            logger.error(f"Ошибка fallback из Sheets: {e2}")
            await loading_msg.edit_text(
                "❌ <b>Ошибка подключения</b>\n\n"
                "Не удалось загрузить каталог.\n"
                "Проверьте соединение и попробуйте снова.",
                parse_mode='HTML'
            )


async def show_my_records_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показ своих записей через inline
    """
    query = update.callback_query
    user_id = query.from_user.id
    
    loading_msg = await query.message.reply_text("⏳ Загрузка ваших пластинок...")
    
    try:
        worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        all_records = worksheet.get_all_records(expected_headers=['Название','Исполнитель','Жанр','Год','Лейбл','Страна','Состояние','Цена','ФОТО_URL','Продавец_TG_ID','Статус','Описание','Минимум_складчиков','Складчина_участников','Цена_ориентир','Последний_интерес'])
        
        user_records = [r for r in all_records if r.get('Продавец_TG_ID') == user_id]
        
        await loading_msg.delete()
        
        if not user_records:
            await query.message.reply_text(
                "📭 <b>У вас пока нет пластинок</b>\n\n"
                "Напишите название пластинки — создам карточку и предложу складчину или предзаказ.",
                parse_mode='HTML'
            )
            return
        
        message = f"📊 <b>Ваши пластинки ({len(user_records)})</b>\n\n"
        
        for idx, record in enumerate(user_records[:10], 1):
            status = record.get('Статус', '')
            status_emoji = "🟢" if "Доступна" in status else "🟡" if "Зарезервирована" in status else "🔴"
            
            message += (
                f"{idx}. {status_emoji} <b>{record.get('Название')}</b>\n"
                f"   {record.get('Исполнитель')} • {record.get('Цена')} ₽\n\n"
            )
        
        if len(user_records) > 10:
            message += f"... и ещё {len(user_records) - 10}"
        
        await query.message.reply_text(message, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка получения записей: {e}")
        await loading_msg.edit_text(
            "❌ Ошибка загрузки данных",
            parse_mode='HTML'
        )


async def show_help_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Помощь через inline
    """
    query = update.callback_query
    
    help_text = """
🎵 <b>Справка по боту</b>

<b>Кнопки:</b>
• Каталог — смотреть записи
• Мои пластинки — ваши записи
• Помощь — справка

<b>Как купить:</b>
Откройте карточку и используйте «🤝 Складчина» или «🛒 Предзаказ».

<b>AI‑описания</b> и защита от дубликатов фото уже включены.
"""
    
    keyboard = [[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def show_record_for_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, record_id: str):
    """Показ записи для бронирования"""
    # Здесь будет логика показа записи и кнопки бронирования
    # Упрощённая версия для MVP
    await update.message.reply_text(
        "📀 Детали пластинки будут здесь\n\n"
        "Функция бронирования в разработке."
    )


async def auto_create_preorder_card(update: Update, context: ContextTypes.DEFAULT_TYPE, search_query: str):
    """
    Автоматическое создание карточки предзаказа с AI-описанием
    
    Когда пользователь ищет пластинку которой нет в каталоге — 
    автоматически создаём карточку, запускаем AI и показываем для редактирования
    """
    user = update.effective_user
    
    # Показываем статус создания
    status_msg = await update.message.reply_text(
        f"🤖 <b>Создаю карточку:</b> {search_query}\n\n"
        "⏳ AI-музыковед ищет информацию...",
        parse_mode='HTML'
    )
    
    try:
        # Парсим запрос (пытаемся извлечь исполнителя и название)
        parts = search_query.split(' - ', 1)
        if len(parts) == 2:
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            # Если нет разделителя, используем весь запрос как название
            title = search_query.strip()
            artist = "Неизвестен"
        
        # Создаём запись в каталоге со статусом "Предзаказ"
        record_data = {
            'title': title,
            'artist': artist,
            'genre': '',
            'year': '',
            'label': '',
            'country': '',
            'condition': '',
            'price': 0,
            'photo_url': '',
            'seller_tg_id': user.id,
            'stock_count': 0,  # Нет в наличии
            'status': '🟡 Предзаказ'  # Статус предзаказа
        }
        
        row_number = sheets_client.add_record(record_data)
        
        # Обновляем статус на "Предзаказ"
        sheets_client.update_status(row_number, '🟡 Предзаказ')
        
        # Обновляем статус сообщения
        await status_msg.edit_text(
            f"✅ <b>Карточка создана!</b>\n\n"
            f"🎵 {title}\n"
            f"🎤 {artist}\n\n"
            "⏳ Генерирую AI-описание...",
            parse_mode='HTML'
        )
        
        # Запускаем AI-генерацию описания
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/generate-description",
                    json={
                        "record_id": f"row_{row_number}",
                        "title": title,
                        "artist": artist,
                        "year": 0,
                        "genre": "Не указан",
                        "label": None,
                        "country": None
                    }
                )
                ai_result = response.json()
                description = ai_result.get('description', '')
                
                if description:
                    logger.info(f"AI-описание сгенерировано для строки {row_number}")
        except Exception as ai_error:
            logger.warning(f"Не удалось сгенерировать AI-описание: {ai_error}")
        
        # Получаем артикул созданной записи
        article_id = f"VIN-{row_number - 1:05d}"
        
        # Удаляем статусное сообщение
        await status_msg.delete()
        
        # Показываем карточку для редактирования
        message = (
            f"✅ <b>Карточка создана для предзаказа!</b>\n\n"
            f"📀 <b>{title}</b>\n"
            f"🎤 <i>{artist}</i>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔖 Артикул: <code>{article_id}</code>\n"
            f"🟡 Статус: Предзаказ\n"
            f"👤 Заявка от: {user.first_name}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✏️ <b>Уточните данные:</b>\n"
            f"Используйте кнопки ниже для редактирования"
        )
        
        # Кнопки редактирования
        keyboard = [
            [
                InlineKeyboardButton("✏️ Цена", callback_data=f"admin_edit_price_{row_number}"),
                InlineKeyboardButton("🔄 Статус", callback_data=f"admin_edit_status_{row_number}")
            ],
            [
                InlineKeyboardButton("🎵 Жанр", callback_data=f"admin_edit_genre_{row_number}"),
                InlineKeyboardButton("🎭 Лейбл", callback_data=f"admin_edit_label_{row_number}")
            ],
            [
                InlineKeyboardButton("📅 Год", callback_data=f"admin_edit_year_{row_number}"),
                InlineKeyboardButton("🌍 Страна", callback_data=f"admin_edit_country_{row_number}")
            ],
            [
                InlineKeyboardButton("📖 AI-описание", callback_data=f"ai_description_{row_number}")
            ]
        ]
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        logger.info(f"Авто-создана карточка предзаказа: {title} - {artist}, строка {row_number}")
        
    except Exception as e:
        logger.error(f"Ошибка авто-создания карточки: {e}")
        await status_msg.edit_text(
            f"❌ Не удалось создать карточку: {search_query}\n\n"
            "Попробуйте добавить вручную через кнопку '➕ Добавить'"
        )


async def handle_free_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Глобальный обработчик свободного текста: поиск/заявка/карточка"""
    text = update.message.text.strip()
    user = update.effective_user
    
    # Обработка кнопки "➕ Добавить" из постоянной клавиатуры
    if text == "➕ Добавить":
        # Очищаем context.user_data перед началом добавления
        context.user_data.clear()
        return await add_record_start(update, context)
    
    # Обработка кнопки "📋 Меню" из постоянной клавиатуры
    if text == "📋 Меню":
        welcome_message = f"""
👋 Привет, {user.first_name}!

📋 <b>Меню управления</b>

📊 <b>Что можно сделать:</b>

• <b>➕ Добавить пластинку</b> - добавить в каталог
• <b>📊 Статистика</b> - инфо по складу
• <b>🌐 Обновить сайт</b> - экспорт для balt-set.ru

🔍 <b>Поиск:</b>
Просто напиши артикул или название в чате
"""
        keyboard = [
            [
                InlineKeyboardButton("➕ Добавить пластинку", callback_data="start_add_record"),
            ],
            [
                InlineKeyboardButton("📊 Статистика", callback_data="statistics"),
                InlineKeyboardButton("🌐 Обновить сайт", callback_data="admin_export_site"),
            ],
        ]
        
        # Отправляем картинку с текстом
        photo_url = "https://drive.google.com/uc?export=view&id=1B3JgQA2KBd3CW0Ey9s-POs2-YxcwFxds"
        try:
            await update.message.reply_photo(
                photo=photo_url,
                caption=welcome_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        except Exception as e:
            logger.warning(f"Не удалось загрузить картинку: {e}")
            await update.message.reply_text(
                welcome_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        return
    
    # Проверка режимов админ-редактирования
    if 'admin_edit_price_row' in context.user_data:
        row_number = context.user_data['admin_edit_price_row']
        try:
            new_price = float(text)
            if new_price <= 0:
                await update.message.reply_text(
                    "❌ Цена должна быть больше 0.\n"
                    "Попробуйте ещё раз:"
                )
                return
            sheets_client.update_price(row_number, new_price)
            await update.message.reply_text(f"✅ Цена обновлена: {new_price} ₽")
            del context.user_data['admin_edit_price_row']
            return
        except ValueError:
            await update.message.reply_text(
                "❌ Введите корректное число.\n"
                "Попробуйте ещё раз:"
            )
            return
        except Exception as e:
            logger.error(f"Ошибка обновления цены: {e}")
            await update.message.reply_text("❌ Ошибка обновления цены")
            del context.user_data['admin_edit_price_row']
            return
    
    if 'admin_edit_stock_row' in context.user_data:
        row_number = context.user_data['admin_edit_stock_row']
        try:
            new_stock = int(text)
            if new_stock < 0:
                await update.message.reply_text(
                    "❌ Количество не может быть отрицательным.\n"
                    "Попробуйте ещё раз:"
                )
                return
            sheets_client.update_stock(row_number, new_stock)
            status_info = ""
            if new_stock == 0:
                status_info = "\n📌 Статус автоматически изменён на '🔴 Продана'"
            await update.message.reply_text(f"✅ Остаток обновлён: {new_stock} шт.{status_info}")
            del context.user_data['admin_edit_stock_row']
            return
        except ValueError:
            await update.message.reply_text(
                "❌ Введите целое число.\n"
                "Попробуйте ещё раз:"
            )
            return
        except Exception as e:
            logger.error(f"Ошибка обновления остатка: {e}")
            await update.message.reply_text("❌ Ошибка обновления остатка")
            del context.user_data['admin_edit_stock_row']
            return
    
    # 1) Попытка интерпретировать ввод как артикул
    article_candidate = text.strip().upper()
    if article_candidate.isdigit():
        article_candidate = f"VIN-{int(article_candidate):05d}"

    record_by_article = None
    try:
        record_by_article = sheets_client.find_record_by_article(article_candidate)
    except Exception as e:
        logger.error(f"Ошибка поиска по артикулу в handle_free_text: {e}")

    if record_by_article:
        await show_record_card(update, context, record_by_article)
        return

    # 2) Поиск пластинки по названию/исполнителю
    loading_msg = await update.message.reply_text("⏳ Ищу пластинку...")

    try:
        results = sheets_client.find_records_by_query(text)
        await loading_msg.delete()
        
        if results:
            # Показ первых 3 совпадений с админ-кнопками
            for rec in results[:3]:
                row_number = rec.get('_row_number', 0)
                price = rec.get('Цена', 0)
                stock = rec.get('Stock_Count', 1)
                status = rec.get('Статус', '🟢 Доступна')
                
                message = (
                    f"🎵 <b>{rec.get('Название','')}</b>\n"
                    f"🎤 {rec.get('Исполнитель','')}\n\n"
                    f"🔖 Артикул: <code>{rec.get('Артикул','')}</code>\n"
                    f"📀 Жанр: {rec.get('Жанр','')}\n"
                    f"📅 Год: {rec.get('Год','')}\n"
                    f"🌍 Страна: {rec.get('Страна','')}\n"
                    f"💿 Состояние: {rec.get('Состояние','')}\n\n"
                    f"💰 <b>Цена: {price:,.0f} ₽</b>\n"
                    f"📦 Остаток: {stock} шт.\n"
                    f"📍 Статус: {status}"
                )
                
                # Админ-кнопки
                keyboard = [
                    [
                        InlineKeyboardButton("✏️ Цена", callback_data=f"admin_edit_price_{row_number}"),
                        InlineKeyboardButton("🔄 Статус", callback_data=f"admin_edit_status_{row_number}")
                    ],
                    [
                        InlineKeyboardButton("📦 Остаток", callback_data=f"admin_edit_stock_{row_number}"),
                        InlineKeyboardButton("📖 AI-описание", callback_data=f"ai_description_{row_number}")
                    ]
                ]

                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
        else:
            # Не нашли — АВТОМАТИЧЕСКИ создаём карточку с AI-описанием
            await auto_create_preorder_card(update, context, text)
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        try:
            await loading_msg.delete()
        except:
            pass
        await update.message.reply_text("❌ Ошибка поиска. Попробуйте ещё раз.")



def main():
    """Запуск бота"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Обработчик добавления записи
    add_record_handler = ConversationHandler(
        entry_points=[
            CommandHandler('add_record', add_record_start),
            CallbackQueryHandler(add_record_start, pattern='^start_add_record$')
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            ARTIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_artist)],
            GENRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_genre)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_year)],
            LABEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_label)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
            CONDITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_condition)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_chat=True,
        per_user=True,
        per_message=False,  # Исправление PTBUserWarning
        allow_reentry=True,
    )
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("my_records", my_records))
    application.add_handler(add_record_handler)
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Обработчик inline кнопок
    application.add_handler(CallbackQueryHandler(button_handler))
    # Глобальный обработчик текста
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_free_text))
    
    # Глобальный обработчик ошибок (внутри main)
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        try:
            raise context.error
        except Conflict:
            logger.warning("Конфликт получения обновлений: другой процесс бота активен.")
        except Exception as e:
            logger.error(f"Глобальная ошибка: {e}")
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Запуск Telegram бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
