# -*- coding: utf-8 -*-
"""
Модуль генерации статических данных для фронтенда
Экспортирует каталог из Google Sheets в JSON формат
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils.sheets_client import SheetsClient

logger = logging.getLogger(__name__)


class StaticExporter:
    """Генератор статических данных каталога"""
    
    def __init__(self):
        """Инициализация экспортера"""
        self.sheets_client = SheetsClient()
    
    def export_catalog_to_json(self, output_dir: str = "./static_export") -> Dict[str, Any]:
        """
        Экспортирует весь каталог в JSON файл
        
        Args:
            output_dir: Директория для сохранения файлов
            
        Returns:
            Статистика экспорта
        """
        try:
            # Создание директории если не существует
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Получение всех записей из каталога
            raw_records = self.sheets_client.get_all_records(filters=None)
            
            # Подготовка записей для экспорта
            export_records = []
            for idx, record in enumerate(raw_records):
                # Безопасное преобразование типов
                try:
                    year_val = int(record.get('Год', 0))
                except (ValueError, TypeError):
                    year_val = 0
                
                try:
                    price_val = float(record.get('Цена', 0))
                except (ValueError, TypeError):
                    price_val = 0.0
                
                try:
                    stock_val = int(record.get('Stock_Count', 1) or 1)
                except (ValueError, TypeError):
                    stock_val = 1
                
                # Формирование записи
                export_record = {
                    "id": f"row_{idx + 2}",
                    "article_id": record.get('Артикул', ''),
                    "title": record.get('Название', ''),
                    "artist": record.get('Исполнитель', ''),
                    "genre": record.get('Жанр', ''),
                    "year": year_val,
                    "label": record.get('Лейбл'),
                    "country": record.get('Страна', ''),
                    "format": record.get('Формат'),
                    "condition": record.get('Состояние', ''),
                    "price": price_val,
                    "photo_url": record.get('ФОТО_URL'),
                    "status": record.get('Статус', ''),
                    "description": record.get('Описание'),
                    "seo_title": record.get('SEO_Title'),
                    "seo_description": record.get('SEO_Description'),
                    "stock_count": stock_val
                }
                
                export_records.append(export_record)
            
            # Сохранение каталога
            catalog_path = os.path.join(output_dir, "catalog.json")
            catalog_data = {
                "generated_at": datetime.now().isoformat(),
                "total_records": len(export_records),
                "records": export_records
            }
            
            with open(catalog_path, 'w', encoding='utf-8') as f:
                json.dump(catalog_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Экспортировано {len(export_records)} записей в {catalog_path}")
            
            # Опционально: создание отдельных файлов для каждого товара
            self._export_individual_records(export_records, output_dir)
            
            return {
                "status": "success",
                "exported_records": len(export_records),
                "catalog_path": catalog_path,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта каталога: {e}")
            raise
    
    def _export_individual_records(self, records: List[Dict], output_dir: str):
        """
        Создает отдельные JSON файлы для каждого товара
        
        Args:
            records: Список записей
            output_dir: Базовая директория для экспорта
        """
        try:
            products_dir = os.path.join(output_dir, "products")
            Path(products_dir).mkdir(parents=True, exist_ok=True)
            
            for record in records:
                article_id = record.get('article_id', '')
                if not article_id:
                    continue
                
                # Безопасное имя файла
                safe_article_id = article_id.replace('/', '_').replace('\\', '_')
                product_path = os.path.join(products_dir, f"{safe_article_id}.json")
                
                with open(product_path, 'w', encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Создано {len(records)} индивидуальных файлов товаров")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка создания индивидуальных файлов: {e}")


# Singleton instance
_exporter_instance: Optional[StaticExporter] = None


def get_exporter() -> StaticExporter:
    """Получение singleton экземпляра экспортера"""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = StaticExporter()
    return _exporter_instance


def export_catalog_to_json(output_dir: str = "./static_export") -> Dict[str, Any]:
    """
    Удобная функция для экспорта каталога
    
    Args:
        output_dir: Директория для сохранения
        
    Returns:
        Статистика экспорта
    """
    exporter = get_exporter()
    return exporter.export_catalog_to_json(output_dir)
