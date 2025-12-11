#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для массового добавления адресов в Google Sheets "Справочник"
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

# Конфигурация
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
OSM_USER_AGENT = "promo_bot_kaliningrad"

# Центры районов
DISTRICT_CENTERS = {
    "Центральный": (54.7104, 20.5120),
    "Ленинградский": (54.7280, 20.4680),
    "Московский": (54.6920, 20.4480),
    "Октябрьский": (54.6750, 20.5350),
}

# АДРЕСА ДЛЯ ДОБАВЛЕНИЯ
ADDRESSES = {
    "Краснопрудная": ["1", "1-3", "2", "2-2А", "2А", "3", "4", "4-4А", "4А", "5", "5-7", "6", "6-8", "7", "8", "9", "9-11", "10", "10-12", "11", "12", "13", "13-15", "14", "14-16", "15", "16", "17", "17-19", "18", "18-20", "19", "20", "21", "21-23", "22", "22-24", "23", "24", "25", "25-27", "26", "26-28", "27", "28", "29", "29-31", "30", "30-32", "31", "32", "33", "33-35", "34", "34-36", "35", "36", "37", "37-39", "38", "38-40", "39", "40", "41", "41-43", "42", "42-44", "43", "44", "45", "45-51", "46", "47", "49", "51", "53", "53-55", "54", "54-56", "55", "56", "57", "57-63", "58", "58-60", "59", "60", "61", "62", "62-64", "63", "64", "65", "66", "66-68", "67", "68", "70", "70-72", "72", "74", "74-76", "76", "78", "78-80", "80", "82", "82-84", "84"],
}


def geocode_address_yandex(address: str) -> Optional[Tuple[float, float]]:
    """Геокодирование через Yandex Geocoder API."""
    if not YANDEX_API_KEY:
        return None
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
            
            if 54.5 <= lat <= 54.9 and 20.2 <= lng <= 20.7:
                logging.info(f"✅ Yandex: '{address}' → {lat}, {lng}")
                return lat, lng
                
    except Exception as e:
        logging.error(f"❌ Ошибка Yandex для '{address}': {e}")
    
    return None


def geocode_address_osm(address: str) -> Optional[Tuple[float, float]]:
    """Геокодирование через OSM Nominatim."""
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
            
            if 54.5 <= lat <= 54.9 and 20.2 <= lng <= 20.7:
                logging.info(f"✅ OSM: '{address}' → {lat}, {lng}")
                return lat, lng
                
    except Exception as e:
        logging.error(f"❌ Ошибка OSM для '{address}': {e}")
    
    return None


def get_district_by_coords(lat: float, lng: float) -> str:
    """Определение района по координатам."""
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
    """Нормализация текста для сравнения."""
    import re
    s = str(s or "").strip().lower().replace("ё", "е")
    s = re.sub(r"[^a-zа-я0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def main():
    """Основная функция."""
    logging.info("=" * 60)
    logging.info("🏢 ДОБАВЛЕНИЕ АДРЕСОВ В СПРАВОЧНИК")
    logging.info("=" * 60)
    
    if not SPREADSHEET_URL:
        print("\n❌ ОШИБКА: Не указан SPREADSHEET_URL в .env")
        return
    
    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        print(f"\n❌ ОШИБКА: Файл {GOOGLE_CREDENTIALS_FILE} не найден")
        return
    
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
    
    # Получение существующих адресов
    try:
        existing_addresses = sprav.col_values(1)[1:]
        existing_normalized = {normalize_text(addr): addr for addr in existing_addresses if addr}
        logging.info(f"📋 Найдено существующих адресов: {len(existing_normalized)}")
    except Exception as e:
        logging.error(f"❌ Ошибка чтения существующих адресов: {e}")
        existing_normalized = {}
    
    # Обработка адресов
    added_count = 0
    skipped_count = 0
    failed_count = 0
    total_count = 0
    
    for street, houses in ADDRESSES.items():
        logging.info(f"\n📍 Улица: {street}")
        
        for house in houses:
            total_count += 1
            full_address = f"{street} {house}"
            
            # Проверка дубликатов
            addr_normalized = normalize_text(full_address)
            if addr_normalized in existing_normalized:
                logging.info(f"⏭️  [{total_count}] Пропуск (дубликат): {full_address}")
                skipped_count += 1
                continue
            
            # Геокодирование
            coords = geocode_address_yandex(full_address)
            
            if not coords:
                coords = geocode_address_osm(full_address)
                time.sleep(1.5)  # OSM rate limit
            
            if not coords:
                logging.error(f"❌ [{total_count}] Не удалось геокодировать: {full_address}")
                failed_count += 1
                continue
            
            lat, lng = coords
            district = get_district_by_coords(lat, lng)
            
            # Добавление в Справочник
            try:
                new_row = [
                    full_address,         # A: Адрес
                    district,             # B: Район
                    "",                   # C: Промоутер
                    "",                   # D: Фото
                    "",                   # E: Последнее посещение
                    "🔴 Не был",         # F: Статус листовок
                    "🔴 Не был",         # G: Статус карты
                    str(lat),             # H: Широта
                    str(lng),             # I: Долгота
                    "",                   # J: Листовки до
                    "",                   # K: Листовки наклеено
                ]
                
                sprav.append_row(new_row)
                logging.info(f"✅ [{total_count}] Добавлен: {full_address} ({district})")
                added_count += 1
                existing_normalized[addr_normalized] = full_address
                
                time.sleep(0.5)
                
            except Exception as e:
                logging.error(f"❌ [{total_count}] Ошибка добавления '{full_address}': {e}")
                failed_count += 1
    
    # Статистика
    logging.info("\n" + "=" * 60)
    logging.info("📊 ИТОГОВАЯ СТАТИСТИКА")
    logging.info("=" * 60)
    logging.info(f"✅ Добавлено: {added_count}")
    logging.info(f"⏭️  Пропущено (дубликаты): {skipped_count}")
    logging.info(f"❌ Ошибок: {failed_count}")
    logging.info(f"📍 Всего обработано: {total_count}")
    logging.info("=" * 60)


if __name__ == "__main__":
    main()
