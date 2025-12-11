#!/usr/bin/env python3
"""
🏠 МАССОВЫЙ ИМПОРТ АДРЕСОВ В СПРАВОЧНИК

Этот скрипт добавляет адреса из TXT-файла в Google Sheets справочник.

📝 ФОРМАТ ВХОДНОГО ФАЙЛА (addresses.txt):

**Формат 1: Улица с номерами через запятую**
Грига: 15, 16, 18, 20, 22, 24, 26, 36, 38, 39, 40, 42, 42-48, 44
Краснопрудная: 1, 1-3, 2, 2-2А, 2А, 3, 4, 4-4А

**Формат 2: Адрес на каждой строке**
Горького 199
Ленинский проспект 81
Октябрьская 12

🔧 КАК ИСПОЛЬЗОВАТЬ:
1. Создай файл addresses.txt в той же папке, что и этот скрипт
2. Заполни его адресами (в любом из форматов выше)
3. Запусти: python3 mass_import_addresses.py

⚙️ ЧТО ПРОИСХОДИТ:
- Скрипт читает каждый адрес
- **Проверяет дубликаты** (точное совпадение + похожие адреса)
- Геокодирует его (ищет координаты и район)
- Добавляет в справочник, если адреса там еще нет
- Если координаты не найдены - все равно добавляет (админ поправит потом)

🎯 БЕЗОПАСНОСТЬ:
- Дубликаты НЕ добавляются (проверка на точное + нечеткое совпадение)
- Все операции логируются
- Есть задержка между запросами (0.5 сек) чтобы не перегрузить API
"""

import os
import sys
import time
import logging
from typing import Optional, Tuple
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==================== НАСТРОЙКИ ====================

# Файл с адресами (по одному на строке)
ADDRESSES_FILE = "addresses.txt"

# Задержка между запросами к API геокодера (секунды)
GEOCODE_DELAY = 0.5

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('mass_import.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# ==================== ЗАГРУЗКА .ENV ====================

load_dotenv()
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")

if not SPREADSHEET_URL:
    logging.error("❌ SPREADSHEET_URL не найден в .env файле!")
    sys.exit(1)

# ==================== ПОДКЛЮЧЕНИЕ К GOOGLE SHEETS ====================

try:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json",
        scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(SPREADSHEET_URL)
    sprav = spreadsheet.worksheet("Справочник адресов")
    logging.info("✅ Подключение к Google Sheets успешно!")
except Exception as e:
    logging.error(f"❌ Ошибка подключения к Google Sheets: {e}")
    sys.exit(1)

# ==================== ФУНКЦИИ ГЕОКОДИРОВАНИЯ ====================

def geocode_yandex(address: str) -> Optional[Tuple[float, float, str]]:
    """Геокодирование через Яндекс API"""
    if not YANDEX_API_KEY:
        return None
    
    import requests
    try:
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": YANDEX_API_KEY,
            "geocode": f"Калининград, {address}",
            "format": "json"
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        members = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
        if not members:
            return None
        
        geo_obj = members[0].get("GeoObject", {})
        pos = geo_obj.get("Point", {}).get("pos", "").split()
        if len(pos) != 2:
            return None
        
        lng, lat = float(pos[0]), float(pos[1])
        
        # Извлекаем район
        components = geo_obj.get("metaDataProperty", {}).get("GeocoderMetaData", {}).get("Address", {}).get("Components", [])
        district = "Центральный"  # По умолчанию
        for comp in components:
            if comp.get("kind") == "district":
                district = comp.get("name", district)
                break
        
        return lat, lng, district
    except Exception as e:
        logging.warning(f"⚠️ Ошибка геокодирования Yandex для '{address}': {e}")
        return None


def geocode_osm(address: str) -> Optional[Tuple[float, float, str]]:
    """Геокодирование через OpenStreetMap (Nominatim)"""
    import requests
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{address}, Калининград, Россия",
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "PromoBot/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if not data:
            return None
        
        lat = float(data[0]["lat"])
        lng = float(data[0]["lon"])
        district = "Центральный"  # OSM не всегда возвращает район
        
        return lat, lng, district
    except Exception as e:
        logging.warning(f"⚠️ Ошибка геокодирования OSM для '{address}': {e}")
        return None


def geocode_address(address: str) -> Optional[Tuple[float, float, str]]:
    """Геокодирование адреса (пробуем Yandex, потом OSM)"""
    result = geocode_yandex(address)
    if result:
        logging.info(f"  ✅ Yandex: {result}")
        return result
    
    result = geocode_osm(address)
    if result:
        logging.info(f"  ✅ OSM: {result}")
        return result
    
    logging.warning(f"  ⚠️ Координаты не найдены для '{address}'")
    return None


# ==================== ФУНКЦИИ РАБОТЫ СО СПРАВОЧНИКОМ ====================

def ensure_sheet_has_enough_rows(worksheet, required_rows: int, buffer: int = 100) -> None:
    """
    Автоматическое расширение таблицы, если недостаточно строк.
    
    Args:
        worksheet: Worksheet объект gspread
        required_rows: Минимальное количество строк
        buffer: Дополнительный запас строк (по умолчанию 100)
    
    🔥 КРИТИЧНО: ЗАЩИТА ОТ ОШИБКИ "Out of rows" при массовом импорте!
    """
    try:
        current_rows = worksheet.row_count
        if current_rows < required_rows + buffer:
            new_rows = required_rows + buffer
            worksheet.add_rows(new_rows - current_rows)
            logging.info(f"✅ Таблица '{worksheet.title}' расширена: {current_rows} → {new_rows} строк")
    except Exception as e:
        logging.error(f"❌ Ошибка расширения таблицы '{worksheet.title}': {e}")


def normalize_address(address: str) -> str:
    """Нормализация адреса для сравнения (убираем пробелы, приводим к нижнему регистру)"""
    import re
    # Убираем лишние пробелы и приводим к нижнему регистру
    normalized = re.sub(r'\s+', ' ', address.strip().lower())
    # Убираем "ул.", "улица", "проспект" и т.д.
    normalized = re.sub(r'^(ул\.|улица|пр\.|проспект|пер\.|переулок)\s+', '', normalized)
    return normalized


def is_similar_address(addr1: str, addr2: str) -> bool:
    """Проверка на похожие адреса (нечеткое сравнение)"""
    norm1 = normalize_address(addr1)
    norm2 = normalize_address(addr2)
    
    # Точное совпадение после нормализации
    if norm1 == norm2:
        return True
    
    # Проверка: адреса отличаются только буквами А, Б, В и т.д.
    # Например: "Горького 199" и "Горького 199А"
    import re
    base1 = re.sub(r'[а-яa-z]$', '', norm1)
    base2 = re.sub(r'[а-яa-z]$', '', norm2)
    if base1 == base2 and base1:
        return True
    
    return False


def address_exists(address: str) -> tuple[bool, str]:
    """Проверка, есть ли адрес в справочнике
    
    Returns:
        (exists, similar_address): exists=True если найден дубликат, similar_address - похожий адрес
    """
    try:
        all_addresses = sprav.col_values(1)[1:]  # Пропускаем заголовок
        
        # Точное совпадение
        if address in all_addresses:
            return True, address
        
        # Нечеткое совпадение
        for existing in all_addresses:
            if is_similar_address(address, existing):
                return True, existing
        
        return False, ""
    except Exception as e:
        logging.error(f"❌ Ошибка проверки адреса '{address}': {e}")
        return False, ""


def add_address(address: str, lat: float = 0.0, lng: float = 0.0, district: str = "Центральный") -> bool:
    """Добавление адреса в справочник"""
    try:
        # 🔥 БЕЗОПАСНО: Определяем следующую строку и добавляем ТОЛЬКО в A:I
        all_rows = sprav.get_all_values()
        next_row = len(all_rows) + 1
        
        # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно (защита от "Out of rows")
        ensure_sheet_has_enough_rows(sprav, next_row)
        
        row = [
            address,                          # A: Адрес
            district,                          # B: Район
            "",                                # C: Промоутер
            "",                                # D: Фото
            "",                                # E: Посещение
            "",                                # F: Статус листовок
            "🔴 Не был",                       # G: Статус карты
            str(lat) if lat != 0.0 else "",   # H: Широта
            str(lng) if lng != 0.0 else ""    # I: Долгота
        ]
        
        # ✅ БЕЗОПАСНЫЙ МЕТОД: Явно указываем диапазон A:I
        range_name = f"A{next_row}:I{next_row}"
        sprav.update(values=[row], range_name=range_name)
        
        logging.info(f"  ✅ Добавлен в строку {next_row}: {address} ({lat}, {lng}, {district})")
        return True
    except Exception as e:
        logging.error(f"  ❌ Ошибка добавления '{address}': {e}")
        return False


# ==================== ПАРСИНГ АДРЕСОВ ====================

def parse_address_line(line: str) -> list[str]:
    """Парсинг строки с адресами
    
    Поддерживает два формата:
    1. "Улица: 15, 16, 18, 20, 22-24" → ["Улица 15", "Улица 16", "Улица 18", "Улица 20", "Улица 22", "Улица 23", "Улица 24"]
    2. "Горького 199" → ["Горького 199"]
    3. "Челнакова 40 (Сев. гора)" → ["Челнакова 40"] (скобки удаляются)
    """
    line = line.strip()
    if not line:
        return []
    
    # 🔥 НОВОЕ: Удаляем пояснения в скобках (например "Челнакова 40 (Сев. гора)" → "Челнакова 40")
    import re
    line = re.sub(r'\s*\([^)]+\)', '', line).strip()
    
    # Формат 1: "Улица: номера"
    if ':' in line:
        street, numbers_str = line.split(':', 1)
        street = street.strip()
        numbers = numbers_str.strip().split(',')
        
        addresses = []
        for num in numbers:
            num = num.strip()
            if not num:
                continue
            
            # 🔥 ИСПРАВЛЕНО: Обрабатываем диапазоны ТОЛЬКО если есть явный дефис между двумя числами
            # Проверяем паттерн: "число-число" (например "22-24")
            range_match = re.match(r'^(\d+)\s*-\s*(\d+)$', num)
            if range_match:
                start_val = int(range_match.group(1))
                end_val = int(range_match.group(2))
                
                # Если диапазон разумный (не больше 20 адресов), разворачиваем
                if 0 < end_val - start_val <= 20:
                    for i in range(start_val, end_val + 1):
                        addresses.append(f"{street} {i}")
                    continue
            
            # 🔥 НОВОЕ: Удаляем пояснения в скобках из НОМЕРА дома (например "40 (корп. 2)" → "40")
            num = re.sub(r'\s*\([^)]+\)', '', num).strip()
            
            # Обычный номер (может быть "15", "16А", "42-48" как название дома)
            addresses.append(f"{street} {num}")
        
        return addresses
    
    # Формат 2: "Горького 199" - уже готовый адрес
    return [line]


def parse_addresses_file(filepath: str) -> list[str]:
    """Читает файл и парсит все адреса"""
    addresses = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            addresses.extend(parse_address_line(line))
    return addresses


# ==================== ОСНОВНАЯ ЛОГИКА ====================

def main():
    """Главная функция"""
    logging.info("=" * 60)
    logging.info("🏠 МАССОВЫЙ ИМПОРТ АДРЕСОВ В СПРАВОЧНИК")
    logging.info("=" * 60)
    
    # Проверяем наличие файла
    if not os.path.exists(ADDRESSES_FILE):
        logging.error(f"❌ Файл '{ADDRESSES_FILE}' не найден!")
        logging.info(f"📝 Создай файл '{ADDRESSES_FILE}' и заполни его адресами")
        logging.info("   Формат 1 (улица с номерами):")
        logging.info("     Грига: 15, 16, 18, 20, 22, 24, 26")
        logging.info("   Формат 2 (готовые адреса):")
        logging.info("     Горького 199")
        logging.info("     Ленинский проспект 81")
        sys.exit(1)
    
    # Читаем и парсим адреса
    addresses = parse_addresses_file(ADDRESSES_FILE)
    
    if not addresses:
        logging.error(f"❌ Файл '{ADDRESSES_FILE}' пустой!")
        sys.exit(1)
    
    logging.info(f"📋 Загружено {len(addresses)} адресов из файла")
    logging.info("")
    
    # Статистика
    stats = {
        "total": len(addresses),
        "added": 0,
        "skipped": 0,
        "failed": 0,
        "geocoded": 0,
        "no_coords": 0
    }
    
    # Обрабатываем каждый адрес
    for i, address in enumerate(addresses, 1):
        logging.info(f"[{i}/{stats['total']}] Обработка: {address}")
        
        # Проверяем дубликаты (точное + похожее совпадение)
        exists, similar = address_exists(address)
        if exists:
            if similar == address:
                logging.info(f"  ⏭️  Пропущен (точный дубликат)")
            else:
                logging.info(f"  ⏭️  Пропущен (похож на '{similar}')")
            stats["skipped"] += 1
            continue
        
        # Геокодируем
        result = geocode_address(address)
        if result:
            lat, lng, district = result
            stats["geocoded"] += 1
        else:
            # Если координаты не найдены - все равно добавляем
            lat, lng, district = 0.0, 0.0, "Центральный"
            stats["no_coords"] += 1
        
        # Добавляем в справочник
        if add_address(address, lat, lng, district):
            stats["added"] += 1
        else:
            stats["failed"] += 1
        
        # Задержка между запросами
        if i < stats["total"]:
            time.sleep(GEOCODE_DELAY)
    
    # Итоговая статистика
    logging.info("")
    logging.info("=" * 60)
    logging.info("📊 ИТОГОВАЯ СТАТИСТИКА")
    logging.info("=" * 60)
    logging.info(f"📋 Всего адресов:          {stats['total']}")
    logging.info(f"✅ Добавлено:              {stats['added']}")
    logging.info(f"   ├─ С координатами:      {stats['geocoded']}")
    logging.info(f"   └─ Без координат:       {stats['no_coords']}")
    logging.info(f"⏭️  Пропущено (дубликаты): {stats['skipped']}")
    logging.info(f"❌ Ошибок:                 {stats['failed']}")
    logging.info("=" * 60)
    logging.info("✅ Импорт завершен!")


if __name__ == "__main__":
    main()
