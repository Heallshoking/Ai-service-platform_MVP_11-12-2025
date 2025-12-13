"""
Notification Service - Multi-channel notification delivery
Сервис многоканальных уведомлений
"""
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json


class NotificationChannel(str, Enum):
    """Каналы доставки уведомлений"""
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


class NotificationType(str, Enum):
    """Типы уведомлений"""
    # Для клиентов
    REQUEST_RECEIVED = "request_received"
    MASTER_ASSIGNED = "master_assigned"
    MASTER_ON_WAY = "master_on_way"
    MASTER_ARRIVED = "master_arrived"
    JOB_COMPLETED = "job_completed"
    PAYMENT_CONFIRMED = "payment_confirmed"
    
    # Для мастеров
    NEW_JOB_ASSIGNED = "new_job_assigned"
    SCHEDULE_CONFIRMATION = "schedule_confirmation"
    PAYMENT_RECEIVED = "payment_received"
    DAILY_SUMMARY = "daily_summary"
    
    # Для админа
    ASSIGNMENT_FAILED = "assignment_failed"
    PAYMENT_ERROR = "payment_error"
    SYSTEM_ERROR = "system_error"


class NotificationTemplate:
    """Шаблон уведомления"""
    
    TEMPLATES = {
        # Клиенты
        NotificationType.REQUEST_RECEIVED: {
            "title": "Заявка принята",
            "message": "✅ Ваша заявка №{job_id} принята!\n\nМы подбираем мастера и свяжемся с вами в ближайшее время."
        },
        NotificationType.MASTER_ASSIGNED: {
            "title": "Мастер назначен",
            "message": "👨‍🔧 Мастер {master_name} назначен на ваш заказ №{job_id}!\n\n📍 Адрес: {address}\n⏰ Время: {scheduled_time}\n💰 Стоимость: {price}₽\n\nМастер свяжется с вами для уточнения деталей."
        },
        NotificationType.MASTER_ON_WAY: {
            "title": "Мастер выехал",
            "message": "🚗 Мастер {master_name} выехал к вам!\n\n📍 Адрес: {address}\n⏱ Ожидаемое время прибытия: {eta} мин"
        },
        NotificationType.MASTER_ARRIVED: {
            "title": "Мастер на месте",
            "message": "✅ Мастер {master_name} прибыл по адресу {address}"
        },
        NotificationType.JOB_COMPLETED: {
            "title": "Работа выполнена",
            "message": "✅ Работа выполнена!\n\nЗаказ №{job_id}\n💰 Оплачено: {amount}₽\n\nСпасибо что воспользовались нашим сервисом! 🙏"
        },
        NotificationType.PAYMENT_CONFIRMED: {
            "title": "Оплата получена",
            "message": "💳 Оплата {amount}₽ успешно получена.\n\nСпасибо за использование нашего сервиса!"
        },
        
        # Мастера
        NotificationType.NEW_JOB_ASSIGNED: {
            "title": "Новый заказ",
            "message": "🔔 Вам назначен новый заказ №{job_id}!\n\n📋 {category}\n📍 {address}\n💰 Ваш заработок: {earnings}₽\n⏰ {scheduled_time}\n\n👉 Откройте терминал для просмотра деталей."
        },
        NotificationType.SCHEDULE_CONFIRMATION: {
            "title": "Подтверждение расписания",
            "message": "📅 Подтвердите ваше расписание на сегодня\n\n⏰ {schedule}\n\n✅ Подтвердить /confirm\n❌ Изменить /change"
        },
        NotificationType.PAYMENT_RECEIVED: {
            "title": "Оплата зачислена",
            "message": "💰 Заработок зачислен!\n\nЗаказ №{job_id}\nСумма: {earnings}₽\n\n📊 Всего сегодня: {daily_total}₽"
        },
        NotificationType.DAILY_SUMMARY: {
            "title": "Итоги дня",
            "message": "📊 Ваши результаты за сегодня:\n\n✅ Выполнено заказов: {jobs_count}\n💰 Заработано: {total_earnings}₽\n⭐ Средняя оценка: {avg_rating}\n\nОтличная работа! 👏"
        },
        
        # Админ
        NotificationType.ASSIGNMENT_FAILED: {
            "title": "Ошибка назначения мастера",
            "message": "⚠️ Не удалось назначить мастера на заказ №{job_id}\n\nКатегория: {category}\nГород: {city}\nВремя: {time}\n\nТребуется ручное назначение."
        },
        NotificationType.PAYMENT_ERROR: {
            "title": "Ошибка оплаты",
            "message": "❌ Ошибка обработки оплаты\n\nЗаказ №{job_id}\nСумма: {amount}₽\nОшибка: {error}\n\nТребуется проверка."
        }
    }
    
    @classmethod
    def render(cls, notification_type: NotificationType, data: Dict[str, Any]) -> Dict[str, str]:
        """Рендер шаблона с данными"""
        template = cls.TEMPLATES.get(notification_type, {
            "title": "Уведомление",
            "message": str(data)
        })
        
        try:
            return {
                "title": template["title"].format(**data),
                "message": template["message"].format(**data)
            }
        except KeyError as e:
            # Если не хватает данных, вернуть шаблон как есть
            return {
                "title": template["title"],
                "message": template["message"] + f"\n\nДанные: {data}"
            }


class NotificationService:
    """Сервис уведомлений"""
    
    def __init__(self, db_connection, telegram_bot=None, sms_client=None, email_client=None):
        self.db = db_connection
        self.telegram_bot = telegram_bot
        self.sms_client = sms_client
        self.email_client = email_client
        self._init_notifications_table()
    
    def _init_notifications_table(self):
        """Инициализация таблицы уведомлений"""
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id TEXT NOT NULL,
                recipient_type TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                channel TEXT NOT NULL,
                title TEXT,
                message TEXT NOT NULL,
                data_json TEXT,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.db.commit()
    
    async def send_notification(
        self,
        recipient_id: str,
        recipient_type: str,  # 'client', 'master', 'admin'
        notification_type: NotificationType,
        data: Dict[str, Any],
        channels: List[NotificationChannel] = None
    ):
        """Отправить уведомление"""
        
        # Если каналы не указаны, определить автоматически
        if not channels:
            channels = await self._get_preferred_channels(recipient_id, recipient_type)
        
        # Рендер шаблона
        rendered = NotificationTemplate.render(notification_type, data)
        
        # Сохранить в БД
        notification_id = self._save_notification(
            recipient_id, recipient_type, notification_type,
            channels[0] if channels else NotificationChannel.TELEGRAM,
            rendered["title"], rendered["message"], data
        )
        
        # Отправить по всем каналам
        success = False
        errors = []
        
        for channel in channels:
            try:
                if channel == NotificationChannel.TELEGRAM:
                    await self._send_telegram(recipient_id, rendered["title"], rendered["message"])
                    success = True
                    break  # Если Telegram успешно, не пробуем другие
                elif channel == NotificationChannel.SMS:
                    await self._send_sms(recipient_id, rendered["message"])
                    success = True
                    break
                elif channel == NotificationChannel.EMAIL:
                    await self._send_email(recipient_id, rendered["title"], rendered["message"])
                    success = True
                    break
            except Exception as e:
                errors.append(f"{channel.value}: {str(e)}")
        
        # Обновить статус
        if success:
            self._update_notification_status(notification_id, "sent")
        else:
            self._update_notification_status(
                notification_id, "failed",
                error="; ".join(errors)
            )
        
        return success
    
    async def _get_preferred_channels(
        self,
        recipient_id: str,
        recipient_type: str
    ) -> List[NotificationChannel]:
        """Получить предпочитаемые каналы уведомлений"""
        # По умолчанию Telegram, потом SMS
        return [NotificationChannel.TELEGRAM, NotificationChannel.SMS]
    
    async def _send_telegram(self, recipient_id: str, title: str, message: str):
        """Отправить Telegram сообщение"""
        if not self.telegram_bot:
            raise Exception("Telegram bot not configured")
        
        full_message = f"<b>{title}</b>\n\n{message}"
        
        # Попытка отправить через Telegram bot
        try:
            await self.telegram_bot.send_message(
                chat_id=recipient_id,
                text=full_message,
                parse_mode="HTML"
            )
        except Exception as e:
            raise Exception(f"Telegram send failed: {str(e)}")
    
    async def _send_sms(self, phone: str, message: str):
        """Отправить SMS"""
        if not self.sms_client:
            raise Exception("SMS client not configured")
        
        # TODO: Интеграция с SMS провайдером (SMS.ru, Twilio, etc)
        # await self.sms_client.send(phone, message)
        raise Exception("SMS not implemented yet")
    
    async def _send_email(self, email: str, subject: str, message: str):
        """Отправить Email"""
        if not self.email_client:
            raise Exception("Email client not configured")
        
        # TODO: Интеграция с SMTP
        # await self.email_client.send(email, subject, message)
        raise Exception("Email not implemented yet")
    
    def _save_notification(
        self,
        recipient_id: str,
        recipient_type: str,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title: str,
        message: str,
        data: Dict
    ) -> int:
        """Сохранить уведомление в БД"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO notifications (
                recipient_id, recipient_type, notification_type,
                channel, title, message, data_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        """, (
            recipient_id, recipient_type, notification_type.value,
            channel.value, title, message, json.dumps(data, ensure_ascii=False)
        ))
        self.db.commit()
        return cursor.lastrowid
    
    def _update_notification_status(
        self,
        notification_id: int,
        status: str,
        error: str = None
    ):
        """Обновить статус уведомления"""
        cursor = self.db.cursor()
        
        if status == "sent":
            cursor.execute("""
                UPDATE notifications
                SET status = ?, sent_at = ?
                WHERE id = ?
            """, (status, datetime.now().isoformat(), notification_id))
        else:
            cursor.execute("""
                UPDATE notifications
                SET status = ?, error = ?
                WHERE id = ?
            """, (status, error, notification_id))
        
        self.db.commit()
    
    # Вспомогательные методы для частых уведомлений
    
    async def notify_client_request_received(self, client_phone: str, job_id: int):
        """Уведомить клиента о принятии заявки"""
        await self.send_notification(
            recipient_id=client_phone,
            recipient_type="client",
            notification_type=NotificationType.REQUEST_RECEIVED,
            data={"job_id": job_id}
        )
    
    async def notify_master_new_job(
        self,
        master_id: str,
        job_id: int,
        category: str,
        address: str,
        earnings: float,
        scheduled_time: str
    ):
        """Уведомить мастера о новом заказе"""
        await self.send_notification(
            recipient_id=master_id,
            recipient_type="master",
            notification_type=NotificationType.NEW_JOB_ASSIGNED,
            data={
                "job_id": job_id,
                "category": category,
                "address": address,
                "earnings": earnings,
                "scheduled_time": scheduled_time
            }
        )
    
    async def notify_client_master_assigned(
        self,
        client_phone: str,
        job_id: int,
        master_name: str,
        address: str,
        scheduled_time: str,
        price: float
    ):
        """Уведомить клиента о назначении мастера"""
        await self.send_notification(
            recipient_id=client_phone,
            recipient_type="client",
            notification_type=NotificationType.MASTER_ASSIGNED,
            data={
                "job_id": job_id,
                "master_name": master_name,
                "address": address,
                "scheduled_time": scheduled_time,
                "price": price
            }
        )
    
    async def notify_payment_received(
        self,
        master_id: str,
        job_id: int,
        earnings: float,
        daily_total: float
    ):
        """Уведомить мастера о получении оплаты"""
        await self.send_notification(
            recipient_id=master_id,
            recipient_type="master",
            notification_type=NotificationType.PAYMENT_RECEIVED,
            data={
                "job_id": job_id,
                "earnings": earnings,
                "daily_total": daily_total
            }
        )
