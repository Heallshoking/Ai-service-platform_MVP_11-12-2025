# -*- coding: utf-8 -*-
"""
Клиент для работы с Supabase
Управление данными виниловых пластинок через REST API
"""

import os
import logging
from typing import List, Dict, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Клиент для работы с Supabase database"""

    def __init__(self):
        """Инициализация клиента Supabase"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL и SUPABASE_SERVICE_ROLE_KEY должны быть установлены")
        
        self.client: Client = None
        self._connect()

    def _connect(self):
        """Подключение к Supabase"""
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info(f"Успешное подключение к Supabase: {self.supabase_url}")
        except Exception as e:
            logger.error(f"Ошибка подключения к Supabase: {e}")
            raise

    def health_check(self) -> bool:
        """Проверка подключения к Supabase"""
        try:
            # Простой запрос для проверки соединения
            response = self.client.table('profiles').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_records(self, filters: Optional[Dict] = None, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Получение записей с фильтрацией
        
        Args:
            filters: Словарь фильтров (genre, year_min, year_max, price_min, price_max, search, status)
            limit: Количество записей
            offset: Смещение для пагинации
            
        Returns:
            Список записей
        """
        try:
            query = self.client.table('records').select('*')
            
            # Применение фильтров
            if filters:
                # Фильтр по жанру (case-insensitive)
                if filters.get('genre'):
                    query = query.ilike('genre', f"%{filters['genre']}%")
                
                # Фильтр по году
                if filters.get('year_min'):
                    query = query.gte('year', filters['year_min'])
                if filters.get('year_max'):
                    query = query.lte('year', filters['year_max'])
                
                # Фильтр по цене
                if filters.get('price_min'):
                    query = query.gte('price', filters['price_min'])
                if filters.get('price_max'):
                    query = query.lte('price', filters['price_max'])
                
                # Фильтр по статусу
                if filters.get('status'):
                    query = query.eq('status', filters['status'])
                else:
                    # По умолчанию только доступные
                    query = query.eq('status', 'available')
                
                # Поиск по названию и исполнителю
                if filters.get('search'):
                    search_term = filters['search']
                    query = query.or_(f"title.ilike.%{search_term}%,artist.ilike.%{search_term}%")
            else:
                # По умолчанию только доступные записи
                query = query.eq('status', 'available')
            
            # Сортировка и пагинация
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            
            response = query.execute()
            logger.info(f"Получено {len(response.data)} записей с фильтрами: {filters}")
            return response.data
            
        except Exception as e:
            logger.error(f"Ошибка получения записей: {e}")
            raise

    def get_record_by_id(self, record_id: str) -> Optional[Dict]:
        """
        Получение записи по ID
        
        Args:
            record_id: UUID записи
            
        Returns:
            Словарь с данными записи или None
        """
        try:
            response = self.client.table('records').select('*').eq('id', record_id).single().execute()
            logger.info(f"Получена запись: {record_id}")
            return response.data
        except Exception as e:
            logger.error(f"Ошибка получения записи {record_id}: {e}")
            return None

    def create_record(self, record_data: Dict) -> str:
        """
        Создание новой записи
        
        Args:
            record_data: Данные записи
            
        Returns:
            UUID созданной записи
        """
        try:
            response = self.client.table('records').insert(record_data).execute()
            record_id = response.data[0]['id']
            logger.info(f"Создана запись: {record_id} - {record_data.get('title')}")
            return record_id
        except Exception as e:
            logger.error(f"Ошибка создания записи: {e}")
            raise

    def update_record(self, record_id: str, updates: Dict) -> Dict:
        """
        Обновление записи
        
        Args:
            record_id: UUID записи
            updates: Словарь с обновлениями
            
        Returns:
            Обновленная запись
        """
        try:
            response = self.client.table('records').update(updates).eq('id', record_id).execute()
            logger.info(f"Обновлена запись: {record_id}, поля: {list(updates.keys())}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Ошибка обновления записи {record_id}: {e}")
            raise

    def delete_record(self, record_id: str) -> bool:
        """
        Удаление записи
        
        Args:
            record_id: UUID записи
            
        Returns:
            True если успешно
        """
        try:
            self.client.table('records').delete().eq('id', record_id).execute()
            logger.info(f"Удалена запись: {record_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления записи {record_id}: {e}")
            return False

    def check_record_exists(self, title: str, artist: str, year: int) -> Optional[str]:
        """
        Проверка существования записи по ключевым полям
        
        Args:
            title: Название
            artist: Исполнитель
            year: Год
            
        Returns:
            UUID записи если найдена, None иначе
        """
        try:
            response = self.client.table('records').select('id').ilike('title', title).ilike('artist', artist).eq('year', year).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"Ошибка проверки существования записи: {e}")
            return None

    def create_profile(self, user_id: str, telegram_id: int, username: str = None, full_name: str = None) -> Dict:
        """
        Создание профиля пользователя
        
        Args:
            user_id: Supabase user UUID
            telegram_id: Telegram ID
            username: Telegram username
            full_name: Полное имя
            
        Returns:
            Созданный профиль
        """
        try:
            profile_data = {
                'id': user_id,
                'telegram_id': telegram_id,
                'telegram_username': username,
                'full_name': full_name
            }
            
            response = self.client.table('profiles').insert(profile_data).execute()
            logger.info(f"Создан профиль для telegram_id: {telegram_id}")
            return response.data[0]
        except Exception as e:
            logger.error(f"Ошибка создания профиля: {e}")
            raise

    def get_profile_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """
        Получение профиля по Telegram ID
        
        Args:
            telegram_id: Telegram ID
            
        Returns:
            Профиль или None
        """
        try:
            response = self.client.table('profiles').select('*').eq('telegram_id', telegram_id).single().execute()
            return response.data
        except Exception as e:
            logger.debug(f"Профиль не найден для telegram_id {telegram_id}")
            return None

    def create_import_log(self, summary: Dict, admin_telegram_id: int, duration: float = None) -> str:
        """
        Создание записи в логах импорта
        
        Args:
            summary: Сводка импорта
            admin_telegram_id: Telegram ID администратора
            duration: Длительность в секундах
            
        Returns:
            UUID лога
        """
        try:
            log_data = {
                'records_created': summary.get('created', 0),
                'records_updated': summary.get('updated', 0),
                'records_skipped': summary.get('skipped', 0),
                'errors': summary.get('error_details'),
                'admin_telegram_id': admin_telegram_id,
                'duration_seconds': duration
            }
            
            response = self.client.table('import_logs').insert(log_data).execute()
            log_id = response.data[0]['id']
            logger.info(f"Создан лог импорта: {log_id}")
            return log_id
        except Exception as e:
            logger.error(f"Ошибка создания лога импорта: {e}")
            raise
