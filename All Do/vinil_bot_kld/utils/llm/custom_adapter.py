# -*- coding: utf-8 -*-
"""
Адаптер для кастомного LLM endpoint (OpenAI-совместимый)
"""

import os
import httpx
import logging
from typing import Dict
from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class CustomAdapter(BaseLLMAdapter):
    """Адаптер для работы с кастомным LLM API (OpenAI-compatible)"""

    def __init__(self):
        """Инициализация Custom адаптера"""
        super().__init__()
        self.api_key = os.getenv('CUSTOM_API_KEY')
        self.endpoint = os.getenv('CUSTOM_LLM_ENDPOINT')
        self.model = os.getenv('CUSTOM_MODEL', 'deepseek-chat')
        
    def validate_config(self) -> bool:
        """Проверка конфигурации custom endpoint"""
        if not self.api_key:
            logger.warning("CUSTOM_API_KEY не установлен")
            return False
        if not self.endpoint:
            logger.warning("CUSTOM_LLM_ENDPOINT не установлен")
            return False
        return True

    def get_timeout(self) -> int:
        """Получение таймаута для custom endpoint"""
        return self.timeout

    def estimate_cost(self, prompt_length: int) -> float:
        """
        Расчёт стоимости для custom endpoint
        Возвращаем 0, так как стоимость неизвестна
        """
        return 0.0

    def _build_prompt(self, record_data: Dict[str, any]) -> str:
        """Построение промпта для custom endpoint"""
        template = self._get_base_prompt_template()
        
        prompt = template.format(
            title=record_data.get('title', ''),
            artist=record_data.get('artist', ''),
            year=record_data.get('year', ''),
            genre=record_data.get('genre', ''),
            label=record_data.get('label', 'неизвестен'),
            country=record_data.get('country', 'неизвестна')
        )
        
        return prompt

    def _call_api(self, prompt: str) -> str:
        """Выполнение запроса к custom LLM endpoint"""
        if not self.validate_config():
            raise ValueError("Custom LLM API не сконфигурирован")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # OpenAI-совместимый формат запроса
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': self.temperature,
            'max_tokens': self.max_tokens
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Попытка извлечь текст из разных форматов ответа
                # OpenAI-compatible format
                if 'choices' in result and len(result['choices']) > 0:
                    if 'message' in result['choices'][0]:
                        return result['choices'][0]['message']['content']
                    elif 'text' in result['choices'][0]:
                        return result['choices'][0]['text']
                
                # Прямой текст
                if 'text' in result:
                    return result['text']
                    
                if 'content' in result:
                    return result['content']
                
                logger.error(f"Неожиданный формат ответа Custom API: {result}")
                raise ValueError("Неверный формат ответа от Custom LLM API")

        except httpx.TimeoutException as e:
            logger.error(f"Таймаут при запросе к Custom LLM API: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка от Custom LLM API: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при вызове Custom LLM API: {e}")
            raise

    def generate_description(self, record_data: Dict[str, any]) -> str:
        """Генерация описания через custom LLM endpoint"""
        try:
            prompt = self._build_prompt(record_data)
            description = self._call_api(prompt)
            logger.info(f"Описание успешно сгенерировано через Custom LLM для: {record_data.get('title')}")
            return description.strip()
        except Exception as e:
            logger.error(f"Не удалось сгенерировать описание через Custom LLM: {e}")
            return self.generate_template_description(record_data)
