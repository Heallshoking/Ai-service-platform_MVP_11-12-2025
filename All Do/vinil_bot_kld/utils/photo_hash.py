# -*- coding: utf-8 -*-
"""
Утилиты для перцептивного хеширования изображений
Используется для обнаружения дубликатов фотографий
"""

import imagehash
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def calculate_photo_hash(image_path: str) -> str:
    """
    Вычисление перцептивного хеша изображения
    
    Args:
        image_path: Путь к файлу изображения
        
    Returns:
        Хеш изображения в виде строки
    """
    try:
        with Image.open(image_path) as img:
            # Используем pHash (perceptual hash) с размером 64 бита
            phash = imagehash.phash(img, hash_size=8)
            return str(phash)
            
    except Exception as e:
        logger.error(f"Ошибка вычисления хеша изображения: {e}")
        raise


def compare_hashes(hash1: str, hash2: str, threshold: int = 5) -> bool:
    """
    Сравнение двух хешей изображений
    
    Args:
        hash1: Первый хеш
        hash2: Второй хеш
        threshold: Порог различия (hamming distance). По умолчанию 5
        
    Returns:
        True если изображения похожи, False иначе
    """
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        
        # Вычисление расстояния Хэмминга
        distance = h1 - h2
        
        return distance <= threshold
        
    except Exception as e:
        logger.error(f"Ошибка сравнения хешей: {e}")
        return False


def get_hamming_distance(hash1: str, hash2: str) -> int:
    """
    Получение расстояния Хэмминга между двумя хешами
    
    Args:
        hash1: Первый хеш
        hash2: Второй хеш
        
    Returns:
        Расстояние Хэмминга
    """
    try:
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)
        
        return h1 - h2
        
    except Exception as e:
        logger.error(f"Ошибка вычисления расстояния: {e}")
        return 999  # Возвращаем большое значение в случае ошибки
