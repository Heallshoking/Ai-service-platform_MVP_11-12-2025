# -*- coding: utf-8 -*-
"""
Базовый абстрактный класс для LLM адаптеров
"""

from abc import ABC, abstractmethod
from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)


class BaseLLMAdapter(ABC):
    """
    Абстрактный базовый класс для всех LLM провайдеров.
    Все адаптеры должны наследовать этот класс и реализовывать абстрактные методы.
    """

    def __init__(self):
        """Инициализация базового адаптера"""
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '500'))
        self.timeout = int(os.getenv('LLM_TIMEOUT', '30'))

    @abstractmethod
    def generate_description(self, record_data: Dict[str, any]) -> str:
        """
        Генерация описания виниловой пластинки
        
        Args:
            record_data: Словарь с данными пластинки (title, artist, year, genre, label, country)
            
        Returns:
            Сгенерированное описание
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Проверка наличия необходимых учётных данных API
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        pass

    @abstractmethod
    def get_timeout(self) -> int:
        """
        Получение таймаута для данного провайдера
        
        Returns:
            Таймаут в секундах
        """
        pass

    @abstractmethod
    def estimate_cost(self, prompt_length: int) -> float:
        """
        Расчёт приблизительной стоимости запроса
        
        Args:
            prompt_length: Длина промпта в символах
            
        Returns:
            Приблизительная стоимость в рублях
        """
        pass

    @abstractmethod
    def _build_prompt(self, record_data: Dict[str, any]) -> str:
        """
        Построение промпта для конкретного провайдера
        
        Args:
            record_data: Данные пластинки
            
        Returns:
            Форматированный промпт
        """
        pass

    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """
        Выполнение API запроса к провайдеру
        
        Args:
            prompt: Промпт для генерации
            
        Returns:
            Сгенерированный текст
        """
        pass

    def generate_template_description(self, record_data: Dict[str, any]) -> str:
        """
        Генерация описания по шаблону (fallback если LLM недоступен)
        
        Args:
            record_data: Данные пластинки
            
        Returns:
            Шаблонное описание
        """
        title = record_data.get('title', 'Неизвестно')
        artist = record_data.get('artist', 'Неизвестный исполнитель')
        year = record_data.get('year', '')
        genre = record_data.get('genre', 'винил')
        label = record_data.get('label', '')
        country = record_data.get('country', '')

        description = f'"{title}" от {artist}'
        if year:
            description += f' ({year})'
        description += f' — редкая находка для ценителей {genre}.'
        
        if label:
            description += f' Издание лейбла {label}'
            if country:
                description += f', пресс {country}.'
            else:
                description += '.'
        elif country:
            description += f' Пресс {country}.'

        return description

    def _get_base_prompt_template(self) -> str:
        """
        Получение базового шаблона промпта
        
        Returns:
            Шаблон промпта
        """
        return """Роль: Ты — музыковед Полина Костина, эксперт по виниловым пластинкам с 15-летним стажем.

Задача: Напиши описание виниловой пластинки для коллекционеров и меломанов. Описание должно быть:
- Тёплым и эмоциональным, но профессиональным
- С историческим контекстом эпохи и лейбла
- С упоминанием музыкальной значимости
- С деталями о редкости и особенностях pressing'а
- Длина: 150-250 слов

Данные пластинки:
Название: {title}
Исполнитель: {artist}
Год: {year}
Жанр: {genre}
Лейбл: {label}
Страна: {country}

Не используй шаблонные фразы. Пиши так, будто рассказываешь другу о находке на барахолке."""
