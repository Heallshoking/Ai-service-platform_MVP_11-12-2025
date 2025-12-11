#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт миграции Google Sheets к новой структуре из 21 колонки
Запуск: python migrate_sheets.py
"""

import os
import logging
from dotenv import load_dotenv
from utils.sheets_client import SheetsClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def migrate_catalog_structure():
    """
    Миграция структуры листа 'Справочник' к новой схеме из 21 колонки
    """
    client = SheetsClient()
    
    logger.info("🔄 Начинаю миграцию структуры каталога...")
    
    try:
        worksheet = client.spreadsheet.worksheet(client.SHEET_CATALOG)
        
        # Получаем текущие заголовки
        current_headers = worksheet.row_values(1)
        logger.info(f"📋 Текущие заголовки ({len(current_headers)} колонок): {current_headers}")
        
        # Целевые заголовки из 21 колонки
        target_headers = client.CATALOG_HEADERS
        logger.info(f"🎯 Целевые заголовки ({len(target_headers)} колонок)")
        
        # Проверяем, нужна ли миграция
        if current_headers == target_headers:
            logger.info("✅ Структура уже актуальна. Миграция не требуется.")
            return
        
        # Бэкап текущих данных
        logger.info("💾 Создаю бэкап текущих данных...")
        all_data = worksheet.get_all_values()
        logger.info(f"📊 Бэкап создан: {len(all_data)} строк")
        
        # Создаём маппинг старых колонок на новые
        column_mapping = {}
        for new_idx, new_header in enumerate(target_headers):
            if new_header in current_headers:
                old_idx = current_headers.index(new_header)
                column_mapping[old_idx] = new_idx
        
        logger.info(f"🔗 Маппинг колонок: {len(column_mapping)} совпадений")
        
        # Подготовка новых данных
        new_data = []
        
        # Заголовки
        new_data.append(target_headers)
        
        # Миграция существующих строк
        for row_idx, row in enumerate(all_data[1:], start=2):  # Пропускаем заголовки
            new_row = [''] * len(target_headers)
            
            # Копируем существующие данные
            for old_idx, new_idx in column_mapping.items():
                if old_idx < len(row):
                    new_row[new_idx] = row[old_idx]
            
            # Генерация артикула, если его нет
            if not new_row[0]:  # Колонка A - Артикул
                article_id = f"VIN-{row_idx - 1:05d}"
                new_row[0] = article_id
            
            # Значения по умолчанию для новых полей
            if not new_row[7]:  # H - Формат
                new_row[7] = 'LP'
            
            if not new_row[12]:  # M - Статус
                new_row[12] = '🟢 Доступна'
            
            if not new_row[16]:  # Q - Stock_Count
                new_row[16] = 1
            
            if not new_row[17]:  # R - Минимум_складчиков
                new_row[17] = 10
            
            if not new_row[18]:  # S - Складчина_участников
                new_row[18] = 0
            
            new_data.append(new_row)
        
        # Очистка и обновление листа
        logger.info("🧹 Очищаю лист...")
        worksheet.clear()
        
        logger.info(f"📝 Записываю новую структуру ({len(new_data)} строк)...")
        worksheet.update(new_data, 'A1')
        
        logger.info("✅ Миграция успешно завершена!")
        logger.info(f"📊 Обновлено строк: {len(new_data) - 1}")
        logger.info(f"📋 Колонок: {len(target_headers)}")
        
        # Форматирование заголовков
        worksheet.format('A1:U1', {
            "textFormat": {"bold": True, "fontSize": 10},
            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
        })
        
        logger.info("🎨 Форматирование заголовков применено")
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        raise


def verify_structure():
    """
    Проверка структуры после миграции
    """
    client = SheetsClient()
    
    logger.info("\n🔍 Проверка структуры...")
    
    try:
        worksheet = client.spreadsheet.worksheet(client.SHEET_CATALOG)
        headers = worksheet.row_values(1)
        
        logger.info(f"📋 Текущие заголовки ({len(headers)} колонок):")
        for idx, header in enumerate(headers, start=1):
            logger.info(f"   {idx:2d}. {header}")
        
        # Проверка соответствия
        if headers == client.CATALOG_HEADERS:
            logger.info("\n✅ Структура соответствует целевой схеме!")
            
            # Проверка данных
            all_records = worksheet.get_all_records(expected_headers=client.CATALOG_HEADERS)
            logger.info(f"📊 Всего записей в каталоге: {len(all_records)}")
            
            if all_records:
                logger.info("\n🎵 Примеры записей:")
                for idx, record in enumerate(all_records[:3], start=1):
                    logger.info(f"   {idx}. {record.get('Артикул')} - {record.get('Исполнитель')} - {record.get('Название')}")
            
        else:
            logger.warning("\n⚠️ Структура не соответствует целевой!")
            logger.warning(f"Ожидалось {len(client.CATALOG_HEADERS)} колонок, получено {len(headers)}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("🎵 Миграция Google Sheets для винилового маркетплейса")
    print("=" * 60)
    print()
    
    # Проверка переменных окружения
    if not os.getenv('GOOGLE_SPREADSHEET_ID'):
        logger.error("❌ GOOGLE_SPREADSHEET_ID не установлен в .env")
        exit(1)
    
    if not os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH'):
        logger.error("❌ GOOGLE_SHEETS_CREDENTIALS_PATH не установлен в .env")
        exit(1)
    
    try:
        # Миграция
        migrate_catalog_structure()
        
        print()
        
        # Проверка
        verify_structure()
        
        print()
        print("=" * 60)
        print("✅ Миграция завершена успешно!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Критическая ошибка: {e}")
        exit(1)
