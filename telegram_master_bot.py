"""
Telegram бот для мастеров - AI Service Platform
Терминал для приёма и обработки заказов
Вдохновлён promo_bot_klg и vinyl_bot с применением принципов Donald Norman UX
"""
import os
import logging
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_MASTER_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "https://heallshoking-ai-service-platform-mvp-11-12-2025-2f94.twc1.net")

# Состояния диалога регистрации
REG_NAME, REG_PHONE, REG_CITY, REG_SPECIALIZATIONS, REG_CONFIRM = range(5)

# Кэш состояния мастеров
master_cache: Dict[int, Dict[str, Any]] = {}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_status_emoji(status: str) -> str:
    """Эмодзи для статусов (Norman UX: визуальная обратная связь)"""
    status_map = {
        'pending': '🟡',
        'accepted': '🟢',
        'in_progress': '⚙️',
        'completed': '✅',
        'cancelled': '🔴'
    }
    return status_map.get(status, '❓')

def get_status_text(status: str) -> str:
    """Читаемое название статуса"""
    status_names = {
        'pending': 'Ожидает',
        'accepted': 'Принят',
        'in_progress': 'В работе',
        'completed': 'Завершён',
        'cancelled': 'Отменён'
    }
    return status_names.get(status, status)

def format_price(amount: float) -> str:
    """Форматирование цены (минималистичное)"""
    return f"{amount:,.0f} ₽".replace(',', ' ')

async def get_master_info(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Получить информацию о мастере из API по Telegram ID"""
    try:
        async with httpx.AsyncClient() as client:
            # Сначала пробуем получить по telegram_id через query параметр
            response = await client.get(
                f"{API_URL}/api/v1/masters",
                params={"telegram_id": telegram_id},
                timeout=10.0
            )
            
            if response.status_code == 200:
                masters = response.json()
                if masters and len(masters) > 0:
                    return masters[0]
            return None
    except Exception as e:
        logger.error(f"Ошибка получения информации о мастере: {e}")
        return None

async def get_available_jobs(city: str = None) -> list:
    """Получить доступные заказы"""
    try:
        params = {"status": "pending"}
        if city:
            params["city"] = city
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/v1/jobs",
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        logger.error(f"Ошибка получения заказов: {e}")
        return []

async def get_my_jobs(master_id: int) -> list:
    """Получить заказы мастера"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/v1/masters/{master_id}/jobs",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        logger.error(f"Ошибка получения заказов мастера: {e}")
        return []

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начальное меню (Norman UX: минималистичный интерфейс)"""
    user = update.effective_user
    
    # Проверка регистрации
    master = await get_master_info(user.id)
    
    if not master:
        # Мастер не зарегистрирован - предложить регистрацию
        keyboard = ReplyKeyboardMarkup(
            [["\u2705 \u0417арегистрироваться"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await update.message.reply_text(
            "\ud83d\udc4b \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c \u0432 <b>\u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b \u043c\u0430\u0441\u0442\u0435\u0440\u0430</b>!\n\n"
            "\ud83d\udd27 \u0417\u0434\u0435\u0441\u044c \u0432\u044b \u0441\u043c\u043e\u0436\u0435\u0442\u0435:\n"
            "\u2022 \u041f\u0440\u0438\u043d\u0438\u043c\u0430\u0442\u044c \u0437\u0430\u043a\u0430\u0437\u044b \u043e\u0442 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u0432\n"
            "\u2022 \u0423\u043f\u0440\u0430\u0432\u043b\u044f\u0442\u044c \u0441\u0432\u043e\u0438\u043c\u0438 \u0437\u0430\u043a\u0430\u0437\u0430\u043c\u0438\n"
            "\u2022 \u041f\u043e\u043b\u0443\u0447\u0430\u0442\u044c \u0441\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0443 \u0438 \u043e\u043f\u043b\u0430\u0442\u0443\n\n"
            "\u26a0\ufe0f \u0412\u044b \u0435\u0449\u0451 \u043d\u0435 \u0437\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u044b.\n"
            "\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f \u0437\u0430\u0439\u043c\u0451\u0442 \u0432\u0441\u0435\u0433\u043e 2 \u043c\u0438\u043d\u0443\u0442\u044b!",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return
    
    # С\u043e\u0445\u0440\u0430\u043d\u044f\u0435\u043c \u0432 \u043a\u044d\u0448
    master_cache[user.id] = master
    
    # \u041f\u043e\u0441\u0442\u043e\u044f\u043d\u043d\u0430\u044f \u043a\u043b\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u0430 (Norman UX: \u0432\u0441\u0435\u0433\u0434\u0430 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f)
    keyboard = ReplyKeyboardMarkup(
        [
            ["\ud83c\udd95 \u041d\u043e\u0432\u044b\u0435 \u0437\u0430\u043a\u0430\u0437\u044b", "\ud83d\udccb \u041c\u043e\u0438 \u0437\u0430\u043a\u0430\u0437\u044b"],
            ["\ud83d\udcb0 \u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430", "\u2699\ufe0f \u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b"]
        ],
        resize_keyboard=True
    )
    
    welcome_message = (
        f"\ud83d\udc4b \u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439\u0442\u0435, {master.get('full_name')}!\n\n"
        f"\ud83d\udd27 <b>\u0422\u0435\u0440\u043c\u0438\u043d\u0430\u043b \u043c\u0430\u0441\u0442\u0435\u0440\u0430</b>\n\n"
        f"\ud83d\udccd \u0413\u043e\u0440\u043e\u0434: {master.get('city')}\n"
        f"\u2b50 \u0420\u0435\u0439\u0442\u0438\u043d\u0433: {master.get('rating', 5.0):.1f}/5.0\n\n"
        f"\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 \u043a\u043d\u043e\u043f\u043a\u0438 \u043d\u0438\u0436\u0435 \u0434\u043b\u044f \u0440\u0430\u0431\u043e\u0442\u044b:"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def show_new_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать новые доступные заказы"""
    user = update.effective_user
    
    # Получаем информацию о мастере
    master = master_cache.get(user.id)
    if not master:
        master = await get_master_info(user.id)
        if not master:
            await update.message.reply_text("❌ Ошибка: мастер не найден")
            return
        master_cache[user.id] = master
    
    # Loading индикатор
    loading = await update.message.reply_text("🔍 Поиск заказов...")
    
    # Получаем доступные заказы
    jobs = await get_available_jobs(city=master.get('city'))
    
    await loading.delete()
    
    if not jobs:
        await update.message.reply_text(
            "📭 Новых заказов пока нет.\n"
            "Я уведомлю вас, когда появятся!"
        )
        return
    
    # Показываем карточки заказов
    for job in jobs[:5]:  # Максимум 5 заказов
        await show_job_card(update, context, job, is_new=True)
    
    if len(jobs) > 5:
        await update.message.reply_text(
            f"📊 Показано 5 из {len(jobs)} заказов.\n"
            "Примите текущие, чтобы увидеть следующие."
        )

async def show_my_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои заказы"""
    user = update.effective_user
    
    master = master_cache.get(user.id)
    if not master:
        await update.message.reply_text("❌ Ошибка: мастер не найден")
        return
    
    loading = await update.message.reply_text("📋 Загрузка ваших заказов...")
    
    jobs = await get_my_jobs(master['id'])
    
    await loading.delete()
    
    if not jobs:
        await update.message.reply_text(
            "📭 У вас пока нет активных заказов.\n\n"
            "Нажмите <b>🆕 Новые заказы</b> чтобы принять работу!",
            parse_mode='HTML'
        )
        return
    
    # Группируем по статусам
    active = [j for j in jobs if j['status'] in ['accepted', 'in_progress']]
    completed = [j for j in jobs if j['status'] == 'completed']
    
    if active:
        await update.message.reply_text(f"<b>⚙️ Активные заказы ({len(active)}):</b>", parse_mode='HTML')
        for job in active:
            await show_job_card(update, context, job, is_new=False)
    
    if completed:
        await update.message.reply_text(f"<b>✅ Завершённые ({len(completed)}):</b>", parse_mode='HTML')
        for job in completed[:3]:  # Только последние 3
            await show_job_card(update, context, job, is_new=False)

async def show_job_card(update: Update, context: ContextTypes.DEFAULT_TYPE, job: dict, is_new: bool = False):
    """
    Показать карточку заказа (Norman UX: минималистичный дизайн)
    
    Args:
        job: Данные заказа
        is_new: True если это новый доступный заказ (не принятый)
    """
    status = job.get('status', 'pending')
    status_emoji = get_status_emoji(status)
    status_text = get_status_text(status)
    
    # Форматирование (без placeholder, только факты)
    message = (
        f"{status_emoji} <b>Заказ #{job.get('id')}</b>\n\n"
        f"📋 {job.get('category_name', job.get('category', ''))}\n"
        f"📝 {job.get('problem_description', '')}\n\n"
        f"👤 {job.get('client_name', '')}\n"
        f"📱 {job.get('client_phone', '')}\n"
        f"📍 {job.get('address', '')}\n\n"
        f"💰 Примерно: {format_price(job.get('estimated_price', 0))}\n"
        f"📅 {job.get('created_at', '')}"
    )
    
    # Кнопки зависят от статуса (Norman UX: действия зависят от контекста)
    keyboard = []
    
    if is_new:
        # Новый заказ - можно принять
        keyboard.append([
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{job['id']}")
        ])
    else:
        # Мой заказ - можно обновить статус
        if status == 'accepted':
            keyboard.append([
                InlineKeyboardButton("🚀 Начать работу", callback_data=f"start_{job['id']}")
            ])
            keyboard.append([
                InlineKeyboardButton("❌ Отказаться", callback_data=f"cancel_{job['id']}")
            ])
        elif status == 'in_progress':
            keyboard.append([
                InlineKeyboardButton("✅ Завершить", callback_data=f"complete_{job['id']}")
            ])
        elif status == 'completed':
            keyboard.append([
                InlineKeyboardButton("📞 Связаться с клиентом", url=f"tel:{job.get('client_phone', '')}")
            ])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику мастера"""
    user = update.effective_user
    
    master = master_cache.get(user.id)
    if not master:
        await update.message.reply_text("❌ Ошибка: мастер не найден")
        return
    
    loading = await update.message.reply_text("📊 Загрузка статистики...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/v1/masters/{master['id']}/statistics",
                timeout=10.0
            )
            
            await loading.delete()
            
            if response.status_code == 200:
                stats = response.json()
                
                message = (
                    f"📊 <b>Статистика</b>\n\n"
                    f"✅ Завершено заказов: {stats.get('completed_jobs', 0)}\n"
                    f"💰 Общий заработок: {format_price(stats.get('total_earnings', 0))}\n"
                    f"⭐ Средняя оценка: {stats.get('average_rating', 5.0):.1f}/5.0\n\n"
                    f"<b>За сегодня:</b>\n"
                    f"• Заказов: {stats.get('today_jobs', 0)}\n"
                    f"• Заработано: {format_price(stats.get('today_earnings', 0))}\n\n"
                    f"<b>За месяц:</b>\n"
                    f"• Заказов: {stats.get('month_jobs', 0)}\n"
                    f"• Заработано: {format_price(stats.get('month_earnings', 0))}"
                )
                
                await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text("❌ Не удалось загрузить статистику")
    
    except Exception as e:
        await loading.delete()
        logger.error(f"Ошибка получения статистики: {e}")
        await update.message.reply_text("❌ Произошла ошибка")

async def toggle_terminal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Включить/выключить терминал (приём заказов)"""
    user = update.effective_user
    
    master = master_cache.get(user.id)
    if not master:
        await update.message.reply_text("❌ Ошибка: мастер не найден")
        return
    
    # Переключаем статус
    current_status = master.get('terminal_active', False)
    new_status = not current_status
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{API_URL}/api/v1/masters/{master['id']}/terminal",
                json={"terminal_active": new_status},
                timeout=10.0
            )
            
            if response.status_code == 200:
                master['terminal_active'] = new_status
                master_cache[user.id] = master
                
                if new_status:
                    message = (
                        "✅ <b>Терминал включён!</b>\n\n"
                        "Вы будете получать уведомления о новых заказах."
                    )
                else:
                    message = (
                        "⏸️ <b>Терминал выключен</b>\n\n"
                        "Вы не будете получать новые заказы до включения."
                    )
                
                await update.message.reply_text(message, parse_mode='HTML')
            else:
                await update.message.reply_text("❌ Не удалось изменить статус терминала")
    
    except Exception as e:
        logger.error(f"Ошибка переключения терминала: {e}")
        await update.message.reply_text("❌ Произошла ошибка")

# ==================== ОБРАБОТЧИКИ CALLBACK ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на inline кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = update.effective_user
    
    master = master_cache.get(user.id)
    if not master:
        await query.message.reply_text("❌ Ошибка: мастер не найден")
        return
    
    # Парсим действие
    if data.startswith("accept_"):
        job_id = int(data.split("_")[1])
        await accept_job(query, context, job_id, master['id'])
    
    elif data.startswith("start_"):
        job_id = int(data.split("_")[1])
        await start_job(query, context, job_id)
    
    elif data.startswith("complete_"):
        job_id = int(data.split("_")[1])
        await complete_job(query, context, job_id)
    
    elif data.startswith("cancel_"):
        job_id = int(data.split("_")[1])
        await cancel_job(query, context, job_id)

async def accept_job(query, context, job_id: int, master_id: int):
    """Принять заказ"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/api/v1/jobs/{job_id}/assign",
                json={"master_id": master_id},
                timeout=10.0
            )
            
            if response.status_code == 200:
                # Обновляем сообщение
                await query.edit_message_text(
                    f"{query.message.text}\n\n✅ <b>Заказ принят!</b>\n"
                    "Свяжитесь с клиентом в ближайшее время.",
                    parse_mode='HTML'
                )
            else:
                await query.message.reply_text("❌ Не удалось принять заказ")
    
    except Exception as e:
        logger.error(f"Ошибка принятия заказа: {e}")
        await query.message.reply_text("❌ Произошла ошибка")

async def start_job(query, context, job_id: int):
    """Начать работу"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{API_URL}/api/v1/jobs/{job_id}/status",
                json={"status": "in_progress"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                await query.edit_message_text(
                    f"{query.message.text}\n\n⚙️ <b>Работа начата!</b>",
                    parse_mode='HTML'
                )
            else:
                await query.message.reply_text("❌ Не удалось обновить статус")
    
    except Exception as e:
        logger.error(f"Ошибка начала работы: {e}")
        await query.message.reply_text("❌ Произошла ошибка")

async def complete_job(query, context, job_id: int):
    """Завершить заказ"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{API_URL}/api/v1/jobs/{job_id}/status",
                json={"status": "completed"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                await query.edit_message_text(
                    f"{query.message.text}\n\n✅ <b>Заказ завершён!</b>\n"
                    "Отличная работа! 🎉",
                    parse_mode='HTML'
                )
            else:
                await query.message.reply_text("❌ Не удалось завершить заказ")
    
    except Exception as e:
        logger.error(f"Ошибка завершения заказа: {e}")
        await query.message.reply_text("❌ Произошла ошибка")

async def cancel_job(query, context, job_id: int):
    """Отменить заказ"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{API_URL}/api/v1/jobs/{job_id}/status",
                json={"status": "cancelled"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                await query.edit_message_text(
                    f"{query.message.text}\n\n🔴 <b>Заказ отменён</b>",
                    parse_mode='HTML'
                )
            else:
                await query.message.reply_text("❌ Не удалось отменить заказ")
    
    except Exception as e:
        logger.error(f"Ошибка отмены заказа: {e}")
        await query.message.reply_text("❌ Произошла ошибка")

# ==================== ОБРАБОТЧИКИ ТЕКСТОВЫХ КОМАНД ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых команд с кнопок"""
    text = update.message.text
    
    if text == "🆕 Новые заказы":
        await show_new_jobs(update, context)
    
    elif text == "📋 Мои заказы":
        await show_my_jobs(update, context)
    
    elif text == "💰 Статистика":
        await show_statistics(update, context)
    
    elif text == "⚙️ Терминал":
        await toggle_terminal(update, context)
    
    else:
        await update.message.reply_text(
            "❓ Используйте кнопки меню для навигации"
        )

# ==================== РЕГИСТРАЦИЯ МАСТЕРА ====================

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало регистрации"""
    await update.message.reply_text(
        "🎯 <b>Регистрация мастера</b>\n\n"
        "Отлично! Давайте заполним ваш профиль.\n\n"
        "Как вас зовут? (Имя и фамилия)",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='HTML'
    )
    return REG_NAME

async def reg_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить имя"""
    name = update.message.text
    
    if len(name) < 3:
        await update.message.reply_text(
            "❌ Слишком короткое имя. Укажите имя и фамилию:"
        )
        return REG_NAME
    
    context.user_data['reg_name'] = name
    
    await update.message.reply_text(
        f"✅ Приятно познакомиться, {name}!\n\n"
        "Укажите ваш номер телефона:\n"
        "(Формат: +79001234567)"
    )
    return REG_PHONE

async def reg_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить телефон"""
    phone = update.message.text
    
    # Валидация
    if not phone.startswith('+7') or len(phone) != 12:
        await update.message.reply_text(
            "❌ Неверный формат номера.\n"
            "Укажите в формате: +79001234567"
        )
        return REG_PHONE
    
    context.user_data['reg_phone'] = phone
    
    await update.message.reply_text(
        "📱 Номер принят!\n\n"
        "В каком городе вы работаете?\n"
        "(Например: Калининград)"
    )
    return REG_CITY

async def reg_get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить город"""
    city = update.message.text
    
    if len(city) < 2:
        await update.message.reply_text(
            "❌ Слишком короткое название. Укажите город:"
        )
        return REG_CITY
    
    context.user_data['reg_city'] = city
    
    # Клавиатура со специализациями
    keyboard = ReplyKeyboardMarkup(
        [
            ["⚡ Электрика", "🚰 Сантехника"],
            ["🔌 Бытовая техника", "🔨 Общие работы"],
            ["✅ Выбрал всё"]
        ],
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "🔧 Выберите ваши специализации\n"
        "(Можно выбрать несколько, потом нажмите \"✅ Выбрал всё\")",
        reply_markup=keyboard
    )
    
    context.user_data['reg_specializations'] = []
    return REG_SPECIALIZATIONS

async def reg_get_specializations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить специализации"""
    text = update.message.text
    
    if text == "✅ Выбрал всё":
        specs = context.user_data.get('reg_specializations', [])
        
        if not specs:
            await update.message.reply_text(
                "❌ Выберите хотя бы одну специализацию!"
            )
            return REG_SPECIALIZATIONS
        
        # Показать резюме
        data = context.user_data
        specs_text = ', '.join([s.replace('⚡ ', '').replace('🚰 ', '').replace('🔌 ', '').replace('🔨 ', '') for s in specs])
        
        summary = (
            "📋 <b>Проверьте ваши данные:</b>\n\n"
            f"👤 Имя: {data['reg_name']}\n"
            f"📱 Телефон: {data['reg_phone']}\n"
            f"📍 Город: {data['reg_city']}\n"
            f"🔧 Специализации: {specs_text}\n\n"
            "Всё верно?"
        )
        
        keyboard = ReplyKeyboardMarkup(
            [["✅ Да, всё верно", "❌ Нет, исправить"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await update.message.reply_text(
            summary,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return REG_CONFIRM
    
    # Добавить специализацию
    spec_map = {
        "⚡ Электрика": "electrical",
        "🚰 Сантехника": "plumbing",
        "🔌 Бытовая техника": "appliance",
        "🔨 Общие работы": "general"
    }
    
    if text in spec_map:
        specs = context.user_data.get('reg_specializations', [])
        
        if text not in specs:
            specs.append(text)
            context.user_data['reg_specializations'] = specs
            context.user_data[f'reg_spec_{spec_map[text]}'] = True
            
            await update.message.reply_text(
                f"✅ Добавлено: {text}\n"
                f"Выбрано: {len(specs)} специализаций"
            )
        else:
            await update.message.reply_text(
                f"⚠️ {text} уже добавлена!"
            )
    
    return REG_SPECIALIZATIONS

async def reg_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и создание мастера"""
    text = update.message.text
    
    if text == "❌ Нет, исправить":
        await update.message.reply_text(
            "❌ Регистрация отменена.\n"
            "Используйте /start чтобы начать заново.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Создать мастера
    data = context.user_data
    user = update.effective_user
    
    # Преобразовать специализации
    spec_map = {
        "⚡ Электрика": "electrical",
        "🚰 Сантехника": "plumbing",
        "🔌 Бытовая техника": "appliance",
        "🔨 Общие работы": "general"
    }
    
    specializations = []
    for spec in data.get('reg_specializations', []):
        if spec in spec_map:
            specializations.append(spec_map[spec])
    
    await update.message.reply_text(
        "⏳ Создаю ваш профиль...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_URL}/api/v1/masters/register",
                json={
                    "full_name": data['reg_name'],
                    "phone": data['reg_phone'],
                    "city": data['reg_city'],
                    "specializations": specializations,
                    "rating": 5.0
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                master_id = result.get('master_id')
                
                # Обновить Telegram ID мастера
                await client.patch(
                    f"{API_URL}/api/v1/masters/{master_id}",
                    json={"telegram_id": user.id},  # Сохраняем Telegram ID
                    timeout=10.0
                )
                
                await update.message.reply_text(
                    "🎉 <b>Регистрация завершена!</b>\n\n"
                    f"✅ Ваш ID: {master_id}\n"
                    f"👤 {data['reg_name']}\n"
                    f"📍 {data['reg_city']}\n\n"
                    "Теперь вы можете принимать заказы!\n"
                    "Используйте /start чтобы открыть терминал.",
                    parse_mode='HTML'
                )
                
                # Очистить данные регистрации
                context.user_data.clear()
                
                return ConversationHandler.END
            
            else:
                await update.message.reply_text(
                    f"❌ Ошибка регистрации: {response.status_code}\n"
                    f"{response.text}\n\n"
                    "Попробуйте ещё раз: /start"
                )
                return ConversationHandler.END
    
    except Exception as e:
        logger.error(f"Ошибка создания мастера: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при регистрации.\n"
            "Попробуйте позже или обратитесь к администратору."
        )
        return ConversationHandler.END

async def reg_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена регистрации"""
    await update.message.reply_text(
        "❌ Регистрация отменена.\n"
        "Используйте /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ==================== ЗАПУСК БОТА ====================

def main():
    """Запуск бота"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_MASTER_BOT_TOKEN не установлен!")
        return
    
    # Создать приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ConversationHandler для регистрации
    registration_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^✅ Зарегистрироваться$"), start_registration)
        ],
        states={
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_get_name)],
            REG_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_get_phone)],
            REG_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_get_city)],
            REG_SPECIALIZATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_get_specializations)],
            REG_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_confirm)],
        },
        fallbacks=[CommandHandler('cancel', reg_cancel)]
    )
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    
    # Регистрация
    application.add_handler(registration_handler)
    
    # Callback кнопки
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    logger.info("🤖 Telegram бот для мастеров запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
