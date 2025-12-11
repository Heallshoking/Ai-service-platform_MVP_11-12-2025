# -*- coding: utf-8 -*-
"""
Адаптер для Anthropic Claude API
"""

import os
import logging
from typing import Dict
from .base_adapter import BaseLLMAdapter

logger = logging.getLogger(__name__)


class ClaudeAdapter(BaseLLMAdapter):
    """Адаптер для работы с Anthropic Claude API"""

    def __init__(self):
        """Инициализация Claude адаптера"""
        super().__init__()
        self.api_key = os.getenv('CLAUDE_API_KEY')
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-haiku-20240307')
        
    def validate_config(self) -> bool:
        """Проверка конфигурации Claude"""
        if not self.api_key:
            logger.warning("CLAUDE_API_KEY не установлен")
            return False
        return True

    def get_timeout(self) -> int:
        """Получение таймаута для Claude"""
        return self.timeout

    def estimate_cost(self, prompt_length: int) -> float:
        """
        Расчёт стоимости запроса к Claude
        Claude 3 Haiku: ~$0.25 / 1M input tokens, ~$1.25 / 1M output tokens
        """
        estimated_input_tokens = prompt_length * 0.5
        estimated_output_tokens = self.max_tokens
        
        cost_usd = (estimated_input_tokens / 1_000_000) * 0.25 + \
                   (estimated_output_tokens / 1_000_000) * 1.25
        
        cost_rub = cost_usd * 90
        return cost_rub

    def _build_prompt(self, record_data: Dict[str, any]) -> str:
        """Построение промпта для Claude"""
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
        """Выполнение запроса к Claude API"""
        if not self.validate_config():
            raise ValueError("Claude API не сконфигурирован")

        try:
            from anthropic import Anthropic
            
            client = Anthropic(
                api_key=self.api_key,
                timeout=self.timeout
            )
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text

        except ImportError:
            logger.error("Библиотека anthropic не установлена. Установите: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Ошибка при вызове Claude API: {e}")
            raise

    def generate_description(self, record_data: Dict[str, any]) -> str:
        """Генерация описания через Claude"""
        try:
            prompt = self._build_prompt(record_data)
            description = self._call_api(prompt)
            logger.info(f"Описание успешно сгенерировано через Claude для: {record_data.get('title')}")
            return description.strip()
        except Exception as e:
            logger.error(f"Не удалось сгенерировать описание через Claude: {e}")
            return self.generate_template_description(record_data)
