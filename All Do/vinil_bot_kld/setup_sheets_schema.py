# -*- coding: utf-8 -*-
"""
Setup Google Sheets Schema for MVP Backend
Initializes all required worksheets with proper headers and structure
"""

import os
import logging
from dotenv import load_dotenv
from utils.sheets_client import SheetsClient

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_catalog_worksheet(sheets_client: SheetsClient):
    """Setup Справочник (Catalog) worksheet with extended schema"""
    try:
        # Try to get existing worksheet
        worksheet = sheets_client.spreadsheet.worksheet("Справочник")
        logger.info("Справочник worksheet already exists")
        
        # Check if we need to add new columns
        headers = worksheet.row_values(1)
        required_headers = [
            "Название", "Исполнитель", "Жанр", "Год", "Лейбл", "Страна", 
            "Состояние", "Цена", "ФОТО_URL", "Продавец_TG_ID", "Статус", 
            "Описание", "SEO_Заголовок", "SEO_Описание", "SEO_Ключевые_слова",
            "Минимум_предзаказов", "Предзаказы_счётчик", "Предзаказы_участники",
            "Последний_интерес"
        ]
        
        if len(headers) < len(required_headers):
            logger.info("Adding missing columns to Справочник")
            worksheet.append_row(required_headers)
            # Move header row to top if needed
            worksheet.delete_rows(1)
            worksheet.insert_row(required_headers, 1)
            
    except Exception as e:
        logger.info(f"Creating new Справочник worksheet: {e}")
        worksheet = sheets_client.spreadsheet.add_worksheet(
            title="Справочник",
            rows=1000,
            cols=19
        )
        
        # Set headers
        headers = [
            "Название", "Исполнитель", "Жанр", "Год", "Лейбл", "Страна",
            "Состояние", "Цена", "ФОТО_URL", "Продавец_TG_ID", "Статус",
            "Описание", "SEO_Заголовок", "SEO_Описание", "SEO_Ключевые_слова",
            "Минимум_предзаказов", "Предзаказы_счётчик", "Предзаказы_участники",
            "Последний_интерес"
        ]
        worksheet.update('A1:S1', [headers])
        
        # Format header row
        worksheet.format('A1:S1', {
            "backgroundColor": {"red": 0.2, "green": 0.7, "blue": 0.5},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })
        
    logger.info("✓ Справочник worksheet configured")


def setup_admin_notifications_worksheet(sheets_client: SheetsClient):
    """Setup Оповещения_админу (Admin Notifications) worksheet"""
    try:
        worksheet = sheets_client.spreadsheet.worksheet("Оповещения_админу")
        logger.info("Оповещения_админу worksheet already exists")
    except Exception:
        logger.info("Creating Оповещения_админу worksheet")
        worksheet = sheets_client.spreadsheet.add_worksheet(
            title="Оповещения_админу",
            rows=500,
            cols=6
        )
        
        headers = [
            "Дата/Время", "Тип_события", "Пластинка", "Детали",
            "Действие_требуется", "Статус_задачи"
        ]
        worksheet.update('A1:F1', [headers])
        
        # Format header row
        worksheet.format('A1:F1', {
            "backgroundColor": {"red": 1, "green": 0.6, "blue": 0.2},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })
        
    logger.info("✓ Оповещения_админу worksheet configured")


def setup_preorders_worksheet(sheets_client: SheetsClient):
    """Setup Предзаказы (Pre-orders) worksheet"""
    try:
        worksheet = sheets_client.spreadsheet.worksheet("Предзаказы")
        logger.info("Предзаказы worksheet already exists")
    except Exception:
        logger.info("Creating Предзаказы worksheet")
        worksheet = sheets_client.spreadsheet.add_worksheet(
            title="Предзаказы",
            rows=1000,
            cols=8
        )
        
        headers = [
            "Дата/Время", "Пользователь_ID", "Пластинка_ID", "Контакт",
            "Статус", "Уведомлён", "Спецпредложение", "Истекает"
        ]
        worksheet.update('A1:H1', [headers])
        
        # Format header row
        worksheet.format('A1:H1', {
            "backgroundColor": {"red": 0.4, "green": 0.6, "blue": 0.9},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })
        
    logger.info("✓ Предзаказы worksheet configured")


def setup_notification_settings_worksheet(sheets_client: SheetsClient):
    """Setup Настройки_уведомлений (Notification Templates) worksheet"""
    try:
        worksheet = sheets_client.spreadsheet.worksheet("Настройки_уведомлений")
        logger.info("Настройки_уведомлений worksheet already exists")
    except Exception:
        logger.info("Creating Настройки_уведомлений worksheet")
        worksheet = sheets_client.spreadsheet.add_worksheet(
            title="Настройки_уведомлений",
            rows=50,
            cols=4
        )
        
        headers = ["Тип_уведомления", "Заголовок", "Текст_шаблона", "Активно"]
        worksheet.update('A1:D1', [headers])
        
        # Format header row
        worksheet.format('A1:D1', {
            "backgroundColor": {"red": 0.6, "green": 0.4, "blue": 0.8},
            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
            "horizontalAlignment": "CENTER"
        })
        
        # Add default notification templates
        default_templates = [
            [
                "pre_order_available",
                "🎉 ЭКСКЛЮЗИВНОЕ ПРЕДЛОЖЕНИЕ ДЛЯ ВАС!",
                "{artist} — {title} ({year})\n\nВы были одним из первых, кто проявил интерес к этой легендарной пластинке!\n\nТеперь она в наличии, и специально для вас:\n\n💰 Цена: ~~{original_price} ₽~~ → {discount_price} ₽ (-25%)\n⏰ Предложение действует до: {expires_date}\n🔑 Ваш промокод: {discount_code}\n\n[🛒 Купить сейчас]({record_url})\n\nЭто предложение создано эксклюзивно для вас и истечёт через 14 дней.\nНе упустите возможность приобрести эту пластинку по специальной цене!",
                "TRUE"
            ],
            [
                "procurement_task",
                "🎯 НОВАЯ ЗАДАЧА НА ЗАКУПКУ",
                "{artist} - {title} ({year})\n\n👥 Спрос: {demand_count} покупателей\n💰 Потенциальная выручка: ~{estimated_revenue} ₽\n📈 Тренд: +{trend_change} за последние 3 дня\n\nРекомендуемая цена: {suggested_price} ₽\nЦена со скидкой: {discount_price} ₽\n\nПожалуйста, найдите эту пластинку и добавьте в каталог.",
                "TRUE"
            ],
            [
                "search_request_created",
                "📬 НОВЫЙ ЗАПРОС НА ПОИСК",
                "🎵 {title} - {artist}\n👤 Покупатель: {customer_contact}\n📊 Всего заинтересовано: {total_demand} чел.",
                "TRUE"
            ]
        ]
        
        worksheet.append_rows(default_templates)
        
    logger.info("✓ Настройки_уведомлений worksheet configured")


def setup_balances_worksheet(sheets_client: SheetsClient):
    """Ensure Балансы worksheet exists (from original schema)"""
    try:
        worksheet = sheets_client.spreadsheet.worksheet("Балансы")
        logger.info("Балансы worksheet already exists")
    except Exception:
        logger.info("Creating Балансы worksheet")
        worksheet = sheets_client.spreadsheet.add_worksheet(
            title="Балансы",
            rows=500,
            cols=5
        )
        
        headers = ["TG ID", "Имя", "Добавлено записей", "Продано записей", "Дата регистрации"]
        worksheet.update('A1:E1', [headers])
        
        # Format header row
        worksheet.format('A1:E1', {
            "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.2},
            "textFormat": {"bold": True},
            "horizontalAlignment": "CENTER"
        })
        
    logger.info("✓ Балансы worksheet configured")


def main():
    """Main setup function"""
    logger.info("Starting Google Sheets schema setup...")
    
    try:
        # Initialize sheets client
        sheets_client = SheetsClient()
        logger.info(f"Connected to spreadsheet: {sheets_client.spreadsheet.title}")
        
        # Setup all worksheets
        setup_catalog_worksheet(sheets_client)
        setup_admin_notifications_worksheet(sheets_client)
        setup_preorders_worksheet(sheets_client)
        setup_notification_settings_worksheet(sheets_client)
        setup_balances_worksheet(sheets_client)
        
        logger.info("\n" + "="*60)
        logger.info("✅ Google Sheets schema setup completed successfully!")
        logger.info("="*60)
        logger.info("\nWorksheets configured:")
        logger.info("  1. Справочник (Catalog) - 19 columns with SEO fields")
        logger.info("  2. Оповещения_админу (Admin Notifications)")
        logger.info("  3. Предзаказы (Pre-orders)")
        logger.info("  4. Настройки_уведомлений (Notification Templates)")
        logger.info("  5. Балансы (User Balances)")
        logger.info("\nYou can now start using the system!")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
