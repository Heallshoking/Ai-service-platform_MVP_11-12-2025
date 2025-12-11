# -*- coding: utf-8 -*-
"""
Адаптер для Qwen Max API
"""

import os
import httpx
import logging
from typing import Dict
from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class QwenAdapter(BaseLLMAdapter):
    """Адаптер для работы с Qwen Max API"""

    def __init__(self):
        """Инициализация Qwen адаптера"""
        super().__init__()
        self.api_key = os.getenv('QWEN_API_KEY')
        self.endpoint = os.getenv('QWEN_API_ENDPOINT', 
                                   'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
        self.model = os.getenv('QWEN_MODEL', 'qwen-max')

    def validate_config(self) -> bool:
        """Проверка конфигурации Qwen"""
        if not self.api_key:
            logger.warning("QWEN_API_KEY не установлен")
            return False
        if not self.endpoint:
            logger.warning("QWEN_API_ENDPOINT не установлен")
            return False
        return True

    def get_timeout(self) -> int:
        """Получение таймаута для Qwen"""
        return self.timeout

    def estimate_cost(self, prompt_length: int) -> float:
        """
        Расчёт стоимости запроса к Qwen Max
        Примерная стоимость: ~0.02 руб за 1000 токенов
        """
        # Приблизительная оценка: 1 символ ≈ 0.5 токена для русского текста
        estimated_tokens = (prompt_length + self.max_tokens) * 0.5
        cost = (estimated_tokens / 1000) * 0.02
        return cost

    def _build_prompt(self, record_data: Dict[str, any]) -> str:
        """Построение промпта для Qwen"""
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
        """Выполнение запроса к Qwen Max API"""
        if not self.validate_config():
            raise ValueError("Qwen API не сконфигурирован")

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            },
            'parameters': {
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            }
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
                
                # Извлечение текста из ответа Qwen
                if 'output' in result and 'text' in result['output']:
                    return result['output']['text']
                elif 'output' in result and 'choices' in result['output']:
                    return result['output']['choices'][0]['message']['content']
                else:
                    logger.error(f"Неожиданный формат ответа Qwen: {result}")
                    raise ValueError("Неверный формат ответа от Qwen API")

        except httpx.TimeoutException as e:
            logger.error(f"Таймаут при запросе к Qwen API: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка от Qwen API: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при вызове Qwen API: {e}")
            raise

    def generate_description(self, record_data: Dict[str, any]) -> str:
        """Генерация описания через Qwen Max"""
        try:
            prompt = self._build_prompt(record_data)
            description = self._call_api(prompt)
            logger.info(f"Описание успешно сгенерировано через Qwen для: {record_data.get('title')}")
            return description.strip()
        except Exception as e:
            logger.error(f"Не удалось сгенерировать описание через Qwen: {e}")
            # Возвращаем шаблонное описание как fallback
            return self.generate_template_description(record_data)
