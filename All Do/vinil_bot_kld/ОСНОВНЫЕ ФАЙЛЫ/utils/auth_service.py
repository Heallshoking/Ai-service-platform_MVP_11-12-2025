# -*- coding: utf-8 -*-
"""
Сервис аутентификации через Supabase Auth
Управление пользователями и токенами
"""

import os
import logging
from typing import Dict, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис аутентификации через Supabase"""

    def __init__(self):
        """Инициализация сервиса аутентификации"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not all([self.supabase_url, self.supabase_anon_key, self.supabase_service_key]):
            raise ValueError("SUPABASE_URL, SUPABASE_ANON_KEY и SUPABASE_SERVICE_ROLE_KEY должны быть установлены")
        
        # Клиент с anon key для публичных операций
        self.anon_client: Client = create_client(self.supabase_url, self.supabase_anon_key)
        
        # Клиент с service role key для админских операций
        self.service_client: Client = create_client(self.supabase_url, self.supabase_service_key)
        
        logger.info("AuthService инициализирован")

    def create_user_from_telegram(self, telegram_id: int, username: str = None, full_name: str = None) -> Dict:
        """
        Создание пользователя через Telegram ID
        
        Args:
            telegram_id: Telegram ID пользователя
            username: Telegram username
            full_name: Полное имя
            
        Returns:
            Словарь с access_token, user_id, expires_in
        """
        try:
            # Генерируем email и пароль на основе telegram_id
            email = f"user_{telegram_id}@vinylbot.temp"
            # Используем детерминированный пароль для возможности повторной аутентификации
            password = self._generate_password(telegram_id)
            
            # Пытаемся войти сначала (пользователь может уже существовать)
            try:
                auth_response = self.anon_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                logger.info(f"Пользователь уже существует: telegram_id={telegram_id}")
                
                return {
                    'access_token': auth_response.session.access_token,
                    'user_id': auth_response.user.id,
                    'expires_in': auth_response.session.expires_in,
                    'is_new': False
                }
            
            except Exception as signin_error:
                # Пользователь не найден, создаем нового
                logger.info(f"Создание нового пользователя: telegram_id={telegram_id}")
                
                auth_response = self.anon_client.auth.sign_up({
                    "email": email,
                    "password": password
                })
                
                # Создаем профиль в таблице profiles через service client
                profile_data = {
                    'id': auth_response.user.id,
                    'telegram_id': telegram_id,
                    'telegram_username': username,
                    'full_name': full_name,
                    'is_admin': False
                }
                
                self.service_client.table('profiles').insert(profile_data).execute()
                
                logger.info(f"Создан новый пользователь: telegram_id={telegram_id}, user_id={auth_response.user.id}")
                
                return {
                    'access_token': auth_response.session.access_token,
                    'user_id': auth_response.user.id,
                    'expires_in': auth_response.session.expires_in,
                    'is_new': True
                }
                
        except Exception as e:
            logger.error(f"Ошибка создания/аутентификации пользователя: {e}")
            raise

    def _generate_password(self, telegram_id: int) -> str:
        """
        Генерация детерминированного пароля на основе telegram_id
        
        Args:
            telegram_id: Telegram ID
            
        Returns:
            Пароль (минимум 6 символов для Supabase)
        """
        import hashlib
        
        # Используем HMAC-подобный подход с секретным ключом
        secret = os.getenv('AUTH_SECRET_KEY', 'vinyl-bot-secret-key-2024')
        combined = f"{telegram_id}{secret}"
        password_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]
        
        return password_hash

    def verify_admin(self, access_token: str) -> bool:
        """
        Проверка является ли пользователь администратором
        
        Args:
            access_token: JWT токен пользователя
            
        Returns:
            True если администратор
        """
        try:
            # Получаем пользователя по токену
            user_response = self.anon_client.auth.get_user(access_token)
            
            if not user_response or not user_response.user:
                return False
            
            # Проверяем флаг is_admin в профиле
            profile = self.service_client.table('profiles').select('is_admin').eq('id', user_response.user.id).single().execute()
            
            return profile.data.get('is_admin', False) if profile.data else False
            
        except Exception as e:
            logger.error(f"Ошибка проверки админ прав: {e}")
            return False

    def get_user_from_token(self, access_token: str) -> Optional[Dict]:
        """
        Получение информации о пользователе из токена
        
        Args:
            access_token: JWT токен
            
        Returns:
            Словарь с данными пользователя или None
        """
        try:
            user_response = self.anon_client.auth.get_user(access_token)
            
            if not user_response or not user_response.user:
                return None
            
            # Получаем профиль из БД
            profile = self.service_client.table('profiles').select('*').eq('id', user_response.user.id).single().execute()
            
            if not profile.data:
                return None
            
            return {
                'user_id': user_response.user.id,
                'telegram_id': profile.data['telegram_id'],
                'telegram_username': profile.data.get('telegram_username'),
                'full_name': profile.data.get('full_name'),
                'is_admin': profile.data.get('is_admin', False)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователя из токена: {e}")
            return None

    def create_admin_user(self, telegram_id: int, username: str = None, full_name: str = None) -> Dict:
        """
        Создание администратора
        
        Args:
            telegram_id: Telegram ID администратора
            username: Telegram username
            full_name: Полное имя
            
        Returns:
            Данные пользователя с токеном
        """
        try:
            # Создаем обычного пользователя
            user_data = self.create_user_from_telegram(telegram_id, username, full_name)
            
            # Устанавливаем is_admin = true через service client
            self.service_client.table('profiles').update({
                'is_admin': True
            }).eq('id', user_data['user_id']).execute()
            
            logger.info(f"Создан администратор: telegram_id={telegram_id}")
            
            user_data['is_admin'] = True
            return user_data
            
        except Exception as e:
            logger.error(f"Ошибка создания администратора: {e}")
            raise

    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Обновление access токена
        
        Args:
            refresh_token: Refresh токен
            
        Returns:
            Новый access_token и expires_in
        """
        try:
            refresh_response = self.anon_client.auth.refresh_session(refresh_token)
            
            return {
                'access_token': refresh_response.session.access_token,
                'refresh_token': refresh_response.session.refresh_token,
                'expires_in': refresh_response.session.expires_in
            }
            
        except Exception as e:
            logger.error(f"Ошибка обновления токена: {e}")
            raise

    def sign_out(self, access_token: str) -> bool:
        """
        Выход пользователя
        
        Args:
            access_token: JWT токен
            
        Returns:
            True если успешно
        """
        try:
            self.anon_client.auth.sign_out(access_token)
            logger.info("Пользователь вышел из системы")
            return True
        except Exception as e:
            logger.error(f"Ошибка выхода: {e}")
            return False
