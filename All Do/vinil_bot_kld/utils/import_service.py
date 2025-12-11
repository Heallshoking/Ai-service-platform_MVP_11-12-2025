# -*- coding: utf-8 -*-
"""
Сервис импорта данных из Google Sheets в Supabase
Синхронизация каталога виниловых пластинок
"""

import logging
import time
from typing import Dict, List
from datetime import datetime

from utils.sheets_client import SheetsClient
from utils.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class ImportService:
    """Сервис импорта из Google Sheets в Supabase"""

    def __init__(self):
        """Инициализация сервиса импорта"""
        self.sheets_client = SheetsClient()
        self.supabase_client = SupabaseClient()
        logger.info("ImportService инициализирован")

    def import_from_sheets(
        self, 
        sheet_name: str = "Справочник",
        update_existing: bool = False,
        preserve_custom_fields: bool = True,
        admin_telegram_id: int = None
    ) -> Dict:
        """
        Импорт записей из Google Sheets в Supabase
        
        Args:
            sheet_name: Имя листа в Google Sheets
            update_existing: Обновлять существующие записи
            preserve_custom_fields: Сохранять кастомные поля (custom_image, custom_description)
            admin_telegram_id: Telegram ID администратора
            
        Returns:
            Сводка импорта
        """
        start_time = time.time()
        summary = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }
        
        try:
            logger.info(f"Начало импорта из {sheet_name}")
            
            # Получаем все записи из Google Sheets
            worksheet = self.sheets_client.spreadsheet.worksheet(sheet_name)
            sheet_records = worksheet.get_all_records()
            
            logger.info(f"Получено {len(sheet_records)} записей из Google Sheets")
            
            # Обрабатываем каждую запись
            for row_idx, sheet_row in enumerate(sheet_records, start=2):  # +2 для учета заголовка
                try:
                    # Трансформируем данные из Sheets в формат Supabase
                    record_data = self._transform_sheet_row(sheet_row, row_idx)
                    
                    if not record_data:
                        logger.warning(f"Пропуск строки {row_idx}: недостаточно данных")
                        summary['skipped'] += 1
                        continue
                    
                    # Проверяем существование записи
                    existing_id = self.supabase_client.check_record_exists(
                        record_data['title'],
                        record_data['artist'],
                        record_data['year']
                    )
                    
                    if existing_id:
                        # Запись существует
                        if update_existing:
                            # Обновляем запись
                            updates = self._prepare_updates(record_data, preserve_custom_fields, existing_id)
                            
                            if updates:
                                self.supabase_client.update_record(existing_id, updates)
                                summary['updated'] += 1
                                logger.debug(f"Обновлена запись {existing_id}: {record_data['title']}")
                            else:
                                summary['skipped'] += 1
                        else:
                            summary['skipped'] += 1
                            logger.debug(f"Пропуск существующей записи: {record_data['title']}")
                    else:
                        # Создаем новую запись
                        self.supabase_client.create_record(record_data)
                        summary['created'] += 1
                        logger.debug(f"Создана новая запись: {record_data['title']}")
                        
                except Exception as row_error:
                    error_msg = f"Ошибка обработки строки {row_idx}: {str(row_error)}"
                    logger.error(error_msg)
                    summary['errors'] += 1
                    summary['error_details'].append(error_msg)
                    continue
            
            duration = time.time() - start_time
            
            logger.info(
                f"Импорт завершен: создано={summary['created']}, "
                f"обновлено={summary['updated']}, пропущено={summary['skipped']}, "
                f"ошибок={summary['errors']}, время={duration:.2f}с"
            )
            
            # Создаем лог импорта
            if admin_telegram_id:
                try:
                    self.supabase_client.create_import_log(summary, admin_telegram_id, duration)
                except Exception as log_error:
                    logger.error(f"Ошибка создания лога импорта: {log_error}")
            
            return {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'summary': summary,
                'duration_seconds': round(duration, 2)
            }
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Критическая ошибка импорта: {str(e)}"
            logger.error(error_msg)
            
            return {
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'error': error_msg,
                'summary': summary,
                'duration_seconds': round(duration, 2)
            }

    def _transform_sheet_row(self, sheet_row: Dict, row_number: int) -> Dict:
        """
        Трансформация строки из Google Sheets в формат Supabase
        
        Args:
            sheet_row: Строка из Google Sheets
            row_number: Номер строки
            
        Returns:
            Словарь с данными для Supabase или None
        """
        try:
            # Обязательные поля
            title = sheet_row.get('Название', '').strip()
            artist = sheet_row.get('Исполнитель', '').strip()
            genre = sheet_row.get('Жанр', '').strip()
            year = sheet_row.get('Год')
            country = sheet_row.get('Страна', '').strip()
            condition = sheet_row.get('Состояние', '').strip()
            price = sheet_row.get('Цена')
            
            # Проверка обязательных полей
            if not all([title, artist, genre, year, country, condition, price]):
                logger.warning(f"Строка {row_number}: отсутствуют обязательные поля")
                return None
            
            # Преобразование типов
            try:
                year = int(year)
                price = float(price)
            except (ValueError, TypeError):
                logger.warning(f"Строка {row_number}: некорректный формат года или цены")
                return None
            
            # Опциональные поля
            label = sheet_row.get('Лейбл', '').strip() or None
            image_url = sheet_row.get('ФОТО_URL', '').strip() or None
            seller_telegram_id = sheet_row.get('Продавец (TG ID)') or None
            status = sheet_row.get('Статус', '').strip()
            description = sheet_row.get('Описание', '').strip() or None
            
            # Нормализация статуса
            if not status or status == '':
                status = 'available'
            elif 'Доступна' in status or '🟢' in status:
                status = 'available'
            elif 'Зарезервирована' in status or '🟡' in status:
                status = 'reserved'
            elif 'Продана' in status or '🔴' in status:
                status = 'sold'
            
            # Формируем запись для Supabase
            record = {
                'title': title,
                'artist': artist,
                'genre': genre,
                'year': year,
                'label': label,
                'country': country,
                'condition': condition,
                'price': price,
                'description': description,
                'image_url': image_url,
                'custom_image': False,  # По умолчанию не кастомное
                'custom_description': False,  # По умолчанию не кастомное
                'status': status,
                'seller_telegram_id': seller_telegram_id,
                'import_source': 'sheets_import',
                'google_sheets_row': row_number
            }
            
            return record
            
        except Exception as e:
            logger.error(f"Ошибка трансформации строки {row_number}: {e}")
            return None

    def _prepare_updates(self, new_data: Dict, preserve_custom: bool, existing_id: str) -> Dict:
        """
        Подготовка обновлений с учетом кастомных полей
        
        Args:
            new_data: Новые данные из Sheets
            preserve_custom: Сохранять кастомные поля
            existing_id: ID существующей записи
            
        Returns:
            Словарь обновлений или пустой словарь
        """
        updates = {}
        
        try:
            # Получаем текущую запись
            existing_record = self.supabase_client.get_record_by_id(existing_id)
            
            if not existing_record:
                logger.warning(f"Запись {existing_id} не найдена при подготовке обновлений")
                return {}
            
            # Определяем какие поля обновлять
            # Всегда обновляем метаданные
            always_update = ['price', 'condition', 'status', 'label', 'country', 'google_sheets_row']
            
            for field in always_update:
                if field in new_data and new_data[field] != existing_record.get(field):
                    updates[field] = new_data[field]
            
            # Обновляем description только если:
            # - preserve_custom=False ИЛИ
            # - custom_description=False в существующей записи
            if not preserve_custom or not existing_record.get('custom_description', False):
                if new_data.get('description') and new_data['description'] != existing_record.get('description'):
                    updates['description'] = new_data['description']
            
            # Обновляем image_url только если:
            # - preserve_custom=False ИЛИ
            # - custom_image=False в существующей записи
            if not preserve_custom or not existing_record.get('custom_image', False):
                if new_data.get('image_url') and new_data['image_url'] != existing_record.get('image_url'):
                    updates['image_url'] = new_data['image_url']
            
            return updates
            
        except Exception as e:
            logger.error(f"Ошибка подготовки обновлений для {existing_id}: {e}")
            return {}
