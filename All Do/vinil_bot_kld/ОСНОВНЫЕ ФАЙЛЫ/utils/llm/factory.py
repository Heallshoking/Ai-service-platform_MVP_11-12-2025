# -*- coding: utf-8 -*-
"""
Фабрика для создания LLM адаптеров
Динамический выбор провайдера на основе переменных окружения
"""

import os
import logging
from typing import Optional, List
from .base_adapter import BaseLLMAdapter
from .qwen_adapter import QwenAdapter
from .openai_adapter import OpenAIAdapter
from .claude_adapter import ClaudeAdapter
from .yandex_adapter import YandexAdapter
from .custom_adapter import CustomAdapter

logger = logging.getLogger(__name__)


class UnsupportedProviderError(Exception):
    """Исключение для неподдерживаемого провайдера"""
    pass


def get_adapter(provider_name: Optional[str] = None) -> BaseLLMAdapter:
    """
    Создание LLM адаптера на основе конфигурации
    
    Args:
        provider_name: Имя провайдера (опционально). 
                      Если не указано, читается из LLM_PROVIDER
    
    Returns:
        Экземпляр адаптера для выбранного провайдера
        
    Raises:
        UnsupportedProviderError: Если провайдер не поддерживается
    """
    # Если провайдер не указан, читаем из переменной окружения
    if provider_name is None:
        provider_name = os.getenv('LLM_PROVIDER', 'qwen')
    
    # Нормализуем имя провайдера к нижнему регистру
    provider_name = provider_name.lower().strip()
    
    logger.info(f"Создание LLM адаптера для провайдера: {provider_name}")
    
    # Маппинг провайдеров на классы адаптеров
    providers_map = {
        'qwen': QwenAdapter,
        'openai': OpenAIAdapter,
        'claude': ClaudeAdapter,
        'yandex': YandexAdapter,
        'custom': CustomAdapter
    }
    
    # Проверка поддержки провайдера
    if provider_name not in providers_map:
        available = ', '.join(providers_map.keys())
        error_msg = f"Провайдер '{provider_name}' не поддерживается. Доступные: {available}"
        logger.error(error_msg)
        raise UnsupportedProviderError(error_msg)
    
    # Создание экземпляра адаптера
    adapter_class = providers_map[provider_name]
    adapter = adapter_class()
    
    # Валидация конфигурации адаптера
    if not adapter.validate_config():
        logger.warning(f"Конфигурация провайдера '{provider_name}' невалидна. Попытка использовать fallback.")
        
        # Попытка получить fallback адаптер
        fallback_adapter = get_fallback_adapter()
        if fallback_adapter:
            logger.info(f"Используется fallback адаптер")
            return fallback_adapter
        else:
            logger.warning(f"Fallback провайдер не настроен. Используем основной адаптер с возможными ошибками.")
    
    return adapter


def get_fallback_adapter() -> Optional[BaseLLMAdapter]:
    """
    Получение резервного LLM адаптера
    
    Returns:
        Экземпляр fallback адаптера или None если не настроен
    """
    fallback_provider = os.getenv('LLM_FALLBACK_PROVIDER')
    
    if not fallback_provider:
        logger.info("LLM_FALLBACK_PROVIDER не установлен")
        return None
    
    fallback_provider = fallback_provider.lower().strip()
    logger.info(f"Создание fallback адаптера: {fallback_provider}")
    
    try:
        # Используем рекурсивный вызов get_adapter, но без fallback чтобы избежать циклов
        # Временно очищаем LLM_FALLBACK_PROVIDER
        original_fallback = os.environ.get('LLM_FALLBACK_PROVIDER')
        if 'LLM_FALLBACK_PROVIDER' in os.environ:
            del os.environ['LLM_FALLBACK_PROVIDER']
        
        adapter = get_adapter(fallback_provider)
        
        # Восстанавливаем LLM_FALLBACK_PROVIDER
        if original_fallback:
            os.environ['LLM_FALLBACK_PROVIDER'] = original_fallback
        
        if adapter.validate_config():
            return adapter
        else:
            logger.warning(f"Fallback провайдер '{fallback_provider}' также невалиден")
            return None
            
    except UnsupportedProviderError as e:
        logger.error(f"Ошибка создания fallback адаптера: {e}")
        return None


def validate_provider(provider_name: str) -> bool:
    """
    Проверка поддержки провайдера
    
    Args:
        provider_name: Имя провайдера для проверки
        
    Returns:
        True если провайдер поддерживается, False иначе
    """
    supported_providers = ['qwen', 'openai', 'claude', 'yandex', 'custom']
    return provider_name.lower().strip() in supported_providers


def list_available_providers() -> List[str]:
    """
    Получение списка доступных провайдеров
    
    Returns:
        Список имён поддерживаемых провайдеров
    """
    return ['qwen', 'openai', 'claude', 'yandex', 'custom']


# Экспортируемые функции
__all__ = [
    'get_adapter',
    'get_fallback_adapter',
    'validate_provider',
    'list_available_providers',
    'UnsupportedProviderError'
]
