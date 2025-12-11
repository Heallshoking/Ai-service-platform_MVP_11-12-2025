#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления адресов жилых комплексов Калининграда в Google Sheets "Справочник"
"""
import os
import logging
import time
import gspread
from google.oauth2.service_account import Credentials
from typing import Optional, Tuple
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Конфигурация из .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("⚠️ python-dotenv не установлен, используются только переменные окружения")

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
OSM_USER_AGENT = "promo_bot_kaliningrad"

# Валидация обязательных параметров
if not SPREADSHEET_URL:
    print("\n" + "="*60)
    print("❌ ОШИБКА: Не указан SPREADSHEET_URL")
    print("="*60)
    print("Установите переменную окружения:")
    print("export SPREADSHEET_URL='https://docs.google.com/spreadsheets/d/YOUR_ID/edit'")
    print("\nИли создайте файл .env из .env.example")
    print("="*60)
    exit(1)

if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
    print("\n" + "="*60)
    print(f"❌ ОШИБКА: Файл {GOOGLE_CREDENTIALS_FILE} не найден")
    print("="*60)
    print("Скачайте credentials.json из Google Cloud Console")
    print("="*60)
    exit(1)

# Центры районов для определения района по координатам
DISTRICT_CENTERS = {
    "Центральный": (54.7104, 20.5120),
    "Ленинградский": (54.7280, 20.4680),
    "Московский": (54.6920, 20.4480),
    "Октябрьский": (54.6750, 20.5350),
}

# Адреса ЖК Калининграда 2000-2025
RESIDENTIAL_COMPLEXES = [
    "Генерала Кузнецова 78",
    "Озёрная 33",
    "Озёрная 35",
    "Озёрная 37",
    "Каштановый переулок 5",
    "Дм. Донского 102",
    "Борзова 9",
    "Тельмана 88",
    "Дм. Донского 110",
    "Генерала Кузнецова 101",
    "Генерала Кузнецова 103",
    "Генерала Кузнецова 105",
    "Павлика Морозова 78",
    "Маршала Бирюзова 21",
    "Аллея Смелых 6",
    "Генерала Кузнецова 44",
    "Литейная 50",
    "Преголя набережная 19",
    "Дм. Донского 130",
    "Александра Невского 8",
    "Некрасова 28",
    "Генерала Кузнецова 112",
    "Красная 11",
    "Октябрьская 62",
    "Каштановая аллея 22",
    "Береговая 45",
    "Дм. Донского 140",
    "Альпийская 15",
    "Победы площадь 1",
    "Немана набережная 50",
    "Генерала Кузнецова 150",
    "Литейная 55",
]


def geocode_address_yandex(address: str) -> Optional[Tuple[float, float]]:
    """Геокодирование через Yandex Geocoder API."""
    try:
        full_address = f"Калининград, {address}"
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": YANDEX_API_KEY,
            "geocode": full_address,
            "format": "json",
            "results": 1,
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if (
            data.get("response")
            and data["response"].get("GeoObjectCollection")
            and data["response"]["GeoObjectCollection"].get("featureMember")
        ):
            pos = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
            lng, lat = map(float, pos.split())
            
            # Проверка координат в пределах Калининграда
            if 54.5 <= lat <= 54.9 and 20.2 <= lng <= 20.7:
                logging.info(f"✅ Yandex: '{address}' → {lat}, {lng}")
                return lat, lng
            else:
                logging.warning(f"⚠️ Координаты вне Калининграда: {address} → {lat}, {lng}")
                
    except Exception as e:
        logging.error(f"❌ Ошибка Yandex для '{address}': {e}")
    
    return None


def geocode_address_osm(address: str) -> Optional[Tuple[float, float]]:
    """Геокодирование через OSM Nominatim (резервный вариант)."""
    try:
        import urllib.parse
        encoded_address = urllib.parse.quote(f"Калининград, {address}")
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded_address}&addressdetails=1"
        headers = {"User-Agent": OSM_USER_AGENT}
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data:
            lat = float(data[0]["lat"])
            lng = float(data[0]["lon"])
            
            # Проверка координат в пределах Калининграда
            if 54.5 <= lat <= 54.9 and 20.2 <= lng <= 20.7:
                logging.info(f"✅ OSM: '{address}' → {lat}, {lng}")
                return lat, lng
            else:
                logging.warning(f"⚠️ Координаты вне Калининграда: {address} → {lat}, {lng}")
                
    except Exception as e:
        logging.error(f"❌ Ошибка OSM для '{address}': {e}")
    
    return None


def get_district_by_coords(lat: float, lng: float) -> str:
    """Определение района по минимальному расстоянию до центра района."""
    try:
        nearest_name = "Центральный"
        nearest_dist = float('inf')
        
        for name, (clat, clng) in DISTRICT_CENTERS.items():
            dist = ((lat - clat) ** 2 + (lng - clng) ** 2) ** 0.5
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_name = name
        
        return nearest_name
    except Exception:
        return "Центральный"


def normalize_text(s: str) -> str:
    """Нормализация текста для сравнения адресов."""
    import re
    s = str(s or "").strip().lower().replace("ё", "е")
    s = re.sub(r"[^a-zа-я0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main():
    """Основная функция скрипта."""
    logging.info("=" * 60)
    logging.info("🏢 ЗАГРУЗКА АДРЕСОВ ЖИЛЫХ КОМПЛЕКСОВ В СПРАВОЧНИК")
    logging.info("=" * 60)
    
    # Подключение к Google Sheets
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SPREADSHEET_URL)
        sprav = sheet.worksheet("Справочник")
        logging.info("✅ Подключение к Google Sheets успешно")
    except Exception as e:
        logging.error(f"❌ Ошибка подключения к Google Sheets: {e}")
        return
    
    # Получение существующих адресов из Справочника
    try:
        existing_addresses = sprav.col_values(1)[1:]  # Пропускаем заголовок
        existing_normalized = {normalize_text(addr): addr for addr in existing_addresses if addr}
        logging.info(f"📋 Найдено существующих адресов: {len(existing_normalized)}")
    except Exception as e:
        logging.error(f"❌ Ошибка чтения существующих адресов: {e}")
        existing_normalized = {}
    
    # Обработка каждого адреса ЖК
    added_count = 0
    skipped_count = 0
    failed_count = 0
    
    for idx, address in enumerate(RESIDENTIAL_COMPLEXES, 1):
        logging.info(f"\n[{idx}/{len(RESIDENTIAL_COMPLEXES)}] Обработка: {address}")
        
        # Проверка на дубликаты
        addr_normalized = normalize_text(address)
        if addr_normalized in existing_normalized:
            logging.info(f"⏭️ Пропуск (уже есть): {address}")
            skipped_count += 1
            continue
        
        # Геокодирование
        coords = geocode_address_yandex(address)
        
        if not coords:
            logging.warning(f"⚠️ Yandex не вернул координаты, пробую OSM...")
            coords = geocode_address_osm(address)
            time.sleep(1.5)  # OSM rate limit: 1 req/sec
        
        if not coords:
            logging.error(f"❌ Не удалось геокодировать: {address}")
            failed_count += 1
            continue
        
        lat, lng = coords
        district = get_district_by_coords(lat, lng)
        
        # Добавление в Справочник
        # Структура: A-Адрес, B-Район, C-Промоутер, D-Фото, E-Посещение, F-Статус листовок, 
        #            G-Статус карты, H-Lat, I-Lng, J-Листовки до, K-Листовки наклеено
        try:
            new_row = [
                address,                  # A: Адрес
                district,                 # B: Район
                "",                       # C: Промоутер (пусто)
                "",                       # D: Фото (пусто)
                "",                       # E: Последнее посещение (пусто)
                "🔴 Не был",             # F: Статус листовок
                "🔴 Не был",             # G: Статус карты
                str(lat),                 # H: Широта
                str(lng),                 # I: Долгота
                "",                       # J: Листовки до (пусто)
                "",                       # K: Листовки наклеено (пусто)
            ]
            
            sprav.append_row(new_row)
            logging.info(f"✅ Добавлен: {address} ({district}, {lat:.6f}, {lng:.6f})")
            added_count += 1
            existing_normalized[addr_normalized] = address  # Обновляем кэш
            
            time.sleep(0.5)  # Небольшая задержка между записями
            
        except Exception as e:
            logging.error(f"❌ Ошибка добавления '{address}': {e}")
            failed_count += 1
    
    # Итоговая статистика
    logging.info("\n" + "=" * 60)
    logging.info("📊 ИТОГОВАЯ СТАТИСТИКА")
    logging.info("=" * 60)
    logging.info(f"✅ Добавлено новых адресов: {added_count}")
    logging.info(f"⏭️ Пропущено (дубликаты): {skipped_count}")
    logging.info(f"❌ Ошибок геокодирования: {failed_count}")
    logging.info(f"📍 Всего обработано: {len(RESIDENTIAL_COMPLEXES)}")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
