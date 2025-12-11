# -*- coding: utf-8 -*-
"""
LLM адаптеры для генерации описаний виниловых пластинок
"""

from .base_adapter import BaseLLMAdapter
from .factory import get_adapter, get_fallback_adapter

__all__ = ['BaseLLMAdapter', 'get_adapter', 'get_fallback_adapter']
