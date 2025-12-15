"""
Модуль уведомления мастеров о новых заявках
БАЛТСЕТЬ - auto-assign система
"""
import os
import logging
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_MASTER_BOT_TOKEN = os.getenv("TELEGRAM_MASTER_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "https://heallshoking-ai-service-platform-mvp-11-12-2025-2f94.twc1.net")


async def notify_masters_about_new_order(
    order_id: int,
    category: str,
    problem: str,
    address: str,
    client_name: str,
    client_phone: str
):
    """Уведомить всех активных мастеров о новой заявке"""
    
    if not TELEGRAM_MASTER_BOT_TOKEN:
        logger.error("❌ TELEGRAM_MASTER_BOT_TOKEN не установлен!")
        return
    
    try:
        # Получаем список активных мастеров из API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/api/v1/masters",
                params={"status": "active"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Не удалось получить список мастеров: {response.status_code}")
                return
            
            masters = response.json()
            
            if not masters:
                logger.warning("⚠️ Нет активных мастеров для уведомления")
                return
            
            # Создаем экземпляр мастер-бота
            master_bot = Bot(token=TELEGRAM_MASTER_BOT_TOKEN)
            
            # Формируем МИЛОЕ сообщение о новой заявке
            time_now = datetime.now().strftime('%H:%M')
            notification_message = (
                f"🆕 <b>Новая заявка для вас!</b> 🚀\n\n"
                f"📋 <b>Заказ #{order_id}</b>\n"
                f"⏰ Время: {time_now}\n\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"🔧 <b>Категория:</b> {category}\n"
                f"💬 <b>Проблема:</b>\n{problem[:150]}{'...' if len(problem) > 150 else ''}\n\n"
                f"📍 <b>Адрес:</b> {address}\n\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"👤 <b>Клиент:</b> {client_name}\n"
                f"📞 <b>Телефон:</b> {client_phone}\n\n"
                f"🎯 <b>Будьте первым!</b> 🚀\n"
                f"💡 <i>Первый откликнувшийся получает заказ!</i>"
            )
            
            # Inline кнопка для принятия заявки - ЯРКАЯ И ПРИВЛЕКАТЕЛЬНАЯ
            keyboard = [[
                InlineKeyboardButton(
                    "✅ ПРИНЯТЬ ЗАКАЗ 🚀", 
                    callback_data=f"accept_{order_id}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем уведомление каждому мастеру
            notified_count = 0
            for master in masters:
                telegram_id = master.get('telegram_id')
                if telegram_id:
                    try:
                        # Отправляем с звуковым уведомлением
                        await master_bot.send_message(
                            chat_id=telegram_id,
                            text=notification_message,
                            parse_mode='HTML',
                            reply_markup=reply_markup,
                            disable_notification=False  # Звуковое уведомление!
                        )
                        notified_count += 1
                        logger.info(f"✅ Мастер {master.get('full_name')} уведомлен")
                    except Exception as e:
                        logger.error(f"❌ Ошибка отправки мастеру {master.get('full_name')}: {e}")
            
            logger.info(f"✅ Уведомлено мастеров: {notified_count}/{len(masters)}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка в notify_masters_about_new_order: {e}")


if __name__ == "__main__":
    # Тест
    import asyncio
    
    async def test():
        await notify_masters_about_new_order(
            order_id=999,
            category="⚡ Электрика",
            problem="Не работает розетка в гостиной",
            address="ул. Ленина, 10",
            client_name="Иван Тестовый",
            client_phone="+79001234567"
        )
    
    asyncio.run(test())
    print("✅ Тест завершен!")
