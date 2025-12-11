# -*- coding: utf-8 -*-
"""
Адаптер для YandexGPT API
"""

import os
import httpx
import logging
from typing import Dict
from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class YandexAdapter(BaseLLMAdapter):
    """Адаптер для работы с YandexGPT API"""

    def __init__(self):
        """Инициализация Yandex адаптера"""
        super().__init__()
        self.api_key = os.getenv('YANDEX_API_KEY')
        self.folder_id = os.getenv('YANDEX_FOLDER_ID')
        self.model = 'yandexgpt/latest'
        
    def validate_config(self) -> bool:
        """Проверка конфигурации YandexGPT"""
        if not self.api_key:
            logger.warning("YANDEX_API_KEY не установлен")
            return False
        if not self.folder_id:
            logger.warning("YANDEX_FOLDER_ID не установлен")
            return False
        return True

    def get_timeout(self) -> int:
        """Получение таймаута для YandexGPT"""
        return self.timeout

    def estimate_cost(self, prompt_length: int) -> float:
        """
        Расчёт стоимости запроса к YandexGPT
        Примерная стоимость: ~1 руб за 1000 токенов
        """
        estimated_tokens = (prompt_length + self.max_tokens) * 0.5
        cost = (estimated_tokens / 1000) * 1.0
        return cost

    def _build_prompt(self, record_data: Dict[str, any]) -> str:
        """Построение промпта для YandexGPT"""
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
        """Выполнение запроса к YandexGPT API"""
        if not self.validate_config():
            raise ValueError("YandexGPT API не сконфигурирован")

        endpoint = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        headers = {
            'Authorization': f'Api-Key {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {
                "stream": False,
                "temperature": self.temperature,
                "maxTokens": str(self.max_tokens)
            },
            "messages": [
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    endpoint,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Извлечение текста из ответа YandexGPT
                if 'result' in result and 'alternatives' in result['result']:
                    return result['result']['alternatives'][0]['message']['text']
                else:
                    logger.error(f"Неожиданный формат ответа YandexGPT: {result}")
                    raise ValueError("Неверный формат ответа от YandexGPT API")

        except httpx.TimeoutException as e:
            logger.error(f"Таймаут при запросе к YandexGPT API: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка от YandexGPT API: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при вызове YandexGPT API: {e}")
            raise

    def generate_description(self, record_data: Dict[str, any]) -> str:
        """Генерация описания через YandexGPT"""
        try:
            prompt = self._build_prompt(record_data)
            description = self._call_api(prompt)
            logger.info(f"Описание успешно сгенерировано через YandexGPT для: {record_data.get('title')}")
            return description.strip()
        except Exception as e:
            logger.error(f"Не удалось сгенерировать описание через YandexGPT: {e}")
            return self.generate_template_description(record_data)
