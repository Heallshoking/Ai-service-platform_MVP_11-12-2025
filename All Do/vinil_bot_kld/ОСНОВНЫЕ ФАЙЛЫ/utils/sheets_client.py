# -*- coding: utf-8 -*-
"""
Клиент для работы с Google Sheets
Управление данными виниловых пластинок
"""

import os
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SheetsClient:
    """Клиент для работы с Google Sheets"""

    # Названия листов
    SHEET_CATALOG = "Справочник"
    SHEET_BALANCES = "Балансы"
    SHEET_REPORTS = "Отчёты"
    SHEET_PHOTO_HASHES = "photo_hashes"
    
    # Структура каталога (полный список колонок)
    CATALOG_HEADERS = [
        'Артикул', 'Название', 'Исполнитель', 'Жанр', 'Год', 'Лейбл', 'Страна',
        'Формат', 'Состояние', 'Цена', 'ФОТО_URL', 'Продавец_TG_ID', 'Статус',
        'Описание', 'SEO_Title', 'SEO_Description', 'Stock_Count',
        'Минимум_складчиков', 'Складчина_участников', 'Цена_ориентир', 'Последний_интерес'
    ]

    def __init__(self):
        """Инициализация клиента Google Sheets"""
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.spreadsheet_url = os.getenv('SPREADSHEET_URL')
        
        if not self.spreadsheet_url:
            raise ValueError("SPREADSHEET_URL не установлен в переменных окружения")
        
        self.client = None
        self.spreadsheet = None
        self._connect()

    def _connect(self):
        """Подключение к Google Sheets"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_url(self.spreadsheet_url)
            
            logger.info(f"Успешное подключение к Google Sheets: {self.spreadsheet.title}")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            raise

    def get_all_records(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Получение всех записей из каталога с фильтрацией
        
        Args:
            filters: Фильтры (genre, year_min, year_max, condition, country, price_min, price_max)
            
        Returns:
            Список записей
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            records = worksheet.get_all_records(expected_headers=self.CATALOG_HEADERS)
            
            # Применение фильтров
            if filters:
                filtered_records = []
                for record in records:
                    # Пропускаем записи с исключающими терминами
                    condition = str(record.get('Состояние', '')).lower()
                    if any(term in condition for term in ['битая', 'повреждённая', 'без конверта']):
                        continue
                    
                    # Фильтр по жанру
                    if filters.get('genre') and filters['genre'].lower() not in str(record.get('Жанр', '')).lower():
                        continue
                    
                    # Фильтр по году
                    year = record.get('Год')
                    if year:
                        if filters.get('year_min') and year < filters['year_min']:
                            continue
                        if filters.get('year_max') and year > filters['year_max']:
                            continue
                    
                    # Фильтр по состоянию
                    if filters.get('condition') and filters['condition'].lower() not in condition:
                        continue
                    
                    # Фильтр по стране
                    if filters.get('country') and filters['country'].lower() not in str(record.get('Страна', '')).lower():
                        continue
                    
                    # Фильтр по цене
                    price = record.get('Цена')
                    if price:
                        if filters.get('price_min') and price < filters['price_min']:
                            continue
                        if filters.get('price_max') and price > filters['price_max']:
                            continue
                    
                    # Проверка статуса - только доступные
                    status = str(record.get('Статус', ''))
                    if '🟢' not in status and 'Доступна' not in status:
                        continue
                    
                    filtered_records.append(record)
                
                return filtered_records
            
            return records
            
        except Exception as e:
            logger.error(f"Ошибка получения записей: {e}")
            raise

    def add_record(self, record_data: Dict) -> int:
        """...
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)

            # Определяем следующий артикул на основе количества строк
            existing_values = worksheet.get_all_values()
            next_index = len(existing_values)
            article_code = f"VIN-{next_index:05d}"

            # Формирование строки данных
            row = [
                article_code,                             # Артикул
                record_data.get('title', ''),             # Название
                record_data.get('artist', ''),            # Исполнитель
                record_data.get('genre', ''),             # Жанр
                record_data.get('year', ''),              # Год
                record_data.get('label', ''),             # Лейбл
                record_data.get('country', ''),           # Страна
                record_data.get('format', 'LP'),          # Формат
                record_data.get('condition', ''),         # Состояние
                record_data.get('price', 0),              # Цена
                record_data.get('photo_url', ''),         # ФОТО_URL
                record_data.get('seller_tg_id', ''),      # Продавец_TG_ID
                '🟢 Доступна',                            # Статус
                '',                                       # Описание
                '',                                       # SEO_Title
                '',                                       # SEO_Description
                record_data.get('stock_count', 1),        # Stock_Count
                10,                                       # Минимум_складчиков
                0,                                        # Складчина_участников
                '',                                       # Цена_ориентир
                ''                                        # Последний_интерес
            ]

            worksheet.append_row(row)
            row_number = len(worksheet.get_all_values())

            logger.info(f"Добавлена запись в строку {row_number}: {record_data.get('title')}, артикул {article_code}")
            return row_number

        except Exception as e:
            logger.error(f"Ошибка добавления записи: {e}")
            raise

    def update_description(self, row_number: int, description: str):
        """
        Обновление описания записи
        
        Args:
            row_number: Номер строки
            description: Текст описания
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            # Колонка L (12) - Описание
            worksheet.update_cell(row_number, 12, description)
            logger.info(f"Обновлено описание для строки {row_number}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления описания: {e}")
            raise

    def update_status(self, row_number: int, status: str):
        """
        Обновление статуса записи
        
        Args:
            row_number: Номер строки
            status: Новый статус (🟢 Доступна / 🟡 Зарезервирована / 🔴 Продана)
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            # Колонка K (11) - Статус
            worksheet.update_cell(row_number, 11, status)
            logger.info(f"Обновлён статус для строки {row_number}: {status}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")
            raise

    def register_user(self, tg_id: int, name: str):
        """
        Регистрация нового пользователя
        
        Args:
            tg_id: Telegram ID
            name: Имя пользователя
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_BALANCES)
            
            # Проверка существования пользователя
            existing_records = worksheet.get_all_records()
            for record in existing_records:
                if record.get('TG ID') == tg_id:
                    logger.info(f"Пользователь {tg_id} уже зарегистрирован")
                    return
            
            # Добавление нового пользователя
            row = [
                tg_id,
                name,
                0,  # Добавлено записей
                0,  # Продано записей
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            worksheet.append_row(row)
            logger.info(f"Зарегистрирован новый пользователь: {name} ({tg_id})")
            
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            raise

    def add_photo_hash(self, photo_hash: str, record_id: int):
        """
        Добавление хеша фото для предотвращения дубликатов
        
        Args:
            photo_hash: Хеш фото
            record_id: ID записи
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_PHOTO_HASHES)
            
            row = [
                photo_hash,
                record_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            worksheet.append_row(row)
            logger.info(f"Добавлен хеш фото для записи {record_id}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления хеша фото: {e}")
            raise

    def check_photo_duplicate(self, photo_hash: str) -> Optional[int]:
        """
        Проверка наличия дубликата фото
        
        Args:
            photo_hash: Хеш фото для проверки
            
        Returns:
            ID записи если дубликат найден, None иначе
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_PHOTO_HASHES)
            rows = worksheet.get_all_values()
            # Если заголовков нет, ожидаем формат: [Photo Hash, Record ID, Timestamp]
            for row in rows[1:] if rows and rows[0] else rows:
                if not row:
                    continue
                ph = row[0] if len(row) > 0 else ''
                rid = row[1] if len(row) > 1 else ''
                if str(ph) == str(photo_hash):
                    try:
                        return int(rid)
                    except Exception:
                        return None
            return None
        except Exception as e:
            logger.error(f"Ошибка проверки дубликата фото: {e}")
            return None

    def find_record_by_article(self, article: str) -> Optional[Dict]:
        """Поиск одной записи по артикулу (точное совпадение, без регистра)."""
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            records = worksheet.get_all_records(expected_headers=self.CATALOG_HEADERS)
            q = str(article).strip().lower()
            for idx, rec in enumerate(records):
                art = str(rec.get('Артикул', '')).strip().lower()
                if q and q == art:
                    item = dict(rec)
                    item['_row_number'] = idx + 2  # +2: заголовки и индексация с 1
                    return item
            return None
        except Exception as e:
            logger.error(f"Ошибка поиска по артикулу: {e}")
            return None



    def update_price(self, row_number: int, new_price: float):
        """Обновление цены записи"""
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            # Колонка J (10) - Цена
            worksheet.update_cell(row_number, 10, float(new_price))
            logger.info(f"Обновлена цена для строки {row_number}: {new_price}")
        except Exception as e:
            logger.error(f"Ошибка обновления цены: {e}")
            raise

    def update_stock(self, row_number: int, stock_count: int):
        """Обновление остатка записи"""
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            # Колонка Q (17) - Stock_Count
            worksheet.update_cell(row_number, 17, int(stock_count))
            logger.info(f"Обновлён остаток для строки {row_number}: {stock_count}")
            
            # Авто-обновление статуса
            if stock_count == 0:
                self.update_status(row_number, '🔴 Продана')
            elif stock_count > 0:
                current_status = worksheet.cell(row_number, 13).value
                if '🔴' in str(current_status):
                    self.update_status(row_number, '🟢 Доступна')
        except Exception as e:
            logger.error(f"Ошибка обновления остатка: {e}")
            raise


        """
        Увеличивает количество участников складчины в строке каталога
        Возвращает текущее состояние: minimum, participants
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            min_val = worksheet.cell(row_number, 13).value  # M
            part_val = worksheet.cell(row_number, 14).value  # N
            minimum = int(min_val) if str(min_val).isdigit() else 10
            participants = int(part_val) if str(part_val).isdigit() else 0
            participants += 1
            worksheet.update_cell(row_number, 14, participants)
            logger.info(f"Складчина: строка {row_number}, {participants}/{minimum}")
            return {"minimum": minimum, "participants": participants}
        except Exception as e:
            logger.error(f"Ошибка обновления складчины: {e}")
            raise

    def set_collective_minimum(self, row_number: int, minimum: int) -> None:
        """
        Установка порога складчины для строки каталога
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            worksheet.update_cell(row_number, 13, int(minimum))  # M
            logger.info(f"Установлен порог складчины {minimum} для строки {row_number}")
        except Exception as e:
            logger.error(f"Ошибка установки порога складчины: {e}")
            raise

    def update_price(self, row_number: int, new_price: float):
        """Обновление цены записи"""
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            # Колонка J (10) - Цена
            worksheet.update_cell(row_number, 10, float(new_price))
            logger.info(f"Обновлена цена для строки {row_number}: {new_price}")
        except Exception as e:
            logger.error(f"Ошибка обновления цены: {e}")
            raise

    def update_stock(self, row_number: int, stock_count: int):
        """Обновление остатка записи"""
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            # Колонка Q (17) - Stock_Count
            worksheet.update_cell(row_number, 17, int(stock_count))
            logger.info(f"Обновлён остаток для строки {row_number}: {stock_count}")
            
            # Авто-обновление статуса
            if stock_count == 0:
                self.update_status(row_number, '🔴 Продана')
            elif stock_count > 0:
                current_status = worksheet.cell(row_number, 13).value
                if '🔴' in str(current_status):
                    self.update_status(row_number, '🟢 Доступна')
        except Exception as e:
            logger.error(f"Ошибка обновления остатка: {e}")
            raise

    def get_collective_status(self, row_number: int) -> Dict:
        """
        Получение состояния складчины и статуса записи по номеру строки
        """
        try:
            worksheet = self.spreadsheet.worksheet(self.SHEET_CATALOG)
            min_val = worksheet.cell(row_number, 13).value
            part_val = worksheet.cell(row_number, 14).value
            status = worksheet.cell(row_number, 11).value
            return {
                "minimum": int(min_val) if str(min_val).isdigit() else 10,
                "participants": int(part_val) if str(part_val).isdigit() else 0,
                "status": status or ''
            }
        except Exception as e:
            logger.error(f"Ошибка получения статуса складчины: {e}")
            raise

    def create_preorder(self, title: str, artist: str, user_tg: int, contact: str, 
                         order_type: str = 'Предзаказ', comment: str = '', status: str = 'Новая'):
        """
        Создание записи предзаказа в листе «Предзаказы»
        """
        try:
            worksheet = self.spreadsheet.worksheet("Предзаказы")
        except Exception:
            worksheet = self.spreadsheet.add_worksheet(title="Предзаказы", rows=100, cols=8)
            worksheet.update([["Дата/Время","Название","Исполнитель","Пользователь TG","Контакт","Тип","Комментарий","Статус"]], 'A1:H1')
        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            title,
            artist,
            user_tg,
            contact,
            order_type,
            comment,
            status
        ]
        worksheet.append_row(row)
        logger.info(f"Создан предзаказ: {artist} - {title} от {user_tg}")

    def log_admin_event(self, event_type: str, title: str, artist: str, details: str = '', link: str = ''):
        """
        Логирование события для администратора в лист «Оповещения_админу»
        """
        try:
            worksheet = self.spreadsheet.worksheet("Оповещения_админу")
        except Exception:
            worksheet = self.spreadsheet.add_worksheet(title="Оповещения_админу", rows=100, cols=5)
            worksheet.update([["Дата/Время","Событие","Пластинка","Детали","Ссылка"]], 'A1:E1')
        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            event_type,
            f"{artist} - {title}",
            details,
            link
        ]
        worksheet.append_row(row)
        logger.info(f"Оповещение администратору: {event_type} для {artist} - {title}")
