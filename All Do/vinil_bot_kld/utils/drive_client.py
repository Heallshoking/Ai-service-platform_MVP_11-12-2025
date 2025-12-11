# -*- coding: utf-8 -*-
"""
Клиент для работы с Google Drive
Загрузка и управление фотографиями виниловых пластинок
"""

import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime

logger = logging.getLogger(__name__)


class DriveClient:
    """Клиент для работы с Google Drive"""

    def __init__(self):
        """Инициализация клиента Google Drive"""
        self.credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.folder_id = os.getenv('DRIVE_FOLDER_ID')
        
        if not self.folder_id:
            raise ValueError("DRIVE_FOLDER_ID не установлен в переменных окружения")
        
        self.service = None
        self._connect()

    def _connect(self):
        """Подключение к Google Drive API"""
        try:
            scopes = ['https://www.googleapis.com/auth/drive']
            
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Успешное подключение к Google Drive API")
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Drive: {e}")
            raise

    def upload_photo(self, file_path: str, record_id: int) -> str:
        """
        Загрузка фото в Google Drive
        
        Args:
            file_path: Путь к файлу фото
            record_id: ID записи виниловой пластинки
            
        Returns:
            Публичный URL загруженного фото
        """
        try:
            # Генерация имени файла
            timestamp = int(datetime.now().timestamp())
            file_extension = os.path.splitext(file_path)[1]
            file_name = f"record_{record_id}_{timestamp}{file_extension}"
            
            # Метаданные файла
            file_metadata = {
                'name': file_name,
                'parents': [self.folder_id]
            }
            
            # Загрузка файла
            media = MediaFileUpload(
                file_path,
                mimetype='image/jpeg',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            # Настройка публичного доступа
            self.service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            # Генерация публичного URL
            public_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            
            logger.info(f"Фото успешно загружено: {file_name} -> {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Ошибка загрузки фото в Google Drive: {e}")
            raise

    def delete_photo(self, file_id: str):
        """
        Удаление фото из Google Drive
        
        Args:
            file_id: ID файла в Google Drive
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Фото успешно удалено: {file_id}")
            
        except Exception as e:
            logger.error(f"Ошибка удаления фото: {e}")
            raise
