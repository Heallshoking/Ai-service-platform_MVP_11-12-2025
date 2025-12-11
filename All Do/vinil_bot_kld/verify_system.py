#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт проверки работоспособности системы
Запуск: python verify_system.py
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def check_env_vars():
    """Проверка переменных окружения"""
    logger.info("🔍 Проверка переменных окружения...")
    
    required_vars = [
        'GOOGLE_SHEETS_CREDENTIALS_PATH',
        'GOOGLE_SPREADSHEET_ID',
        'TELEGRAM_BOT_TOKEN',
        'ADMIN_TELEGRAM_ID'
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            logger.error(f"❌ {var} не установлен")
        else:
            # Скрываем секретные значения
            if 'TOKEN' in var or 'KEY' in var:
                display_value = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display_value = value
            logger.info(f"✅ {var}: {display_value}")
    
    if missing:
        logger.error(f"\n❌ Отсутствуют обязательные переменные: {', '.join(missing)}")
        return False
    
    logger.info("✅ Все переменные окружения установлены\n")
    return True


def check_google_credentials():
    """Проверка учётных данных Google"""
    logger.info("🔍 Проверка Google Sheets credentials...")
    
    creds_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
    
    if not os.path.exists(creds_path):
        logger.error(f"❌ Файл credentials не найден: {creds_path}")
        return False
    
    logger.info(f"✅ Credentials файл найден: {creds_path}")
    
    # Проверка подключения
    try:
        from utils.sheets_client import SheetsClient
        client = SheetsClient()
        
        # Проверка доступа к таблице
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        worksheet = client.spreadsheet.worksheet(client.SHEET_CATALOG)
        
        headers = worksheet.row_values(1)
        logger.info(f"✅ Подключение к Google Sheets успешно")
        logger.info(f"📊 Найден лист '{client.SHEET_CATALOG}' с {len(headers)} колонками\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Google Sheets: {e}\n")
        return False


def check_sheets_structure():
    """Проверка структуры листа Справочник"""
    logger.info("🔍 Проверка структуры каталога...")
    
    try:
        from utils.sheets_client import SheetsClient
        client = SheetsClient()
        
        worksheet = client.spreadsheet.worksheet(client.SHEET_CATALOG)
        headers = worksheet.row_values(1)
        
        # Проверка соответствия целевой структуре
        if headers == client.CATALOG_HEADERS:
            logger.info(f"✅ Структура каталога корректна ({len(headers)} колонок)")
            
            # Проверка данных
            all_records = worksheet.get_all_records(expected_headers=client.CATALOG_HEADERS)
            logger.info(f"📊 Записей в каталоге: {len(all_records)}")
            
            if all_records:
                # Проверка артикулов
                articles_ok = True
                for record in all_records:
                    article = record.get('Артикул', '')
                    if not article or not article.startswith('VIN-'):
                        articles_ok = False
                        break
                
                if articles_ok:
                    logger.info("✅ Все записи имеют корректные артикулы VIN-XXXXX")
                else:
                    logger.warning("⚠️ Некоторые записи не имеют артикулов. Запустите migrate_sheets.py")
            
            logger.info("")
            return True
        else:
            logger.error(f"❌ Структура не соответствует целевой!")
            logger.error(f"Ожидалось {len(client.CATALOG_HEADERS)} колонок, получено {len(headers)}")
            logger.warning("⚠️ Запустите migrate_sheets.py для миграции\n")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки структуры: {e}\n")
        return False


def check_api_imports():
    """Проверка импортов для API"""
    logger.info("🔍 Проверка зависимостей API...")
    
    try:
        import fastapi
        import uvicorn
        import httpx
        logger.info("✅ FastAPI зависимости установлены")
        
        # Проверка модулей проекта
        from utils.static_export import StaticExporter
        logger.info("✅ Модуль StaticExporter доступен")
        
        logger.info("")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Отсутствуют зависимости: {e}")
        logger.error("Запустите: pip install -r requirements.txt\n")
        return False


def check_bot_imports():
    """Проверка импортов для бота"""
    logger.info("🔍 Проверка зависимостей бота...")
    
    try:
        import telegram
        from telegram.ext import Application
        logger.info("✅ python-telegram-bot установлен")
        logger.info("")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Отсутствуют зависимости: {e}")
        logger.error("Запустите: pip install -r requirements.txt\n")
        return False


def print_summary(results):
    """Вывод итогов проверки"""
    print("=" * 60)
    print("📊 ИТОГИ ПРОВЕРКИ")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    print("=" * 60)
    
    if all_passed:
        print("✅ Система готова к запуску!")
        print("\nЗапустите:")
        print("  1. python main.py         # FastAPI Backend")
        print("  2. python vinyl_bot.py    # Telegram Bot")
    else:
        print("❌ Обнаружены проблемы. Исправьте их перед запуском.")
        print("\nСмотрите SETUP.md для подробной инструкции.")
    
    print("=" * 60)


def main():
    """Основная функция проверки"""
    print("=" * 60)
    print("🎵 Проверка системы винилового маркетплейса")
    print("=" * 60)
    print()
    
    results = {}
    
    # Проверки
    results["Переменные окружения"] = check_env_vars()
    results["Google Sheets доступ"] = check_google_credentials()
    results["Структура каталога"] = check_sheets_structure()
    results["API зависимости"] = check_api_imports()
    results["Bot зависимости"] = check_bot_imports()
    
    # Итоги
    print_summary(results)
    
    # Код возврата
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
