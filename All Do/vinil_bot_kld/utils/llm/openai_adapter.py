# -*- coding: utf-8 -*-
"""
Адаптер для OpenAI GPT API
"""

import os
import logging
from typing import Dict
from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseLLMAdapter):
    """Адаптер для работы с OpenAI GPT API"""

    def __init__(self):
        """Инициализация OpenAI адаптера"""
        super().__init__()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
    def validate_config(self) -> bool:
        """Проверка конфигурации OpenAI"""
        if not self.api_key:
            logger.warning("OPENAI_API_KEY не установлен")
            return False
        return True

    def get_timeout(self) -> int:
        """Получение таймаута для OpenAI"""
        return self.timeout

    def estimate_cost(self, prompt_length: int) -> float:
        """
        Расчёт стоимости запроса к OpenAI
        GPT-4o-mini: ~$0.15 / 1M input tokens, ~$0.60 / 1M output tokens
        """
        # Приблизительная оценка для русского текста
        estimated_input_tokens = prompt_length * 0.5
        estimated_output_tokens = self.max_tokens
        
        # Стоимость в долларах
        cost_usd = (estimated_input_tokens / 1_000_000) * 0.15 + \
                   (estimated_output_tokens / 1_000_000) * 0.60
        
        # Конвертация в рубли (примерно 90 руб за доллар)
        cost_rub = cost_usd * 90
        return cost_rub

    def _build_prompt(self, record_data: Dict[str, any]) -> str:
        """Построение промпта для OpenAI"""
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
        """Выполнение запроса к OpenAI API"""
        if not self.validate_config():
            raise ValueError("OpenAI API не сконфигурирован")

        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=self.api_key,
                timeout=self.timeout
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content

        except ImportError:
            logger.error("Библиотека openai не установлена. Установите: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI API: {e}")
            raise

    def generate_description(self, record_data: Dict[str, any]) -> str:
        """Генерация описания через OpenAI GPT"""
        try:
            prompt = self._build_prompt(record_data)
            description = self._call_api(prompt)
            logger.info(f"Описание успешно сгенерировано через OpenAI для: {record_data.get('title')}")
            return description.strip()
        except Exception as e:
            logger.error(f"Не удалось сгенерировать описание через OpenAI: {e}")
            return self.generate_template_description(record_data)
