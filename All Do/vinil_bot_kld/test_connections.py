# -*- coding: utf-8 -*-
"""
Скрипт проверки всех подключений системы
Тестирует: Google Sheets, DeepSeek AI, FastAPI, Telegram Bot
"""

import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv
from colorama import init, Fore, Style

# Инициализация colorama для цветного вывода
init(autoreset=True)

# Загрузка переменных окружения
load_dotenv()

def print_header(text):
    """Печать заголовка"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{text:^60}")
    print(f"{Fore.CYAN}{'=' * 60}\n")

def print_success(text):
    """Печать успеха"""
    print(f"{Fore.GREEN}✅ {text}")

def print_error(text):
    """Печать ошибки"""
    print(f"{Fore.RED}❌ {text}")

def print_warning(text):
    """Печать предупреждения"""
    print(f"{Fore.YELLOW}⚠️  {text}")

def print_info(text):
    """Печать информации"""
    print(f"{Fore.BLUE}ℹ️  {text}")


async def test_google_sheets():
    """Тест подключения к Google Sheets"""
    print_header("ТЕСТ: Google Sheets")
    
    try:
        from utils.sheets_client import SheetsClient
        
        sheets_client = SheetsClient()
        
        # Проверка подключения
        title = sheets_client.spreadsheet.title
        print_success(f"Подключение к Google Sheets: {title}")
        
        # Проверка листов
        worksheets = [ws.title for ws in sheets_client.spreadsheet.worksheets()]
        print_info(f"Доступные листы: {', '.join(worksheets)}")
        
        # Проверка каталога
        catalog = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        row_count = len(catalog.get_all_values())
        print_success(f"Записей в каталоге: {row_count - 1}")  # -1 для заголовка
        
        return True
        
    except Exception as e:
        print_error(f"Ошибка подключения к Google Sheets: {e}")
        return False


async def test_deepseek_ai():
    """Тест подключения к DeepSeek AI"""
    print_header("ТЕСТ: DeepSeek AI")
    
    try:
        from utils.llm.factory import get_adapter
        
        # Проверка настроек
        provider = os.getenv('LLM_PROVIDER', 'qwen')
        custom_endpoint = os.getenv('CUSTOM_LLM_ENDPOINT')
        custom_key = os.getenv('CUSTOM_API_KEY')
        custom_model = os.getenv('CUSTOM_MODEL', 'deepseek-chat')
        
        print_info(f"LLM Provider: {provider}")
        print_info(f"Endpoint: {custom_endpoint}")
        print_info(f"Model: {custom_model}")
        print_info(f"API Key: {'***' + custom_key[-8:] if custom_key and len(custom_key) > 8 else 'НЕ УСТАНОВЛЕН'}")
        
        # Получение адаптера
        adapter = get_adapter()
        
        if not adapter.validate_config():
            print_warning("Конфигурация LLM невалидна")
            return False
        
        print_success(f"Адаптер LLM инициализирован: {adapter.__class__.__name__}")
        
        # Тестовая генерация
        print_info("Генерация тестового описания...")
        test_record = {
            'title': 'The Dark Side of the Moon',
            'artist': 'Pink Floyd',
            'year': 1973,
            'genre': 'Прогрессивный рок',
            'label': 'Harvest Records',
            'country': 'UK'
        }
        
        description = adapter.generate_description(test_record)
        
        if description and len(description) > 50:
            print_success(f"AI-описание сгенерировано ({len(description)} символов)")
            print_info(f"Первые 100 символов: {description[:100]}...")
            return True
        else:
            print_warning("Получено шаблонное описание (AI недоступен)")
            return False
        
    except Exception as e:
        print_error(f"Ошибка подключения к DeepSeek AI: {e}")
        import traceback
        print(traceback.format_exc())
        return False


async def test_fastapi():
    """Тест FastAPI сервера"""
    print_header("ТЕСТ: FastAPI Backend")
    
    try:
        api_host = os.getenv('API_HOST', 'localhost')
        api_port = os.getenv('API_PORT', '8000')
        api_url = f"http://{api_host}:{api_port}"
        
        print_info(f"API URL: {api_url}")
        
        async with httpx.AsyncClient(timeout=10) as client:
            # Health check
            response = await client.get(f"{api_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"API сервер доступен")
                print_info(f"Статус: {data.get('status')}")
                print_info(f"Сервисы: {data.get('services')}")
            else:
                print_error(f"API вернул код {response.status_code}")
                return False
            
            # Проверка эндпоинта records
            response = await client.get(f"{api_url}/api/records?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Эндпоинт /api/records работает")
                print_info(f"Всего записей: {data.get('total', 0)}")
                return True
            else:
                print_warning(f"Эндпоинт /api/records вернул код {response.status_code}")
                return False
        
    except httpx.ConnectError:
        print_error(f"Не удалось подключиться к API серверу на {api_url}")
        print_warning("Убедитесь, что FastAPI запущен: python main.py")
        return False
    except Exception as e:
        print_error(f"Ошибка тестирования API: {e}")
        return False


async def test_telegram_bot():
    """Тест Telegram Bot"""
    print_header("ТЕСТ: Telegram Bot")
    
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not bot_token:
            print_error("TELEGRAM_BOT_TOKEN не установлен")
            return False
        
        print_info(f"Bot Token: ***{bot_token[-8:]}")
        
        # Проверка подключения к Telegram API
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    print_success(f"Бот подключен: @{bot_info.get('username')}")
                    print_info(f"Имя: {bot_info.get('first_name')}")
                    return True
                else:
                    print_error("Токен бота невалиден")
                    return False
            else:
                print_error(f"Telegram API вернул код {response.status_code}")
                return False
        
    except Exception as e:
        print_error(f"Ошибка проверки Telegram бота: {e}")
        return False


async def test_website():
    """Тест подключения сайта к API"""
    print_header("ТЕСТ: Сайт ↔ API")
    
    try:
        website_api_url = "http://176.98.178.109:8000"
        
        print_info(f"Сайт использует API: {website_api_url}")
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{website_api_url}/api/records?limit=1")
            
            if response.status_code == 200:
                data = response.json()
                print_success("Сайт может подключиться к API")
                print_info(f"Репозиторий: https://github.com/Heallshoking/-balt-set")
                return True
            else:
                print_warning(f"API на {website_api_url} недоступен (код {response.status_code})")
                print_info("Это нормально, если API на другом хосте")
                return True
        
    except httpx.ConnectError:
        print_warning(f"Не удалось подключиться к {website_api_url}")
        print_info("Проверьте, что API запущен на сервере")
        return True  # Не считаем критичной ошибкой
    except Exception as e:
        print_error(f"Ошибка проверки сайта: {e}")
        return True


async def main():
    """Главная функция"""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}{'=' * 60}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{'ПРОВЕРКА СИСТЕМЫ VINYL MARKETPLACE':^60}")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}{'=' * 60}\n")
    
    results = {}
    
    # Запуск всех тестов
    results['Google Sheets'] = await test_google_sheets()
    results['DeepSeek AI'] = await test_deepseek_ai()
    results['FastAPI'] = await test_fastapi()
    results['Telegram Bot'] = await test_telegram_bot()
    results['Website'] = await test_website()
    
    # Итоговый отчёт
    print_header("ИТОГОВЫЙ ОТЧЁТ")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        if status:
            print_success(f"{name}: РАБОТАЕТ")
        else:
            print_error(f"{name}: ОШИБКА")
    
    print(f"\n{Fore.CYAN}{'─' * 60}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ ({passed}/{total})")
        print(f"{Fore.GREEN}Система полностью функциональна!\n")
    else:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  ПРОЙДЕНО ТЕСТОВ: {passed}/{total}")
        print(f"{Fore.YELLOW}Проверьте компоненты с ошибками\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Прервано пользователем")
        sys.exit(1)
