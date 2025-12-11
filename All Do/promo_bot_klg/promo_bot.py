import os
import logging
import asyncio
import hashlib
import threading
import re  # Для фильтрации адресов без номера дома

def looks_like_address(text: str) -> bool:
    """
    Validates address like 'StreetName 123' or 'Street Name, 123'.
    Requires street words and a house number (supports suffixes like 'к1', 'а', 'б').
    """
    s = (text or "").strip().lower().replace("ё", "е")
    if len(s) < 4 or not re.search(r"\d", s):
        return False
    return bool(re.match(r"^[a-zа-яё\-\s]+\s*(\d+[a-zа-я]?([\s\-/]*к\d+)?)$", s))
from datetime import datetime, timedelta

def normalize_text(s: str) -> str:
    """
    Нормализует текст адреса для сравнения:
    - нижний регистр, замена 'ё'→'е'
    - удаление лишних символов (кроме букв, цифр и пробелов)
    - схлопывание пробелов
    """
    try:
        s = str(s or "").strip().lower().replace("ё", "е")
        import re as _re
        s = _re.sub(r"[^a-zа-я0-9\s]", " ", s)
        s = _re.sub(r"\s+", " ", s).strip()
        return s
    except Exception:
        return str(s or "").strip()

from math import radians, cos, sin, sqrt, atan2, degrees
from typing import Dict, Any, Tuple, List, Optional, Set
import requests
import gspread
from google.oauth2.service_account import Credentials
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# 🗺️ НОВОЕ: OSMnx для точного геопространственного анализа
try:
    import osmnx as ox
    import networkx as nx
    OSMNX_AVAILABLE = True
    logging.info("✅ OSMnx загружен успешно")
except ImportError:
    OSMNX_AVAILABLE = False
    logging.warning("⚠️ OSMnx не установлен. Установите: pip install osmnx networkx")

# APScheduler imports - will be used for push notifications
try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    import pytz  # 🔥 НОВОЕ: Для таймзон Europe/Moscow
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logging.warning("⚠️ apscheduler not installed. Push notifications disabled. Install with: pip install apscheduler pytz")

# Google Sheets Charts API
try:
    from googleapiclient.discovery import build
    SHEETS_API_AVAILABLE = True
except ImportError:
    SHEETS_API_AVAILABLE = False
    logging.warning("⚠️ google-api-python-client не установлен. Авто-графики в Google Sheets будут отключены. Установите: pip install google-api-python-client")

# ============================
# 🔧 КОНФИГУРАЦИЯ
# ============================
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
# 🔒 Список Telegram ID админов (можно указать несколько через запятую в ADMIN_IDS)
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", str(os.getenv("ADMIN_CHAT_ID", "0"))).split(",") if x.strip().isdigit()]
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_URL = os.getenv("SPREADSHEET_URL")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
BONUS_DAYS = [0, 3, 5]  # Пн, Чт, Сб
MAX_NEARBY_ADDRESSES = 3
SESSION_TIMEOUT_MINUTES = 15
LOCATION_RADIUS_METERS = 800
DAILY_GOAL = 70
BONUS_AMOUNT = 500.0  # БОНУСНАЯ СИСТЕМА
MIN_REVISIT_HOURS = 18
MIN_REVISIT_HOURS_NO_ACCESS = 18  # 🔧 ИСПРАВЛЕНО: было 6, теперь 18 часов для "Нет доступа"
DAYS_TO_RESET_STATUS = 6  # через 6 дней → сброс / ожидание
DEFAULT_FREQUENCY_DAYS = "6"
OSM_USER_AGENT = "promo_bot_kaliningrad"
KALININGRAD_CENTER = (54.710426, 20.452218)
ERROR_REPORT_EMAIL = os.getenv("ERROR_REPORT_EMAIL", "")  # 🆘 Email для отчетов об ошибках
MAP_URL = os.getenv("PROMO_MAP_URL", "https://promo.example.com/map")

# Константы геймификации
MIN_PHOTOS_REQUIRED = 4  # Минимум фото для завершения
SUGGESTION_RADIUS_METERS = 1000  # Радиус для следующих адресов (1 км)

# Константы бонусной системы (многоуровневая)
BONUS_TIERS = [
    {"threshold": 70, "bonus": 500, "name": "🥉 Бронзовый"},
    {"threshold": 100, "bonus": 700, "name": "🥈 Серебряный"},
    {"threshold": 150, "bonus": 1000, "name": "🥇 Золотой"}
]
BONUS_WORK_DAYS = [0, 1, 2, 3, 4, 5]  # Пн-Сб (0=Пн, 6=Вс)

# Официальные районы Калининграда (4 административных района)
# Источник: Реальные координаты центров административных районов (проверено 2025)
DISTRICT_CENTERS: dict[str, tuple[float, float]] = {
    "Центральный": (54.7104, 20.5120),    # Исторический центр, площадь Победы
    "Ленинградский": (54.7280, 20.4680),  # ✅ Северо-запад, им. А.Космодемьянского (ИСПРАВЛЕНО)
    "Московский": (54.6920, 20.4480),     # ✅ Юго-запад, Сельма, Космонавтов (ИСПРАВЛЕНО)
    "Октябрьский": (54.6750, 20.5350),    # ✅ Юго-восток, Балтийский, Менделеево (ИСПРАВЛЕНО)
}

# 🔧 Определение района по координатам и подсказкам улиц
STREET_DISTRICT_HINTS = {
    "еловая": "Ленинградский",
    "еловая аллея": "Ленинградский",
}

def infer_district_from_coords(lat: float, lng: float) -> str:
    try:
        nearest_name = None
        nearest_dist = float('inf')
        for name, (clat, clng) in DISTRICT_CENTERS.items():
            d = ((lat - clat) ** 2 + (lng - clng) ** 2) ** 0.5
            if d < nearest_dist:
                nearest_dist = d
                nearest_name = name
        return nearest_name or "Центральный"
    except Exception:
        return "Центральный"

def ensure_real_district(address_text: str, lat: float, lng: float, district: str | None) -> str:
    addr_norm = normalize_text(address_text)
    for hint, name in STREET_DISTRICT_HINTS.items():
        if hint in addr_norm:
            return name
    inferred = infer_district_from_coords(lat, lng)
    if not district or district.strip() == "" or district not in DISTRICT_CENTERS:
        return inferred
    return district

# Глобальное состояние пользователей (FSM - Finite State Machine)
user_state: Dict[int, Dict[str, Any]] = {}
# Возможные состояния:
# - "awaiting_address": ожидание ввода адреса
# - "address_selected": адрес выбран, ожидание подтверждения "Я на месте!"
# - "awaiting_entrance_count": ожидание количества подъездов
# - "awaiting_photos": ожидание загрузки фото электрощитов
# - "awaiting_door_photo": ожидание фото двери (при "Нет доступа")

used_photo_hashes: Set[str] = set()  # Хеши уже загруженных фото (антидубль)
session_stats: Dict[int, Dict[str, int]] = {}  # Сессионный счётчик
user_message_history: Dict[int, List[int]] = {}  # История ID сообщений бота для каждого пользователя
scheduler: Optional['AsyncIOScheduler'] = None  # Планировщик фоновых задач
sheet = sprav = balances_sheet = flyers_sheet = requests_sheet = otchety = photo_hashes_sheet = config_sheet = flyer_requests_sheet = priority_addresses_sheet = finance_sheet = roi_sheet = None

# 🎯 НОВОЕ: Кэш приоритетов адресов (обновляется каждые 60 минут)
PRIORITY_CACHE: Dict[str, Any] = {"loaded_at": None, "data": {}}
PRIORITY_ADDRESSES_CACHE: Dict[str, Any] = {"loaded_at": None, "addresses": []}  # 🔥 НОВОЕ: Отдельный кэш для списка приоритетных адресов

# 🗺️ НОВОЕ: Кэш OSMnx графа улично-дорожной сети Калининграда
OSMNX_GRAPH_CACHE: Dict[str, Any] = {
    "graph": None,
    "loaded_at": None,
    "bbox": (54.5, 54.9, 20.2, 20.7)  # (мин_лат, макс_лат, мин_лнг, макс_лнг)
}

# 💸 ПРАЙСЫ ПЕЧАТИ ВИЗИТОК
PRICE_TABLE_PRINT_ONE_SIDE = {120: 600, 216: 972, 312: 1248, 504: 1512, 1008: 2000, 2016: 3600, 3000: 4500}
PRICE_TABLE_PRINT_TWO_SIDES = {120: 720, 216: 1080, 312: 1404, 504: 1890, 1008: 3000, 2016: 5200, 3000: 7500}

# 🔔 НОВОЕ: Временное хранилище для уведомлений админу
_pending_admin_notification: Optional[Dict[str, Any]] = None

# 📍 ПИНЫ СООБЩЕНИЙ ЗАЯВОК
pinned_admin_request_messages: Dict[tuple[int, int], int] = {}
# key: (admin_id, promoter_id) -> message_id
pinned_promoter_request_messages: Dict[int, int] = {}
# 🔥 НОВОЕ: ПИНЫ ДЛЯ ЗАЯВОК НА КООРДИНАТЫ
pinned_admin_coord_messages: Dict[tuple[int, int], int] = {}
pinned_promoter_coord_messages: Dict[int, int] = {}
# 🔥 НОВОЕ: ПАМЯТЬ О ЖДУЩИХ ПОДТВЕРЖДЕНИЙ КООРДИНАТ
coords_pending_requests: Dict[int, Dict[str, Any]] = {}

# 🔔 АНТИ-ДУБЛИКАТЫ ДЛЯ ПЛАНОВЫХ УВЕДОМЛЕНИЙ
last_notification_sent: Dict[str, datetime] = {}  # key: "morning"/"evening"/"cleanup" -> last_sent_time
notification_lock = threading.Lock()  # Блокировка для предотвращения параллельных запусков

# 🔥 НОВОЕ: Глобальные async locks для планировщика (инициализируются при запуске)
cleanup_warning_lock: Optional['asyncio.Lock'] = None
morning_cleanup_lock: Optional['asyncio.Lock'] = None

# 🔒 ДЕДУПЛИКАЦИЯ КОМАНД: предотвращаем двойную обработку /start и др.
last_command_handled: Dict[str, datetime] = {}

# ============================
# 📚 ЛОГГИРОВАНИЕ
# ============================
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "promoter_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler(),
    ],
)

# ============================
# 📚 GOOGLE SHEETS
# ============================
SETTINGS_CACHE: Dict[str, Any] = {"loaded_at": None, "data": {}}
SETTINGS: Dict[str, str] = {}  # 🔥 Глобальные настройки из листа "Настройки"
DEFAULT_SETTINGS = {
    "LOCATION_RADIUS_METERS": "800",
    "MAX_NEARBY_ADDRESSES": "3",
    "LOW_VALUE_BLOCKLIST": "невского,красная 123,ленинский проспект 88,гараж,склад,промзона",
    "PREFERRED_SUFFIXES": "а,б,в,к1,к2,к3",
    "MIN_HIGH_HOUSE_NUMBER": "100",
    "ENABLE_SMART_EXPANSION": "1",
    "VERIFY_OSM_RESIDENTIAL": "1",
    "MAX_SPEED_KMH": "150",
    "MIN_PHOTOS_REQUIRED": "4",
    "PHOTO_PRICE": "3",
    "BONUS_BRONZE_THRESHOLD": "70",
    "BONUS_BRONZE_AMOUNT": "500",
    "BONUS_SILVER_THRESHOLD": "100",
    "BONUS_SILVER_AMOUNT": "700",
    "BONUS_GOLD_THRESHOLD": "150",
    "BONUS_GOLD_AMOUNT": "1000",
    "PHOTO_FUTURE_GRACE_SECONDS": "30",
    "FLYER_UNIT_COST": "2.50",
    "ROI_CHARTS_CREATED": "0",
    "SESSION_MAX_MINUTES": "25",
    "LOCATION_MAX_AGE_MINUTES": "40"  # 🔧 ИСПРАВЛЕНО: увеличено до 40 минут для удобства промоутеров
}

# 🔥 НОВОЕ: Автоматическое расширение таблицы
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

def ensure_settings_sheet() -> None:
    """
    Создаёт или обновляет лист 'Настройки' в Google Sheets.
    Все параметры бота управляются через этот лист.
    Автоматически синхронизируется каждые 10 минут.
    """
    global sheet, config_sheet
    try:
        try:
            config_sheet = sheet.worksheet("Настройки")
            logging.info("✅ Лист 'Настройки' найден")
        except gspread.exceptions.WorksheetNotFound:
            config_sheet = sheet.add_worksheet(title="Настройки", rows=50, cols=3)
            logging.info("✅ Лист 'Настройки' создан")
        
        rows = config_sheet.get_all_values()
        if not rows or len(rows) == 0:
            # Создаём заголовки
            config_sheet.update("A1:C1", [["Ключ", "Значение", "Описание"]])
            
            # Данные с ПОЛНЫМ набором параметров
            data = [
                ["LOCATION_RADIUS_METERS", DEFAULT_SETTINGS["LOCATION_RADIUS_METERS"], "Радиус поиска адресов (м)"],
                ["MAX_NEARBY_ADDRESSES", DEFAULT_SETTINGS["MAX_NEARBY_ADDRESSES"], "Сколько адресов показывать"],
                ["LOW_VALUE_BLOCKLIST", DEFAULT_SETTINGS["LOW_VALUE_BLOCKLIST"], "Строки-исключения (через запятую)"],
                ["PREFERRED_SUFFIXES", DEFAULT_SETTINGS["PREFERRED_SUFFIXES"], "Приоритетные суффиксы домов"],
                ["MIN_HIGH_HOUSE_NUMBER", DEFAULT_SETTINGS["MIN_HIGH_HOUSE_NUMBER"], "Номер дома для новостройки"],
                ["ENABLE_SMART_EXPANSION", DEFAULT_SETTINGS["ENABLE_SMART_EXPANSION"], "Умное расширение: 1=вкл, 0=выкл"],
                ["VERIFY_OSM_RESIDENTIAL", DEFAULT_SETTINGS["VERIFY_OSM_RESIDENTIAL"], "Проверка жилого дома: 1=вкл, 0=выкл"],
                ["MAX_SPEED_KMH", DEFAULT_SETTINGS["MAX_SPEED_KMH"], "Порог скорости (анти-спуф)"],
                ["MIN_PHOTOS_REQUIRED", DEFAULT_SETTINGS["MIN_PHOTOS_REQUIRED"], "Минимум фото для завершения"],
                ["PHOTO_PRICE", DEFAULT_SETTINGS["PHOTO_PRICE"], "Стоимость за 1 фото (₽)"],
                ["BONUS_BRONZE_THRESHOLD", DEFAULT_SETTINGS["BONUS_BRONZE_THRESHOLD"], "🥉 Бронза: фото для бонуса"],
                ["BONUS_BRONZE_AMOUNT", DEFAULT_SETTINGS["BONUS_BRONZE_AMOUNT"], "🥉 Бронза: сумма бонуса (₽)"],
                ["BONUS_SILVER_THRESHOLD", DEFAULT_SETTINGS["BONUS_SILVER_THRESHOLD"], "🥈 Серебро: фото для бонуса"],
                ["BONUS_SILVER_AMOUNT", DEFAULT_SETTINGS["BONUS_SILVER_AMOUNT"], "🥈 Серебро: сумма бонуса (₽)"],
                ["BONUS_GOLD_THRESHOLD", DEFAULT_SETTINGS["BONUS_GOLD_THRESHOLD"], "🥇 Золото: фото для бонуса"],
                ["BONUS_GOLD_AMOUNT", DEFAULT_SETTINGS["BONUS_GOLD_AMOUNT"], "🥇 Золото: сумма бонуса (₽)"],
                ["PHOTO_FUTURE_GRACE_SECONDS", DEFAULT_SETTINGS["PHOTO_FUTURE_GRACE_SECONDS"], "Допуск будущего времени фото (сек)"],
                ["FLYER_UNIT_COST", DEFAULT_SETTINGS["FLYER_UNIT_COST"], "Себестоимость 1 листовки (₽)"],
                ["ROI_CHARTS_CREATED", DEFAULT_SETTINGS["ROI_CHARTS_CREATED"], "Флаг: авто-графики ROI созданы (1/0)"],
                ["SESSION_MAX_MINUTES", DEFAULT_SETTINGS["SESSION_MAX_MINUTES"], "Макс. время сессии после 'Я на месте!' (мин)"],
                ["LOCATION_MAX_AGE_MINUTES", DEFAULT_SETTINGS["LOCATION_MAX_AGE_MINUTES"], "Макс. возраст геолокации (мин)"]
            ]
            config_sheet.update(f"A2:C{len(data)+1}", data)
            logging.info(f"✅ Созданы настройки ({len(data)} параметров)")
    except Exception as e:
        logging.warning(f"⚠️ Не удалось инициализировать лист 'Настройки': {e}")


def load_settings(force: bool = False) -> None:
    """
    Загружает настройки из Google Sheets 'Настройки'.
    Кэш обновляется каждые 10 минут.
    Автоматически обновляет глобальные переменные и константы бонусов.
    """
    global LOCATION_RADIUS_METERS, MAX_NEARBY_ADDRESSES, MIN_PHOTOS_REQUIRED, BONUS_TIERS, SETTINGS_CACHE, SETTINGS
    try:
        now = datetime.now()
        
        # Кэш-проверка: если менее 10 минут и не принудительно
        if SETTINGS_CACHE["loaded_at"] and not force:
            if now < SETTINGS_CACHE["loaded_at"] + timedelta(minutes=10):
                # Используем кэшированные данные
                data = SETTINGS_CACHE["data"]
                SETTINGS = data  # 🔥 Обновляем глобальную переменную
                LOCATION_RADIUS_METERS = int(data.get("LOCATION_RADIUS_METERS", LOCATION_RADIUS_METERS))
                MAX_NEARBY_ADDRESSES = int(data.get("MAX_NEARBY_ADDRESSES", MAX_NEARBY_ADDRESSES))
                MIN_PHOTOS_REQUIRED = int(data.get("MIN_PHOTOS_REQUIRED", MIN_PHOTOS_REQUIRED))
                
                # Обновляем бонусные пороги
                BONUS_TIERS = [
                    {
                        "threshold": int(data.get("BONUS_BRONZE_THRESHOLD", 70)),
                        "bonus": int(data.get("BONUS_BRONZE_AMOUNT", 500)),
                        "name": "🥉 Бронзовый"
                    },
                    {
                        "threshold": int(data.get("BONUS_SILVER_THRESHOLD", 100)),
                        "bonus": int(data.get("BONUS_SILVER_AMOUNT", 700)),
                        "name": "🥈 Серебряный"
                    },
                    {
                        "threshold": int(data.get("BONUS_GOLD_THRESHOLD", 150)),
                        "bonus": int(data.get("BONUS_GOLD_AMOUNT", 1000)),
                        "name": "🥇 Золотой"
                    }
                ]
                return
        
        # 🛡️ ЗАЩИТА: Проверяем наличие листа "Настройки"
        if not config_sheet:
            logging.warning("⚠️ Лист 'Настройки' не инициализирован. Используются значения по умолчанию.")
            # Создаём пустой словарь с значениями по умолчанию
            SETTINGS = {
                "SESSION_MAX_MINUTES": "25",
                "LOCATION_MAX_AGE_MINUTES": "40",
                "PHOTO_FUTURE_GRACE_SECONDS": "30",
                "FLYER_UNIT_COST": "2.50",
                "LOCATION_RADIUS_METERS": str(LOCATION_RADIUS_METERS),
                "MAX_NEARBY_ADDRESSES": str(MAX_NEARBY_ADDRESSES),
                "MIN_PHOTOS_REQUIRED": str(MIN_PHOTOS_REQUIRED)
            }
            SETTINGS_CACHE = {"loaded_at": now, "data": SETTINGS}
            return
        
        # Читаем из Google Sheets
        rows = config_sheet.get_all_values()
        kv = {}
        
        for row in rows[1:]:  # Пропускаем заголовок
            if len(row) >= 2 and row[0]:
                kv[row[0].strip()] = row[1].strip()
        
        # 🔥 Обновляем глобальную переменную SETTINGS
        SETTINGS = kv
        
        # Обновляем глобальные переменные
        LOCATION_RADIUS_METERS = int(kv.get("LOCATION_RADIUS_METERS", LOCATION_RADIUS_METERS))
        MAX_NEARBY_ADDRESSES = int(kv.get("MAX_NEARBY_ADDRESSES", MAX_NEARBY_ADDRESSES))
        MIN_PHOTOS_REQUIRED = int(kv.get("MIN_PHOTOS_REQUIRED", MIN_PHOTOS_REQUIRED))
        
        # Обновляем бонусные пороги
        BONUS_TIERS = [
            {
                "threshold": int(kv.get("BONUS_BRONZE_THRESHOLD", 70)),
                "bonus": int(kv.get("BONUS_BRONZE_AMOUNT", 500)),
                "name": "🥉 Бронзовый"
            },
            {
                "threshold": int(kv.get("BONUS_SILVER_THRESHOLD", 100)),
                "bonus": int(kv.get("BONUS_SILVER_AMOUNT", 800)),
                "name": "🥈 Серебряный"
            },
            {
                "threshold": int(kv.get("BONUS_GOLD_THRESHOLD", 150)),
                "bonus": int(kv.get("BONUS_GOLD_AMOUNT", 1500)),
                "name": "🥇 Золотой"
            }
        ]
        
        # Сохраняем кэш
        SETTINGS_CACHE = {"loaded_at": now, "data": kv}
        
        logging.info(
            f"✅ Настройки загружены: "
            f"радиус={LOCATION_RADIUS_METERS}м, "
            f"max_addrs={MAX_NEARBY_ADDRESSES}, "
            f"min_photos={MIN_PHOTOS_REQUIRED}, "
            f"bonus_tiers={len(BONUS_TIERS)}"
        )
    except Exception as e:
        logging.warning(f"⚠️ Не удалось загрузить настройки: {e}")

def init_sheets() -> None:
    global sheet, sprav, balances_sheet, flyers_sheet, requests_sheet, otchety, photo_hashes_sheet, flyer_requests_sheet, priority_addresses_sheet
    try:
        # 🔥 КРИТИЧНО: Проверяем SPREADSHEET_URL перед подключением
        if not SPREADSHEET_URL or SPREADSHEET_URL.strip() == "":
            logging.critical("❌ SPREADSHEET_URL не задан!")
            logging.critical("💡 Установите переменную окружения SPREADSHEET_URL с URL таблицы Google Sheets")
            logging.critical("💡 Пример: export SPREADSHEET_URL='https://docs.google.com/spreadsheets/d/YOUR_ID/edit'")
            raise SystemExit("SPREADSHEET_URL не задан")
        
        # Проверяем формат URL (должен содержать /d/)
        if "/d/" not in SPREADSHEET_URL:
            logging.critical(f"❌ Неверный формат SPREADSHEET_URL: {SPREADSHEET_URL}")
            logging.critical("💡 URL должен содержать ID документа, например:")
            logging.critical("   https://docs.google.com/spreadsheets/d/1ABC-xyz123/edit")
            raise SystemExit("Неверный формат SPREADSHEET_URL")
        
        # Проверка наличия файла credentials
        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            logging.critical(f"❌ ОШИБКА: Файл credentials не найден: {GOOGLE_CREDENTIALS_FILE}")
            logging.critical("💡 Создайте файл credentials.json с данными сервисного аккаунта Google.")
            logging.critical(f"📁 Текущая директория: {os.getcwd()}")
            logging.critical(f"📁 Проверьте наличие файла: ls -lh {GOOGLE_CREDENTIALS_FILE}")
            raise SystemExit(f"Не найден файл: {GOOGLE_CREDENTIALS_FILE}")
        
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        logging.info(f"🔑 Загрузка credentials из: {GOOGLE_CREDENTIALS_FILE}")
        
        try:
            creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scope)
        except Exception as creds_error:
            logging.critical(f"❌ Ошибка загрузки credentials: {creds_error}")
            logging.critical(f"💡 Проверьте формат файла {GOOGLE_CREDENTIALS_FILE}")
            raise
        
        try:
            client = gspread.authorize(creds)
        except Exception as auth_error:
            logging.critical(f"❌ Ошибка авторизации gspread: {auth_error}")
            logging.critical("💡 Проверьте, что сервисный аккаунт имеет доступ к Google Sheets API")
            raise
        
        logging.info(f"📄 Подключение к Google Sheets: {SPREADSHEET_URL[:50]}...")
        
        try:
            sheet = client.open_by_url(SPREADSHEET_URL)
        except Exception as sheet_error:
            logging.critical(f"❌ Ошибка открытия таблицы: {sheet_error}")
            logging.critical(f"💡 Проверьте URL: {SPREADSHEET_URL}")
            logging.critical("💡 Проверьте, что сервисный аккаунт имеет доступ к этой таблице (Editor/Viewer)")
            raise
        
        # 🔧 ИСПРАВЛЕНО: Добавлена глобальная объявление для finance_sheet и roi_sheet
        global sprav, balances_sheet, flyers_sheet, requests_sheet, otchety, photo_hashes_sheet
        global flyer_requests_sheet, priority_addresses_sheet, finance_sheet, roi_sheet
        
        sprav = sheet.worksheet("Справочник")
        
        # 🔧 ПРОВЕРКА И ИСПРАВЛЕНИЕ ЗАГОЛОВКОВ СПРАВОЧНИКА
        try:
            sprav_headers = sprav.row_values(1)
            expected_sprav_headers = [
                "Адрес",           # A
                "Район",           # B
                "Промоутер",      # C
                "Частота (дни)",  # D
                "Последнее посещение",  # E
                "Статус листовок",  # F
                "Статус карты",  # G
                "Широта",        # H
                "Долгота"         # I
            ]
            
            # Проверяем и обновляем заголовки
            if not sprav_headers or len(sprav_headers) < 9:
                # Заголовки отсутствуют или неполные
                sprav.update(values=[expected_sprav_headers], range_name="A1:I1")
                logging.info("✅ Созданы заголовки в 'Справочник': A1:I1")
            else:
                # Проверяем соответствие первых 9 колонок
                headers_correct = True
                for i in range(9):
                    if i >= len(sprav_headers) or sprav_headers[i] != expected_sprav_headers[i]:
                        headers_correct = False
                        break
                
                if not headers_correct:
                    # Обновляем заголовки A1:I1
                    sprav.update(values=[expected_sprav_headers], range_name="A1:I1")
                    logging.warning("⚠️ Обновлены заголовки 'Справочник': A1:I1")
                
                # 🔥 КРИТИЧНО: Очищаем лишние заголовки справа (J и далее)
                if len(sprav_headers) > 9:
                    # Есть лишние колонки - очищаем их заголовки
                    extra_cols_count = len(sprav_headers) - 9
                    empty_headers = [""] * extra_cols_count
                    # Очищаем J1 и далее
                    end_col_letter = chr(ord('J') + extra_cols_count - 1)  # J, K, L...
                    sprav.update(values=[empty_headers], range_name=f"J1:{end_col_letter}1")
                    logging.warning(f"⚠️ Очищены лишние заголовки в 'Справочник': J1:{end_col_letter}1")
                
                if headers_correct and len(sprav_headers) == 9:
                    logging.info("✅ Заголовки 'Справочник' корректны")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось проверить/создать заголовки Справочника: {e}")
        balances_sheet = sheet.worksheet("Балансы")
        flyers_sheet = sheet.worksheet("Листовки")
        # Убедимся, что есть заголовки A1:B1 для корректного баланса листовок
        try:
            flyers_headers = flyers_sheet.row_values(1)
        except Exception:
            flyers_headers = []
        if not flyers_headers:
            try:
                flyers_sheet.update(values=[["Промоутер", "Листовки"]], range_name="A1:B1")
                logging.info("✅ Заголовки для 'Листовки' установлены: A1:B1")
            except Exception as e:
                logging.warning(f"⚠️ Не удалось установить заголовки 'Листовки': {e}")
        
        # Пытаемся открыть лист "Заявки на листовки" (старый формат), если нет - пропускаем
        try:
            requests_sheet = sheet.worksheet("Заявки на листовки")
            logging.info("✅ Лист 'Заявки на листовки' найден (старый формат)")
        except gspread.exceptions.WorksheetNotFound:
            logging.warning("⚠️ Лист 'Заявки на листовки' не найден, используем только новый лист 'Заявки'")
            requests_sheet = None  # Не критично, основной лист - 'Заявки'
        otchety = sheet.worksheet("Отчёты")
        photo_hashes_sheet = sheet.worksheet("photo_hashes")
        
        # 🎉 НОВОЕ: Инициализация листа "Заявки на листовки"
        try:
            flyer_requests_sheet = sheet.worksheet("Заявки")
            logging.info("✅ Лист 'Заявки' найден")
        except gspread.exceptions.WorksheetNotFound:
            flyer_requests_sheet = sheet.add_worksheet(title="Заявки", rows=100, cols=6)
            # Создаём заголовки
            flyer_requests_sheet.update(values=[["Промоутер", "Имя", "Дата заявки", "Количество", "Статус", "Дата одобрения"]], range_name="A1:F1")
            logging.info("✅ Лист 'Заявки' создан")
        
        # 🎯 НОВОЕ: Инициализация листа "Приоритетные адреса"
        try:
            priority_addresses_sheet = sheet.worksheet("Приоритетные адреса")
            logging.info("✅ Лист 'Приоритетные адреса' найден")
        except gspread.exceptions.WorksheetNotFound:
            priority_addresses_sheet = sheet.add_worksheet(title="Приоритетные адреса", rows=100, cols=5)
            # Создаём заголовки
            priority_addresses_sheet.update(values=[["Адрес", "Дата добавления", "Статус", "Приоритет", "Последнее посещение"]], range_name="A1:E1")
            logging.info("✅ Лист 'Приоритетные адреса' создан")
        
        # 💰 НОВОЕ: Инициализация листа "Финансы" (учёт доходов/расходов)
        try:
            finance_sheet = sheet.worksheet("Финансы")
            logging.info("✅ Лист 'Финансы' найден")
            # Убедимся, что есть как минимум 11 колонок (A..K)
            try:
                headers = finance_sheet.row_values(1)
            except Exception:
                headers = []
            # Если меньше 11 колонок — расширяем
            try:
                finance_sheet.resize(cols=11)
            except Exception:
                pass
            # Обновим заголовки, добавив 'Статус' в K1, если его нет
            if headers:
                if len(headers) < 11:
                    headers += [""] * (11 - len(headers))
                if headers[10] != "Статус":
                    headers[10] = "Статус"
                try:
                    finance_sheet.update(values=[headers[:11]], range_name="A1:K1")
                except Exception:
                    pass
            else:
                try:
                    finance_sheet.update(values=[[
                        "Дата", "Промоутер", "Адрес", "Район", "Тип", "Категория", "Количество", "Цена за единицу", "Сумма", "Комментарий", "Статус"
                    ]], range_name="A1:K1")
                except Exception:
                    pass
        except gspread.exceptions.WorksheetNotFound:
            finance_sheet = sheet.add_worksheet(title="Финансы", rows=500, cols=11)
            finance_sheet.update(values=[[
                "Дата", "Промоутер", "Адрес", "Район", "Тип", "Категория", "Количество", "Цена за единицу", "Сумма", "Комментарий", "Статус"
            ]], range_name="A1:K1")
            logging.info("✅ Лист 'Финансы' создан (11 колонок, включая 'Статус')")
        
        # 💹 НОВОЕ: Инициализация листа "ROI" (агрегация доход/расход/ROI)
        try:
            roi_sheet = sheet.worksheet("ROI")
            logging.info("✅ Лист 'ROI' найден")
        except gspread.exceptions.WorksheetNotFound:
            roi_sheet = sheet.add_worksheet(title="ROI", rows=500, cols=20)  # 🔧 Увеличено до 20 колонок для Dashboard
            roi_sheet.update(values=[[
                "Дата", "Район", "Промоутер", "Доход (₽)", "Расход (₽)", "ROI", "Адресов", "Фото"
            ]], range_name="A1:H1")
            logging.info("✅ Лист 'ROI' создан")

        # ИСПРАВЛЕНО: Проверяем и создаём колонки в таблице "Балансы" (6 колонок: ID | Баланс ₽ | Баланс листовок | Телефон | Имя | Дата регистрации)
        try:
            headers = balances_sheet.row_values(1)
            if not headers:
                # Если заголовков нет, создаём их
                balances_sheet.update(values=[["ПромоутерID", "Баланс (₽)", "Листовки (шт)", "Телефон", "Имя", "Дата регистрации"]], range_name="A1:F1")
                logging.info("✅ Созданы заголовки в таблице 'Балансы': ID | Баланс ₽ | Листовки | Телефон | Имя | Дата")
            else:
                # Приводим заголовки к единому формату
                expected_headers = ["ПромоутерID", "Баланс (₽)", "Листовки (шт)", "Телефон", "Имя", "Дата регистрации"]
                if len(headers) < 6:
                    while len(headers) < 6:
                        headers.append("")
                for i, header in enumerate(expected_headers):
                    if i < len(headers) and headers[i] != header:
                        headers[i] = header
                # Обновляем заголовки
                balances_sheet.update(values=[headers[:6]], range_name="A1:F1")
                logging.info("✅ Обновлены заголовки в таблице 'Балансы'")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось проверить/создать колонки: {e}")

        logging.info("✅ Подключение к Google Sheets успешно")
        
        # Настройки и сводные столбцы
        ensure_settings_sheet()
        load_settings(force=True)
        ensure_flyers_before_column()
        
        # Авто-графики ROI
        try:
            ensure_roi_dashboard_and_charts()
        except Exception as e:
            logging.warning(f"⚠️ Не удалось создать авто-графики ROI: {e}")
        
        # ОТКЛЮЧЕНО: Автоматическое исправление координат при запуске
        # Раскомментируй только если нужно массово исправить координаты:
        # fix_invalid_coordinates()
        
    except FileNotFoundError as fnf_error:
        logging.critical(f"❌ Файл не найден: {fnf_error}")
        logging.critical(f"💡 Проверьте путь к credentials.json: {GOOGLE_CREDENTIALS_FILE}")
        raise SystemExit("Не удалось подключиться к Google Sheets")
    except gspread.exceptions.APIError as api_error:
        logging.critical(f"❌ API ошибка Google Sheets: {api_error}")
        logging.critical("💡 Проверьте доступ сервисного аккаунта к таблице")
        raise SystemExit("Не удалось подключиться к Google Sheets")
    except gspread.exceptions.SpreadsheetNotFound:
        logging.critical(f"❌ Таблица не найдена: {SPREADSHEET_URL}")
        logging.critical("💡 Проверьте URL таблицы и доступ сервисного аккаунта")
        raise SystemExit("Не удалось подключиться к Google Sheets")
    except Exception as e:
        logging.critical(f"❌ ФАТАЛЬНАЯ ОШИБКА Google Sheets: {type(e).__name__}: {e}")
        import traceback
        logging.critical(f"🐞 Traceback:\n{traceback.format_exc()}")
        raise SystemExit("Не удалось подключиться к Google Sheets")


def fix_invalid_coordinates() -> None:
    """
    Исправляет неправильные координаты в справочнике.
    Если координаты выглядят подозрительно (user_id или очень маленькие значения),
    то перегеокодирует адрес и обновляет координаты.
    """
    try:
        if not sprav:
            return
        
        logging.info("🔧 Проверка координат в справочнике...")
        all_values = sprav.get_all_values()
        if len(all_values) <= 1:
            return
        
        fixed_count = 0
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) < 4:
                continue
            
            addr = row[0]
            try:
                lat = float(row[7]) if len(row) > 7 and row[7] else 0  # ШИРОТА (столбец H)
                lng = float(row[8]) if len(row) > 8 and row[8] else 0  # ДОЛГОТА (столбец I)
            except (ValueError, TypeError):
                lat = 0
                lng = 0
            
            # Проверяем, что координаты подозрительные:
            # - не в пределах Калининграда (54.5-54.9, 20.2-20.7)
            # - или равны 0
            # - или слишком большие (похожи на user_id)
            is_invalid = (
                lat == 0 or lng == 0 or
                lat > 1000 or lng > 1000 or  # Это точно user_id
                lat < 50 or lng < 15 or      # Слишком маленькие для Калининграда
                not (54.5 <= lat <= 54.9) or
                not (20.2 <= lng <= 20.7)
            )
            
            if is_invalid and addr:
                logging.info(f"🔍 Исправляю координаты для '{addr}': ({lat}, {lng})")
                # Геокодируем адрес заново
                result = geocode_address(addr)
                if result:
                    new_lat, new_lng, new_district = result  # 🔥 НОВОЕ: Извлекаем район!
                    # Обновляем координаты в таблице
                    sprav.update_cell(i, 8, str(new_lat))  # ШИРОТА (колонка H)
                    sprav.update_cell(i, 9, str(new_lng))  # ДОЛГОТА (колонка I)
                    # 🗺️ НОВОЕ: Обновляем РАЙОН!
                    sprav.update_cell(i, 2, new_district)  # РАЙОН (колонка B)
                    fixed_count += 1
                    logging.info(f"✅ Исправлено: '{addr}' -> ({new_lat}, {new_lng}, {new_district})")
                else:
                    logging.warning(f"⚠️ Не удалось геокодировать '{addr}'")
        
        if fixed_count > 0:
            logging.info(f"✅ Исправлено координат: {fixed_count}")
        else:
            logging.info("✅ Все координаты корректны")
    except Exception as e:
        logging.critical(f"❌ ФАТАЛЬНАЯ ОШИБКА Google Sheets: {e}")
        raise SystemExit("Не удалось подключиться к Google Sheets")


def ensure_flyers_before_column() -> None:
    """
    🎯 НОВОЕ: Добавляет столбцы 'Листовки до' и 'Листовки наклеено' в 'Справочник' если их нет.
    Эти столбцы фиксируют:
    - J: Сколько листовок уже БЫЛО до начала работы
    - K: Сколько листовок промоутер НАКЛЕИЛ (по количеству фото)
    
    Структура Справочника:
    A: АДРЕС
    B: РАЙОН
    C: ПРОМОУТЕР
    D: ФОТО
    E: ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ
    F: СТАТУС ЛИСТОВОК
    G: СТАТУС КАРТЫ
    H: ШИРОТА
    I: ДОЛГОТА
    J: ЛИСТОВКИ ДО (новый столбец)
    K: ЛИСТОВКИ НАКЛЕЕНО (новый столбец)
    """
    try:
        if not sprav:
            return
        
        headers = sprav.row_values(1)
        if not headers:
            logging.warning("⚠️ Заголовки 'Справочник' отсутствуют")
            return
        
        modified = False
        
        # Проверяем наличие столбца 'ЛИСТОВКИ ДО' (J)
        if len(headers) < 10 or headers[9] != "ЛИСТОВКИ ДО":
            if len(headers) < 10:
                headers.extend([""] * (10 - len(headers)))
            headers[9] = "ЛИСТОВКИ ДО"
            modified = True
            logging.info("✅ Добавлен столбец 'ЛИСТОВКИ ДО' в 'Справочник'")
        
        # Проверяем наличие столбца 'ЛИСТОВКИ НАКЛЕЕНО' (K)
        if len(headers) < 11 or headers[10] != "ЛИСТОВКИ НАКЛЕЕНО":
            if len(headers) < 11:
                headers.extend([""] * (11 - len(headers)))
            headers[10] = "ЛИСТОВКИ НАКЛЕЕНО"
            modified = True
            logging.info("✅ Добавлен столбец 'ЛИСТОВКИ НАКЛЕЕНО' в 'Справочник'")
        
        if modified:
            sprav.update(values=[headers], range_name=f"A1:{chr(65 + len(headers) - 1)}1")
            logging.info("✅ Заголовки Справочника обновлены")
        else:
            logging.info("✅ Столбцы 'ЛИСТОВКИ ДО' и 'ЛИСТОВКИ НАКЛЕЕНО' уже существуют")
    except Exception as e:
        logging.error(f"❌ Ошибка добавления столбцов листовок: {e}")


def add_priority_addresses(addresses_text: str, added_by_admin: int) -> Dict[str, Any]:
    """
    🎯 НОВОЕ: Добавляет приоритетные адреса в лист 'Приоритетные адреса'.
    
    Args:
        addresses_text: Строка с адресами через запятую ("Еловая 50, Дзержинского 200")
        added_by_admin: Telegram ID админа
    
    Returns:
        Dict {
            "success": bool,
            "added": int,
            "failed": List[str],
            "updated": int
        }
    """
    try:
        if not priority_addresses_sheet:
            return {"success": False, "error": "Лист 'Приоритетные адреса' не инициализирован"}
        
        # Парсим адреса
        raw_addresses = [addr.strip() for addr in addresses_text.split(",") if addr.strip()]
        
        added_count = 0
        updated_count = 0
        failed = []
        
        # Получаем существующие приоритетные адреса
        existing_data = priority_addresses_sheet.get_all_values()
        existing_addresses = {normalize_text(row[0]): i + 1 for i, row in enumerate(existing_data[1:], start=2) if len(row) > 0 and row[0]}
        
        for address in raw_addresses:
            if not looks_like_address(address):
                failed.append(f"{address} (неверный формат)")
                continue
            
            # Геокодируем
            coords = geocode_address(address)
            if not coords:
                failed.append(f"{address} (не найден)")
                continue
            
            normalized_addr = normalize_text(address)
            current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Проверяем, есть ли адрес в Справочнике
            addr_info = get_address_info(address)
            status = "🟢 Показы идут" if addr_info else "🟡 Обновить"
            last_visit = addr_info[6] if addr_info and len(addr_info) > 6 else ""
            
            # Проверяем, есть ли уже в приоритетных
            if normalized_addr in existing_addresses:
                # Обновляем
                row_num = existing_addresses[normalized_addr]
                priority_addresses_sheet.update(values=[[address, current_time, status, "100", last_visit]], range_name=f"A{row_num}:E{row_num}")
                updated_count += 1
            else:
                # Добавляем новый
                # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно
                all_rows = priority_addresses_sheet.get_all_values()
                next_row = len(all_rows) + 1
                ensure_sheet_has_enough_rows(priority_addresses_sheet, next_row)
                
                priority_addresses_sheet.update(values=[[address, current_time, status, "100", last_visit]], range_name=f"A{next_row}:E{next_row}")
                added_count += 1
        
        # Обновляем кэш приоритетов
        load_address_priorities(force=True)
        
        return {
            "success": True,
            "added": added_count,
            "updated": updated_count,
            "failed": failed
        }
    except Exception as e:
        logging.error(f"❌ Ошибка добавления приоритетных адресов: {e}")
        return {"success": False, "error": str(e)}


def bulk_add_addresses_to_sprav(addresses_text: str, added_by_admin: int) -> Dict[str, Any]:
    """
    📥 Массовый импорт адресов в Справочник.
    
    Поддерживаемые форматы:
    1. Построчный:
       ул. Осенняя, д. 22
       ул. Пражская, д. 25
    
    2. Компактный (улица: номера):
       Краснопрудная: 1, 2, 3, 4, 5
       Московский пркт.: 10, 12А, 14
    """
    try:
        global sprav
        if not sprav:
            return {"success": False, "error": "Лист 'Справочник' не инициализирован"}
        
        # 🔍 Парсинг входных данных
        raw_lines = [l.strip() for l in str(addresses_text).splitlines() if l.strip()]
        addresses_to_add = []
        
        for line in raw_lines:
            # 🔥 НОВОЕ: Удаляем пояснения в скобках (например "Челнакова 40 (Сев. гора)" → "Челнакова 40")
            line = re.sub(r'\s*\([^)]+\)', '', line).strip()
            
            # Проверяем формат "Улица: номер1, номер2..."
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    street = parts[0].strip()
                    house_numbers = parts[1].strip()
                    
                    # Разбиваем номера по запятым
                    numbers = [n.strip() for n in house_numbers.split(',') if n.strip()]
                    
                    # Создаём полные адреса
                    for num in numbers:
                        # 🔥 ИСПРАВЛЕНО: Обрабатываем диапазоны ТОЛЬКО если есть явный дефис между двумя числами
                        range_match = re.match(r'^(\d+)\s*-\s*(\d+)$', num)
                        if range_match:
                            start_val = int(range_match.group(1))
                            end_val = int(range_match.group(2))
                            
                            # Если диапазон разумный (не больше 20 адресов), разворачиваем
                            if 0 < end_val - start_val <= 20:
                                for i in range(start_val, end_val + 1):
                                    full_address = f"{street} {i}"
                                    addresses_to_add.append(full_address)
                            else:
                                # Слишком большой диапазон - оставляем как есть
                                full_address = f"{street} {num}"
                                addresses_to_add.append(full_address)
                        else:
                            # 🔥 НОВОЕ: Удаляем скобки из номера дома
                            num = re.sub(r'\s*\([^)]+\)', '', num).strip()
                            # Обычный номер (может быть "15", "16А", "42-48" как название дома)
                            full_address = f"{street} {num}"
                            addresses_to_add.append(full_address)
                else:
                    # Не похоже на компактный формат, считаем обычным адресом
                    addresses_to_add.append(line)
            else:
                # Обычный построчный формат
                addresses_to_add.append(line)
        
        # 📋 Обработка адресов
        added = 0
        skipped = 0
        failed = []
        
        # 🔥 КРИТИЧНО: Существующие адреса (читаем ТОЛЬКО колонки A-I, игнорируя всё справа)
        all_values_range = sprav.get("A:I")  # Читаем только нужные колонки
        all_values = all_values_range if all_values_range else []
        existing = {normalize_text(row[0]) for row in all_values[1:] if len(row) > 0 and row[0]}
        
        # Определяем следующую свободную строку
        next_row = len(all_values) + 1
        
        logging.info(f"📊 Начало импорта: всего строк={len(all_values)}, существующих адресов={len(existing)}, следующая строка={next_row}")
        
        for raw in addresses_to_add:
            s = sanitize_address_input(raw)
            if not s:
                failed.append(f"{raw} (неверный формат)")
                continue
            
            norm = normalize_text(s)
            if norm in existing:
                skipped += 1
                logging.info(f"⏭️ Пропущен дубликат: {s}")
                continue
            
            # Геокодирование
            coords = geocode_address(s)
            lat, lng, district = (None, None, None)
            if coords:
                lat, lng, district = coords
                district = ensure_real_district(s, lat, lng, district)
            
            status_card = "🔴 Не был"
            new_row = [
                s,
                district or "",
                "",
                str(DEFAULT_FREQUENCY_DAYS),
                "",
                status_card,
                status_card,
                str(lat) if lat is not None else "",
                str(lng) if lng is not None else ""
            ]
            
            try:
                # 🔥 КРИТИЧНО: Добавляем ТОЛЬКО в колонки A-I, игнорируя всё справа
                range_name = f"A{next_row}:I{next_row}"
                sprav.update(values=[new_row], range_name=range_name)
                added += 1
                existing.add(norm)
                next_row += 1
                logging.info(f"✅ Добавлен: {s} | Район: {district} | Строка: {next_row-1}")
            except Exception as e:
                failed.append(f"{raw} (ошибка добавления: {e})")
                logging.error(f"❌ Ошибка добавления {s}: {e}")
        
        return {"success": True, "added": added, "skipped": skipped, "failed": failed}
    
    except Exception as e:
        logging.error(f"❌ Ошибка группового добавления адресов: {e}")
        return {"success": False, "error": str(e)}

def sanitize_address_input(raw: str) -> Optional[str]:
    """
    Очищает и валидирует входной адрес.
    Убирает префиксы 'ул.', 'дом', запятые, лишние пробелы.
    """
    try:
        if raw is None:
            return None
        txt = str(raw).strip()
        if not txt:
            return None
        # Исключаем ссылки
        if re.search(r"(https?://|www\.)", txt, re.IGNORECASE):
            return None
        if re.search(r"[a-z0-9]\.(ru|com|net|org|io|app|gg|ai|co)", txt, re.IGNORECASE):
            return None
        # 🔥 НОВОЕ: Удаляем пояснения в скобках (например "Челнакова 40 (Сев. гора)" → "Челнакова 40")
        txt = re.sub(r'\s*\([^)]+\)', '', txt).strip()
        # Убираем декоративные символы в начале
        txt = re.sub(r"^[\s\-—*•·]+", "", txt)
        # Удаляем префиксы и запятые
        txt = re.sub(r"^\s*(ул\.?|улица)\s*", "", txt, flags=re.IGNORECASE)
        txt = re.sub(r"\s*,\s*", " ", txt)
        txt = re.sub(r"\s*(д\.?|дом)\s*", " ", txt, flags=re.IGNORECASE)
        # Убираем кавычки
        txt = txt.replace('"', "").replace("'", "")
        # Схлопываем пробелы
        txt = re.sub(r"\s+", " ", txt).strip()
        # Валидируем
        return txt if looks_like_address(txt) else None
    except Exception:
        return None


    """
    🎯 НОВОЕ: Получает все приоритетные адреса с кэшированием.
    Кэш обновляется каждые 10 минут для снижения нагрузки на Google Sheets API.
    
    Args:
        force: Принудительно обновить кэш
    
    Returns:
        List[Dict] [
            {
                "address": str,
                "added_date": str,
                "status": str,
                "priority": int,
                "last_visit": str
            },
            ...
        ]
    """
    global PRIORITY_ADDRESSES_CACHE
    
    try:
        # Проверяем кэш
        now = datetime.now()
        if not force and PRIORITY_ADDRESSES_CACHE["loaded_at"]:
            elapsed = (now - PRIORITY_ADDRESSES_CACHE["loaded_at"]).total_seconds()
            if elapsed < 600:  # 10 минут кэш
                return PRIORITY_ADDRESSES_CACHE["addresses"]
        
        # Загружаем из Google Sheets
        if not priority_addresses_sheet:
            return []
        
        all_values = priority_addresses_sheet.get_all_values()
        if len(all_values) <= 1:
            PRIORITY_ADDRESSES_CACHE = {"loaded_at": now, "addresses": []}
            return []
        
        result = []
        for row in all_values[1:]:
            if len(row) >= 4 and row[0]:
                result.append({
                    "address": row[0],
                    "added_date": row[1] if len(row) > 1 else "",
                    "status": row[2] if len(row) > 2 else "",
                    "priority": int(row[3]) if len(row) > 3 and row[3].isdigit() else 100,
                    "last_visit": row[4] if len(row) > 4 else ""
                })
        
        # Обновляем кэш
        PRIORITY_ADDRESSES_CACHE = {"loaded_at": now, "addresses": result}
        logging.info(f"✅ Загружено {len(result)} приоритетных адресов (кэш обновлён)")
        
        return result
    except Exception as e:
        logging.error(f"❌ Ошибка получения приоритетных адресов: {e}")
        # Возвращаем старый кэш при ошибке
        return PRIORITY_ADDRESSES_CACHE.get("addresses", [])

# ============================
# 🧮 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================
def looks_like_address(text: str) -> bool:
    """
    Validates address like 'StreetName 123' or 'Street Name, 123'.
    Requires street words and a house number (supports suffixes like 'к1', 'а', 'б').
    """
    raw = (text or "").strip().lower()
    # 🚫 Не считаем ссылки адресами
    if re.search(r"(https?://|www\.)", raw):
        return False
    if re.search(r"[a-z0-9]\.(ru|com|net|org|io|app|gg|ai|co)", raw):
        return False
    s = normalize_text(text)
    if len(s) < 4 or not re.search(r"\d", s):
        return False
    return bool(re.match(r"^[a-zа-яё\-\s]+\s*(\d+[a-zа-я]?([\s\-/]*к\d+)?)$", s))

def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    Гибкий парсинг даты, поддерживает форматы:
    - DD.MM.YYYY HH:MM (с временем)
    - DD.MM.YYYY (только дата, время = 00:00)
    Возвращает None если формат некорректен
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip()
    
    # Попытка 1: Полный формат с временем
    try:
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M")
    except ValueError:
        pass
    
    # Попытка 2: Только дата (добавляем 00:00)
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        pass
    
    # Если ничего не подошло
    logging.warning(f"⚠️ Неверный формат даты: {date_str} | Ожидается DD.MM.YYYY или DD.MM.YYYY HH:MM")
    return None

def get_promoter_identifier(user) -> str:
    return str(user.id)

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lng2 - lng1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def geocode_address_yandex(address: str) -> Optional[Tuple[float, float]]:
    """Геокодирование через Yandex Geocoder API."""
    try:
        import urllib.parse
        # Не кодируем строку дважды - передаем как есть в параметрах requests
        full_address = f"Калининград, {address}"
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": YANDEX_API_KEY,
            "geocode": full_address,
            "format": "json",
            "results": 1,
        }
        response = requests.get(url, params=params, timeout=3)
        response.raise_for_status()
        data = response.json()
        if (
            data.get("response")
            and data["response"].get("GeoObjectCollection")
            and data["response"]["GeoObjectCollection"].get("featureMember")
        ):
            pos = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
            lng, lat = map(float, pos.split())
            # Проверяем, что координаты в пределах Калининграда
            if 54.5 <= lat <= 54.9 and 20.2 <= lng <= 20.7:
                logging.info(f"✅ Yandex геокодирование '{address}' -> {lat}, {lng}")
                return lat, lng
    except Exception as e:
        logging.error(f"Ошибка геокодирования Yandex '{address}': {e}")
    return None

def geocode_address_osm(address: str) -> Optional[Tuple[float, float, str]]:
    """
    🔥 УЛУЧШЕНО: Геокодирование через OSM Nominatim + извлечение района!
    
    Returns:
        Tuple[lat, lng, district] или None
    """
    try:
        import urllib.parse
        # Не кодируем строку дважды - передаем как есть в параметрах requests
        full_address = f"Калининград, {address}"
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={full_address}&addressdetails=1"
        headers = {"User-Agent": OSM_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=3)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]["lat"])
            lng = float(data[0]["lon"])
            
            # Проверяем, что координаты в пределах Калининграда
            if 54.5 <= lat <= 54.9 and 20.2 <= lng <= 20.7:
                # 🗺️ НОВОЕ: Извлекаем район из OSM!
                district = extract_district_from_osm(data[0])
                logging.info(f"✅ OSM геокодирование '{address}' -> {lat}, {lng} ({district})")
                return lat, lng, district
    except Exception as e:
        logging.error(f"Ошибка геокодирования OSM '{address}': {e}")
    return None

def geocode_address(address: str) -> Optional[Tuple[float, float, str]]:
    """
    🔥 УЛУЧШЕНО: Геокодирование адреса + автоматическое определение района!
    
    Returns:
        Tuple[lat, lng, district] или None
    """
    import re
    # Убираем "— подъезд N" из адреса перед геокодированием
    clean_address = re.sub(r'\s*[—–-]\s*подъезд\s*\d+', '', address, flags=re.IGNORECASE)
    clean_address = clean_address.strip()
    
    # Пробуем Yandex (возвращает только coords)
    coords = geocode_address_yandex(clean_address)
    if coords:
        lat, lng = coords
        # Определяем район через OSM reverse
        district = get_district_from_osm_reverse(lat, lng)
        if not district:
            # Fallback на расчёт по центрам районов
            district = get_district_by_coords(lat, lng)
        logging.info(f"✅ Геокодирование через Yandex: {clean_address} -> ({lat}, {lng}, {district})")
        return lat, lng, district
    
    # Fallback на OSM (возвращает coords + district)
    logging.warning(f"Yandex не вернул координаты для '{clean_address}', пробую OSM...")
    result = geocode_address_osm(clean_address)
    if result:
        return result  # (lat, lng, district)
    
    logging.error(f"Не удалось геокодировать адрес '{clean_address}' ни через Yandex, ни через OSM")
    return None

# ИСПРАВЛЕНО: Добавлен docstring и значение по умолчанию
def get_district_by_coords(lat: float, lng: float) -> str:
    """
    Определяет ближайший административный район Калininграда по координатам.
    
    Использует метод минимального расстояния до центра района (алгоритм Хаверсина).
    Для координат за пределами Калininграда возвращает "Центральный" по умолчанию.
    
    Args:
        lat: Широта (latitude) в градусах
        lng: Долгота (longitude) в градусах
    
    Returns:
        Название ближайшего района из 4 официальных:
        Центральный, Ленинградский, Московский, Октябрьский
    
    Example:
        >>> get_district_by_coords(54.710, 20.512)
        'Центральный'
    """
    min_distance: float = float("inf")
    closest_district: str = "Центральный"  # Значение по умолчанию
    
    for district_name, (d_lat, d_lng) in DISTRICT_CENTERS.items():
        distance = haversine_distance(lat, lng, d_lat, d_lng)
        if distance < min_distance:
            min_distance = distance
            closest_district = district_name
    
    return closest_district


def extract_district_from_osm(osm_data: Dict[str, Any]) -> str:
    """
    🗺️ НОВОЕ: Извлекает район из OSM Nominatim response (прямое геокодирование).
    
    Приоритет извлечения:
    1. address.suburb (микрорайон)
    2. address.district (административный район)
    3. address.neighbourhood (квартал)
    4. Fallback на get_district_by_coords() если ничего не найдено
    
    Args:
        osm_data: JSON response от OSM Nominatim
    
    Returns:
        Название района ("Ленинградский", "Московский", "Центральный", "Октябрьский")
    """
    try:
        address = osm_data.get("address", {})
        
        # Пытаемся извлечь район из нескольких полей
        raw_district = (
            address.get("suburb") or 
            address.get("district") or 
            address.get("neighbourhood") or 
            address.get("quarter") or
            ""
        )
        
        if raw_district:
            # Нормализуем название района
            normalized = normalize_district_name(raw_district)
            if normalized:
                logging.info(f"🗺️ Район из OSM address: '{raw_district}' -> '{normalized}'")
                return normalized
        
        # Fallback на координаты
        lat = float(osm_data.get("lat", 0))
        lng = float(osm_data.get("lon", 0))
        if lat and lng:
            district = get_district_by_coords(lat, lng)
            logging.info(f"🗺️ Район через координаты: {lat},{lng} -> {district}")
            return district
        
    except Exception as e:
        logging.warning(f"⚠️ Ошибка извлечения района из OSM: {e}")
    
    return "Ленинградский"  # Default по памяти пользователя


def get_district_from_osm_reverse(lat: float, lng: float) -> Optional[str]:
    """
    🗺️ НОВОЕ: Определяет район через OSM Nominatim reverse geocoding.
    
    Args:
        lat: Широта
        lng: Долгота
    
    Returns:
        Название района или None при ошибке
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&addressdetails=1"
        headers = {"User-Agent": OSM_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=3)
        response.raise_for_status()
        data = response.json()
        
        if data and "address" in data:
            address = data["address"]
            
            # Извлекаем район из нескольких полей
            raw_district = (
                address.get("suburb") or 
                address.get("district") or 
                address.get("neighbourhood") or
                address.get("quarter") or
                ""
            )
            
            if raw_district:
                normalized = normalize_district_name(raw_district)
                if normalized:
                    logging.info(f"🗺️ Район через OSM reverse ({lat},{lng}): '{raw_district}' -> '{normalized}'")
                    return normalized
        
    except Exception as e:
        logging.debug(f"⚠️ Ошибка OSM reverse для района: {e}")
    
    return None


def normalize_district_name(raw_name: str) -> Optional[str]:
    """
    🗺️ НОВОЕ: Нормализует название района из OSM к официальным названиям Калининграда.
    
    Сопоставляет различные написания (включая транслитерацию) с 4 официальными районами:
    - Центральный (Tsentralny)
    - Ленинградский (Leningradsky)
    - Московский (Moskovsky)
    - Октябрьский (Oktyabrsky)
    
    Args:
        raw_name: Сырое название из OSM (может быть на русском или латинице)
    
    Returns:
        Официальное название района или None если не удалось распознать
    """
    if not raw_name:
        return None
    
    # Приводим к нижнему регистру для сравнения
    name_lower = raw_name.lower().strip()
    
    # Маппинг: различные варианты написания -> официальное название
    DISTRICT_MAPPINGS = {
        "центральный": "Центральный",
        "tsentralny": "Центральный",
        "central": "Центральный",
        "center": "Центральный",
        
        "ленинградский": "Ленинградский",
        "leningradsky": "Ленинградский",
        "leningrad": "Ленинградский",
        
        "московский": "Московский",
        "moskovsky": "Московский",
        "moscow": "Московский",
        
        "октябрьский": "Октябрьский",
        "oktyabrsky": "Октябрьский",
        "october": "Октябрьский",
    }
    
    # Проверяем точное совпадение
    if name_lower in DISTRICT_MAPPINGS:
        return DISTRICT_MAPPINGS[name_lower]
    
    # Проверяем частичное совпадение (если название содержит ключевое слово)
    for key, official_name in DISTRICT_MAPPINGS.items():
        if key in name_lower or name_lower in key:
            return official_name
    
    return None


# ============================
# 🗺️ OSMNX ГЕОПРОСТРАНСТВЕННЫЙ АНАЛИЗ
# ============================

def load_osmnx_graph() -> Optional[Any]:
    """
    🗺️ НОВОЕ: Загружает граф улично-дорожной сети Калининграда через OSMnx.
    
    Кэшируется на 24 часа для производительности.
    
    Returns:
        networkx.MultiDiGraph или None если OSMnx недоступен
    """
    global OSMNX_GRAPH_CACHE
    
    if not OSMNX_AVAILABLE:
        return None
    
    try:
        # Проверяем кэш (24 часа)
        now = datetime.now()
        if OSMNX_GRAPH_CACHE["graph"] and OSMNX_GRAPH_CACHE["loaded_at"]:
            if now < OSMNX_GRAPH_CACHE["loaded_at"] + timedelta(hours=24):
                logging.info("🗺️ OSMnx граф из кэша")
                return OSMNX_GRAPH_CACHE["graph"]
        
        # Загружаем граф для Калининграда
        logging.info("🗺️ Загрузка OSMnx графа для Калининграда...")
        
        # Используем геокодирование по названию города
        G = ox.graph_from_place(
            "Kaliningrad, Russia",
            network_type="walk",  # Пешеходная сеть (для промоутеров)
            simplify=True
        )
        
        OSMNX_GRAPH_CACHE["graph"] = G
        OSMNX_GRAPH_CACHE["loaded_at"] = now
        
        logging.info(f"✅ OSMnx граф загружен: {len(G.nodes)} узлов, {len(G.edges)} рёбер")
        return G
        
    except Exception as e:
        logging.warning(f"⚠️ Ошибка загрузки OSMnx графа: {e}")
        return None


def get_walking_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> Optional[float]:
    """
    🗺️ НОВОЕ: Рассчитывает РЕАЛЬНОЕ пешеходное расстояние по OSMnx.
    
    Преимущества перед Haversine:
    - Учитывает реальные улицы и дороги
    - Не проходит сквозь здания
    - Точнее для промоутеров (пешком)
    
    Args:
        lat1, lng1: Координаты точки А
        lat2, lng2: Координаты точки Б
    
    Returns:
        Расстояние в метрах или None (если OSMnx недоступен)
    """
    G = load_osmnx_graph()
    if not G:
        # Fallback на Haversine
        return haversine_distance(lat1, lng1, lat2, lng2)
    
    try:
        # Находим ближайшие узлы на графе
        orig_node = ox.nearest_nodes(G, lng1, lat1)
        dest_node = ox.nearest_nodes(G, lng2, lat2)
        
        # Рассчитываем кратчайший путь
        try:
            shortest_path_length = nx.shortest_path_length(
                G, 
                orig_node, 
                dest_node, 
                weight="length"
            )
            logging.debug(f"🗺️ OSMnx: {shortest_path_length:.0f}м ({lat1},{lng1}) -> ({lat2},{lng2})")
            return shortest_path_length
        except nx.NetworkXNoPath:
            # Нет пути по графу - fallback на Haversine
            logging.debug(f"⚠️ Нет пути по графу, использую Haversine")
            return haversine_distance(lat1, lng1, lat2, lng2)
            
    except Exception as e:
        logging.debug(f"⚠️ Ошибка OSMnx расчёта: {e}")
        return haversine_distance(lat1, lng1, lat2, lng2)


def get_nearby_buildings_osmnx(lat: float, lng: float, radius_m: int = 100) -> List[Dict[str, Any]]:
    """
    🗺️ НОВОЕ: Находит ближайшие жилые здания через OSMnx.
    
    Преимущества:
    - Получаем данные о зданиях (building:levels, addr:housenumber)
    - Фильтруем нежилые здания
    - Точные координаты адресов
    
    Args:
        lat, lng: Центр поиска
        radius_m: Радиус поиска (метры)
    
    Returns:
        Список словарей с данными о зданиях
    """
    if not OSMNX_AVAILABLE:
        return []
    
    try:
        # Загружаем здания в радиусе
        tags = {"building": True}
        buildings = ox.geometries_from_point(
            (lat, lng),
            dist=radius_m,
            tags=tags
        )
        
        if buildings.empty:
            return []
        
        # Фильтруем жилые здания
        residential_types = ["residential", "apartments", "house", "detached", "yes"]
        
        results = []
        for idx, row in buildings.iterrows():
            building_type = row.get("building", "")
            
            # Пропускаем нежилые
            if building_type not in residential_types:
                continue
            
            # Извлекаем адрес
            street = row.get("addr:street", "")
            housenumber = row.get("addr:housenumber", "")
            
            if not street or not housenumber:
                continue
            
            # Координаты центра здания
            centroid = row.geometry.centroid
            b_lat = centroid.y
            b_lng = centroid.x
            
            results.append({
                "address": f"{street} {housenumber}",
                "lat": b_lat,
                "lng": b_lng,
                "levels": row.get("building:levels", None),
                "building_type": building_type
            })
        
        logging.info(f"🗺️ OSMnx: найдено {len(results)} жилых зданий")
        return results
        
    except Exception as e:
        logging.warning(f"⚠️ Ошибка OSMnx поиска зданий: {e}")
        return []


def is_address_available(last_visit_str: str, status_card: str) -> Tuple[bool, bool]:
    """
    Возвращает (доступен ли адрес сейчас, нужно ли сбросить статус по давности).
    """
    reset_needed = False
    effective_status = status_card
    # Сброс статуса через DAYS_TO_RESET_STATUS дней
    if last_visit_str:
        last_visit = parse_date_flexible(last_visit_str)
        if last_visit and datetime.now() >= last_visit + timedelta(days=DAYS_TO_RESET_STATUS):
            reset_needed = True
            effective_status = "🟡 Ожидает"

    if effective_status == "🟡 Нет доступа":
        min_hours = MIN_REVISIT_HOURS_NO_ACCESS
    else:
        min_hours = MIN_REVISIT_HOURS

    if last_visit_str and not reset_needed:
        last_visit = parse_date_flexible(last_visit_str)
        if last_visit and datetime.now() < last_visit + timedelta(hours=min_hours):
            return False, reset_needed

    return True, reset_needed

def update_reklama_status_if_needed(cell_row: int, last_visit_str: str) -> bool:
    """Если прошло DAYS_TO_RESET_STATUS дней — сбрасываем статус."""
    if not last_visit_str:
        return False
    
    last_visit = parse_date_flexible(last_visit_str)
    if last_visit and datetime.now() >= last_visit + timedelta(days=DAYS_TO_RESET_STATUS):
        sprav.update_cell(cell_row, 6, "🟡 Ожидает")
        sprav.update_cell(cell_row, 7, "🟡 Ожидает")
        logging.info(
            f"🔄 Статус рекламы и карты для строки {cell_row} обновлён на '🟡 Ожидает'."
        )
        return True
    
    return False

def reverse_geocode(lat: float, lng: float) -> Optional[str]:
    """
    Обратное геокодирование: координаты -> адрес.
    Сначала Yandex, затем OSM.
    """
    try:
        # Пробуем Yandex Geocoder
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": YANDEX_API_KEY,
            "geocode": f"{lng},{lat}",
            "format": "json",
            "results": 1,
            "kind": "house",
        }
        response = requests.get(url, params=params, timeout=3)
        response.raise_for_status()
        data = response.json()
        if (
            data.get("response")
            and data["response"].get("GeoObjectCollection")
            and data["response"]["GeoObjectCollection"].get("featureMember")
        ):
            geo_object = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            address = geo_object.get("name", "")
            if address:
                # Извлекаем только улицу и дом
                parts = address.split(",")
                if len(parts) >= 1:
                    address = parts[0].strip()
                    logging.info(f"✅ Yandex обратное геокодирование {lat},{lng} -> {address}")
                    return address
    except Exception as e:
        logging.error(f"Ошибка обратного геокодирования Yandex: {e}")

    try:
        # Пробуем OSM Nominatim
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&addressdetails=1"
        headers = {"User-Agent": OSM_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=3)
        response.raise_for_status()
        data = response.json()
        if data and "address" in data:
            addr_parts = data["address"]
            road = addr_parts.get("road", "")
            house_number = addr_parts.get("house_number", "")
            if road:
                address = f"{road} {house_number}".strip() if house_number else road
                logging.info(f"✅ OSM обратное геокодирование {lat},{lng} -> {address}")
                return address
    except Exception as e:
        logging.error(f"Ошибка обратного геокодирования OSM: {e}")

    return None


def get_osm_extratags(lat: float, lng: float) -> Dict[str, Any]:
    """Запрашивает extratags с Nominatim для объекта по координатам."""
    try:
        import urllib.parse
        # Не кодируем строку дважды - передаем как есть в параметрах requests
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&addressdetails=1&extratags=1"
        headers = {"User-Agent": OSM_USER_AGENT}
        response = requests.get(url, headers=headers, timeout=3)
        response.raise_for_status()
        data = response.json()
        return data.get("extratags", {}) if isinstance(data, dict) else {}
    except Exception as e:
        logging.debug(f"OSM extratags error: {e}")
        return {}


def get_or_create_nearby_addresses(
    current_lat: float, current_lng: float, exclude_address: str = "", limit: int = MAX_NEARBY_ADDRESSES
) -> List[Tuple[str, float, float, float, str]]:
    """
    Умный поиск и создание адресов:
    1. Ищет существующие адреса в радиусе LOCATION_RADIUS_METERS
    2. Если найдено меньше limit — создаёт новые через обратное геокодирование с фильтрацией качества
    3. Автоматически добавляет в Справочник
    Returns: List[(address, lat, lng, distance_meters, status_icon)]
    """
    try:
        all_records = sprav.get_all_records()
        candidates: List[Tuple[float, str, float, float, str]] = []
        existing_addresses = set()

        # Настройки
        load_settings()
        settings = SETTINGS
        blocklist = [s.strip().lower() for s in str(settings.get("LOW_VALUE_BLOCKLIST", "")).split(",") if s.strip()]
        preferred_suffixes = [s.strip().lower() for s in str(settings.get("PREFERRED_SUFFIXES", "")).split(",") if s.strip()]
        min_high_house = int(settings.get("MIN_HIGH_HOUSE_NUMBER", "100")) if settings.get("MIN_HIGH_HOUSE_NUMBER") else 100
        verify_residential = str(settings.get("VERIFY_OSM_RESIDENTIAL", "1")) == "1"

        # Сначала ищем существующие адреса в радиусе
        for r in all_records:
            addr = str(r.get("АДРЕС", "")).strip()
            if not addr:
                continue
            existing_addresses.add(normalize_text(addr))
            if normalize_text(addr) == normalize_text(exclude_address):
                continue
            try:
                lat = float(r.get("ШИРОТА", 0) or 0)
                lng = float(r.get("ДОЛГОТА", 0) or 0)
            except (ValueError, TypeError):
                lat, lng = 0.0, 0.0
            if not lat or not lng:
                # ⚡ УСКОРЕНИЕ UX: Пропускаем адреса без координат вместо геокодирования
                # Геокодирование внутри цикла замедляло отклик до 40+ секунд!
                # Решение: Админ должен заполнить координаты в таблице заранее
                logging.debug(f"⚡ Пропущен адрес без координат: '{addr}'")
                continue
            dist = haversine_distance(current_lat, current_lng, lat, lng)
            if dist > LOCATION_RADIUS_METERS:
                continue
            last_visit = r.get("ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ", "")
            status_card = r.get("СТАТУС КАРТЫ", "🔴 Не был")
            
            # 🔍 ОТЛАДКА: Логируем ВСЕ адреса Еловая 66/68 перед фильтрацией
            if "Еловая" in addr and ("66" in addr or "68" in addr):
                logging.info(f"🔍 ПРОВЕРКА: '{addr}' | status='{status_card}' | last_visit='{last_visit}' | lat={lat}, lng={lng}")
            
            # 🕒 ПРОВЕРКА 18 ЧАСОВ: Скрываем выполненные адреса
            if last_visit:
                last_visit_datetime = parse_date_flexible(last_visit)
                if last_visit_datetime:
                    time_since_last_visit = datetime.now() - last_visit_datetime
                    hours_since_visit = time_since_last_visit.total_seconds() / 3600
                    
                    # ПРАВИЛО #1: "🟢 Показы идут" - скрываем на 18 часов
                    # 🔧 ИСПРАВЛЕНО: Гибкая проверка статуса (с эмодзи и без)
                    if "Показы идут" in status_card:
                        if hours_since_visit < 18:
                            logging.info(f"⏳ Адрес '{addr}' скрыт (🟢 Показы идут, прошло {hours_since_visit:.1f}ч, посл. визит: {last_visit})")
                            continue
                        else:
                            # 🔍 ОТЛАДКА: Логируем когда адрес ПРОХОДИТ фильтр (прошло >=18ч)
                            logging.info(f"✅ Адрес '{addr}' ПРОШЁЛ фильтр (🟢 Показы идут, прошло {hours_since_visit:.1f}ч >= 18ч, посл. визит: {last_visit})")
                    
                    # ПРАВИЛО #2: "🟡 Нет доступа" ИЛИ "Недоступен" - скрываем на 18 часов
                    # 🔧 ИСПРАВЛЕНО: Гибкая проверка статуса (с эмодзи и без)
                    if ("Нет доступа" in status_card or "Недоступ" in status_card) and hours_since_visit < 18:
                        logging.info(f"⏳ Адрес '{addr}' скрыт (🟡 Нет доступа, прошло {hours_since_visit:.1f}ч, посл. визит: {last_visit}, статус: '{status_card}')")
                        continue
                else:
                    logging.debug(f"⚠️ Адрес '{addr}': не удалось распарсить дату '{last_visit}'")
            
            # 🛡️ ИСПРАВЛЕНО: Проверяем доступность только если НЕ прошли проверку 18 часов
            # Если адрес прошёл проверку выше (прошло >18 часов) — не фильтруем его снова!
            # Функция is_address_available() используется только для старых адресов без даты посещения
            if not last_visit:
                is_available_now, status_reset = is_address_available(last_visit, status_card)
                if not is_available_now:
                    continue
                if status_reset:
                    try:
                        cell = sprav.find(addr, in_column=1)
                        update_reklama_status_if_needed(cell.row, last_visit)
                    except Exception:
                        logging.warning(f"⚠️ Адрес '{addr}' не найден при попытке сброса статуса.")
            
            status_icon = "🟢" if status_card == "🔴 Не был" else ("🟡" if "Нет доступа" in status_card else "🟢")
            candidates.append((dist, addr, lat, lng, status_icon))

        # Если найдено меньше limit адресов - пробуем создать новые
        if len(candidates) < limit and str(settings.get("ENABLE_SMART_EXPANSION", "1")) == "1":
            logging.info(f"🔍 Найдено {len(candidates)} адресов в радиусе {LOCATION_RADIUS_METERS}м, пробуем добавить новые...")
            logging.info(f"🔧 Параметры: ENABLE_SMART_EXPANSION={settings.get('ENABLE_SMART_EXPANSION')}, sprav={'OK' if sprav else 'None'}")
            
            # 🔥 ЛИМИТ: Максимум 5 попыток геокодирования за 1 сканирование (ускорение UX)
            max_geocoding_attempts = 5
            geocoding_count = 0
            
            angles = [0, 90, 180, 270]  # ⚡ УСКОРЕНИЕ: 4 направления вместо 8
            max_r = LOCATION_RADIUS_METERS
            distances = [min(max_r, d) for d in [200, 400, 600]]  # ⚡ УСКОРЕНИЕ: 3 радиуса вместо 5
            for dist_m in distances:
                if len(candidates) >= limit or geocoding_count >= max_geocoding_attempts:
                    break
                for angle in angles:
                    if len(candidates) >= limit or geocoding_count >= max_geocoding_attempts:
                        break
                    # Вычисляем координаты точки
                    from math import radians as rad, sin, cos, degrees
                    R = 6371000
                    lat_rad = rad(current_lat)
                    lng_rad = rad(current_lng)
                    bearing = rad(angle)
                    new_lat_rad = lat_rad + (dist_m / R) * cos(bearing)
                    new_lng_rad = lng_rad + (dist_m / R) * sin(bearing) / cos(lat_rad)
                    new_lat = degrees(new_lat_rad)
                    new_lng = degrees(new_lng_rad)

                    new_addr = reverse_geocode(new_lat, new_lng)
                    geocoding_count += 1  # 🔥 Увеличиваем счётчик
                    
                    if not new_addr:
                        continue
                    norm_new_addr = normalize_text(new_addr)
                    if norm_new_addr in existing_addresses:
                        continue
                    # Блок-лист
                    if any(bl in norm_new_addr for bl in blocklist):
                        logging.debug(f"⏭️ Блок-лист: {new_addr}")
                        continue
                    # Эвристики качества
                    house_number = None
                    suffix = None
                    m = re.search(r"(\d+)([абв]|к\d+)?$", new_addr.strip(), re.IGNORECASE)
                    if m:
                        try:
                            house_number = int(m.group(1))
                        except ValueError:
                            house_number = None
                        suffix = m.group(2).lower() if m.group(2) else None
                    
                    # 🚫 Требуем номер дома. Если его нет — пропускаем адрес
                    if not house_number:
                        logging.debug(f"❌ Исключён адрес без номера дома: '{new_addr}'")
                        continue
                    
                    # 🗺️ Определяем район: сначала OSM reverse, затем по координатам
                    district = get_district_from_osm_reverse(new_lat, new_lng) or get_district_by_coords(new_lat, new_lng)
                    score = 0
                    if suffix and suffix.lower() in preferred_suffixes:
                        score += 2
                    if house_number and district == "Центральный" and house_number >= min_high_house:
                        score += 1
                    floors_count = None
                    if verify_residential:
                        extratags = get_osm_extratags(new_lat, new_lng)
                        building_type = str(extratags.get("building", ""))
                        if building_type and building_type not in ["residential", "apartments", "house"]:
                            logging.debug(f"⏭️ Не жилое здание ({building_type}): {new_addr}")
                            continue
                        # Этажность
                        levels = extratags.get("building:levels") or extratags.get("levels")
                        try:
                            floors_count = int(levels) if levels else None
                        except Exception:
                            floors_count = None
                    # Решение
                    if score < 0:
                        continue
                    status_icon = "🟢" if score >= 1 else "🟡"
                    status_card_new = "🔴 Не был" if score >= 1 else "🟡 Ожидает"
                    # Добавляем в Справочник (структура по факту: A-B-C-D-E-F-G-H-I-J)
                    try:
                        # 🔥 БЕЗОПАСНО: Определяем следующую строку и добавляем ТОЛЬКО в A:I
                        all_rows = sprav.get_all_values()
                        next_row = len(all_rows) + 1
                        
                        # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно
                        ensure_sheet_has_enough_rows(sprav, next_row)
                        
                        new_row = [
                            new_addr,  # A: АДРЕС
                            district,  # B: РАЙОН
                            "",  # C: ПРОМОУТЕР (пусто)
                            str(DEFAULT_FREQUENCY_DAYS),  # D: ЧАСТОТА
                            "",  # E: ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ (пусто)
                            status_card_new,  # F: СТАТУС
                            status_card_new,  # G: СТАТУС КАРТЫ
                            str(new_lat),   # H: ШИРОТА
                            str(new_lng),   # I: ДОЛГОТА
                        ]
                        if floors_count is not None:
                            new_row.append(str(floors_count))  # J: ЭТАЖНОСТЬ
                        
                        # ✅ БЕЗОПАСНЫЙ МЕТОД: Явно указываем диапазон A:I (или A:J если есть этажность)
                        if floors_count is not None:
                            range_name = f"A{next_row}:J{next_row}"
                        else:
                            range_name = f"A{next_row}:I{next_row}"
                        
                        sprav.update(values=[new_row], range_name=range_name)
                        existing_addresses.add(norm_new_addr)
                        dist_to_new = haversine_distance(current_lat, current_lng, new_lat, new_lng)
                        candidates.append((dist_to_new, new_addr, new_lat, new_lng, status_icon))
                        logging.info(f"✅ Добавлен новый адрес в Справочник (строка {next_row}): {new_addr} ({district}, {score} pts)")
                    except Exception as e:
                        logging.error(f"Ошибка добавления адреса '{new_addr}' в Справочник: {e}")
            
            # 🔥 Логируем статистику
            if geocoding_count > 0:
                logging.info(f"📊 Геокодирований выполнено: {geocoding_count}/{max_geocoding_attempts}")

        # 🎯 НОВОЕ: Сортируем по приоритету (сначала самые важные, потом по расстоянию)
        # ⚡ УСКОРЕНИЕ UX: Загрузка приоритетов только если кэш уже загружен!
        # Не загружаем приоритеты заново на каждом сканировании (30с задержка!)
        if PRIORITY_CACHE["loaded_at"] and PRIORITY_CACHE["data"]:
            # Кэш уже есть - используем его
            priorities = PRIORITY_CACHE["data"]
            candidates.sort(key=lambda x: (-priorities.get(x[1], 50), x[0]))
            logging.info(f"🎯 Адреса отсортированы по приоритету (кэш)")
        else:
            # Кэша нет - сортируем только по расстоянию (быстро!)
            candidates.sort(key=lambda x: x[0])
            logging.info(f"⚡ Адреса отсортированы по расстоянию (приоритеты не загружены)")
        
        # ✨ НОВОЕ: Фильтр адресов БЕЗ номера дома (Donald Norman UX)
        # Примеры неверных адресов: "Полевая улица", "Артиллерийская улица"
        # Правильные адреса: "Еловая 48", "Ленина 12а"
        filtered_candidates = []
        for dist, addr, lat, lng, icon in candidates[:limit]:
            # Проверяем, есть ли в адресе цифры (номер дома)
            if re.search(r'\d', addr):  # Есть хотя бы одна цифра
                filtered_candidates.append((addr, lat, lng, dist, icon))
            else:
                logging.debug(f"❌ Исключён адрес без номера дома: '{addr}'")
        
        logging.info(f"✨ После фильтрации: {len(filtered_candidates)} адресов (было {len(candidates[:limit])})")
        return filtered_candidates
    except Exception as e:
        logging.error(f"Ошибка get_or_create_nearby_addresses: {e}")
        return []


# Алиас для обратной совместимости
def get_nearest_available_addresses(
    current_lat: float, current_lng: float, exclude_address: str = ""
) -> List[Tuple[str, float, float]]:
    """
    Обратная совместимость: возвращает только (addr, lat, lng) без distance и icon.
    Внутри использует новую функцию get_or_create_nearby_addresses.
    """
    results = get_or_create_nearby_addresses(current_lat, current_lng, exclude_address)
    return [(addr, lat, lng) for addr, lat, lng, _, _ in results]


# ============================
# 🔐 АУТЕНТИФИКАЦИЯ
# ============================
def get_keyboard_login() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой 'Войти через телефон'"""
    keyboard = [
        [KeyboardButton("📱 Войти через телефон", request_contact=True)]
    ]
    # 🔧 ИСПРАВЛЕНО: one_time_keyboard=False чтобы кнопка была видна при повторном входе в чат
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_main_menu_keyboard(user_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    """Главное меню после авторизации"""
    keyboard = [
        ["🗺️ Создать маршрут", "📦 Запросить листовки"],  # 🔧 ИСПРАВЛЕНО: "Дневной отчёт"→"Создать маршрут"
        ["Начать работу 🚀"]
    ]
    # Админ-кнопка для проверки отчётов
    if user_id and user_id in ADMIN_IDS:
        keyboard.insert(0, ["📋 Проверка отчётов"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def is_user_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь в Google Sheets 'Балансы'"""
    try:
        if not balances_sheet:
            return False
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:  # Только заголовки
            return False
        for row in all_values[1:]:
            if len(row) > 0 and str(row[0]) == str(user_id):
                return True
        return False
    except Exception as e:
        logging.error(f"❌ Ошибка проверки регистрации: {e}")
        return False


def register_user(user_id: int, phone: str, name: str) -> bool:
    """Регистрирует нового пользователя в Google Sheets 'Балансы' с полной информацией"""
    try:
        if not balances_sheet:
            logging.error("❌ balances_sheet не инициализирован")
            return False

        # Проверяем, не зарегистрирован ли уже
        if is_user_registered(user_id):
            logging.warning(f"⚠️ Пользователь {user_id} уже зарегистрирован")
            return True

        from datetime import datetime
        reg_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Добавляем новую строку в 'Балансы' с 6 колонками: ID | Баланс ₽ | Листовки | Телефон | Имя | Дата
        new_row = [
            str(user_id),  # ПромоутерID (A)
            "0",           # Баланс (₽) (B)
            "0",           # Листовки (шт) (C)
            phone,         # Телефон (D)
            name,          # Имя (E)
            reg_date       # Дата регистрации (F)
        ]
        
        # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно
        all_rows = balances_sheet.get_all_values()
        next_row = len(all_rows) + 1
        ensure_sheet_has_enough_rows(balances_sheet, next_row)
        
        balances_sheet.update(values=[new_row], range_name=f"A{next_row}:F{next_row}")
        logging.info(f"✅ Пользователь зарегистрирован: ID={user_id}, Телефон={phone}, Имя={name}, Дата={reg_date}")
        return True

    except Exception as e:
        logging.error(f"❌ Ошибка регистрации пользователя: {e}")
        return False


def get_user_name_from_balances(user_id: int) -> Optional[str]:
    """Получает имя пользователя из первой транзакции 'Регистрация' в листе 'Балансы'"""
    try:
        if not balances_sheet:
            return None
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:
            return None
        
        # Ищем первую транзакцию типа "Регистрация" для этого пользователя
        # Структура: [ПромоутерID, Дата, Тип, ...]
        for row in all_values[1:]:
            if len(row) >= 3 and str(row[0]) == str(user_id) and row[2] == "Регистрация":
                # Имя не хранится в транзакциях - возвращаем None
                # Имя будет получено из Telegram profile
                return None
        return None
    except Exception as e:
        logging.error(f"❌ Ошибка получения имени: {e}")
        return None


# ============================
# 📨 HANDLERS
# ============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start с проверкой регистрации и восстановлением состояния"""
    try:
        chat_id = update.effective_chat.id
        user = update.effective_user
        user_id = user.id
        # 🔒 ДЕДУПЛИКАЦИЯ /start: игнорируем повтор в течение 5 секунд
        with notification_lock:
            now = datetime.utcnow()
            key = f"cmd_start_{user_id}"
            last = last_command_handled.get(key)
            if last and (now - last).total_seconds() < 5:
                logging.warning(f"⚠️ Повторная /start от {user_id} в течение 5с — игнорируем")
                return
            last_command_handled[key] = now
        
        # 🔄 УМНАЯ ЛОГИКА: Проверяем, есть ли незавершённая работа
        current_state = user_state.get(user_id, {}).get("state")
        selected_address = user_state.get(user_id, {}).get("selected_address")
        
        # Если пользователь в процессе работы - восстанавливаем контекст
        if current_state and current_state in ["awaiting_access_answer", "awaiting_photos", "awaiting_door_photo", "awaiting_exit_door_photo"]:
            logging.info(f"🔄 Восстановление состояния для пользователя {user_id}: {current_state}")
            
            if current_state == "awaiting_access_answer":
                # Показываем кнопки доступа
                keyboard = [
                    ["✅ Да!"],
                    ["🚪 Нет доступа"],
                    ["Вернуться в меню"]
                ]
                await update.message.reply_text(
                    f"🔄 Продолжаем работу!\n\n"
                    f"📍 Адрес: {selected_address or 'выбран'}\n\n"
                    f"🚪 Есть доступ в подъезд?",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                )
                return
            
            elif current_state == "awaiting_photos":
                # Показываем кнопки загрузки фото
                await update.message.reply_text(
                    f"🔄 Продолжаем работу!\n\n"
                    f"📍 Адрес: {selected_address or 'выбран'}\n\n"
                    f"📸 Отправляй фото электрощитов с листовками.\n\n"
                    f"💾 Когда закончишь - нажми 'Сохранить'",
                    reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"], ["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
                )
                return
            
            elif current_state in ["awaiting_door_photo", "awaiting_exit_door_photo"]:
                # Ожидаем фото двери
                await update.message.reply_text(
                    f"🔄 Продолжаем работу!\n\n"
                    f"📍 Адрес: {selected_address or 'выбран'}\n\n"
                    f"📸 Отправь фото входной двери с визиткой Балтсеть³⁹",
                    reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
                )
                return
        
        # 🛡️ СБРОС СОСТОЯНИЯ: пользователь явно хочет вернуться в меню
        if user_id in user_state:
            user_state[user_id]["state"] = None
            logging.info(f"🔄 Состояние пользователя {user_id} сброшено (/start)")

        # Проверяем, зарегистрирован ли пользователь
        if is_user_registered(user_id):
            # Пользователь уже зарегистрирован
            user_name = get_user_name_from_balances(user_id) or user.first_name or "Промоутер"
            # Получаем текущий streak для мотивационного сообщения
            streak_days = get_work_streak(user_id)
            if streak_days >= 5:
                bonus_text = "🔥 +50% за 5 дней подряд!"
            elif streak_days >= 3:
                bonus_text = "🔥 +20% за 3 дня подряд!"
            else:
                bonus_text = "— начни активность для бонуса!"
            
            welcome_text = (
                f"✅ Используй кнопки меню для работы.\n"
                f"Если нужны листовки - нажми '📦 Запросить листовки'.\n\n"
                f"🔥 Активность: {streak_days} дней подряд"
            )
            # Отправляем картинку с приветствием
            try:
                await update.message.reply_photo(
                    photo="https://disk.yandex.ru/i/XtsI3bZE0H9yHQ",
                    caption=welcome_text,
                    reply_markup=get_main_menu_keyboard()
                )
                await update.message.reply_text(
                    "ℹ️ Активность - получай бонусы до +50% вознаграждения за ежедневную работу!",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить фото: {e}")
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=get_main_menu_keyboard()
                )
            logging.info(f"✅ /start от зарегистрированного пользователя {user_id}")
        else:
            # Новый пользователь — показываем кнопку регистрации
            user_name = user.first_name or user.username or "Промоутер"
            welcome_text = (
                f"👋 Я - Ян, помощник промоутера в Калининграде.\n\n"
                f"🔐 Для начала работы нажми кнопку ниже и поделись своим номером телефона."
            )
            try:
                await update.message.reply_photo(
                    photo="https://disk.yandex.ru/i/z4V1cofhtrQHig",
                    caption=welcome_text,
                    reply_markup=get_keyboard_login()
                )
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить фото при регистрации: {e}")
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=get_keyboard_login()
                )
            logging.info(f"✅ /start от нового пользователя {user_id}")

    except Exception as e:
        logging.error(f"❌ Ошибка в start(): {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже."
        )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик получения контакта (регистрация через телефон)"""
    try:
        chat_id = update.effective_chat.id
        user = update.effective_user
        contact = update.message.contact

        if not contact:
            await update.message.reply_text("❌ Не удалось получить контакт.")
            return

        # Проверяем, что пользователь отправил свой контакт
        if contact.user_id != user.id:
            await update.message.reply_text(
                "❌ Пожалуйста, отправь свой номер телефона, а не чужой.",
                reply_markup=get_keyboard_login()
            )
            return

        phone = contact.phone_number
        name = contact.first_name or user.first_name or user.username or "Промоутер"
        user_id = user.id

        # Регистрируем пользователя
        success = register_user(user_id, phone, name)

        if success:
            welcome_text = (
                f"✅ Отлично, {name}!\n\n"
                f"📱 Телефон: {phone}\n"
                f"🆔 ID: <code>{user_id}</code>\n\n"
                f"🎯 Ты успешно зарегистрирован!\n"
                f"Теперь ты можешь начать работу.\n\n"
                f"💡 Совет: регулярная работа = больше денег!\n"
                f"🔥 3 дня подряд = +20% к листовкам\n"
                f"🔥 5 дней подряд = +50% к листовкам"
            )
            await update.message.reply_text(
                welcome_text,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard()
            )
            logging.info(f"✅ Новый пользователь зарегистрирован: ID={user_id}, Phone={phone}, Name={name}")
        else:
            await update.message.reply_text(
                "❌ Произошла ошибка при регистрации. Попробуйте позже.",
                reply_markup=get_keyboard_login()
            )

    except Exception as e:
        logging.error(f"❌ Ошибка в handle_contact(): {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "📚 <b>Доступные команды:</b>\n\n"
        "/start — Начало работы\n"
        "/help — Справка\n"
        "/profile — Мой профиль\n\n"
        "📊 <b>Возможности:</b>\n"
        "• Умное расширение адресов\n"
        "• Автоматическое геокодирование\n"
        "• Фильтрация низкокачественных адресов\n"
        "• Настройки через Google Sheets\n\n"
        "💰 <b>Оплата и мотивация:</b>\n"
        "• 🚪 Дверь: 1₽ днём, 0.5₽ ночью (21:00–07:00)\n"
        "• ⚡ Электрощит: 3₽ за фото с визиткой\n"
        "• 🔥 Активность: +10% за день работы, до +50% (обнуляется при пропуске дня)\n"
        "• 🏆 Призовой фонд: 🥉 +500₽ (70 фото), 🥈 +700₽ (100 фото), 🥇 +1000₽ (150 фото)\n"
        "• 💎 Бонусы начисляются автоматически в полночь"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /profile - полноценный профиль с балансом и статистикой!"""
    user = update.effective_user
    user_id = user.id
    
    # 💰 Получаем баланс из Google Sheets (сумма всех транзакций)
    balance = 0.0
    try:
        if balances_sheet:
            all_values = balances_sheet.get_all_values()
            if len(all_values) > 1:
                # Суммируем все транзакции для этого пользователя
                # Структура: [ПромоутерID, Дата, Тип, Листовки, Фото двери, Фото щитов, Оплата дверь, Оплата щиты, Премия, Итого]
                # Колонка "Итого" - это индекс 9
                for row in all_values[1:]:
                    if len(row) >= 10 and str(row[0]) == str(user_id):
                        try:
                            balance += float(row[9])  # Колонка "Итого (₽)"
                        except (ValueError, IndexError):
                            continue
    except Exception as e:
        logging.error(f"❌ Ошибка получения баланса в профиле: {e}")
    
    # 📦 Листовки
    flyer_balance = get_flyer_balance(user_id)
    
    # 📸 Фото за сегодня
    today_photos = get_today_photo_count(user_id)
    
    # 💵 Текущая цена фото
    current_price = get_photo_price()
    current_hour = datetime.now().hour
    time_status = "☀️ День" if 7 <= current_hour < 21 else "🌙 Вечер"
    
    # 📊 Заработано за сегодня
    today_earnings = today_photos * current_price
    
    # 🎯 Прогресс до бонуса
    bonus_progress = get_bonus_progress(user_id)
    
    # 👤 Имя
    user_name = get_user_name_from_balances(user_id) or user.first_name or "Промоутер"
    
    # 🔥 Мотивация: streak и сессионная цель
    streak_days = get_work_streak(user_id)
    activity_multiplier = min(1.0 + 0.10 * streak_days, 1.5)
    bonus_text = f"🔥 Активность: +{int((activity_multiplier - 1.0)*100)}% (ежедневно +10%, максимум +50%; пропуск дня — обнуление)"
    # Base rates: door = 1₽, inside panel = 3₽; evening (21:00–07:00) halves base
    base_panel_rate = 3.0
    base_door_rate = 1.0
    current_hour = datetime.now().hour
    is_evening = (current_hour >= 21 or current_hour < 7)
    if is_evening:
        base_door_rate = base_door_rate / 2.0
    address_multiplier = user_state.get(user_id, {}).get("address_bonus_multiplier", 1.0)
    effective_panel_rate = base_panel_rate * address_multiplier
    effective_door_rate = base_door_rate * address_multiplier
    
    session_target = user_state.get(user_id, {}).get("session_target_photos", MIN_PHOTOS_REQUIRED)
    photos_uploaded = user_state.get(user_id, {}).get("photos_uploaded", 0)
    filled = min(int((photos_uploaded / session_target) * 10), 10) if session_target else 0
    progress_bar = "█" * filled + "░" * (10 - filled)
    percentage = min(int((photos_uploaded / session_target) * 100), 100) if session_target else 0
    
    bronze_tier = BONUS_TIERS[0] if BONUS_TIERS else {'threshold': DAILY_GOAL, 'bonus': BONUS_AMOUNT, 'name': '🥉 Бронзовый'}
    bronze_threshold = bronze_tier['threshold']
    bronze_bonus = bronze_tier['bonus']
    bronze_filled = min(int((today_photos / bronze_threshold) * 10), 10) if bronze_threshold else 0
    bronze_bar = '█' * bronze_filled + '░' * (10 - bronze_filled)
    bronze_percent = min(int((today_photos / bronze_threshold) * 100), 100) if bronze_threshold else 0
    # Динамическая строка бонуса в профиле
    achieved_tier = None
    for _tier in reversed(BONUS_TIERS):
        if today_photos >= _tier['threshold']:
            achieved_tier = _tier
            break
    if achieved_tier:
        dynamic_bonus_amount = int(achieved_tier['bonus'] * activity_multiplier)
        bonus_line = f"🔥 БОНУС: +{dynamic_bonus_amount}₽ будет начислен сегодня (условие выполнено)"
    else:
        _next = None
        for _tier in BONUS_TIERS:
            if today_photos < _tier['threshold']:
                _next = _tier
                break
        if _next is None:
            dynamic_bonus_amount = int(BONUS_TIERS[-1]['bonus'] * activity_multiplier)
            bonus_line = f"🔥 БОНУС: +{dynamic_bonus_amount}₽ (максимальный уровень достигнут)"
        else:
            remaining = max(_next['threshold'] - today_photos, 0)
            dynamic_bonus_amount = int(_next['bonus'] * activity_multiplier)
            bonus_line = f"🔥 БОНУС: +{dynamic_bonus_amount}₽ при достижении {_next['threshold']} фото сегодня (осталось: {remaining})"

    profile_text = (
        f"👤 {user_name}\n"
        f"└─ 📦 {flyer_balance} листовок\n"
        f"└─ ⏰ Время: {time_status}\n\n"
        f"{bronze_tier['name'].split()[0]} СЕГОДНЯ: {today_earnings:.2f}₽\n"
        f"└─ 🚪 Ставка у домофона: {'100%' if time_status == '☀️ День' else '-50%'}\n"
        f"└─ ⚡ Ставка электрощита: {effective_panel_rate:.1f}₽ +{int((activity_multiplier - 1.0)*100)}%\n\n"
        f"🎯 БОНУС: +{dynamic_bonus_amount}₽, только сегодня:\n"
        f"🔥{bronze_bar}, осталось: {max(bronze_threshold - today_photos, 0)}\n"
        f"└─  Сделано: {today_photos} / {bronze_threshold} | {bronze_percent}%\n\n"
        f"💰 БАЛАНС: {balance:.2f}₽"
    )
    await update.message.reply_text(profile_text, parse_mode="Markdown")


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик получения геолокации.
    1. Сканирует местность в радиусе 800м
    2. Автоматически добавляет новые адреса в Справочник
    3. Показывает ближайшие адреса для работы
    """
    try:
        chat_id = update.effective_chat.id
        user = update.effective_user
        location = update.message.location

        if not location:
            await update.message.reply_text("❌ Не удалось получить геолокацию.")
            return

        lat = location.latitude
        lng = location.longitude
        user_id = user.id

        # Сохраняем текущую геолокацию пользователя
        if user_id not in user_state:
            user_state[user_id] = {}
        user_state[user_id]["current_location"] = (lat, lng)
        user_state[user_id]["current_location_time"] = datetime.utcnow()

        # Проверка регистрации
        if not is_user_registered(user_id):
            await update.message.reply_text(
                "❌ Сначала зарегистрируйся! Нажми /start",
                reply_markup=get_keyboard_login()
            )
            return
        
        # 📍 Обработка корректировки координат
        if user_state.get(user_id, {}).get("state") == "awaiting_coordinates_fix":
            selected_address = user_state[user_id].get("selected_address")
            if not selected_address:
                await update.message.reply_text(
                    "❌ Ошибка: адрес не найден.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Обновляем координаты в Справочнике
            try:
                rows = sprav.get_all_values()
                updated = False
                for i, row in enumerate(rows):
                    if len(row) > 0 and normalize_text(row[0]) == normalize_text(selected_address):
                        # Обновляем координаты (столбцы B и C - lat и lng)
                        sprav.update_cell(i + 1, 8, lat)  # Lat (колонка H)
                        sprav.update_cell(i + 1, 9, lng)  # Lng (колонка I)
                        updated = True
                        logging.info(f"✅ Координаты обновлены для {selected_address}: ({lat}, {lng})")
                        break
                
                if updated:
                    # ✅ Координаты обновлены!
                    # 🔔 Отправляем заявку администратору на подтверждение координат и закрепляем сообщения
                    try:
                        coords_pending_requests[user_id] = {
                            "address": selected_address,
                            "lat": lat,
                            "lng": lng,
                            "requested_at": datetime.now().strftime("%d.%m.%Y %H:%M")
                        }
                        admin_kb = InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ Подтвердить координаты", callback_data=f"coord_approve_{user_id}")],
                            [InlineKeyboardButton("❌ Отклонить", callback_data=f"coord_reject_{user_id}")],
                            [InlineKeyboardButton("💬 Связаться", url=f"tg://user?id={user_id}")]
                        ])
                        admin_text = (
                            f"🆕 <b>НОВАЯ ЗАЯВКА НА ИСПРАВЛЕНИЕ КООРДИНАТ</b>\n\n"
                            f"👤 Промоутер ID: <code>{user_id}</code>\n"
                            f"📄 Адрес: <b>{selected_address}</b>\n"
                            f"🌍 Новые координаты: {lat:.6f}, {lng:.6f}\n"
                            f"⏰ Дата: {coords_pending_requests[user_id]['requested_at']}\n\n"
                            f"⚡ Подтвердить или отклонить:" )
                        for admin_id in ADMIN_IDS:
                            try:
                                amsg = await context.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML", reply_markup=admin_kb)
                                pinned_admin_coord_messages[(admin_id, user_id)] = amsg.message_id
                                await context.bot.pin_chat_message(chat_id=admin_id, message_id=amsg.message_id, disable_notification=False)
                            except Exception as e:
                                logging.warning(f"⚠️ Ошибка уведомления админа {admin_id}: {e}")
                        # Сообщение промоутеру и закрепление
                        pm_msg = await context.bot.send_message(
                            chat_id=user_id,
                            text=(
                                "✅ Координаты обновлены в справочнике!\n\n"
                                "⏳ Статус: ожидает подтверждения админа\n"
                                "🔔 Уведомлю, как только админ примет решение."),
                            parse_mode="HTML"
                        )
                        pinned_promoter_coord_messages[user_id] = pm_msg.message_id
                        await context.bot.pin_chat_message(chat_id=user_id, message_id=pm_msg.message_id, disable_notification=False)
                    except Exception as e:
                        logging.warning(f"⚠️ Ошибка отправки заявок на подтверждение координат: {e}")
                            
                    # Возвращаемся к вопросу о доступе
                    user_state[user_id]["state"] = "awaiting_access_answer"
                    addr_info = get_address_info(selected_address)
                    user_state[user_id]["address_info"] = addr_info
                    
                    keyboard = [
                        ["✅ Да!"],
                        ["🚪 Нет доступа"],
                        ["📍 Исправить координаты"],
                        ["Вернуться в меню"]
                    ]
                    
                    await update.message.reply_text(
                        f"✅ Координаты обновлены!\n\n"
                        f"📍 Адрес: <b>{selected_address}</b>\n"
                        f"🌍 Новые координаты: {lat:.6f}, {lng:.6f}\n\n"
                        f"🎯 Отлично! Есть доступ в подъезд?",
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
                    return
                else:
                    await update.message.reply_text(
                        f"❌ Адрес {selected_address} не найден в справочнике.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    user_state[user_id]["state"] = None
                    return
            except Exception as e:
                logging.error(f"❌ Ошибка обновления координат: {e}")
                await update.message.reply_text(
                    "❌ Ошибка обновления координат. Попробуй позже.",
                    reply_markup=get_main_menu_keyboard()
                )
                user_state[user_id]["state"] = None
                return
        
        # ✅ ВАЖНО: если адрес уже выбран → проверяем, подтверждено ли местоположение
        selected_address = user_state[user_id].get("selected_address")
        if selected_address:
            # Проверяем, подтверждено ли уже местоположение
            if user_state[user_id].get("state") == "awaiting_access_answer":
                # 🔧 ИСПРАВЛЕНО: Местоположение уже подтверждено, показываем кнопки доступа
                keyboard = [
                    ["✅ Да!"],
                    ["🚪 Нет доступа"],
                    ["Вернуться в меню"]
                ]
                await update.message.reply_text(
                    "✅ Местоположение уже подтверждено. Продолжайте работу.",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                )
                return
            
            # Получаем информацию об адресе
            addr_info = get_address_info(selected_address)
            if not addr_info:
                # 🔧 ИСПРАВЛЕНО: Не прерываем сканирование, если адрес не найден
                logging.warning(f"⚠️ Выбранный адрес '{selected_address}' не найден. Продолжаю сканирование ближайших адресов.")
                user_state[user_id]["selected_address"] = None
            else:
                # ИСПРАВЛЕНО: get_address_info возвращает 7 значений (addr, lat, lng, district, status_card, last_promoter, last_visit)
                # ЗАЩИТА: Проверяем длину перед распаковкой
                if len(addr_info) != 7:
                    logging.error(f"❌ addr_info имеет неправильную длину: {len(addr_info)}, ожидается 7")
                    await update.message.reply_text(
                        "❌ Ошибка данных адреса.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return
                addr, dest_lat, dest_lng, district, status_card, last_promoter, last_visit = addr_info
                
                # Проверяем расстояние до адреса (используем OSMnx пешеходный маршрут)
                distance = get_walking_distance(lat, lng, dest_lat, dest_lng)
                
                # Генерируем маршрут
                route_url = generate_yandex_maps_route_url(lat, lng, dest_lat, dest_lng)
                
                # Спрашиваем про доступ в подъезд
                keyboard = [
                    ["🎯 ✅ Я на месте!"],
                    ["Вернуться в меню"]
                ]
                
                # Мягкое предупреждение, но НЕ блокируем работу
                if distance and distance > LOCATION_RADIUS_METERS:
                    await update.message.reply_text(
                        f"📍 **{addr}**\n\n"
                        f"⚠️ Ты довольно далеко от адреса!\n"
                        f"📍 Расстояние: {int(distance)} м\n"
                        f"🎯 Рекомендуем подойти ближе.\n\n"
                        f"💡 Если координаты адреса неправильные — остановись у входа и нажми «📍 Исправить координаты».\n\n"
                        f"🗺️ [Маршрут на Яндекс.Картах]({route_url})\n\n"
                        f"🪧 Статус: {status_card}",
                        parse_mode="Markdown",
                        reply_markup=ReplyKeyboardMarkup([["🎯 ✅ Я на месте!"], ["📍 Исправить координаты"], ["Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
                    )
                else:
                    keyboard = [
                        ["🎯 ✅ Я на месте!"],
                        ["Вернуться в меню"]
                    ]
                    await update.message.reply_text(
                        f"📍 <b>{addr}</b>\n"
                        f"🔑 Расстояние до входа: {int(distance)} м\n\n"
                        f"🪧 Статус: {addr_info[4] if len(addr_info) > 4 else '🔴 Не был'}\n"
                        f"🗺️ <a href='{route_url}'>Маршрут на Яндекс.Картах</a>",
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    )
                
                # Сохраняем состояние
                user_state[user_id]["state"] = "awaiting_access_answer"
                user_state[user_id]["address_info"] = addr_info
                return

        # 📍 Атмосферное сообщение о сканировании с указанием времени ожидания
        scan_msg = await update.message.reply_text(
            "📡 **Сканирование района...**\n\n"
            "🔍 Анализирую адреса в радиусе 800м...\n\n"
            "⏰ Подожди ~30 сек, загружаю данные!",
            parse_mode="Markdown"
        )

        # Умный поиск и создание адресов
        logging.info(f"🔍 Начало сканирования для пользователя {user_id} в координатах ({lat}, {lng})")
        nearby_addresses = get_or_create_nearby_addresses(lat, lng, exclude_address="", limit=MAX_NEARBY_ADDRESSES)
        
        # 🗑️ Удаляем сообщение о загрузке
        try:
            await scan_msg.delete()
        except Exception as e:
            logging.debug(f"⚠️ Не удалось удалить сообщение о сканировании: {e}")

        if not nearby_addresses:
            keyboard = [
                ["📍 Добавить адрес"],
                ["Вернуться в меню"]
            ]
            await update.message.reply_text(
                "❌ Нет доступных адресов рядом.\n\n"
                "💬 Введи любой адрес в чат, например: <a href='https://2gis.ru/kaliningrad'>Куйбышева 84</a>. Я добавлю его и начнём.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            )
            return

        # ✅ Сообщение о завершении сканирования
        result_text = (
            "✅ **Сканирование завершено!**\n"
            f"📍 Найдено адресов: **{len(nearby_addresses)} шт**\n"
            f"📏 Радиус поиска: **800м**\n\n"
        )

        # Формируем список адресов с эмодзи статусов
        address_list = []
        for i, (addr, addr_lat, addr_lng, distance, status_icon) in enumerate(nearby_addresses, 1):
            address_list.append(f"{status_icon} {addr} ({int(distance) + 50} м)")

        result_text += "\n".join(address_list)

        # Кнопки для выбора адреса
        keyboard = []
        
        # 🔥 UX: Добавляем кнопку ближайшего адреса без эмодзи для простоты парсинга
        if nearby_addresses:
            closest_addr = nearby_addresses[0][0]  # Первый адрес - самый близкий
            keyboard.append([f"{closest_addr}"])  # 🔥 Без эмодзи!
        
        # Остальные адреса тоже без эмодзи
        for addr, _, _, distance, status_icon in nearby_addresses[1:]:
            keyboard.append([f"{addr}"])  # 🔥 Без эмодзи и расстояния!
        
        keyboard.append(["Вернуться в меню"])

        # 🔧 ИСПРАВЛЕНО: Одно сообщение с кнопками
        await update.message.reply_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        )

        logging.info(f"✅ Сканирование завершено для пользователя {user_id}: найдено {len(nearby_addresses)} адресов")

    except Exception as e:
        logging.error(f"❌ Ошибка в handle_location(): {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке геолокации. Попробуйте позже."
        )


def record_finance_entry(user_id: int, address: str, district: str, entry_type: str, category: str, quantity: float, unit_price: float, amount: float, comment: str = "") -> bool:
    """
    📒 Записывает строку в лист 'Финансы'
    entry_type: 'Доход' | 'Расход'
    category: например: 'Фото двери', 'Фото щитов', 'Премия', 'Производство листовок', 'Распространение листовок'
    """
    try:
        if not finance_sheet:
            logging.error("❌ finance_sheet не инициализирован")
            return False
        current_date = datetime.now().strftime("%d.%m.%Y")
        promoter = str(user_id)
        
        # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно
        all_rows = finance_sheet.get_all_values()
        next_row = len(all_rows) + 1
        ensure_sheet_has_enough_rows(finance_sheet, next_row)
        
        new_row = [
            current_date, promoter, address, district, entry_type, category,
            str(quantity), f"{unit_price:.2f}", f"{amount:.2f}", comment
        ]
        finance_sheet.update(values=[new_row], range_name=f"A{next_row}:J{next_row}")
        logging.info(f"✅ Финансы: {entry_type} {category} {amount:.2f}₽ ({address})")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка записи в 'Финансы': {e}")
        return False


def get_flyer_balance(user_id: int) -> int:
    """Получает баланс листовок промоутера из листа 'Балансы' (колонка C)"""
    try:
        if not balances_sheet:
            logging.warning("⚠️ balances_sheet не инициализирован, используем фолбэк на flyers_sheet")
            # Фолбэк: проверяем старый лист "Листовки"
            if not flyers_sheet:
                return 0
            all_values = flyers_sheet.get_all_values()
            if len(all_values) <= 1:
                return 0
            for row in all_values[1:]:
                if len(row) > 0 and str(row[0]) == str(user_id):
                    try:
                        return int(row[1]) if len(row) > 1 else 0
                    except ValueError:
                        return 0
            return 0
        
        # Основной метод: читаем баланс листовок из 'Балансы' (колонка C)
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:
            return 0
        for row in all_values[1:]:
            if len(row) > 0 and str(row[0]) == str(user_id):
                try:
                    # Колонка C (индекс 2) = Листовки (шт)
                    return int(row[2]) if len(row) > 2 and row[2] else 0
                except ValueError:
                    return 0
        return 0
    except Exception as e:
        logging.error(f"❌ Ошибка получения баланса листовок: {e}")
        return 0


def create_flyer_request(user_id: int, user_name: str, quantity: int = 1000) -> bool:
    """
    🎉 НОВОЕ: Создаёт заявку на листовки в Google Sheets
    Структура: [Промоутер, Имя, Дата заявки, Количество, Статус, Дата одобрения]
    """
    try:
        if not flyer_requests_sheet:
            logging.error("❌ flyer_requests_sheet не инициализирован")
            return False
        
        from datetime import datetime
        request_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Проверяем, нет ли уже ожидающей заявки
        all_values = flyer_requests_sheet.get_all_values()
        for row in all_values[1:]:
            if len(row) >= 5 and str(row[0]) == str(user_id) and row[4] == "⏳ Ожидает":
                logging.warning(f"⚠️ У пользователя {user_id} уже есть ожидающая заявка")
                return False
        
        # Создаём новую заявку
        new_row = [
            str(user_id),  # Промоутер
            user_name,     # Имя
            request_date,  # Дата заявки
            str(quantity), # Количество
            "⏳ Ожидает",  # Статус
            ""             # Дата одобрения (пусто)
        ]  
        
        # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно
        next_row = len(all_values) + 1
        ensure_sheet_has_enough_rows(flyer_requests_sheet, next_row)
        
        flyer_requests_sheet.update(values=[new_row], range_name=f"A{next_row}:F{next_row}")
        logging.info(f"✅ Заявка создана: {user_id} ({user_name}) - {quantity} листовок")
        
        # 🔔 НОВОЕ: Уведомляем админа о новой заявке
        try:
            # Импортируем глобальную переменную application (будет доступна после запуска бота)
            from telegram.ext import Application
            admin_message = (
                f"🆕 **НОВАЯ ЗАЯВКА НА ЛИСТОВКИ**\n\n"
                f"👤 Промоутер: {user_name} (ID: `{user_id}`)\n"
                f"📦 Количество: {quantity} листовок\n"
                f"⏰ Дата: {request_date}\n\n"
                f"⚡ Одобри заявку командой:\n"
                f"`/approve {user_id} {quantity}`"
            )
            # Примечание: уведомление будет отправлено через глобальный application
            # в handle_text_message где вызывается create_flyer_request
            global _pending_admin_notification
            _pending_admin_notification = {
                "user_id": user_id,
                "user_name": user_name,
                "quantity": quantity,
                "request_date": request_date
            }
        except Exception as e:
            logging.warning(f"⚠️ Не удалось подготовить уведомление админу: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Ошибка создания заявки: {e}")
        return False


def calculate_address_priority(row: List[str], row_index: int) -> int:
    """
    🎯 НОВОЕ: Расчёт приоритета адреса для умной сортировки
    
    Формула приоритета:
    - Базовый балл: 100
    - +50 если статус "🔴 Не был"
    - +30 если статус "🟡 Обновить" или "🔴 Пусто"
    - +20 если район "Центральный"
    - -2 за каждый день с последнего визита (макс -60)
    - +10 если листовки заканчивались (статус "🔴 Пусто")
    
    Args:
        row: строка из Справочника [Адрес, Район, Промоутер, Фото, Посещение, Статус листовок, Статус карты, ...]
        row_index: индекс строки (для логирования)
    
    Returns:
        int: приоритет от 0 до ~200
    """
    try:
        priority = 100  # Базовый балл
        
        # Извлекаем данные из строки
        address = row[0] if len(row) > 0 else ""
        district = row[1] if len(row) > 1 else ""
        last_visit = row[4] if len(row) > 4 else ""  # Столбец E (ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ)
        status_leaflets = row[5] if len(row) > 5 else ""  # Столбец F (СТАТУС ЛИСТОВОК)
        status_card = row[6] if len(row) > 6 else ""  # Столбец G (СТАТУС КАРТЫ)
        flyers_before = row[9] if len(row) > 9 else ""  # Столбец J (ЛИСТОВКИ ДО)
        
        # 🎯 ПРИОРИТЕТ #0: Приоритетные адреса (САМЫЙ ВЫСОКИЙ!)
        if address:
            priority_addrs = get_priority_addresses()
            normalized_addr = normalize_text(address)
            for p_addr in priority_addrs:
                if normalize_text(p_addr["address"]) == normalized_addr:
                    priority += 200  # МАКСИМАЛЬНЫЙ бонус!
                    logging.debug(f"🎯 Приоритетный адрес: {address} (+200)")
                    break
        
        # 🔴 ПРИОРИТЕТ #1: Адреса, где никогда не были (+50)
        if status_card == "🔴 Не был":
            priority += 50
        
        # 🟡 ПРИОРИТЕТ #2: "Нет доступа" (более 3 дней) — высокий приоритет! (+40)
        if status_card == "🟡 Нет доступа" and last_visit:
            try:
                last_visit_date = parse_date_flexible(last_visit)
                if last_visit_date:
                    days_passed = (datetime.now() - last_visit_date).days
                    if days_passed >= 3:
                        priority += 40
                        logging.debug(f"🟡 Нет доступа > 3 дней: {address} (+40)")
            except Exception as e:
                logging.debug(f"⚠️ Ошибка парсинга даты last_visit: {e}")
        
        # 🟡 ПРИОРИТЕТ #3: Адреса, требующие обновления (+30)
        if status_card in ["🟡 Обновить", "🔴 Пусто"]:
            priority += 30
        
        # 🏙 ПРИОРИТЕТ #3: Центральный район (+20)
        if "центральн" in district.lower():
            priority += 20
        
        # ⏰ ПРИОРИТЕТ #4: Давность визита (чем старше, тем приоритетнее)
        if last_visit:
            try:
                from datetime import datetime
                last_visit_date = datetime.strptime(last_visit, "%d.%m.%Y %H:%M")
                days_passed = (datetime.now() - last_visit_date).days
                # -2 балла за каждый день, но не более -60
                priority -= min(days_passed * 2, 60)
            except ValueError:
                pass  # Неверный формат даты - игнорируем
        
        # 📦 ПРИОРИТЕТ #5: Листовки закончились (+10)
        if status_leaflets == "🔴 Пусто":
            priority += 10
        
        # 📝 ПРИОРИТЕТ #5.5: Листовки плохо держатся (+15)
        # Логика: если при последнем посещении было 10 листовок, а статус != "Показы идут" → люди их снимают!
        if flyers_before and flyers_before.isdigit():
            flyers_count = int(flyers_before)
            if flyers_count > 0 and status_card != "🟢 Показы идут":
                priority += 15
                logging.debug(f"📝 Листовки плохо держатся: {address} (+15, было {flyers_count})")
        
        # Не даём приоритету уйти в отрицательные значения
        priority = max(priority, 0)
        
        return priority
        
    except Exception as e:
        logging.warning(f"⚠️ Ошибка расчёта приоритета (строка {row_index}): {e}")
        return 50  # Средний приоритет при ошибке


def load_address_priorities(force: bool = False) -> Dict[str, int]:
    """
    🎯 НОВОЕ: Загружает и кэширует приоритеты всех адресов из Справочника
    
    Кэш обновляется каждые 60 минут или при force=True.
    
    Returns:
        Dict[str, int]: {"адрес": приоритет, ...}
    """
    global PRIORITY_CACHE
    
    try:
        now = datetime.now()
        
        # Кэш-проверка: если менее 60 минут и не принудительно
        if PRIORITY_CACHE["loaded_at"] and not force:
            if now < PRIORITY_CACHE["loaded_at"] + timedelta(minutes=60):
                logging.info(f"📊 Используем кэшированные приоритеты ({len(PRIORITY_CACHE['data'])} адресов)")
                return PRIORITY_CACHE["data"]
        
        # Читаем из Google Sheets
        if not sprav:
            logging.warning("⚠️ sprav не инициализирован")
            return {}
        
        all_values = sprav.get_all_values()
        if len(all_values) <= 1:
            return {}
        
        priorities = {}
        
        # Проходим по всем адресам и рассчитываем приоритеты
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= 1 and row[0]:  # Есть адрес
                address = row[0]
                priority = calculate_address_priority(row, i)
                priorities[address] = priority
        
        # Сохраняем в кэш
        PRIORITY_CACHE = {
            "loaded_at": now,
            "data": priorities
        }
        
        logging.info(f"✅ Приоритеты загружены: {len(priorities)} адресов (кэш на 60 мин)")
        return priorities
        
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки приоритетов: {e}")
        return {}


def get_address_info(address: str) -> Optional[Tuple[str, float, float, str, str, str, str]]:
    """
    Получает информацию об адресе из Справочника.
    Returns: (address, lat, lng, district, status_card, last_promoter, last_visit) или None
    """
    try:
        if not sprav:
            return None
        all_values = sprav.get_all_values()
        if len(all_values) <= 1:
            return None
        
        normalized_input = normalize_text(address)
        
        for row in all_values[1:]:
            if len(row) >= 7:
                addr = row[0]
                if normalize_text(addr) == normalized_input or addr == address:
                    district = row[1] if len(row) > 1 else "Неизвестный"
                    lat = float(row[7]) if len(row) > 7 and row[7] else 0.0  # ШИРОТА (столбец H)
                    lng = float(row[8]) if len(row) > 8 and row[8] else 0.0  # ДОЛГОТА (столбец I)
                    status_card = row[6] if len(row) > 6 else "🔴 Не был"
                    last_visit = row[4] if len(row) > 4 else ""  # ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ (столбец E)
                    last_promoter = row[2] if len(row) > 2 else ""  # ПРОМОУТЕР (столбец C)
                    return (addr, lat, lng, district, status_card, last_promoter, last_visit)
        return None
    except Exception as e:
        logging.error(f"❌ Ошибка получения инфо об адресе: {e}")
        return None


def generate_yandex_maps_route_url(user_lat: float, user_lng: float, dest_lat: float, dest_lng: float) -> str:
    """Генерирует ссылку на пеший маршрут в Яндекс.Картах"""
    return f"https://yandex.ru/maps/?rtext={user_lat},{user_lng}~{dest_lat},{dest_lng}&rtt=pd"


async def get_photo_hash(photo_file) -> Optional[str]:
    """Вычисляет SHA-256 хеш фото для проверки дублей (с таймаутом и ретраем)"""
    import hashlib, asyncio
    for attempt in range(2):
        try:
            file_bytes = await asyncio.wait_for(photo_file.download_as_bytearray(), timeout=12)
            return hashlib.sha256(file_bytes).hexdigest()
        except asyncio.TimeoutError:
            logging.warning("⚠️ Таймаут загрузки фото для хеша, пробуем ещё раз…" if attempt == 0 else "⚠️ Повторный таймаут при вычислении хеша.")
        except Exception as e:
            logging.error(f"❌ Ошибка вычисления хеша фото: {e}")
            break
    return None


def is_photo_duplicate(photo_hash: str) -> bool:
    """Проверяет, было ли фото уже загружено"""
    return photo_hash in used_photo_hashes


def add_photo_hash(photo_hash: str) -> None:
    """Добавляет хеш фото в глобальный список И сохраняет в Google Sheets"""
    used_photo_hashes.add(photo_hash)
    
    # Сохраняем в Google Sheets для персистентности
    try:
        if photo_hashes_sheet:
            timestamp = datetime.now().isoformat()
            photo_hashes_sheet.append_row([photo_hash, timestamp])
            logging.info(f"✅ Хеш фото сохранён в Google Sheets: {photo_hash[:16]}...")
    except Exception as e:
        logging.error(f"❌ Ошибка сохранения хеша фото: {e}")


def load_photo_hashes() -> None:
    """Загружает хеши фото из Google Sheets (последние 30 дней)"""
    global used_photo_hashes
    try:
        if not photo_hashes_sheet:
            logging.warning("⚠️ photo_hashes_sheet не инициализирован")
            return
        
        rows = photo_hashes_sheet.get_all_values()
        if len(rows) <= 1:
            logging.info("ℹ️ Лист photo_hashes пуст")
            return
        
        cutoff = datetime.now() - timedelta(days=30)
        valid_hashes = set()
        
        for row in rows[1:]:  # Пропускаем заголовок
            if len(row) < 2:
                continue
            
            photo_hash, timestamp_str = row[0], row[1]
            try:
                # Пробуем разные форматы даты
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    # Если не ISO формат, пробуем другие форматы
                    timestamp = datetime.strptime(timestamp_str, "%d.%m.%Y %H:%M")
                
                # Сохраняем только хеши за последние 30 дней
                if timestamp >= cutoff:
                    valid_hashes.add(photo_hash)
            except (ValueError, TypeError) as e:
                logging.warning(f"⚠️ Некорректная дата в photo_hashes: {timestamp_str}")
                continue
        
        used_photo_hashes = valid_hashes
        logging.info(f"✅ Загружено {len(valid_hashes)} хешей фото за последние 30 дней")
        
    except Exception as e:
        logging.error(f"❌ Ошибка загрузки photo_hashes: {e}")


def get_session_stats(user_id: int) -> Dict[str, int]:
    """Получает статистику текущей сессии"""
    if user_id not in session_stats:
        session_stats[user_id] = {"addresses": 0, "photos": 0, "earnings": 0}
    return session_stats[user_id]


def update_session_stats(user_id: int, addresses: int = 0, photos: int = 0, earnings: float = 0) -> None:
    """Обновляет сессионный счётчик"""
    stats = get_session_stats(user_id)
    stats["addresses"] += addresses
    stats["photos"] += photos
    stats["earnings"] += int(earnings)


def track_bot_message(user_id: int, message_id: int, max_messages: int = 100) -> None:
    """Сохраняет ID сообщения бота для последующей очистки"""
    if user_id not in user_message_history:
        user_message_history[user_id] = []
    user_message_history[user_id].append(message_id)
    # Ограничиваем количество хранимых ID (храним последние N сообщений)
    if len(user_message_history[user_id]) > max_messages:
        user_message_history[user_id] = user_message_history[user_id][-max_messages:]


async def delete_user_bot_messages(application, user_id: int) -> int:
    """Удаляет все отслеживаемые сообщения бота для конкретного пользователя"""
    if user_id not in user_message_history:
        return 0
    
    deleted_count = 0
    for msg_id in user_message_history[user_id]:
        try:
            await application.bot.delete_message(chat_id=user_id, message_id=msg_id)
            deleted_count += 1
        except Exception as e:
            # Сообщение могло быть уже удалено или слишком старое
            logging.debug(f"⚠️ Не удалось удалить сообщение {msg_id} для {user_id}: {e}")
    
    # Очищаем историю
    user_message_history[user_id] = []
    return deleted_count


async def send_and_track(update_or_chat_id, text: str, **kwargs):
    """
    Вспомогательная функция для отправки сообщения с автоматическим отслеживанием message_id
    
    Принимает Update или chat_id
    Возвращает отправленное сообщение
    """
    if hasattr(update_or_chat_id, 'message'):
        # Это Update объект
        msg = await update_or_chat_id.message.reply_text(text, **kwargs)
        track_bot_message(update_or_chat_id.effective_user.id, msg.message_id)
        return msg
    else:
        # Это chat_id - нужен context или bot
        # В этом случае предполагаем, что kwargs содержит 'bot'
        bot = kwargs.pop('bot', None)
        if bot:
            msg = await bot.send_message(chat_id=update_or_chat_id, text=text, **kwargs)
            track_bot_message(update_or_chat_id, msg.message_id)
            return msg
    return None


# ============================
# ⏰ АВТОМАТИЧЕСКАЯ СМЕНА СТАТУСОВ
# ============================
async def auto_update_statuses() -> None:
    """
    Фоновая задача: автоматическое обновление статусов по таймерам:
    - 18 часов после '🟡 Нет доступа' → сброс (можно зайти снова)
    - 4 дня после '🟢 Показы идут' → '🟡 Обновить'
    - 14 дней после '🟢 Показы идут' → '🔴 Пусто'
    """
    try:
        if not sprav:
            logging.warning("⚠️ sprav не инициализирован, пропуск auto_update_statuses")
            return
        
        all_values = sprav.get_all_values()
        if len(all_values) <= 1:
            return
        
        now = datetime.now()
        updates_made = 0
        
        # Проходим по всем адресам
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) < 7:
                continue
            
            status_card = row[6] if len(row) > 6 else ""  # Столбец G (СТАТУС КАРТЫ)
            last_visit = row[4] if len(row) > 4 else ""    # Столбец E (ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ)
            
            if not last_visit:
                continue
            
            try:
                # Парсим дату последнего визита (🔥 ИСПРАВЛЕНО: поддержка обоих форматов)
                last_visit_date = parse_flexible_date(last_visit)
                if not last_visit_date:
                    continue
                
                hours_passed = (now - last_visit_date).total_seconds() / 3600
                days_passed = hours_passed / 24
                
                new_status = None
                
                # Правило 1: 18 часов после '🟡 Нет доступа' → сброс
                if status_card == "🟡 Нет доступа" and hours_passed >= MIN_REVISIT_HOURS:
                    new_status = ""  # Сбрасываем статус (можно зайти снова)
                
                # Правило 2: 4 дня после '🟢 Показы идут' → '🟡 Обновить'
                elif status_card == "🟢 Показы идут" and days_passed >= 4:
                    new_status = "🟡 Обновить"
                
                # Правило 3: 14 дней после '🟢 Показы идут' → '🔴 Пусто'
                elif status_card == "🟢 Показы идут" and days_passed >= 14:
                    new_status = "🔴 Пусто"
                
                if new_status is not None:
                    sprav.update_cell(i, 7, new_status)  # Обновляем столбец G
                    updates_made += 1
                    addr = row[0] if row else "Unknown"
                    logging.info(f"✅ Авто-обновление: {addr} | {status_card} → {new_status} ({days_passed:.1f} дней)")
                    
            except ValueError as e:
                logging.warning(f"⚠️ Неверный формат даты: {last_visit} | {e}")
                continue
        
        if updates_made > 0:
            logging.info(f"✅ Авто-обновление статусов: {updates_made} адресов")
            
    except Exception as e:
        logging.error(f"❌ Ошибка в auto_update_statuses: {e}")


# ============================
# 🎁 БОНУСНАЯ СИСТЕМА
# ============================
def get_today_photo_count(user_id: int) -> int:
    """
    🔥 ИСПРАВЛЕНО: Подсчитывает ТОЛЬКО фото электрощитов (исключая фото двери и бонусы)
    Цель: листовки наклеиваются только на электрощиты, а не на входные двери!
    """
    try:
        if not otchety:
            return 0
        
        all_values = otchety.get_all_values()
        if len(all_values) <= 1:
            return 0
        
        today = datetime.now().strftime("%d.%m.%Y")
        total_photos = 0
        
        # Структура: [Дата, Промоутер, Адрес, Фото, Сумма, Район, Время, Комментарий]
        for row in all_values[1:]:
            if len(row) >= 4:
                date = row[0]
                promoter = row[1]
                address = row[2]  # Проверяем адрес/комментарий
                photos = row[3]
                comment = row[7] if len(row) > 7 else ""  # Комментарий в столбце 8
                
                if date == today and str(promoter) == str(user_id):
                    # ✅ ФИЛЬТР: Исключаем фото двери и бонусы!
                    if "входной двери" in comment.lower() or "фото двери" in comment.lower():
                        logging.debug(f"⏭️ Пропущено фото двери: {address}")
                        continue
                    
                    if "БОНУС" in address:
                        logging.debug(f"⏭️ Пропущена бонусная запись: {address}")
                        continue
                    
                    # ✅ ТОЛЬКО электрощиты!
                    try:
                        total_photos += int(photos)
                    except ValueError:
                        continue
        
        return total_photos
        
    except Exception as e:
        logging.error(f"❌ Ошибка подсчёта фото за сегодня: {e}")
        return 0


def has_received_bonus_today(user_id: int) -> bool:
    """
    Проверяет, получал ли промоутер бонус сегодня (проверка по листу 'Отчёты')
    """
    try:
        if not otchety:
            return False
        
        all_values = otchety.get_all_values()
        if len(all_values) <= 1:
            return False
        
        today = datetime.now().strftime("%d.%m.%Y")
        
        # Ищем запись с комментарием "БОНУС" для этого промоутера сегодня
        for row in all_values[1:]:
            if len(row) >= 3:
                date = row[0]
                promoter = row[1]
                address = row[2]
                
                if date == today and str(promoter) == str(user_id) and "БОНУС" in address:
                    return True
        
        return False
        
    except Exception as e:
        logging.error(f"❌ Ошибка проверки бонуса: {e}")
        return False


def award_daily_bonus(user_id: int, photo_count: int, context=None) -> Optional[Dict[str, Any]]:
    """
    Начисляет ежедневный бонус за достижение порога фото.
    Возвращает информацию о бонусе или None, если бонус не начислен.
    
    Args:
        user_id: ID промоутера
        photo_count: Количество фото за сегодня
        context: Контекст для отправки проактивного уведомления (опционально)
    """
    try:
        # Проверка 1: Только рабочие дни (Пн-Сб)
        today_weekday = datetime.now().weekday()
        if today_weekday not in BONUS_WORK_DAYS:
            logging.info(f"⚠️ Сегодня выходной (воскресенье), бонусы не начисляются")
            return None
        
        # Проверка 2: Уже получал бонус сегодня?
        if has_received_bonus_today(user_id):
            logging.info(f"⚠️ Промоутер {user_id} уже получил бонус сегодня")
            return None
        
        # Проверка 3: Определяем уровень бонуса (берём максимальный доступный)
        awarded_tier = None
        for tier in reversed(BONUS_TIERS):  # От большего к меньшему
            if photo_count >= tier["threshold"]:
                awarded_tier = tier
                break
        
        if not awarded_tier:
            logging.info(f"⚠️ Промоутер {user_id} не достиг порога ({photo_count} фото)")
            return None
        
        # Начисляем бонус
        bonus_amount = awarded_tier["bonus"]
        tier_name = awarded_tier["name"]
        
        # 1. Обновляем баланс
        if not update_balance(user_id, bonus_amount):
            logging.error(f"❌ Не удалось начислить бонус {user_id}")
            return None
        
        # 2. Записываем в "Отчёты" (для проверки повторного бонуса)
        try:
            current_date = datetime.now().strftime("%d.%m.%Y")
            current_time = datetime.now().strftime("%H:%M")
            
            bonus_row = [
                current_date,
                str(user_id),
                f"🎁 БОНУС {tier_name}",  # Специальная метка
                str(photo_count),
                f"{bonus_amount:.2f}",
                "Система",
                current_time
            ]
            
            if otchety:
                otchety.append_row(bonus_row)
        except Exception as e:
            logging.error(f"❌ Ошибка записи бонуса в 'Отчёты': {e}")
        
        logging.info(f"🎁 Бонус начислен: {user_id} | {tier_name} | {photo_count} фото | +{bonus_amount}₽")
        
        # 🔔 НОВОЕ: Проактивное уведомление о достижении бонуса
        if context:
            try:
                import asyncio
                user_name = get_user_name_from_balances(user_id) or "Промоутер"
                
                bonus_message = (
                    f"🎉 **ПОЗДРАВЛЯЕМ, {user_name}!**\n\n"
                    f"{tier_name} УРОВЕНЬ ДОСТИГНУТ!\n\n"
                    f"📸 Фото за сегодня: **{photo_count}**\n"
                    f"💰 Бонус: **+{bonus_amount:.0f}₽**\n\n"
                    f"🚀 Отличная работа! Так держать! 💪🔥"
                )
                
                # Отправляем асинхронное уведомление
                async def send_bonus_notification():
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=bonus_message,
                            parse_mode="Markdown"
                        )
                        logging.info(f"✅ Проактивное уведомление о бонусе отправлено: {user_id}")
                    except Exception as e:
                        logging.warning(f"⚠️ Не удалось отправить уведомление о бонусе: {e}")
                
                # Создаём задачу для отправки
                asyncio.create_task(send_bonus_notification())
                
            except Exception as e:
                logging.warning(f"⚠️ Ошибка при отправке проактивного уведомления: {e}")
        
        return {
            "tier_name": tier_name,
            "bonus_amount": bonus_amount,
            "photo_count": photo_count,
            "threshold": awarded_tier["threshold"]
        }
        
    except Exception as e:
        logging.error(f"❌ Ошибка начисления бонуса: {e}")
        return None


def check_and_award_bonus(user_id: int, context=None) -> Optional[str]:
    """
    Проверяет условия и начисляет бонус. Возвращает сообщение для пользователя.
    """
    photo_count = get_today_photo_count(user_id)
    bonus_info = award_daily_bonus(user_id, photo_count, context=context)
    
    if bonus_info:
        return (
            f"🎉 **ПОЗДРАВЛЯЕМ!**\n\n"
            f"{bonus_info['tier_name']} УРОВЕНЬ ДОСТИГНУТ!\n\n"
            f"📸 Фото за сегодня: **{bonus_info['photo_count']}**\n"
            f"💰 Бонус: **+{bonus_info['bonus_amount']:.0f}₽**\n\n"
            f"Отличная работа! Так держать! 💪🔥"
        )
    
    return None


def get_bonus_progress(user_id: int) -> str:
    """
    Возвращает текст с прогрессом до следующего бонуса
    """
    photo_count = get_today_photo_count(user_id)
    
    # Получаем текущий streak для мотивационного сообщения
    streak_days = get_work_streak(user_id)
    activity_multiplier = min(1.0 + 0.10 * streak_days, 1.5)
    bonus_text = f"🔥 Активность: +{int((activity_multiplier - 1.0)*100)}% (ежедневно +10%, максимум +50%; пропуск дня — обнуление)"
    effective_panel_rate = 3.0 * activity_multiplier * user_state.get(user_id, {}).get("address_bonus_multiplier", 1.0)
    
    # Находим следующий уровень
    next_tier = None
    for tier in BONUS_TIERS:
        if photo_count < tier["threshold"]:
            next_tier = tier
            break
    
    if not next_tier:
        # Все уровни пройдены!
        return f"🏆 **ВСЕ УРОВНИ ПРОЙДЕНЫ!** ({photo_count} фото)\n✨ Ты легенда!\n\n🔥 Активность: {streak_days} дн.\n⚡ Ставка электрощита: {effective_panel_rate:.1f}₽ +{int((activity_multiplier - 1.0)*100)}%"
    
    remaining = next_tier["threshold"] - photo_count
    progress_percent = int((photo_count / next_tier["threshold"]) * 100)
    
    # Прогресс-бар
    filled = int((photo_count / next_tier["threshold"]) * 10)
    progress_bar = "█" * filled + "░" * (10 - filled)
    
    return (
        f"📊 **Прогресс до {next_tier['name']}:**\n"
        f"[{progress_bar}] {progress_percent}%\n\n"
        f"📸 Сделано: {photo_count} / {next_tier['threshold']}\n"
        f"🎯 Осталось: {remaining} фото\n"
        f"💰 Награда: +{next_tier['bonus']}₽\n\n"
        f"🔥 Активность: {streak_days} дн.\n"
        f"⚡ Ставка электрощита: {effective_panel_rate:.1f}₽ +{int((activity_multiplier - 1.0)*100)}%"
    )


# ============================
# 🔔 PUSH-УВЕДОМЛЕНИЯ
# ============================
async def send_morning_reminder(application) -> None:
    """
    Утреннее напоминание (10:00): показывает текущий прогресс
    Отправляется всем активным промоутерам из листа 'Балансы'
    """
    global last_notification_sent
    
    # 🔥 УСИЛЕННАЯ ЗАЩИТА ОТ ДУБЛИКАТОВ: проверяем дату
    with notification_lock:
        now = datetime.now()
        today_key = f"morning_{now.strftime('%Y-%m-%d')}"
        last_sent = last_notification_sent.get(today_key)
        
        # Если сообщение отправлено сегодня - пропускаем
        if last_sent:
            time_diff = (now - last_sent).total_seconds()
            logging.warning(f"⚠️ Утреннее напоминание уже отправлено сегодня ({int(time_diff)} сек. назад). Пропускаем.")
            return
        
        # Отмечаем время отправки
        last_notification_sent[today_key] = now
        # Удаляем старые записи
        for key in list(last_notification_sent.keys()):
            if key.startswith("morning_"):
                try:
                    key_date = datetime.strptime(key.replace("morning_", ""), "%Y-%m-%d")
                    if (now - key_date).days > 2:
                        del last_notification_sent[key]
                except Exception:
                    pass
    
    try:
        if not balances_sheet:
            logging.warning("⚠️ balances_sheet не инициализирован")
            return
        
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:
            logging.info("ℹ️ Нет промоутеров в 'Балансы'")
            return
        
        headers = all_values[0]
        name_col_idx = headers.index("Имя") if "Имя" in headers else 4
        
        sent_count = 0
        for row in all_values[1:]:
            if len(row) > 0 and row[0]:  # Есть Telegram ID
                try:
                    user_id = int(row[0])
                    user_name = row[name_col_idx] if len(row) > name_col_idx else "Промоутер"
                    
                    # Получаем прогресс
                    photo_count = get_today_photo_count(user_id)
                    
                    # Находим ближайший бонус
                    next_tier = None
                    for tier in BONUS_TIERS:
                        if photo_count < tier["threshold"]:
                            next_tier = tier
                            break
                    
                    if next_tier:
                        remaining = next_tier["threshold"] - photo_count
                        message = (
                            f"☀️ Доброе утро, {user_name}!\n\n"
                            f"📸 Сегодня у тебя **{photo_count} / {next_tier['threshold']}** фото\n"
                            f"🎯 Осталось: **{remaining}** до {next_tier['name']}\n"
                            f"💰 Награда: **+{next_tier['bonus']}₽**\n\n"
                            f"💪 Вперёд к победе!"
                        )
                    else:
                        # Получаем текущий streak для мотивационного сообщения
                        streak_days = get_work_streak(user_id)
                        activity_multiplier = min(1.0 + 0.10 * streak_days, 1.5)
                        bonus_text = f"🔥 Активность: +{int((activity_multiplier - 1.0)*100)}% (ежедневно +10%, максимум +50%; пропуск дня — обнуление)"
                        effective_panel_rate = 3.0 * activity_multiplier * user_state.get(user_id, {}).get("address_bonus_multiplier", 1.0)
                        
                        # Все бонусы получены
                        message = (
                            f"☀️ Доброе утро, {user_name}!\n\n"
                            f"🏆 Сегодня ты уже прошёл все уровни!\n"
                            f"📸 Фото за сегодня: **{photo_count}**\n\n"
                            f"✨ Ты легенда! Продолжай в том же духе!\n\n"
                            f"🔥 Активность: {streak_days} дн.\n"
                            f"⚡ Ставка электрощита: {effective_panel_rate:.1f}₽ +{int((activity_multiplier - 1.0)*100)}%"
                        )
                    
                    await application.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                    sent_count += 1
                    
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось отправить утреннее напоминание {user_id}: {e}")
                    continue
        
        logging.info(f"✅ Утренние напоминания отправлены ({sent_count} промоутеров)")
        
    except Exception as e:
        logging.error(f"❌ Ошибка отправки утренних напоминаний: {e}")


async def send_evening_reminder(application) -> None:
    """
    Вечернее напоминание (18:00): мотивация добить до бонуса
    Отправляется только тем, кто близок к бонусу (50%+ прогресса)
    """
    global last_notification_sent
    
    # 🔥 УСИЛЕННАЯ ЗАЩИТА ОТ ДУБЛИКАТОВ
    with notification_lock:
        now = datetime.now()
        today_key = f"evening_{now.strftime('%Y-%m-%d')}"
        last_sent = last_notification_sent.get(today_key)
        
        if last_sent:
            time_diff = (now - last_sent).total_seconds()
            logging.warning(f"⚠️ Вечернее напоминание уже отправлено сегодня ({int(time_diff)} сек. назад). Пропускаем.")
            return
        
        last_notification_sent[today_key] = now
        # Удаляем старые записи
        for key in list(last_notification_sent.keys()):
            if key.startswith("evening_"):
                try:
                    key_date = datetime.strptime(key.replace("evening_", ""), "%Y-%m-%d")
                    if (now - key_date).days > 2:
                        del last_notification_sent[key]
                except Exception:
                    pass
    
    try:
        if not balances_sheet:
            logging.warning("⚠️ balances_sheet не инициализирован")
            return
        
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:
            return
        
        headers = all_values[0]
        name_col_idx = headers.index("Имя") if "Имя" in headers else 4
        
        sent_count = 0
        for row in all_values[1:]:
            if len(row) > 0 and row[0]:
                try:
                    user_id = int(row[0])
                    user_name = row[name_col_idx] if len(row) > name_col_idx else "Промоутер"
                    
                    photo_count = get_today_photo_count(user_id)
                    
                    # Находим ближайший бонус
                    next_tier = None
                    for tier in BONUS_TIERS:
                        if photo_count < tier["threshold"]:
                            next_tier = tier
                            break
                    
                    if next_tier:
                        remaining = next_tier["threshold"] - photo_count
                        progress_percent = (photo_count / next_tier["threshold"]) * 100
                        
                        # Отправляем только если прогресс >= 50%
                        if progress_percent >= 50:
                            # Прогресс-бар
                            filled = int((photo_count / next_tier["threshold"]) * 10)
                            progress_bar = "█" * filled + "░" * (10 - filled)
                            
                            # Получаем текущий streak для мотивационного сообщения
                            streak_days = get_work_streak(user_id)
                            if streak_days >= 5:
                                flyer_multiplier = 1.5
                                bonus_text = "🔥 +50% за 5 дней подряд!"
                            elif streak_days >= 3:
                                flyer_multiplier = 1.2
                                bonus_text = "🔥 +20% за 3 дня подряд!"
                            else:
                                flyer_multiplier = 1.0
                                bonus_text = "— продолжай работать для бонуса!"
                            effective_flyer_rate = 3.0 * user_state.get(user_id, {}).get("address_bonus_multiplier", 1.0)
                            
                            message = (
                                f"🌆 {user_name}, вечер — самое время!\n\n"
                                f"📊 Прогресс: [{progress_bar}] {int(progress_percent)}%\n\n"
                                f"🎯 Добей до **{next_tier['threshold']}** — получи **+{next_tier['bonus']}₽**!\n"
                                f"📸 Осталось всего: **{remaining} фото**\n\n"
                                f"🔥 Давай, ты почти у цели!\n\n"
                                f"🔥 Активность: {streak_days} дн. ({bonus_text})\n"
                                f"⚡ Ставка электрощита: {effective_flyer_rate:.1f}₽ +{int((activity_multiplier - 1.0)*100)}%"
                            )
                            
                            await application.bot.send_message(
                                chat_id=user_id,
                                text=message,
                                parse_mode="Markdown"
                            )
                            sent_count += 1
                    
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось отправить вечернее напоминание {user_id}: {e}")
                    continue
        
        logging.info(f"✅ Вечерние напоминания отправлены ({sent_count} промоутеров)")
        
    except Exception as e:
        logging.error(f"❌ Ошибка отправки вечерних напоминаний: {e}")


async def send_cleanup_warning(application) -> None:
    """Вечернее предупреждение: в 07:00 будет авто-очистка чата"""
    global last_notification_sent, cleanup_warning_lock
    
    # 🔥 КРИТИЧЕСКАЯ ИСПРАВЛЕННАЯ БЛОКИРОВКА: используем глобальную async lock
    if cleanup_warning_lock is None:
        cleanup_warning_lock = asyncio.Lock()
    
    async with cleanup_warning_lock:
        now = datetime.now()
        today_key = f"cleanup_{now.strftime('%Y-%m-%d')}"
        last_sent = last_notification_sent.get(today_key)
        
        # Проверяем: если уже отправляли сегодня (и прошло < 1 часа) - пропускаем
        if last_sent:
            time_diff = (now - last_sent).total_seconds()
            if time_diff < 3600:  # 1 час
                logging.warning(f"⚠️ Предупреждение об очистке уже отправлено сегодня ({int(time_diff)} сек. назад). Пропускаем.")
                return
        
        # Отмечаем, что отправили сегодня
        last_notification_sent[today_key] = now
        # Удаляем старые записи (старше 2 дней)
        for key in list(last_notification_sent.keys()):
            if key.startswith("cleanup_"):
                try:
                    key_date = datetime.strptime(key.replace("cleanup_", ""), "%Y-%m-%d")
                    if (now - key_date).days > 2:
                        del last_notification_sent[key]
                except Exception:
                    pass
    
    try:
        if not balances_sheet:
            logging.warning("⚠️ balances_sheet не инициализирован")
            return
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:
            return
        sent = 0
        for row in all_values[1:]:
            if len(row) > 0 and row[0]:
                try:
                    uid = int(row[0])
                    # 🔥 НОВОЕ: Задержка перед отправкой (предотвращает дубли)
                    await asyncio.sleep(0.2)
                    msg = await application.bot.send_message(
                        chat_id=uid,
                        text=(
                            "⚠️ Напоминание: в 07:00 будет авто-очистка чата за прошедший день.\n\n"
                            "💡 Сохрани важные сообщения, если нужно. Работа продолжится завтра с чистого листа."
                        ),
                        reply_markup=get_main_menu_keyboard()
                    )
                    # Не отслеживаем предупреждение - оно удалится утром вместе со всеми
                    track_bot_message(uid, msg.message_id)
                    sent += 1
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось отправить предупреждение {row[0]}: {e}")
                    continue
        logging.info(f"✅ Отправлено предупреждений об очистке: {sent}")
    except Exception as e:
        logging.error(f"❌ Ошибка отправки предупреждений об очистке: {e}")

async def perform_chat_cleanup(application) -> None:
    """Утренняя авто-очистка: сброс состояний и старт нового дня"""
    global last_notification_sent, morning_cleanup_lock
    
    # 🔥 КРИТИЧЕСКАЯ ИСПРАВЛЕННАЯ БЛОКИРОВКА: используем глобальную async lock
    if morning_cleanup_lock is None:
        morning_cleanup_lock = asyncio.Lock()
    
    async with morning_cleanup_lock:
        now = datetime.now()
        today_key = f"morning_cleanup_{now.strftime('%Y-%m-%d')}"
        last_sent = last_notification_sent.get(today_key)
        
        if last_sent:
            time_diff = (now - last_sent).total_seconds()
            # 🔥 НОВОЕ: Если очистка уже была сегодня (и прошло < 1 часа), пропускаем
            if time_diff < 3600:  # 1 час = 3600 секунд
                logging.warning(f"⚠️ Утренняя очистка уже выполнена сегодня ({int(time_diff)} сек. назад). Пропускаем.")
                return
        
        last_notification_sent[today_key] = now
        # Удаляем старые записи
        for key in list(last_notification_sent.keys()):
            if key.startswith("morning_cleanup_"):
                try:
                    key_date = datetime.strptime(key.replace("morning_cleanup_", ""), "%Y-%m-%d")
                    if (now - key_date).days > 2:
                        del last_notification_sent[key]
                except Exception:
                    pass
    
    try:
        if not balances_sheet:
            logging.warning("⚠️ balances_sheet не инициализирован")
            return
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:
            return
        cleaned = 0
        for row in all_values[1:]:
            if len(row) > 0 and row[0]:
                try:
                    uid = int(row[0])
                    
                    # 🗑️ Удаляем все сообщения бота за предыдущий день
                    deleted_count = await delete_user_bot_messages(application, uid)
                    if deleted_count > 0:
                        logging.info(f"🗑️ Удалено {deleted_count} сообщений бота для {uid}")
                    
                    # Сбрасываем состояние работы по адресу и сессионную статистику
                    user_state[uid] = {}
                    session_stats[uid] = {"addresses": 0, "photos": 0, "earnings": 0}
                    
                    # 🔥 НОВОЕ: Отправляем сообщение нового дня с задержкой 0.2 сек (предотвращает дубли)
                    await asyncio.sleep(0.2)
                    await application.bot.send_message(
                        chat_id=uid,
                        text=(
                            "🧹 Чат очищен — новый день!\n\n"
                            "🚀 Нажми 'Начать работу' и отправь геолокацию, чтобы получить ближайшие адреса."
                        ),
                        reply_markup=get_main_menu_keyboard()
                    )
                    cleaned += 1
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось очистить чат {row[0]}: {e}")
                    continue
        logging.info(f"✅ Авто-очистка завершена: {cleaned} чатов")
    except Exception as e:
        logging.error(f"❌ Ошибка авто-очистки: {e}")


def get_photo_price() -> float:
    """Получает стоимость за 1 фото из листа 'Настройки'"""
    try:
        load_settings()  # Обновляем настройки
        load_settings()
        price_str = SETTINGS.get("Стоимость за 1 фото", "2.5")  # 🔥 ИСПРАВЛЕНО: 3.0₽ → 2.5₽ (снижение затрат)
        return float(price_str)
    except Exception as e:
        logging.warning(f"⚠️ Ошибка получения цены фото: {e}")
        return 2.5  # 🔥 ИСПРАВЛЕНО: Цена по умолчанию 2.5₽


def update_balance(user_id: int, amount: float) -> bool:
    """Добавляет транзакцию в лист 'Балансы' (больше не обновляет баланс напрямую)"""
    try:
        if not balances_sheet:
            logging.error("❌ balances_sheet не инициализирован")
            return False
        
        # Добавляем транзакцию с 10 колонками
        # [ПромоутерID, Дата, Тип, Листовки (шт), Фото двери (шт), Фото щитов (шт), Оплата дверь (₽), Оплата щиты базовая (₽), Премия активность (₽), Итого (₽)]
        transaction_row = [
            str(user_id),
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            "Начисление",
            "0",      # Листовки
            "0",      # Фото двери
            "0",      # Фото щитов
            "0.00",   # Оплата дверь
            "0.00",   # Оплата щиты
            "0.00",   # Премия активность
            f"{amount:.2f}"  # Итого
        ]
        balances_sheet.append_row(transaction_row)
        logging.info(f"✅ Транзакция добавлена: {user_id} +{amount:.2f}₽")
        return True
        
    except Exception as e:
        logging.error(f"❌ Ошибка добавления транзакции: {e}")
        return False


def deduct_flyers(user_id: int, count: int) -> bool:
    """
    🔥 УЛУЧШЕНО: Списывает листовки из 'Балансы' (колонка C)
    Система: 5₽/шт + бонусы за streak (3 дня +20%, 5 дней +50%)
    """
    try:
        if not balances_sheet:
            logging.error("❌ balances_sheet не инициализирован")
            return False
        
        all_values = balances_sheet.get_all_values()
        if len(all_values) <= 1:
            logging.error("❌ Лист 'Балансы' пуст")
            return False
        
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) > 0 and str(row[0]) == str(user_id):
                # Структура: [ПромоутерID, Баланс ₽, Листовки шт, ...]
                current_balance = 0
                if len(row) > 2 and row[2]:
                    try:
                        current_balance = int(row[2])  # Колонка C (индекс 2)
                    except ValueError:
                        current_balance = 0
                
                new_balance = max(0, current_balance - count)
                balances_sheet.update_cell(i, 3, str(new_balance))  # Колонка C = 3
                
                # 💰 Начисление денег за листовки отключено — оплата идёт по базовой ставке фото и дневной премии
                flyer_earnings = 0.0
                logging.info(f"✅ Листовки списаны: {user_id} -{count} (={new_balance})")
                
                return True
        
        logging.warning(f"⚠️ Промоутер {user_id} не найден в 'Балансы'")
        return False
        
    except Exception as e:
        logging.error(f"❌ Ошибка списания листовок: {e}")
        return False


def calculate_flyer_earnings(user_id: int, flyer_count: int) -> float:
    """
    💯 НОВОЕ: Рассчитывает заработок за листовки с бонусами streak
    
    Система начисления:
    - Базовая ставка: 5₽ за 1 листовку
    - 🔥 Серия 3 дня подряд: +20% (6₽/шт)
    - 🔥 Серия 5 дней подряд: +50% (7.5₽/шт)
    
    Args:
        user_id: ID промоутера
        flyer_count: Количество листовок
    
    Returns:
        Сумма к начислению с учётом бонусов
    """
    try:
        # Базовая ставка: 2.5₽/шт (🔥 ИСПРАВЛЕНО: было 3.0₽)
        BASE_FLYER_PRICE = 2.5
        
        # Получаем текущую серию дней
        streak_days = get_work_streak(user_id)
        
        # Определяем множитель
        if streak_days >= 5:
            multiplier = 1.5  # +50%
            bonus_text = "🔥 5 дней streak (+50%)"
        elif streak_days >= 3:
            multiplier = 1.2  # +20%
            bonus_text = "🔥 3 дня streak (+20%)"
        else:
            multiplier = 1.0  # Без бонуса
            bonus_text = ""
        
        # Рассчитываем сумму
        address_mult = user_state.get(user_id, {}).get("address_bonus_multiplier", 1.0)
        total = BASE_FLYER_PRICE * flyer_count * multiplier * address_mult
        
        if bonus_text:
            logging.info(f"💰 Расчёт за листовки: {flyer_count} шт × {BASE_FLYER_PRICE}₽ × {multiplier} = {total:.2f}₽ ({bonus_text})")
        else:
            logging.info(f"💰 Расчёт за листовки: {flyer_count} шт × {BASE_FLYER_PRICE}₽ = {total:.2f}₽")
        
        return total
        
    except Exception as e:
        logging.error(f"❌ Ошибка расчёта заработка за листовки: {e}")
        return 0.0


def get_work_streak(user_id: int) -> int:
    """
    🔥 НОВОЕ: Подсчитывает количество дней подряд с фото электрощитов
    
    Логика:
    - Смотрим на лист 'Отчёты'
    - Считаем количество дней подряд с записями (исключая фото двери и бонусы)
    - Работает от сегодня назад
    
    Returns:
        Количество дней подряд (0-N)
    """
    try:
        if not otchety:
            return 0
        
        all_values = otchety.get_all_values()
        if len(all_values) <= 1:
            return 0
        
        from datetime import datetime, timedelta
        
        # Собираем уникальные даты с работой (только электрощиты!)
        work_dates = set()
        
        for row in all_values[1:]:
            if len(row) >= 4:
                date_str = row[0]  # Дата
                promoter = row[1]  # Промоутер
                address = row[2]   # Адрес
                comment = row[7] if len(row) > 7 else ""  # Комментарий
                
                if str(promoter) == str(user_id):
                    # ✅ ФИЛЬТР: Исключаем фото двери и бонусы
                    if "входной двери" in comment.lower() or "фото двери" in comment.lower():
                        continue
                    if "БОНУС" in address:
                        continue
                    
                    # Добавляем дату
                    work_dates.add(date_str)
        
        if not work_dates:
            return 0
        
        # Преобразуем в datetime и сортируем
        work_dates_dt = []
        for date_str in work_dates:
            try:
                dt = datetime.strptime(date_str, "%d.%m.%Y")
                work_dates_dt.append(dt)
            except ValueError:
                continue
        
        if not work_dates_dt:
            return 0
        
        work_dates_dt.sort(reverse=True)  # От новых к старым
        
        # Считаем streak от сегодня назад
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        streak = 0
        
        for i, work_date in enumerate(work_dates_dt):
            expected_date = today - timedelta(days=i)
            work_date_normalized = work_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if work_date_normalized == expected_date:
                streak += 1
            else:
                break  # Прерываем при пропуске
        
        logging.info(f"🔥 Серия для {user_id}: {streak} дней подряд")
        return streak
        
    except Exception as e:
        logging.error(f"❌ Ошибка подсчёта streak: {e}")
        return 0


def update_address_status(address: str, new_status: str, photos_count: int = 0) -> bool:
    """
    Обновляет статус адреса в Справочнике:
    - Столбец G: СТАТУС КАРТЫ
    - Столбец E: ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ
    - Столбец K: ЛИСТОВКИ НАКЛЕЕНО (если photos_count > 0)
    """
    try:
        if not sprav:
            logging.error("❌ sprav не инициализирован")
            return False
        
        # 🔥 ИСПОЛЬЗУЕМ get_all_values() чтобы получить свежие данные без кэша
        all_values = sprav.get_all_values()
        if len(all_values) <= 1:
            return False
        
        normalized_input = normalize_text(address)
        current_datetime = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= 7:
                addr = row[0]
                if normalize_text(addr) == normalized_input or addr == address:
                    # 🎯 ОБНОВЛЯЕМ ДАННЫЕ ЗА ОДИН ВЫЗОВ (batch update)
                    try:
                        # Колонка E (5) = ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ
                        # Колонка G (7) = СТАТУС КАРТЫ
                        # Колонка K (11) = ЛИСТОВКИ НАКЛЕЕНО
                        
                        if photos_count > 0:
                            # Обновляем с количеством листовок
                            sprav.update(
                                [[current_datetime, '', new_status, '', '', '', str(photos_count)]],
                                f'E{i}:K{i}',
                                value_input_option='RAW'
                            )
                            logging.info(f"✅ Статус обновлён: {address} → {new_status}, листовок: {photos_count} (строка {i})")
                        else:
                            # Обновляем только статус и время
                            sprav.update(
                                [[current_datetime, '', new_status]],
                                f'E{i}:G{i}',
                                value_input_option='RAW'
                            )
                            logging.info(f"✅ Статус обновлён: {address} → {new_status} (время: {current_datetime}, строка {i})")
                        # 🔥 ВАЖНО: Принудительно обновляем кэш gspread
                        import time
                        time.sleep(0.3)  # Короткая задержка для синхронизации Google Sheets
                        return True
                    except Exception as e:
                        logging.error(f"❌ Ошибка batch update: {e}")
                        # Fallback: обновляем по одной ячейке
                        try:
                            sprav.update_cell(i, 7, new_status)
                            sprav.update_cell(i, 5, current_datetime)
                            if photos_count > 0:
                                sprav.update_cell(i, 11, str(photos_count))  # Столбец K
                            logging.info(f"✅ Статус обновлён (fallback): {address} → {new_status}")
                            import time
                            time.sleep(0.3)
                            return True
                        except Exception as e2:
                            logging.error(f"❌ Ошибка fallback update: {e2}")
                            return False
        
        logging.warning(f"⚠️ Адрес {address} не найден в Справочнике")
        return False
        
    except Exception as e:
        logging.error(f"❌ Ошибка обновления статуса адреса: {e}")
        return False


def save_report_to_otchety(user_id: int, address: str, photo_count: int, total_amount: float, district: str) -> bool:
    """Записывает отчёт в лист 'Отчёты'"""
    try:
        if not otchety:
            logging.error("❌ otchety не инициализирован")
            return False
        
        from datetime import datetime
        current_date = datetime.now().strftime("%d.%m.%Y")
        current_time = datetime.now().strftime("%H:%M")
        
        # Структура: [Дата, Промоутер, Адрес, Фото, Сумма, Район, Время]
        new_row = [
            current_date,
            str(user_id),
            address,
            str(photo_count),
            f"{total_amount:.2f}",
            district,
            current_time
        ]
        
        otchety.append_row(new_row)
        logging.info(f"✅ Отчёт записан: {user_id} | {address} | {photo_count} фото | {total_amount:.2f}₽")
        return True
        
    except Exception as e:
        logging.error(f"❌ Ошибка записи отчёта: {e}")
        return False


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик получения фото (электрощиты или дверь)"""
    try:
        user_id = update.effective_user.id
        
        if user_id not in user_state:
            # 🔧 ИСПРАВЛЕНО: Добавлена inline-кнопка "🚀 Начать работу"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 Начать работу", callback_data="start_work")
            ]])
            await update.message.reply_text(
                "❌ Сначала начни работу!",
                reply_markup=keyboard
            )
            return
        
        state = user_state[user_id].get("state")
        
        # 🔥 НОВОЕ: Если state is None и нет активной сессии - показываем инструкцию
        if state is None and not user_state[user_id].get("selected_address"):
            await update.message.reply_text(
                "📸 **Фото не ожидается**\n\n"
                "ℹ️ Чтобы начать работу:\n"
                "1️⃣ Нажми 'Начать работу 🚀'\n"
                "2️⃣ Отправь геолокацию\n"
                "3️⃣ Выбери адрес и нажми '🎯 Я на месте!'",
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard(user_id)
            )
            return
        
        # 💡 Если идёт этап выбора количества уже наклеенных листовок — фото не принимаем
        if state == "awaiting_existing_flyers_count":
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            keyboard = []
            row = []
            for i in range(0, 11):
                row.append(InlineKeyboardButton(str(i), callback_data=f"existing_flyers_{i}"))
                if (i + 1) % 5 == 0:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton("➡️ Пропустить", callback_data="existing_flyers_skip")])
            await update.message.reply_text(
                "📊 Сейчас этап выбора количества.\n\nВыбери число на клавиатуре ниже или нажми «➡️ Пропустить».",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # 🔥 ЗАЩИТА: Если фото пришло не в ожидаемом состоянии
        if state not in ["awaiting_door_photo", "awaiting_exit_door_photo", "awaiting_photos"]:
            logging.warning(f"⚠️ Пользователь {user_id} отправил фото в неожиданном состоянии: {state}")
            
            # 🔧 ИСПРАВЛЕНО: Если состояние awaiting_access_answer → переводим в awaiting_door_photo
            if state == "awaiting_access_answer" and user_state[user_id].get("selected_address"):
                user_state[user_id]["state"] = "awaiting_door_photo"
                state = "awaiting_door_photo"
                logging.info(f"✅ Пользователь {user_id}: состояние сброшено в awaiting_door_photo (фото двери 'Нет доступа')")
            # Если адрес уже выбран И есть сессия — принимаем фото
            elif user_state[user_id].get("selected_address") and user_state[user_id].get("session_started_at"):
                # Проверяем, не истекла ли сессия
                now_utc = datetime.utcnow()
                load_settings()
                max_minutes = int(SETTINGS.get("SESSION_MAX_MINUTES", "25"))
                session_started_at = user_state[user_id].get("session_started_at")
                # 🔧 ИСПРАВЛЕНО: обе даты naive UTC
                if isinstance(session_started_at, datetime) and session_started_at.tzinfo:
                    session_started_at = session_started_at.replace(tzinfo=None)
                
                if isinstance(session_started_at, datetime) and now_utc <= session_started_at + timedelta(minutes=max_minutes):
                    # Сессия ещё активна — переводим в awaiting_photos
                    user_state[user_id]["state"] = "awaiting_photos"
                    state = "awaiting_photos"
                    logging.info(f"✅ Пользователь {user_id}: состояние сброшено в awaiting_photos (сессия активна)")
                else:
                    # Сессия истекла
                    await update.message.reply_text(
                        "⏰ **Сессия истекла**\n\n"
                        "🔄 Чтобы продолжить работу:\n"
                        "1️⃣ Отправь геолокацию (кнопка '🔍 Сканировать район')\n"
                        "2️⃣ Выбери адрес\n"
                        "3️⃣ Нажми '🎯 Я на месте!'",
                        parse_mode="Markdown",
                        reply_markup=get_main_menu_keyboard(user_id)
                    )
                    user_state[user_id]["state"] = None
                    return
            else:
                # Нет активной сессии
                await update.message.reply_text(
                    "📸 **Фото не ожидается**\n\n"
                    "ℹ️ Чтобы начать работу:\n"
                    "1️⃣ Нажми 'Начать работу 🚀'\n"
                    "2️⃣ Отправь геолокацию\n"
                    "3️⃣ Выбери адрес и нажми '🎯 Я на месте!'",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
                return
        
        # 🚪 Фото двери (при отсутствии доступа)
        if state == "awaiting_door_photo":
            # Получаем фото двери
            photo = update.message.photo[-1]
            photo_file = await context.bot.get_file(photo.file_id)
            photo_hash = await get_photo_hash(photo_file)
            if not photo_hash:
                await update.message.reply_text("❌ Ошибка обработки фото. Попробуй ещё раз.")
                return
            if is_photo_duplicate(photo_hash):
                await update.message.reply_text("❌ Это фото уже было загружено! Отправь другое фото двери.")
                return
            add_photo_hash(photo_hash)
            
            # 🛡️ АНТИ-ФРОД: проверка времени сессии и геолокации
            now_utc = datetime.utcnow()
            load_settings()
            max_minutes = int(SETTINGS.get("SESSION_MAX_MINUTES", "25"))
            session_started_at = user_state[user_id].get("session_started_at")
            # 🔧 ИСПРАВЛЕНО: преобразуем в naive если aware
            if isinstance(session_started_at, datetime) and session_started_at.tzinfo:
                session_started_at = session_started_at.replace(tzinfo=None)
            if not session_started_at or now_utc > session_started_at + timedelta(minutes=max_minutes):
                await update.message.reply_text(
                    "⏰ **Сессия истекла**\n\n"
                    "🔄 Чтобы продолжить работу:\n"
                    "1️⃣ Отправь геолокацию (кнопка '🔍 Сканировать район')\n"
                    "2️⃣ Выбери адрес\n"
                    "3️⃣ Нажми '🎯 Я на месте!'",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
                user_state[user_id]["state"] = None
                return
            msg_time = getattr(update.message, "date", None)
            load_settings()
            future_grace = int(SETTINGS.get("PHOTO_FUTURE_GRACE_SECONDS", "30"))
            # 🔧 ИСПРАВЛЕНО: преобразуем msg_time в naive datetime для сравнения
            if msg_time:
                msg_time_utc = msg_time.replace(tzinfo=None)  # Убираем timezone
                if msg_time_utc > (now_utc + timedelta(seconds=future_grace)):
                    await update.message.reply_text("❌ Фото отклонено: время сообщения из будущего.", reply_markup=get_main_menu_keyboard())
                    return
            loc_time = user_state[user_id].get("current_location_time")
            load_settings()
            loc_max_age = int(SETTINGS.get("LOCATION_MAX_AGE_MINUTES", "40"))
            if not loc_time or now_utc > loc_time + timedelta(minutes=loc_max_age):
                await update.message.reply_text(
                    "📍 Геолокация устарела. Отправь текущую геолокацию кнопкой «🔍 Сканировать район».",
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔍 Сканировать район", request_location=True)],["Вернуться в меню"]], resize_keyboard=True)
                )
                return
            
            # Инфо об адресе
            selected_address = user_state[user_id].get("selected_address", "Неизвестный адрес")
            addr_info_no_geo = get_address_info(selected_address)
            district = addr_info_no_geo[3] if (addr_info_no_geo and len(addr_info_no_geo) > 3) else "Неизвестный"
            
            # Обновляем статус
            update_address_status(selected_address, "🟡 Нет доступа", photos_count=1)
            
            # 🔧 ИСПРАВЛЕНО: Увеличена задержка для синхронизации Google Sheets
            # Проблема: Адрес появляется снова, потому что get_or_create_nearby_addresses читает старые данные
            # Решение: Увеличиваем задержку до 2 секунд
            import time
            time.sleep(2.0)  # Увеличено с 0.5 до 2.0 сек
            
            # Базовая ставка двери (вечер 21:00–07:00 = 0.5₽)
            current_hour = datetime.now().hour
            base_door_rate = 1.0
            if (current_hour >= 21 or current_hour < 7):
                base_door_rate = 0.5
            address_mult = user_state.get(user_id, {}).get("address_bonus_multiplier", 1.0)
            door_amount = base_door_rate * address_mult
            
            # Запись в 'Отчёты'
            try:
                current_date = datetime.now().strftime("%d.%m.%Y")
                current_time = datetime.now().strftime("%H:%M")
                
                # Получаем ссылку на фото Telegram
                photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{photo_file.file_path}"
                
                new_row = [
                    current_date,
                    str(user_id),
                    selected_address,
                    "1",
                    f"{door_amount:.2f}",
                    district,
                    current_time,
                    "фото входной двери с визиткой",
                    photo_url,  # Ссылка на фото
                    ""
                ]
                if otchety:
                    otchety.append_row(new_row)
                    logging.info(f"✅ Отчёт обновлён: {user_id} | {selected_address} | фото двери (+{door_amount:.2f}₽)")
                    # 💰 Финансы: доход за фото двери
                    try:
                        record_finance_entry(user_id, selected_address, district, "Доход", "Фото двери", 1, door_amount, door_amount, "Фото входной двери")
                    except Exception as e:
                        logging.warning(f"⚠️ Не удалось записать доход (Фото двери): {e}")
                    # ✅ Начисляем оплату за фото двери в баланс
                    try:
                        update_balance(user_id, door_amount)
                        logging.info(f"✅ Баланс обновлён: {user_id} +{door_amount:.2f}₽ (фото двери)")
                    except Exception as e:
                        logging.error(f"❌ Ошибка обновления баланса: {e}")
            except Exception as e:
                logging.error(f"❌ Ошибка записи в 'Отчёты': {e}")
            
            # Списываем листовку
            try:
                deduct_flyers(user_id, 1)
            except Exception as e:
                logging.warning(f"⚠️ Не удалось списать листовки за фото двери: {e}")
            
            # 💸 Финансы: расход за листовку при фото двери
            load_settings()
            unit_cost = float(SETTINGS.get("FLYER_UNIT_COST", "2.50"))
            try:
                record_finance_entry(user_id, selected_address, district, "Расход", "Распространение листовок", 1, unit_cost, unit_cost, "Фото двери")
            except Exception as e:
                logging.warning(f"⚠️ Не удалось записать расход (листовка у двери): {e}")
            
            # Очищаем состояние
            user_state[user_id]["state"] = None
            
            # Показываем ближайшие адреса (НЕ возвращаем в меню!)
            if "current_location" in user_state[user_id]:
                user_lat = user_state[user_id]["current_location"][0]
                user_lng = user_state[user_id]["current_location"][1]
                
                # 📡 Показываем индикатор загрузки
                scan_msg = await update.message.reply_text(
                    "📡 **Сканирование района...**\n\n"
                    "🔍 Анализирую адреса в радиусе 800м...\n\n"
                    "⏰ Подожди ~10 сек!",
                    parse_mode="Markdown"
                )
                
                # Ищем ближайшие адреса (исключаем текущий)
                nearby_addresses = get_or_create_nearby_addresses(user_lat, user_lng, exclude_address=selected_address, limit=MAX_NEARBY_ADDRESSES)
                
                # 🛡️ УДАЛЯЕМ только что обработанный адрес из списка!
                nearby_addresses = [
                    item for item in nearby_addresses 
                    if normalize_text(item[0]) != normalize_text(selected_address)
                ]
                
                # Удаляем сообщение о загрузке
                try:
                    await scan_msg.delete()
                except Exception as e:
                    logging.debug(f"⚠️ Не удалось удалить сообщение: {e}")
                
                if nearby_addresses:
                    # Формируем сообщение с эффектом сканирования
                    result_text = (
                        f"✅ Фото двери принято!\n\n"
                        f"🟡 Адрес {selected_address}: Нет доступа.\n"
                        f"🔎 Сканирую местность поблизости…\n\n"
                        f"💡 Продолжай работу по адресам — либо напиши адрес в чат '🎯 Ян обновит карту!'\n"
                    )
                    # Автоматически назначаем ближайший адрес как если бы пользователь ввёл его в чат
                    nearest_addr, nearest_lat, nearest_lng, nearest_distance, status_icon = nearby_addresses[0]
                    # Сохраняем выбранный адрес
                    user_state[user_id]["selected_address"] = nearest_addr
                    addr_info_nearest = get_address_info(nearest_addr)
                    if addr_info_nearest and len(addr_info_nearest) == 7:
                        user_state[user_id]["address_info"] = addr_info_nearest
                    # Отправляем сообщение о принятии фото
                    await update.message.reply_text(
                        f"✅ **Фото двери принято!**\n\n"
                        f"🟡 Адрес {selected_address}: Нет доступа.\n"
                        f"⏰ Попробуем зайти сюда позже!\n\n"
                        f"🔎 **Следующий адрес:**\n"
                        f"📍 {nearest_addr} ({int(nearest_distance)} м)",
                        parse_mode="Markdown"
                    )
                    # Показываем карточку автоматически назначенного адреса
                    # 🔧 ИСПРАВЛЕНО: Кнопка "Сканировать район" должна запрашивать геолокацию
                    keyboard = [
                        ["🎯 ✅ Я на месте!"],
                        [KeyboardButton("🔍 Сканировать район", request_location=True)],
                        ["Вернуться в меню"]
                    ]
                    route_url = f"https://yandex.ru/maps/?text={nearest_addr.replace(' ', '%20')}"
                    await update.message.reply_text(
                        f"📍 {nearest_addr}\n"  # 🔧 ИСПРАВЛЕНО: убран <b>
                        f"🔑 Расстояние до входа: {int(nearest_distance)} м\n\n"
                        f"🪧 Статус: {status_icon}\n"
                        f"🗺️ <a href='{route_url}'>Маршрут на Яндекс.Картах</a>",
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    )
                    await update.message.reply_text(
                        "💬 Напишите любой адрес в чат, я добавлю его в маршрут"
                    )
                else:
                    # Нет ближайших адресов
                    # KeyboardButton импортируется на уровне модуля
                    keyboard = [
                        ["📍 Добавить адрес"],
                        [KeyboardButton("🔍 Сканировать район", request_location=True)],
                        ["Вернуться в меню"]
                    ]
                    await update.message.reply_text(
                        "✅ Фото двери принято!\n\n"
                        f"🟡 Адрес {selected_address}: Нет доступа.\n"
                        "⏰ Попробуем зайти сюда позже!\n\n"
                        "📍 Добавь новый адрес для работы: просто напиши улицу и номер дома.",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
            else:
                # 📍 Нет геолокации — используем координаты выбранного адреса для поиска соседних подъездов
                # 📡 Показываем индикатор загрузки
                scan_msg = await update.message.reply_text(
                    "📡 **Сканирование района...**\n\n"
                    "🔍 Ищу соседние подъезды...\n\n"
                    "⏰ Подожди ~10 сек!",
                    parse_mode="Markdown"
                )
                
                try:
                    addr_info_no_geo = get_address_info(selected_address)
                    if addr_info_no_geo and len(addr_info_no_geo) == 7:
                        _, sel_lat, sel_lng, _, _, _, _ = addr_info_no_geo
                        nearby_addresses = get_or_create_nearby_addresses(sel_lat, sel_lng, exclude_address=selected_address, limit=MAX_NEARBY_ADDRESSES)
                        # 🛡️ УДАЛЯЕМ только что обработанный адрес!
                        nearby_addresses = [
                            item for item in nearby_addresses 
                            if normalize_text(item[0]) != normalize_text(selected_address)
                        ]
                    else:
                        nearby_addresses = []
                except Exception as e:
                    logging.warning(f"⚠️ Ошибка поиска ближайших адресов без гео: {e}")
                    nearby_addresses = []
                
                # Удаляем сообщение о загрузке
                try:
                    await scan_msg.delete()
                except Exception as e:
                    logging.debug(f"⚠️ Не удалось удалить сообщение: {e}")
                
                if nearby_addresses:
                    # Формируем сообщение
                    result_text = (
                        f"✅ Фото двери принято!\n\n"
                        f"🟡 Адрес {selected_address}: Нет доступа.\n"
                        f"🔎 Сканирую местность поблизости…\n\n"
                        f"🎯 Вот ближайшие адреса для продолжения (соседние подъезды):\n\n"
                    )
                    # Список адресов
                    address_list = []
                    for i, (addr, addr_lat, addr_lng, distance, status_icon) in enumerate(nearby_addresses, 1):
                        address_list.append(f"{status_icon} **{addr}** ({int(distance)} м)")
                    result_text += "\n".join(address_list)
                    result_text += "\n\n👇 Выбери следующий адрес:"
                    
                    # Кнопки с адресами
                    keyboard = []
                    keyboard.append(["📍 Добавить адрес"])  # свой адрес всегда первым
                    for addr, _, _, distance, status_icon in nearby_addresses:
                        keyboard.append([f"{status_icon} {addr} ({int(distance)} м)"])
                    keyboard.append(["Вернуться в меню"])
                    
                    await update.message.reply_text(
                        result_text,
                        parse_mode="Markdown"
                    )
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="Используй кнопки ниже:",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    )
                else:
                    # Нет ближайших адресов
                    # KeyboardButton импортируется на уровне модуля
                    keyboard = [
                        ["📍 Добавить адрес"],
                        [KeyboardButton("🔍 Сканировать район", request_location=True)],
                        ["Вернуться в меню"]
                    ]
                    await update.message.reply_text(
                        "✅ Фото двери принято!\n\n"
                        f"🟡 Адрес {selected_address}: Нет доступа.\n"
                        "⏰ Попробуем зайти сюда позже!\n\n"
                        "📍 Добавь новый адрес для работы: просто напиши улицу и номер дома.",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
        
        # 📸 🚪 Фото двери при ВЫХОДЕ (ОБЯЗАТЕЛЬНОЕ)
        elif state == "awaiting_exit_door_photo":
            # Получаем фото
            photo = update.message.photo[-1]
            photo_file = await context.bot.get_file(photo.file_id)
            
            # Вычисляем SHA-256 хеш
            photo_hash = await get_photo_hash(photo_file)
            
            if not photo_hash:
                await update.message.reply_text(
                    "❌ Ошибка обработки фото. Попробуй ещё раз."
                )
                return
            
            # Проверяем на дубликат
            if is_photo_duplicate(photo_hash):
                await update.message.reply_text(
                    "❌ Это фото уже было загружено!\n\n"
                    "📸 Загрузи другое фото двери с визиткой."
                )
                return
            
            # Добавляем хеш в список
            add_photo_hash(photo_hash)
            
            # Получаем сохранённые данные
            exit_stats = user_state[user_id].get("exit_stats", {})
            photos_uploaded = exit_stats.get("photos_uploaded", 0)
            total_amount = exit_stats.get("total_amount", 0)
            selected_address = exit_stats.get("selected_address", "Неизвестный адрес")
            district = exit_stats.get("district", "Неизвестный")
            
            # 🔥 ВАЖНО: Если total_amount не определён, вычисляем его
            if total_amount == 0 and photos_uploaded > 0:
                photo_price = get_photo_price()
                total_amount = photos_uploaded * photo_price  # 🔧 ИСПРАВЛЕНО: убран bonus_multiplier
            
            # Базовая ставка двери (вечер 21:00–07:00 = 0.5₽)
            current_hour = datetime.now().hour
            base_door_rate = 1.0
            if (current_hour >= 21 or current_hour < 7):
                base_door_rate = 0.5
            door_amount = base_door_rate  # 🔧 ИСПРАВЛЕНО: убран address_mult

            # Записываем фото двери в отчёт
            try:
                current_date = datetime.now().strftime("%d.%m.%Y")
                current_time = datetime.now().strftime("%H:%M")
                
                # Получаем ссылку на фото Telegram
                photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{photo_file.file_path}"
                
                new_row = [
                    current_date,
                    str(user_id),
                    selected_address,
                    "1",  # 1 фото двери
                    f"{door_amount:.2f}",  # Оплачивается по базовой ставке двери
                    district,
                    current_time,
                    "фото входной двери с визиткой",
                    photo_url  # Ссылка на фото
                ]
                
                if otchety:
                    otchety.append_row(new_row)
                    logging.info(f"✅ Отчёт обновлён: {user_id} | {selected_address} | фото двери (+{door_amount:.2f}₽)")
                    # 💰 Финансы: доход за фото двери
                    try:
                        record_finance_entry(user_id, selected_address, district, "Доход", "Фото двери", 1, door_amount, door_amount, "Фото входной двери (выход)")
                    except Exception as e:
                        logging.warning(f"⚠️ Не удалось записать доход (Фото двери): {e}")
                
                # ✅ Начисляем оплату за фото двери в баланс
                try:
                    update_balance(user_id, door_amount)
                    logging.info(f"✅ Баланс обновлён: {user_id} +{door_amount:.2f}₽ (фото двери)")
                except Exception as e:
                    logging.error(f"❌ Ошибка обновления баланса: {e}")
                
                # Списываем 1 листовку
                try:
                    deduct_flyers(user_id, 1)
                    # 💸 Финансы: расход за листовку при фото двери
                    load_settings()
                    unit_cost = float(SETTINGS.get("FLYER_UNIT_COST", "2.50"))
                    try:
                        record_finance_entry(user_id, selected_address, district, "Расход", "Распространение листовок", 1, unit_cost, unit_cost, "Фото двери (выход)")
                    except Exception as e:
                        logging.warning(f"⚠️ Не удалось записать расход (листовка у двери): {e}")
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось списать листовку за фото двери: {e}")
            except Exception as e:
                logging.error(f"❌ Ошибка записи в 'Отчёты': {e}")
            
            # Обновляем статус в Справочнике
            update_address_status(selected_address, "🟢 Показы идут", photos_count=photos_uploaded + 1)
            
            # 🔧 ИСПРАВЛЕНО: Даём Google Sheets время обновиться (защита от повторного показа адреса)
            import time
            time.sleep(0.5)
            
            # Обновляем сессионный счётчик (завершённый адрес)
            update_session_stats(user_id, addresses=1)
            stats = get_session_stats(user_id)
            
            # 🎁 ПРОВЕРКА И НАЧИСЛЕНИЕ БОНУСА! (с проактивным уведомлением)
            bonus_message = check_and_award_bonus(user_id, context=context)
            
            # 🔥 НОВОЕ: Спрашиваем о количестве уже наклеенных листовок (узнаём количество щитов)
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            keyboard = []
            row = []
            for i in range(0, 11):  # От 0 до 10
                row.append(InlineKeyboardButton(str(i), callback_data=f"existing_flyers_{i}"))
                if (i + 1) % 5 == 0:  # 5 кнопок в ряду
                    keyboard.append(row)
                    row = []
            if row:  # Добавляем оставшиеся кнопки
                keyboard.append(row)
            # Добавляем кнопку "Пропустить"
            keyboard.append([InlineKeyboardButton("➡️ Пропустить", callback_data="existing_flyers_skip")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Сохраняем данные для использования после ответа
            user_state[user_id]["state"] = "awaiting_existing_flyers_count"
            user_state[user_id]["exit_stats"] = exit_stats  # Сохраняем статистику
            
            await update.message.reply_text(
                f"📸 Фото двери принято!\n\n"
                f"📍 <b>{selected_address}</b>\n\n"
                f"📊 Помоги нам отследить конкуренцию!\n\n"
                f"📄 <b>Сколько электрощитов с НАШИМИ листовками здесь уже было?</b>\n"
                f"(до твоей работы)\n\n"
                f"🔢 Выбери количество:",
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            
            # 🎁 Если бонус начислен - отправляем уведомление!
            if bonus_message:
                await update.message.reply_text(
                    bonus_message,
                    parse_mode="Markdown"
                )
            
            # Показываем ближайшие адреса (НЕ возвращаем в меню!)
            if "current_location" in user_state[user_id]:
                user_lat = user_state[user_id]["current_location"][0]
                user_lng = user_state[user_id]["current_location"][1]
                
                # Ищем ближайшие адреса (исключаем текущий) в радиусе 1 км
                nearby_addresses = get_or_create_nearby_addresses(user_lat, user_lng, exclude_address=selected_address, limit=MAX_NEARBY_ADDRESSES)
                
                # 🔧 ИСПРАВЛЕНО: Двойная фильтрация — ОБЯЗАТЕЛЬНО исключаем только что обработанный адрес!
                # Защита от race condition с Google Sheets
                nearby_addresses = [
                    item for item in nearby_addresses 
                    if normalize_text(item[0]) != normalize_text(selected_address)
                ]
                
                if nearby_addresses:
                    # Рассчитываем текущий бонус активности
                    streak_days = get_work_streak(user_id)
                    activity_bonus_percent = min(streak_days * 10, 50)  # +10% за день, максимум +50%
                    
                    # Формируем сообщение
                    result_text = (
                        f"✅ **Работа завершена!**\n\n"
                        f"📬 Баланс успешно пополнен\n"
                        f"💰 Начислено: **{total_amount + door_amount:.2f}₽** ({photos_uploaded + 1} фото)\n"
                        f"📦 Списано листовок: {photos_uploaded + 1} шт\n\n"  # +1 за фото двери
                        f"📈 **Сессия:** {stats['addresses']} адресов | {stats['photos']} фото | {stats['earnings']}₽\n"
                        f"🔥 **Активность:** +{activity_bonus_percent}%\n\n"
                        f"🎯 **Вот ближайшие адреса для продолжения:**\n\n"
                    )
                    
                    address_list = []
                    for i, (addr, addr_lat, addr_lng, distance, status_icon) in enumerate(nearby_addresses, 1):
                        address_list.append(f"{status_icon} **{addr}** ({int(distance)} м)")
                    
                    result_text += "\n".join(address_list)
                    result_text += "\n\n🚀 Ты на волне! Продолжай зарабатывать →"
                    
                    # Кнопки с адресами
                    keyboard = []
                    # Кнопка добавления своего адреса - всегда первая
                    keyboard.append(["📍 Добавить адрес"])
                    
                    for addr, _, _, distance, status_icon in nearby_addresses:
                        keyboard.append([f"{status_icon} {addr} ({int(distance)} м)"])
                    
                    keyboard.append(["Вернуться в меню"])
                    
                    await update.message.reply_text(
                        result_text,
                        parse_mode="Markdown",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    )
                else:
                    # Нет ближайших адресов
                    # KeyboardButton импортируется на уровне модуля
                    keyboard = [
                        [KeyboardButton("🔍 Сканировать район", request_location=True)],
                        ["📍 Добавить адрес"],
                        ["Вернуться в меню"]
                    ]
                    
                    await update.message.reply_text(
                        f"✅ **Работа завершена!**\n\n"
                        f"📬 Баланс успешно пополнен\n"
                        f"💰 Начислено: **{total_amount + door_amount:.2f}₽** ({photos_uploaded + 1} фото)\n"
                        f"📦 Списано листовок: {photos_uploaded + 1} шт\n\n"  # +1 за фото двери
                        f"📈 **Сессия:** {stats['addresses']} адресов | {stats['photos']} фото | {stats['earnings']}₽\n\n"
                        f"👏 Отличная работа! Переместись в другое место или вернись в меню.",
                        parse_mode="Markdown",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                    )
            else:
                # Нет геолокации
                keyboard = [
                    ["📍 Добавить адрес"],
                    ["Вернуться в меню"]
                ]
                
                await update.message.reply_text(
                    f"✅ **Работа завершена!**\n\n"
                    f"📬 Баланс успешно пополнен\n"
                    f"💰 Начислено: **{total_amount + door_amount:.2f}₽** ({photos_uploaded + 1} фото)\n"
                    f"📦 Списано листовок: {photos_uploaded + 1} шт\n\n"  # +1 за фото двери
                    f"📈 **Сессия:** {stats['addresses']} адресов | {stats['photos']} фото | {stats['earnings']}₽\n\n"
                    f"👏 Отличная работа!\n\n"
                    f"📍 Добавь новый адрес для продолжения работы!",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            
        # 📸 Фото электрощитов
        elif state == "awaiting_photos":
            # 🔥 ЗАЩИТА ОТ МАССОВОЙ ОТПРАВКИ: проверяем таймаут между фото
            import time
            current_time = time.time()
            last_photo_time = user_state[user_id].get("last_photo_time", 0)
            
            # Минимум 0.5 секунды между фото (ускоренный процесс)
            if current_time - last_photo_time < 0.5:
                await update.message.reply_text(
                    "⚠️ Погоди секунду! 📸"
                )
                return
            
            # Обновляем время последнего фото
            user_state[user_id]["last_photo_time"] = current_time
            
            # Получаем файл фото
            photo = update.message.photo[-1]  # Самое большое разрешение
            photo_file = await context.bot.get_file(photo.file_id)
            
            # Вычисляем SHA-256 хеш
            photo_hash = await get_photo_hash(photo_file)
            
            if not photo_hash:
                await update.message.reply_text(
                    "❌ Ошибка обработки фото. Попробуй ещё раз."
                )
                return
            
            # Проверяем на дубликат
            if is_photo_duplicate(photo_hash):
                await update.message.reply_text(
                    "❌ Это фото уже было загружено!\n\n"
                    "📸 Загрузи другое фото электрощита."
                )
                return
            
            add_photo_hash(photo_hash)
            
            # 🛡️ АНТИ-ФРОД: проверка времени сессии и геолокации
            now_utc = datetime.utcnow()
            load_settings()
            max_minutes = int(SETTINGS.get("SESSION_MAX_MINUTES", "25"))
            session_started_at = user_state[user_id].get("session_started_at")
            # 🔧 ИСПРАВЛЕНО: преобразуем в naive если aware
            if isinstance(session_started_at, datetime) and session_started_at.tzinfo:
                session_started_at = session_started_at.replace(tzinfo=None)
            if not session_started_at or now_utc > session_started_at + timedelta(minutes=max_minutes):
                await update.message.reply_text(
                    "⏰ **Сессия истекла**\n\n"
                    "🔄 Чтобы продолжить работу:\n"
                    "1️⃣ Отправь геолокацию (кнопка '🔍 Сканировать район')\n"
                    "2️⃣ Выбери адрес\n"
                    "3️⃣ Нажми '🎯 Я на месте!'",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
                user_state[user_id]["state"] = None
                return
            msg_time = getattr(update.message, "date", None)
            load_settings()
            future_grace = int(SETTINGS.get("PHOTO_FUTURE_GRACE_SECONDS", "30"))
            # 🔧 ИСПРАВЛЕНО: преобразуем msg_time в naive datetime для сравнения
            if msg_time:
                msg_time_utc = msg_time.replace(tzinfo=None)  # Убираем timezone
                if msg_time_utc > (now_utc + timedelta(seconds=future_grace)):
                    await update.message.reply_text("❌ Фото отклонено: время сообщения из будущего.", reply_markup=get_main_menu_keyboard())
                    return
            loc_time = user_state[user_id].get("current_location_time")
            load_settings()
            loc_max_age = int(SETTINGS.get("LOCATION_MAX_AGE_MINUTES", "40"))
            if not loc_time or now_utc > loc_time + timedelta(minutes=loc_max_age):
                await update.message.reply_text(
                    "📍 Геолокация устарела. Отправь текущую геолокацию кнопкой «🔍 Сканировать район».",
                    reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔍 Сканировать район", request_location=True)],["Вернуться в меню"]], resize_keyboard=True)
                )
                return
            
            photos_uploaded = user_state[user_id].get("photos_uploaded", 0)
            min_photos = user_state[user_id].get("min_photos", MIN_PHOTOS_REQUIRED)
            
            photos_uploaded += 1
            user_state[user_id]["photos_uploaded"] = photos_uploaded
            
            # 🚫 Анти-фрод: более 30 фото в рамках одной сессии — блокируем отчёт и уведомляем админа
            if photos_uploaded > 30:
                try:
                    # Сообщение пользователю
                    await update.message.reply_text(
                        "🚫 Подозрительная активность\n\n"
                        "📸 Добавлено слишком много фото за один адрес (более 30).\n"
                        "🔔 История работы передана в службу безопасности для проверки.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    # Уведомление админам
                    now_dt = datetime.now()
                    current_date = now_dt.strftime("%d.%m.%Y")
                    current_time = now_dt.strftime("%H:%M")
                    selected_address = user_state[user_id].get("selected_address", "Неизвестный адрес")
                    alert_text = (
                        f"⚠️ ПОДОЗРИТЕЛЬНАЯ АКТИВНОСТЬ\n\n"
                        f"📅 Дата: {current_date}\n"
                        f"⏰ Время: {current_time}\n"
                        f"👤 Промоутер ID: `{user_id}`\n"
                        f"📍 Адрес: {selected_address}\n"
                        f"📸 Фото за сессию: {photos_uploaded}\n"
                        f"📝 Причина: превышение лимита (более 30 фото)"
                    )
                    for admin_id in ADMIN_IDS:
                        try:
                            await context.bot.send_message(chat_id=admin_id, text=alert_text, parse_mode="Markdown")
                        except Exception:
                            pass
                except Exception:
                    pass
                # Завершаем сессию
                user_state[user_id]["state"] = None
                return
            
            # Получаем информацию об адресе
            selected_address = user_state[user_id].get("selected_address", "Неизвестный адрес")
            addr_info = user_state[user_id].get("address_info")
            # ЗАЩИТА: Проверяем, что addr_info существует и имеет правильную длину
            district = addr_info[3] if (addr_info and len(addr_info) > 3) else "Неизвестный"
            
            # Получаем цену за фото
            photo_price = get_photo_price()  # 🔧 ИСПРАВЛЕНО: убран bonus_multiplier (фиксированная ставка 3₽)
            
            # 🔧 ОПТИМИЗАЦИЯ UX: Обновляем сессионную статистику СРАЗУ (в памяти, быстро)
            update_session_stats(user_id, photos=1, earnings=photo_price)
            stats = get_session_stats(user_id)
            total_amount = stats['earnings']
            
            session_target = user_state[user_id].get("session_target_photos", MIN_PHOTOS_REQUIRED)
            # Прогресс-бар (до 15 фото)
            filled = min(int((photos_uploaded / session_target) * 10), 10)
            progress_bar = "█" * filled + "░" * (10 - filled)
            percentage = min(int((photos_uploaded / session_target) * 100), 100)
            
            # 🎮 ГЕЙМИФИКАЦИЯ: Разные сообщения в зависимости от прогресса
            if photos_uploaded == 1:
                first_photo_messages = [
                    "🎊 УРА! Первое фото в деле! Ты молодец!",
                    "⚡ БИНГО! Отличное начало! Так держать!",
                    "🌟 КРАСАВА! Первый шаг сделан — дальше легче!",
                    "🎯 ПОПАЛ! Теперь ты в игре! Вперёд к новым высотам!",
                    "🔥 ПОЕХАЛИ! Ты запустил процесс — это круто!"
                ]
                motivational_messages = first_photo_messages
            elif photos_uploaded == 2:
                second_photo_messages = [
                    "💪 О ДА! Два фото — это уже серьёзно!",
                    "🚀 РАЗГОНЯЕШЬСЯ! Каждое фото приближает к цели!",
                    "⭐ МАСТЕР! Ты в потоке — продолжай!",
                    "🎉 КЛАСС! Темп набран — давай дальше!"
                ]
                motivational_messages = second_photo_messages
            elif photos_uploaded == 3:
                third_photo_messages = [
                    "🏆 ТРИ В РЯД! Ты на коне! Продолжай в том же духе!",
                    "✨ ТРОЙНОЙ УДАР! Это уже мастерство!",
                    "🎯 ТРИ ПОПАДАНИЯ! Ты профессионал!",
                    "🔥 КОМБО х３! Невероятный темп!"
                ]
                motivational_messages = third_photo_messages
            elif photos_uploaded >= session_target:
                goal_reached_messages = [
                    "🏅 ЦЕЛЬ ДОСТИГНУТА! Ты просто ЧЕМПИОН!",
                    "👑 КОРОЛЬ/КОРОЛЕВА! Минимум выполнен на 100%!",
                    "🌟 ЗВЕЗДА ПРОМОУТИНГА! Ты достиг цели!",
                    "💎 ЛЕГЕНДА! План выполнен — ты лучший!"
                ]
                motivational_messages = goal_reached_messages
            else:
                regular_messages = [
                    "🔥 ОГОНЬ! Продолжай — каждое фото это ДЕНЬГИ!",
                    "💰 ЧИК-ЧИК! Твой баланс растёт прямо сейчас!",
                    "⚡ ЭНЕРГИЯ! Ты делаешь это потрясающе!",
                    "🎯 ТОЧНО В ЦЕЛЬ! Каждое фото — шаг к успеху!",
                    "🚀 КОСМОС! Ты на правильном пути!",
                    "💪 СИЛА! Ещё немного и результат превзойдёт ожидания!",
                    "🌈 КРАСОТА! Ты создаёшь что-то важное!",
                    "⭐ БЛЕСК! Каждый щит — это твоя работа!"
                ]
                motivational_messages = regular_messages
            import random
            motivation = random.choice(motivational_messages)
            
            # 🔧 ОПТИМИЗАЦИЯ UX: ОТПРАВЛЯЕМ СООБЩЕНИЕ СРАЗУ (до Google Sheets)
            if photos_uploaded < session_target:
                # 🔥 После первого фото показываем кнопку "Завершить этап"
                if photos_uploaded == 1:
                    await update.message.reply_text(
                        f"✅ Первое фото ПРИНЯТО!\n\n"
                        f"{motivation}\n\n"
                        f"💵 +{photo_price:.0f}₽ → Твой баланс растёт!\n\n"
                        f"🚀 Продолжай работу или заверши этап!",
                        reply_markup=ReplyKeyboardMarkup([["📸 Зафиксировать листовку"],["🎉 Завершить этап"]], resize_keyboard=True)
                    )
                elif photos_uploaded == 2:
                    await update.message.reply_text(
                        f"✨ Фото #{photos_uploaded} ЗАСЧИТАНО!\n\n"
                        f"{motivation}\n\n"
                        f"💰 Уже заработано: +{total_amount:.0f}₽\n"
                        f"📊 Прогресс: {progress_bar} {percentage}%\n\n"
                        f"🔥 Ещё {session_target - photos_uploaded} фото до цели!",
                        reply_markup=ReplyKeyboardMarkup([["📸 Зафиксировать листовку"],["🎉 Завершить этап"]], resize_keyboard=True)
                    )
                elif photos_uploaded == 3:
                    await update.message.reply_text(
                        f"🎊 Фото #{photos_uploaded} В ЗАЧЁТЕ!\n\n"
                        f"{motivation}\n\n"
                        f"💎 Заработано: +{total_amount:.0f}₽\n"
                        f"🎯 {progress_bar} {percentage}%\n\n"
                        f"⚡ Осталось всего {session_target - photos_uploaded} фото!",
                        reply_markup=ReplyKeyboardMarkup([["📸 Зафиксировать листовку"],["🎉 Завершить этап"]], resize_keyboard=True)
                    )
                else:
                    await update.message.reply_text(
                        f"✅ Фото #{photos_uploaded} ГОТОВО!\n\n"
                        f"{motivation}\n\n"
                        f"💵 Сумма: {total_amount:.0f}₽\n"
                        f"📈 {progress_bar} {percentage}%",
                        reply_markup=ReplyKeyboardMarkup([["📸 Зафиксировать листовку"],["🎉 Завершить этап"]], resize_keyboard=True)
                    )
            else:
                # 🏆 МИНИМУМ ВЫПОЛНЕН - ПРАЗДНИК!
                keyboard = [["📸 Зафиксировать листовку"],["🎉 Завершить этап"]]
                # Специальные награды за перевыполнение
                if photos_uploaded > session_target + 2:
                    celebration = "🎆🏆 ПЕРЕВЫПОЛНЕНИЕ! Ты превзошёл себя!"
                elif photos_uploaded > session_target:
                    celebration = "🌟 БОЛЬШЕ ПЛАНА! Так держать!"
                else:
                    celebration = "🎊 ЦЕЛЬ ДОСТИГНУТА! Это победа!"
                
                await update.message.reply_text(
                    f"{celebration}\n\n"
                    f"{motivation}\n\n"
                    f"📸 Фото щитков: {photos_uploaded}\n"  # 🔧 ИСПРАВЛЕНО: "Фото сегодня"→"Фото щитков"
                    f"💰 Заработано: +{total_amount:.0f}₽\n"
                    f"📊 Прогресс: {progress_bar} {percentage}%\n\n"
                    f"✨ Ты можешь продолжить или завершить этап!",  # 🔧 ИСПРАВЛЕНО: убрана последняя строка
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                )
            
            # 📊 ТЕПЕРЬ ЗАПИСЫВАЕМ В GOOGLE SHEETS (в фоне, после отправки сообщения):
            
            # 1. Записываем в "Отчёты" (каждое фото отдельной строкой)
            try:
                current_date = datetime.now().strftime("%d.%m.%Y")
                current_time = datetime.now().strftime("%H:%M")
                
                # Получаем ссылку на фото Telegram
                photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{photo_file.file_path}"
                
                # Структура: [Дата, Промоутер, Адрес, Фото, Сумма, Район, Время, Комментарий, Ссылка на фото]
                new_row = [
                    current_date,
                    str(user_id),
                    selected_address,
                    "1",
                    f"{photo_price:.2f}",
                    district,
                    current_time,
                    f"фото электрощита, подъезд №{user_state[user_id].get('entrance_number', '-') }",
                    photo_url,  # Ссылка на фото
                    ""
                ]
                
                if otchety:
                    otchety.append_row(new_row)
                    logging.info(f"✅ Отчёт обновлён: {user_id} | {selected_address} | фото #{photos_uploaded}")
                    # 💰 Финансы: доход за фото электрощита
                    try:
                        record_finance_entry(user_id, selected_address, district, "Доход", "Фото щитов", 1, photo_price, photo_price, f"Фото электрощита #{photos_uploaded}")
                    except Exception as e:
                        logging.warning(f"⚠️ Не удалось записать доход (Фото щитов): {e}")
            except Exception as e:
                logging.error(f"❌ Ошибка записи в 'Отчёты': {e}")
            
            # 2. Начисляем деньги в "Балансы"
            try:
                update_balance(user_id, photo_price)
                logging.info(f"✅ Баланс обновлён: {user_id} +{photo_price:.2f}₽")  # 🔧 ИСПРАВЛЕНО: убран множитель
            except Exception as e:
                logging.error(f"❌ Ошибка обновления баланса: {e}")
            
            # 3. Списываем листовки
            try:
                # 🔧 ИСПРАВЛЕНО: убран address_multiplier (фиксированная ставка)
                effective_panel_rate = 3.0
                
                # Списываем листовку за фото (без дополнительной оплаты здесь)
                deduct_flyers(user_id, 1)  # 1 листовка за 1 фото
                logging.info(f"✅ Листовки списаны: {user_id} -1 шт (по {effective_panel_rate:.1f}₽ +{int((activity_multiplier - 1.0)*100)}%)")
                # 💸 Финансы: расход на распространение при фото щита
                load_settings()
                unit_cost = float(SETTINGS.get("FLYER_UNIT_COST", "2.50"))
                try:
                    record_finance_entry(user_id, selected_address, district, "Расход", "Распространение листовок", 1, unit_cost, unit_cost, f"Фото электрощита #{photos_uploaded}")
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось записать расход (листовка при щите): {e}")
            except Exception as e:
                logging.error(f"❌ Ошибка списания листовок: {e}")
            
            # 🔧 ИСПРАВЛЕНО: Убран дублирующий блок отправки сообщений (строки 4441-4556)
            # Сообщения уже отправлены в блоке 4323-4379
        else:
            await update.message.reply_text(
                "❌ Сначала выбери адрес и начни работу!",
                reply_markup=ReplyKeyboardRemove()
            )
            
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_photo(): {e}")
        # 🔧 ИСПРАВЛЕНО: Добавлены кнопки меню при ошибке
        await update.message.reply_text(
            "❌ Произошла ошибка при обработке фото. Попробуйте позже.",
            reply_markup=get_main_menu_keyboard(update.effective_user.id)
        )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений (кнопок меню)"""
    try:
        text = update.message.text
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # ОТЛАДКА: Логируем ВСЕ текстовые сообщения
        logging.info(f"📨 handle_text_message: user={user_id}, text='{text}'")

        # 👑 Админ: ввод категории и суммы внепланового расхода
        if user_state.get(user_id, {}).get("state") == "awaiting_expense_category":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ У тебя нет прав администратора!")
                user_state[user_id]["state"] = None
                return
            category_text = text.strip()
            if not category_text:
                await update.message.reply_text("❌ Введите название категории расхода, например: Логистика")
                return
            user_state[user_id]["expense_category"] = category_text
            user_state[user_id]["state"] = "awaiting_expense_amount"
            await update.message.reply_text("💸 Введите сумму расхода (₽), например: 1234.56")
            return

        # 👑 Админ: ввод суммы внепланового расхода
        if user_state.get(user_id, {}).get("state") == "awaiting_expense_amount":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ У тебя нет прав администратора!")
                user_state[user_id]["state"] = None
                return
            try:
                amount = float(text.replace(",", ".").strip())
            except Exception:
                await update.message.reply_text("❌ Введите сумму в ₽, например: 1234.56")
                return
            category = user_state[user_id].get("expense_category", "Внеплановый расход")
            ok = record_finance_entry(user_id, "", "Общий", "Расход", category, 1, amount, amount, "Ад-хок расход")
            user_state[user_id]["state"] = None
            if ok:
                await update.message.reply_text(f"✅ Расход записан: {amount:.2f}₽ ({category})", reply_markup=get_main_menu_keyboard())
            else:
                await update.message.reply_text("❌ Не удалось записать расход", reply_markup=get_main_menu_keyboard())
            return

        # 📸 Подсказка при ожидании фото двери ("Нет доступа")
        if user_state.get(user_id, {}).get("state") == "awaiting_door_photo":
            # Пользователь написал текст вместо фото - даём подсказку
            await update.message.reply_text(
                "📸 Пожалуйста, отправь ФОТО входной двери с визиткой Балтсеть³⁹\n\n"
                "📄 Как добавить фото:\n"
                "• Нажми на значок 📎 (скрепка) внизу\n"
                "• Выбери '🖼️ Фото или видео'\n"
                "• Сделай фото или выбери из галереи\n"
                "• Отправь фото в чат\n\n"
                "⚠️ Отправляй как ФОТО, а не как файл!",
                reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"], ["❌ Отмена"], ["Вернуться в меню"]], resize_keyboard=True)
            )
            return
        
        # 📸 Подсказка при ожидании фото двери (при выходе)
        if user_state.get(user_id, {}).get("state") == "awaiting_exit_door_photo":
            # Пользователь написал текст вместо фото - даём подсказку
            await update.message.reply_text(
                "📸 Пожалуйста, отправь ФОТО входной двери с визиткой Балтсеть³⁹\n\n"
                "📄 Как добавить фото:\n"
                "• Нажми на значок 📎 (скрепка) внизу\n"
                "• Выбери '🖼️ Фото или видео'\n"
                "• Сделай фото или выбери из галереи\n"
                "• Отправь фото в чат\n\n"
                "⚠️ Отправляй как ФОТО, а не как файл!",
                reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"], ["❌ Отмена"], ["Вернуться в меню"]], resize_keyboard=True)
            )
            return
        
        # 📸 Подсказка при ожидании фото электрощитов (после "Да!")
        # 🔧 ИСПРАВЛЕНО: Пропускаем команды кнопок, показываем подсказку только для обычного текста
        if user_state.get(user_id, {}).get("state") == "awaiting_photos":
            # Проверяем, не является ли текст командой кнопки
            control_buttons = ["💾 Сохранить", "🎉 Завершить этап", "❌ Отмена", "Вернуться в меню", 
                             "📸 Зафиксировать листовку", "📤 Добавить несколько фото"]
            if text not in control_buttons:
                # Пользователь написал текст вместо фото - даём подсказку
                selected_address = user_state[user_id].get("selected_address", "Адрес")
                await update.message.reply_text(
                    f"📸 Отлично! Ты работаешь по адресу:\n"
                    f"📍 <b>{selected_address}</b>\n\n"
                    f"📸 Как добавить фото в Telegram:\n"
                    f"• Нажми на значок 📎 (скрепка) внизу\n"
                    f"• Выбери '🖼️ Фото или видео'\n"
                    f"• Сделай фото электрощита с листовкой\n"
                    f"• Отправь фото в чат (не как документ!)\n\n"
                    "⚠️ Отправляй как ФОТО, а не как файл!\n\n"
                    f"💾 Когда закончишь - нажми '💾 Сохранить'",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"], ["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
                )
                return
        
        # 🎯 Подсказка на этапе "Есть доступ в подъезд?" если пользователь пишет текст
        if user_state.get(user_id, {}).get("state") == "awaiting_access_answer":
            # Проверяем, не является ли текст командой кнопки
            control_buttons = ["✅ Да!", "🚪 Нет доступа", "Вернуться в меню", "📍 Исправить координаты"]
            if text not in control_buttons:
                selected_address = user_state[user_id].get("selected_address", "Адрес")
                try:
                    await update.message.reply_photo(
                        photo="https://disk.yandex.ru/i/5IsEqKDk2lopxg",
                        caption=(
                            f"🎯 Есть ли доступ в подъезд?\n\n"
                            f"📍 <b>{selected_address}</b>\n\n"
                            f"✅ Да, если удалось проникнуть внутрь"
                        ),
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardMarkup([["✅ Да!", "🚪 Нет доступа"], ["Вернуться в меню"]], resize_keyboard=True)
                    )
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось отправить фото подсказки: {e}")
                    await update.message.reply_text(
                        f"🎯 Есть ли доступ в подъезд?\n\n"
                        f"📍 <b>{selected_address}</b>\n\n"
                        f"✅ Да, если удалось проникнуть внутрь",
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardMarkup([["✅ Да!", "🚪 Нет доступа"], ["Вернуться в меню"]], resize_keyboard=True)
                    )
                return

        # 🚫 Во время работы по адресу запрещаем менять адрес или начинать новый поток
        current_state = user_state.get(user_id, {}).get("state")
        working_states = {"awaiting_access_answer", "awaiting_photos", "awaiting_door_photo", "awaiting_exit_door_photo"}
        if current_state in working_states:
            if text in {"Начать работу 🚀", "📍 Добавить адрес"} or looks_like_address(text):
                # 🔧 ИСПРАВЛЕНО: Получаем реальное название адреса
                current_address = user_state.get(user_id, {}).get("selected_address") or user_state.get(user_id, {}).get("current_address", "текущий адрес")
                # Предлагаем продолжить по текущей цепочке
                if current_state == "awaiting_photos":
                    keyboard = ReplyKeyboardMarkup([["📸 Зафиксировать листовку", "📤 Добавить несколько фото"],["💾 Сохранить"]], resize_keyboard=True)
                    msg = (
                        f"🚫 Сейчас идёт работа по адресу: {current_address}\n\n"
                        "📸 Заверши фотоотчёт, затем можно сменить адрес."
                    )
                elif current_state == "awaiting_access_answer":
                    keyboard = ReplyKeyboardMarkup([["✅ Да!", "🚪 Нет доступа"],["Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
                    msg = (
                        f"🚫 Сейчас идёт работа по адресу: {current_address}\n\n"
                        "🚪 Есть ли доступ в подъезд?"
                    )
                else:
                    keyboard = get_main_menu_keyboard()
                    msg = (
                        "🚫 Сначала заверши текущий этап, затем можно сменить адрес."
                    )
                await update.message.reply_text(msg, reply_markup=keyboard)
                return
        # 💡 Обработка фидбека "Есть идея?"
        if user_state.get(user_id, {}).get("state") == "awaiting_feedback_idea":
            idea_text = text.strip()
            user_state[user_id]["state"] = None
            logging.info(f"💡 Идея от {user_id}: {idea_text}")
            await update.message.reply_text("✅ Спасибо! Идея принята.")
            # 📧 Уведомление на почту администратору
            try:
                import smtplib
                from email.mime.text import MIMEText
                msg = MIMEText(f"Идея от пользователя {user_id}:\n\n{idea_text}", "plain", "utf-8")
                msg["Subject"] = "Новая идея от промоутера"
                msg["From"] = "bot@promobot.local"
                msg["To"] = "electro.me@yandex.ru"
                with smtplib.SMTP("localhost") as s:
                    s.send_message(msg)
                logging.info("📧 Идея отправлена на email electro.me@yandex.ru")
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить email с идеей: {e}")
            return
        
        # 🆘 Обработка отчета об ошибке
        if text == "🆘 Сообщить о проблеме":
            user_state[user_id] = user_state.get(user_id, {})
            user_state[user_id]["awaiting_error_report"] = True
            await update.message.reply_text(
                "📝 Опиши проблему:\n\n"
                "• Что ты делал?\n"
                "• Что пошло не так?\n"
                "• Какой адрес? (если актуально)\n\n"
                "💡 Отправь сообщение с описанием.",
                reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
            )
            return
        
        # 📝 Прием текста отчета об ошибке
        if user_state.get(user_id, {}).get("awaiting_error_report"):
            error_description = text.strip()
            user_state[user_id]["awaiting_error_report"] = False
            
            # 📧 Отправляем отчет на email
            try:
                import smtplib
                from email.mime.text import MIMEText
                
                # Собираем информацию о состоянии пользователя
                user_info = user_state.get(user_id, {})
                current_state = user_info.get("state", "Нет")
                current_address = user_info.get("current_address", "Нет")
                username = update.effective_user.username or "Нет"
                
                email_body = (
                    f"🆘 ОТЧЕТ ОБ ОШИБКЕ\n"
                    f"{'='*50}\n\n"
                    f"👤 User ID: {user_id}\n"
                    f"📛 Username: @{username}\n"
                    f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                    f"📊 Состояние бота:\n"
                    f"  • State: {current_state}\n"
                    f"  • Адрес: {current_address}\n\n"
                    f"📝 Описание проблемы:\n"
                    f"{error_description}\n\n"
                    f"{'='*50}\n"
                )
                
                msg = MIMEText(email_body, "plain", "utf-8")
                msg["Subject"] = f"🆘 Отчет об ошибке от {user_id}"
                msg["From"] = "bot@promobot.local"
                msg["To"] = ERROR_REPORT_EMAIL
                
                with smtplib.SMTP("localhost") as s:
                    s.send_message(msg)
                
                logging.info(f"📧 Отчет об ошибке отправлен: {user_id}")
                
                await update.message.reply_text(
                    "✅ Спасибо! Отчет отправлен разработчику.\n\n"
                    "🔧 Мы разберемся с проблемой в ближайшее время.",
                    reply_markup=get_main_menu_keyboard()
                )
            except Exception as e:
                logging.error(f"❌ Ошибка отправки email с отчетом: {e}")
                await update.message.reply_text(
                    "⚠️ Не удалось отправить отчет.\n\n"
                    "📞 Свяжись с администратором напрямую.",
                    reply_markup=get_main_menu_keyboard()
                )
            return

        # ❌ Отмена (на любом этапе)
        if text in ["❌ Отмена", "Отмена", "отмена"]:
            current_state = user_state.get(user_id, {}).get("state")
            
            # 🔧 ИСПРАВЛЕНО: Всегда возвращаем в меню при awaiting_door_photo и awaiting_exit_door_photo
            if current_state in ["awaiting_door_photo", "awaiting_exit_door_photo"]:
                user_state[user_id]["state"] = None
                user_state[user_id]["awaiting_error_report"] = False  # 🔧 Очищаем флаг
                await update.message.reply_text(
                    "❌ Отменено.\n\n"
                    "🏠 Возвращаюсь в главное меню.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # 🔥 НОВОЕ: Остальные случаи - очищаем состояние и возвращаем в меню (без команды /start)
            user_state[user_id] = {"state": None}
            user_name = get_user_name_from_balances(user_id) or update.effective_user.first_name
            await update.message.reply_text(
                f"❌ Отменено.\n\n"
                f"✅ Привет, {user_name}! Используй кнопки меню для работы.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        # Проверка регистрации
        if not is_user_registered(user_id):
            await update.message.reply_text(
                "❌ Сначала зарегистрируйся! Нажми /start",
                reply_markup=get_keyboard_login()
            )
            return

        # Начать работу 🚀 → сразу запрашиваем геолокацию
        if text == "Начать работу 🚀":
            # 🔥 ИСПРАВЛЕНО: НЕ вызываем /start, обрабатываем как обычную кнопку
            # Проверяем баланс листовок
            flyer_balance = get_flyer_balance(user_id)
            if flyer_balance <= 0:
                await update.message.reply_text(
                    "❗ У тебя нет листовок.\n\n"
                    "Нажми «📦 Запросить листовки» и дождись подтверждения от админа.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Листовки есть - запрашиваем геолокацию для сканирования
            keyboard = [
                [KeyboardButton("🔍 Сканировать район", request_location=True)],
                ["Вернуться в меню"]
            ]
            try:
                await update.message.reply_photo(
                    photo="https://disk.yandex.ru/i/6DjXrMN5aH5p-Q",
                    caption=(
                        "📍 Добавить можно любой адрес в Калининграде, например: ул. Дадаева 55\n\n"
                        "💬 Напишите адрес в чат, я сохраню его!"
                    ),
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                )
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить фото при старте работы: {e}")
                await update.message.reply_text(
                    "📍 Добавить можно любой адрес в Калининграде, например: ул. Дадаева 55\n\n"
                    "💬 Напишите адрес в чат, я сохраню его!",
                    parse_mode="Markdown",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                )
            logging.info(f"🚀 Пользователь {user_id} нажал 'Начать работу' (кнопка меню)")
            return

        # 📍 Кнопка ручного ввода адреса
        elif text == "📍 Добавить адрес":
            user_state[user_id] = {"state": "awaiting_manual_address"}
            await update.message.reply_text(
                "📝 Образец:\n"
                "· Проспект Мира 25\n"
                "· Дадаева 55 корпус 1\n"
                "· Куйбышева 84\n\n"
                "📍 Напиши адрес в формате:\n"
                "[Улица НомерДома](https://2gis.ru/kaliningrad)",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup([["Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
            )

        # ✅ Завершить работу (оплата + следующие адреса)
        elif text == "🎉 Завершить этап":
            if user_id not in user_state or user_state[user_id].get("state") != "awaiting_photos":
                await update.message.reply_text(
                    "❌ Сначала загрузи фото!",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Получаем данные о работе
            photos_uploaded = user_state[user_id].get("photos_uploaded", 0)
            min_photos = user_state[user_id].get("min_photos", MIN_PHOTOS_REQUIRED)
            
            # Защита: нельзя завершить без фото!
            if photos_uploaded == 0:
                await update.message.reply_text(
                    "❌ Сначала загрузи фото!\n\n"
                    f"📸 Минимум {min_photos} фото электрощитов с листовками."
                )
                return
            
            # 🔧 ИСПРАВЛЕНО: Упрощаем текст и заменяем кнопку "Отмена" на "Сохранить"
            caption_text = (
                f"🎉 Отличная работа, так держать!\n\n"
                f"🚪 Теперь ОБЯЗАТЕЛЬНО сфотографируй входную дверь с визиткой Балтсеть³⁹\n\n"
                f"📸 Без этого фото этап не будет завершён."
            )
            
            # Получаем инфо об адресе для статистики
            selected_address = user_state[user_id].get("selected_address", "Неизвестный адрес")
            addr_info = user_state[user_id].get("address_info")
            district = addr_info[3] if (addr_info and len(addr_info) > 3) else "Неизвестный"
            photo_price = get_photo_price()
            total_amount = photos_uploaded * photo_price
            
            # Переводим в состояние "ожидание фото двери"
            user_state[user_id]["state"] = "awaiting_exit_door_photo"
            user_state[user_id]["exit_stats"] = {
                "photos_uploaded": photos_uploaded,
                "total_amount": total_amount,
                "selected_address": selected_address,
                "district": district
            }
            
            # 🔧 ИСПРАВЛЕНО: Отправляем с кнопкой "Сохранить" вместо "Отмена"
            await update.message.reply_photo(
                photo="https://disk.yandex.ru/i/xWAtwVqcN7H9zQ",
                caption=caption_text,
                reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"]], resize_keyboard=True, one_time_keyboard=False)
            )

        # Вернуться в меню (работает как /start без показа команды)
        elif text == "Вернуться в меню":
            # 🔥 UX: Очищаем состояние и возвращаем в меню
            if user_id in user_state:
                user_state[user_id]["state"] = None
            user_name = get_user_name_from_balances(user_id) or update.effective_user.first_name
            await update.message.reply_text(
                f"✅ Привет, {user_name}! Используй кнопки меню для работы.",
                reply_markup=get_main_menu_keyboard()
            )

        # 📋 Проверка отчётов (только для админа)
        elif text == "📋 Проверка отчётов":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ Нет прав.", reply_markup=get_main_menu_keyboard(user_id))
                return
            keyboard = [
                ["📥 Импорт адресов"],
                ["📄 5 последних адресов"],
                ["🔍 Поиск по адресу"],
                ["← Вернуться в меню"]
            ]
            await update.message.reply_text(
                "📋 **Проверка отчётов**\n\nВыбери действие:",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
        
        elif text == "📥 Импорт адресов":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ Нет прав.", reply_markup=get_main_menu_keyboard(user_id))
                return
            user_state[user_id] = user_state.get(user_id, {})
            user_state[user_id]["state"] = "awaiting_admin_bulk_addresses"
            
            help_message = (
                "📥 <b>МАССОВЫЙ ИМПОРТ АДРЕСОВ</b>\n\n"
                "📝 <b>Поддерживаемые форматы:</b>\n\n"
                "1️⃣ <b>Построчный:</b>\n"
                "<code>ул. Осенняя, д. 22\n"
                "ул. Пражская, д. 25</code>\n\n"
                "2️⃣ <b>Компактный (Улица: номера):</b>\n"
                "<code>Краснопрудная: 1, 2, 3, 4, 5\n"
                "Московский пркт.: 10, 12А, 14</code>\n\n"
                "✅ <b>Бот автоматически:</b>\n"
                "• Геокодирует адреса\n"
                "• Определит район\n"
                "• Проверит дубликаты\n"
                "• Добавит в Справочник\n\n"
                "⏱ <b>Обработка:</b> ~2-3 сек на адрес\n\n"
                "💡 Можно смешивать форматы!"
            )
            
            await update.message.reply_text(
                help_message,
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup([["Добавить ещё"],["← Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
            )
            return
        elif text == "Добавить ещё":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ Нет прав.", reply_markup=get_main_menu_keyboard(user_id))
                return
            user_state[user_id] = user_state.get(user_id, {})
            user_state[user_id]["state"] = "awaiting_admin_bulk_addresses"
            
            help_message = (
                "📥 <b>МАССОВЫЙ ИМПОРТ АДРЕСОВ</b>\n\n"
                "📝 <b>Поддерживаемые форматы:</b>\n\n"
                "1️⃣ <b>Построчный:</b>\n"
                "<code>ул. Осенняя, д. 22\n"
                "ул. Пражская, д. 25</code>\n\n"
                "2️⃣ <b>Компактный (Улица: номера):</b>\n"
                "<code>Краснопрудная: 1, 2, 3, 4, 5\n"
                "Московский пркт.: 10, 12А, 14</code>\n\n"
                "✅ <b>Бот автоматически:</b>\n"
                "• Геокодирует адреса\n"
                "• Определит район\n"
                "• Проверит дубликаты\n"
                "• Добавит в Справочник\n\n"
                "⏱ <b>Обработка:</b> ~2-3 сек на адрес\n\n"
                "💡 Можно смешивать форматы!"
            )
            
            await update.message.reply_text(
                help_message,
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup([["Добавить ещё"],["← Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
            )
            return
        # 📄 5 последних адресов
        elif text == "📄 5 последних адресов":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ Нет прав.", reply_markup=get_main_menu_keyboard(user_id))
                return
            try:
                rows = otchety.get_all_values()
                if len(rows) <= 1:
                    await update.message.reply_text("ℹ️ Отчёты пусты.")
                    return
                last_five = rows[-5:] if len(rows) > 5 else rows[1:]
                result = ["📄 **5 последних адресов:**\n"]
                for i, row in enumerate(reversed(last_five), start=1):
                    if len(row) < 9:
                        continue
                    date, promoter, address, photo_count, amount, district, time_str, comment, photo_url = row[:9]
                    status = row[9] if len(row) > 9 else ""
                    status_mark = "❌" if status == "ОТКЛОНЕНО" else "✅"
                    row_idx = len(rows) - len(last_five) + (len(last_five) - i + 1)
                    result.append(f"{status_mark} **#{row_idx}** {date} {time_str}")
                    result.append(f"👤 {promoter} | 🏘️ {address}")
                    result.append(f"💸 {amount}₽ | 📍 {district}")
                    if photo_url:
                        result.append(f"🔗 [photo]({photo_url})")
                    result.append(f"💬 /reject {row_idx}\n")
                # Inline-кнопки для отклонения
                inline_kb = []
                for i, row in enumerate(reversed(last_five), start=1):
                    if len(row) < 9:
                        continue
                    status = row[9] if len(row) > 9 else ""
                    if status != "ОТКЛОНЕНО":
                        row_idx = len(rows) - len(last_five) + (len(last_five) - i + 1)
                        inline_kb.append([InlineKeyboardButton(f"❌ #{row_idx}", callback_data=f"reject_{row_idx}")])
                        inline_kb.append([InlineKeyboardButton(f"❌ Аннулировать '{row[2]}'", callback_data=f"void_addr_idx_{row_idx}")])
                markup = InlineKeyboardMarkup(inline_kb) if inline_kb else None
                await update.message.reply_text("\n".join(result), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=markup)
            except Exception as e:
                logging.error(f"❌ Ошибка чтения отчётов: {e}")
                await update.message.reply_text("❌ Ошибка чтения отчётов.")
        
        # 🔍 Поиск по адресу
        elif text == "🔍 Поиск по адресу":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ Нет прав.", reply_markup=get_main_menu_keyboard(user_id))
                return
            user_state[user_id] = user_state.get(user_id, {})
            user_state[user_id]["state"] = "awaiting_admin_search_address"
            await update.message.reply_text(
                "🔍 Введи адрес для поиска (например: Елизаветинская 5):",
                reply_markup=ReplyKeyboardMarkup([["← Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
            )
        
        # Обработка поиска по адресу
        elif user_state.get(user_id, {}).get("state") == "awaiting_admin_bulk_addresses":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ Нет прав.", reply_markup=get_main_menu_keyboard(user_id))
                return
            bulk_text = text
            res = bulk_add_addresses_to_sprav(bulk_text, user_id)
            if not res.get("success"):
                await update.message.reply_text(f"❌ Ошибка импорта: {res.get('error','неизвестно')}", reply_markup=ReplyKeyboardMarkup([["Добавить ещё"],["← Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False))
                user_state[user_id]["state"] = None
                return
            added = res.get("added", 0)
            skipped = res.get("skipped", 0)
            failed_list = res.get("failed", [])
            summary = [
                "✅ Импорт завершён.",
                f"➕ Добавлено: {added}",
                f"⏭️ Пропущено (дубликаты): {skipped}",
                f"❌ Ошибки: {len(failed_list)}"
            ]
            if failed_list:
                summary.append("\nНе удалось:")
                summary.extend([f"• {item}" for item in failed_list[:10]])
                if len(failed_list) > 10:
                    summary.append(f"… и ещё {len(failed_list)-10} строк")
            await update.message.reply_text("\n".join(summary), reply_markup=ReplyKeyboardMarkup([["Добавить ещё"],["← Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False))
            user_state[user_id]["state"] = None
            return
        elif user_state.get(user_id, {}).get("state") == "awaiting_admin_search_address":
            if user_id not in ADMIN_IDS:
                await update.message.reply_text("❌ Нет прав.", reply_markup=get_main_menu_keyboard(user_id))
                return
            search_addr = normalize_text(text)
            user_state[user_id]["state"] = None
            try:
                rows = otchety.get_all_values()
                matches = []
                for i, row in enumerate(rows[1:], start=2):
                    if len(row) < 9:
                        continue
                    date, promoter, address, photo_count, amount, district, time_str, comment, photo_url = row[:9]
                    status = row[9] if len(row) > 9 else ""
                    if search_addr in normalize_text(address):
                        matches.append((i, date, promoter, address, amount, district, time_str, photo_url, status))
                if not matches:
                    await update.message.reply_text(f"ℹ️ Ничего не найдено по '«{text}»'.")
                    return
                result = [f"🔍 **Найдено:** {len(matches)} записей\n"]
                for row_idx, date, promoter, address, amount, district, time_str, photo_url, status in matches[-10:]:
                    status_mark = "❌" if status == "ОТКЛОНЕНО" else "✅"
                    result.append(f"{status_mark} **#{row_idx}** {date} {time_str}")
                    result.append(f"👤 {promoter} | 🏘️ {address}")
                    result.append(f"💸 {amount}₽ | 📍 {district}")
                    if photo_url:
                        result.append(f"🔗 [photo]({photo_url})")
                    result.append(f"💬 /reject {row_idx}\n")
                # Inline-кнопки для отклонения
                inline_kb = []
                for row_idx, date, promoter, address, amount, district, time_str, photo_url, status in matches[-5:]:
                    if status != "ОТКЛОНЕНО":
                        inline_kb.append([InlineKeyboardButton(f"❌ #{row_idx}", callback_data=f"reject_{row_idx}")])
                        inline_kb.append([InlineKeyboardButton(f"❌ Аннулировать '{address}'", callback_data=f"void_addr_idx_{row_idx}")])
                markup = InlineKeyboardMarkup(inline_kb) if inline_kb else None
                await update.message.reply_text("\n".join(result), parse_mode="Markdown", disable_web_page_preview=True, reply_markup=markup)
            except Exception as e:
                logging.error(f"❌ Ошибка поиска: {e}")
                await update.message.reply_text("❌ Ошибка поиска.")

        # ← Вернуться в меню
        elif text == "← Вернуться в меню" or text == "Вернуться в меню":
            user_state[user_id] = {}
            await update.message.reply_text(
                "🏠 Главное меню",
                reply_markup=get_main_menu_keyboard(user_id)
            )

        # 📦 Запросить листовки
        elif text == "📦 Запросить листовки":
            # 🆕 НОВОЕ: Промоутер выбирает количество листовок
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            
            keyboard = [
                [
                    InlineKeyboardButton("📦 500 шт", callback_data=f"request_flyers_{user_id}_500"),
                    InlineKeyboardButton("📦 1000 шт", callback_data=f"request_flyers_{user_id}_1000"),
                ],
                [
                    InlineKeyboardButton("📦 1500 шт", callback_data=f"request_flyers_{user_id}_1500"),
                    InlineKeyboardButton("💯 Своё кол-во", callback_data=f"request_flyers_{user_id}_custom"),
                ],
                [
                    InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_flyers_{user_id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📦 **ЗАКАЗ ЛИСТОВОК**\n\n"
                "📄 Выбери количество листовок для заказа:\n\n"
                "⏱️ **Важно:** Изготовление занимает **1-3 дня**\n"
                "📦 После одобрения заявки админ свяжется с тобой!",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

        # 🗺️ Создать маршрут
        elif text == "🗺️ Создать маршрут":
            # 🔧 ИСПРАВЛЕНО: Заменили "Дневной отчёт" на "Создать маршрут"
            # Отправляем профиль
            await profile_command(update, context)
            # Добавляем inline-кнопку для создания маршрута
            inline_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🗺️ Создать свой маршрут", callback_data="create_route")
            ]])
            # 🔥 ИСПРАВЛЕНО: Добавили нормальный текст вместо пустого
            await update.message.reply_text(
                "💡 Нажми кнопку ниже, чтобы создать свой личный маршрут:",
                reply_markup=inline_kb
            )

        # ✅ 📍 Я на месте! (подтверждение местоположения)
        elif text in ["🎯 ✅ Я на месте!", "🎯 Я на месте!", "Я на месте!"]:
            logging.info(f"🎯 Пользователь {user_id} нажал 'Я на месте!'")
            
            selected_address = user_state.get(user_id, {}).get("selected_address")
            if not selected_address:
                logging.warning(f"⚠️ У пользователя {user_id} не выбран адрес")
                await update.message.reply_text(
                    "❌ Адрес не выбран. Выбери адрес из списка.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            logging.info(f"📍 Выбранный адрес: {selected_address}")
            # Получаем информацию об адресе
            addr_info = get_address_info(selected_address)
            if not addr_info:
                logging.error(f"❌ Адрес '{selected_address}' не найден в справочнике")
                await update.message.reply_text(
                    "❌ Адрес не найден в справочнике.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            addr, dest_lat, dest_lng, district, status_card, last_promoter, last_visit = addr_info
            
            # 🔥 НОВОЕ: Если есть геолокация - проверяем расстояние, если нет - пропускаем
            if user_id in user_state and "current_location" in user_state[user_id]:
                user_lat, user_lng = user_state[user_id]["current_location"]
                logging.info(f"📏 Проверка расстояния: user=({user_lat}, {user_lng}), dest=({dest_lat}, {dest_lng})")
                distance = haversine_distance(user_lat, user_lng, dest_lat, dest_lng)
                logging.info(f"📏 Расстояние до адреса: {distance:.0f} м")
                route_url = generate_yandex_maps_route_url(user_lat, user_lng, dest_lat, dest_lng)
            else:
                # 📍 Ручной ввод - просто ссылка на адрес без маршрута
                logging.info(f"📍 Ручной ввод адреса - пропускаем проверку расстояния")
                distance = 0
                route_url = f"https://yandex.ru/maps/?text={addr.replace(' ', '%20')}"
            
            # 🚪 Спрашиваем про доступ в подъезд
            keyboard = [
                ["✅ Да!", "🚪 Нет доступа"],
                ["📍 Исправить координаты"],
                ["Вернуться в меню"]
            ]
            
            logging.info(f"✅ Отправляем вопрос про доступ пользователю {user_id}")
            
            # Получаем последнее посещение
            last_visit = addr_info[6] if len(addr_info) > 6 and addr_info[6] else "—"
            
            # 🔧 ИСПРАВЛЕНО: Скрываем последнее посещение если его нет
            if last_visit == "—":
                message_text = f"🎯 Отлично! Есть доступ в подъезд?"
            else:
                message_text = f"🎯 Отлично! Есть доступ в подъезд?\n🕒 Последнее посещение: {last_visit}"
            
            # 🔧 ИСПРАВЛЕНО: Убираем one_time_keyboard чтобы кнопки всегда были видны
            await update.message.reply_photo(
                photo="https://disk.yandex.ru/i/5IsEqKDk2lopxg",
                caption=message_text,
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            
            # Сохраняем состояние
            user_state[user_id]["state"] = "awaiting_access_answer"
            user_state[user_id]["address_info"] = addr_info
            logging.info(f"✅ Состояние пользователя {user_id} изменено на 'awaiting_access_answer'")

        # 📍 Исправить координаты адреса
        elif text == "📍 Исправить координаты":
            if user_id not in user_state or user_state[user_id].get("state") != "awaiting_access_answer":
                await update.message.reply_text(
                    "❌ Сначала выбери адрес!",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Сохраняем состояние для корректировки координат
            selected_address = user_state[user_id].get("selected_address", "Неизвестный адрес")
            user_state[user_id]["state"] = "awaiting_coordinates_fix"
            
            # Просим отправить геолокацию
            keyboard = [
                [KeyboardButton("📍 Отправить геолокацию", request_location=True)],
                ["❌ Отмена"]
            ]
            
            await update.message.reply_photo(
                photo="https://disk.yandex.ru/i/6DjXrMN5aH5p-Q",
                caption=(
                    f"📍 <b>Корректировка координат</b>\n\n"
                    f"📄 Адрес: <b>{selected_address}</b>\n\n"
                    f"📍 Подойди к реальному входу в подъезд и нажми кнопку '📍 Отправить геолокацию'\n\n"
                    f"❗ Важно: Стой у входной двери когда отправляешь геолокацию!\n\n"
                    f"✨ Я обновлю координаты этого адреса в справочнике."
                ),
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )

        # ✅ Да! (есть доступ в подъезд)
        elif text == "✅ Да!":
            if user_id not in user_state or user_state[user_id].get("state") != "awaiting_access_answer":
                await update.message.reply_text(
                    "❌ Сначала подтверди своё местоположение!",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Получаем информацию об адресе
            addr_info = user_state[user_id].get("address_info")
            if not addr_info:
                await update.message.reply_text(
                    "❌ Ошибка получения информации об адресе!",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Извлекаем адрес с защитой
            address = addr_info[0] if (addr_info and len(addr_info) > 0) else ""
            
            # 🔥 НОВОЕ: Сначала рекомендуем начать с последнего этажа и спускаться вниз
            user_state[user_id]["selected_address"] = address
            user_state[user_id]["photos_uploaded"] = 0
            user_state[user_id]["state"] = "awaiting_photos"
            user_state[user_id]["session_started_at"] = datetime.utcnow()
            # Макс. время сессии берём из настроек (по умолчанию из константы)
            load_settings()
            max_minutes = int(SETTINGS.get("SESSION_MAX_MINUTES", "25"))
            user_state[user_id]["session_expires_at"] = datetime.utcnow() + timedelta(minutes=max_minutes)
            
            # 🔧 ИСПРАВЛЕНО: Добавляем кнопку "💾 Сохранить" сразу, чтобы пользователь видел опции
            await update.message.reply_photo(
                photo="https://disk.yandex.ru/i/IOt7MAvTfPD9YQ",
                caption=(
                    f"🎯 Супер!! Начинаем работу по адресу:\n\n"
                    f"📍 <b>{address}</b>\n\n"
                    f"📸 Как добавить фото в Telegram:\n"
                    f"• Нажми на значок 📎 (скрепка) внизу\n"
                    f"• Выбери '🖼️ Фото или видео'\n"
                    f"• Сделай фото или выбери из галереи\n"
                    f"• Отправь фото в чат (не как документ!)\n\n"
                    f"ℹ️ Стартуй с последнего этажа и иди вниз."
                ),
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"], ["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
            )
                    
        # 📤 Режим добавления нескольких фото
        elif text == "📸 Зафиксировать листовку":
            if user_state.get(user_id, {}).get("state") == "awaiting_photos":
                await update.message.reply_text(
                    "📸 Отлично!\n\nОтправь одно фото электрощита с листовкой. Потом можно добавить ещё или нажать «💾 Сохранить».",
                    reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"]], resize_keyboard=True, one_time_keyboard=False)
                )
            else:
                await update.message.reply_text("❌ Сначала подтверди доступ по адресу.", reply_markup=get_main_menu_keyboard())
        elif text == "📤 Добавить несколько фото":
            if user_state.get(user_id, {}).get("state") == "awaiting_photos":
                user_state[user_id]["multi_mode"] = True
                await update.message.reply_text(
                    "📤 Открыл режим серии фото.\n\nОтправляй по одному фото подряд. Когда закончишь — нажми «💾 Сохранить».",
                    reply_markup=ReplyKeyboardMarkup([["📘 Краткая инструкция","💾 Сохранить"]], resize_keyboard=True)
                )
            else:
                await update.message.reply_text("❌ Сначала подтверди доступ по адресу.", reply_markup=get_main_menu_keyboard())
                    
        # 💾 Сохранить (завершение этапа или рекомендация)
        elif text == "💾 Сохранить":
            current_state = user_state.get(user_id, {}).get("state")
            
            # 📍 Обработка сохранения фото двери (awaiting_exit_door_photo или awaiting_door_photo)
            if current_state in ["awaiting_exit_door_photo", "awaiting_door_photo"]:
                await update.message.reply_text(
                    "📸 Пожалуйста, отправь фото входной двери с визиткой.\n\n"
                    "⚠️ Без этого фото этап не будет завершён.",
                    reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"]], resize_keyboard=True, one_time_keyboard=False)
                )
                return
            
            # 📸 Обработка завершения фотоотчёта электрощитов
            if user_state.get(user_id, {}).get("state") == "awaiting_photos":
                photos_uploaded = user_state[user_id].get("photos_uploaded", 0)
                if photos_uploaded == 0:
                    # Первый раз: даём рекомендацию сделать хотя бы 1 фото
                    if not user_state[user_id].get("save_attempted_zero"):
                        user_state[user_id]["save_attempted_zero"] = True
                        await update.message.reply_text(
                            "ℹ️ Чтобы завершить работу по адресу, отправьте хотя бы 1 фото электрощита с визиткой.\n\n📸 Нажмите «📸 Зафиксировать листовку» чтобы добавить фото.",
                            reply_markup=ReplyKeyboardMarkup([["📸 Зафиксировать листовку"],["Вернуться в меню"]], resize_keyboard=True)  # 🔧 ИСПРАВЛЕНО: убрана кнопка "Сканировать район"
                        )
                    else:
                        # Второй раз: возвращаемся к выбору ближайших адресов
                        user_state[user_id]["state"] = None
                        # KeyboardButton импортируется на уровне модуля
                        await update.message.reply_text(
                            "↩️ Возвращаемся к выбору ближайших адресов.\n\n🔍 Отправьте геолокацию или нажмите «🔍 Сканировать район».",
                            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔍 Сканировать район", request_location=True)],["Вернуться в меню"]], resize_keyboard=True)
                        )
                else:
                    # Есть фото → запускаем завершение этапа (как '🎉 Завершить этап')
                    selected_address = user_state[user_id].get("selected_address", "Неизвестный адрес")
                    addr_info = user_state[user_id].get("address_info")
                    district = addr_info[3] if (addr_info and len(addr_info) > 3) else "Неизвестный"
                    photo_price = get_photo_price()
                    total_amount = photos_uploaded * photo_price
                    user_state[user_id]["state"] = "awaiting_exit_door_photo"
                    user_state[user_id]["exit_stats"] = {
                        "photos_uploaded": photos_uploaded,
                        "total_amount": total_amount,
                        "selected_address": selected_address,
                        "district": district
                    }
                    await update.message.reply_photo(
                        photo="https://disk.yandex.ru/i/xWAtwVqcN7H9zQ",
                        caption=(
                            "🎉 Отличная работа, так держать!\n\n"
                            "🚪 Теперь ОБЯЗАТЕЛЬНО сфотографируй входную дверь с визиткой Балтсеть³⁹\n\n"
                            "📸 Без этого фото этап не будет завершён."
                        ),
                        reply_markup=ReplyKeyboardMarkup([["💾 Сохранить"], ["❌ Отмена"], ["Вернуться в меню"]], resize_keyboard=True)
                    )
            else:
                await update.message.reply_text("❌ Сначала подтверди доступ по адресу.", reply_markup=get_main_menu_keyboard())
        # 🚪 Нет доступа (нет доступа в подъезд)
        elif text == "🚪 Нет доступа":
            if user_id not in user_state or user_state[user_id].get("state") != "awaiting_access_answer":
                await update.message.reply_text(
                    "❌ Сначала подтверди своё местоположение!",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Просим фото двери с визиткой
            # Запускаем сессию для фото двери
            load_settings()
            max_minutes = int(SETTINGS.get("SESSION_MAX_MINUTES", "25"))
            user_state[user_id]["session_started_at"] = datetime.utcnow()
            user_state[user_id]["session_expires_at"] = datetime.utcnow() + timedelta(minutes=max_minutes)
            
            try:
                from telegram.error import TelegramError, BadRequest
                await update.message.reply_photo(
                    photo="https://disk.yandex.ru/i/xWAtwVqcN7H9zQ",
                    caption=(
                        "🚪 Нет проблем!\n\n"
                        "📸 Пожалуйста, сфотографируй входную дверь с визиткой Балтсеть³⁹\n\n"
                        "Это поможет нам отследить покрытие и вернуться сюда позже!"
                    ),
                    reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
                )
            except (TelegramError, BadRequest) as e:
                logging.warning(f"⚠️ Не удалось отправить сообщение: {e}")
                await update.message.reply_photo(
                    photo="https://disk.yandex.ru/i/xWAtwVqcN7H9zQ",
                    caption=(
                        "🚪 Нет проблем!\n\n"
                        "📸 Пожалуйста, сфотографируй входную дверь с визиткой Балтсеть³⁹\n\n"
                        "Это поможет нам отследить покрытие и вернуться сюда позже!"
                    ),
                    reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
                )
            
            user_state[user_id]["state"] = "awaiting_door_photo"

        # 📘 Краткая инструкция
        elif text == "📘 Краткая инструкция":
            # 🔥 Показываем инструкцию, но НЕ убираем кнопки работы!
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            inline_kb = InlineKeyboardMarkup([[InlineKeyboardButton("Есть идея?", callback_data="feedback_idea")]])
            await update.message.reply_text(
                "📘 Краткая инструкция:\n\n"
                "Как отправлять фото в Telegram:\n"
                "— Отправляй фото по одному сообщению (не как документ)\n"
                "— Убедись, что визитка читаема и на кадре есть электрощит\n"
                "— Можно добавить короткий текст, если нужно пояснить\n"
                "— Если связь слабая — подожди, фото дойдёт\n\n"
                "📸 Готов? Отправляй фото прямо сейчас!",
                reply_markup=inline_kb
            )
        # 📸 Зафиксировать листовку (подсказка для промоутера)
        elif user_state.get(user_id, {}).get("state") == "awaiting_manual_address":
            if not looks_like_address(text):
                await update.message.reply_text(
                    "🧭 Введи адрес как 'Улица 40' (например: Елизаветинская 5).",
                    reply_markup=ReplyKeyboardMarkup([["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=False)
                )
                return
            # Валидный адрес: геокодируем и добавляем
            manual_address = text.strip()
            logging.info(f"📝 Пользователь {user_id} ввёл адрес вручную: '{manual_address}'")
            await update.message.reply_text("✨ Подготавливаю информацию... Чуть-чуть!")
            
            # 🔥 УЛУЧШЕННЫЙ UX: Геокодируем, но НЕ отказываем если не нашли
            result = geocode_address(manual_address)
            
            if result:
                # Координаты найдены - отлично!
                addr_lat, addr_lng, addr_district = result
                addr_district = ensure_real_district(manual_address, addr_lat, addr_lng, addr_district)
            else:
                # Координаты НЕ найдены - всё равно добавляем, админ потом поправит
                logging.warning(f"⚠️ Координаты для '{manual_address}' не найдены, добавляем без координат")
                addr_lat, addr_lng, addr_district = 0.0, 0.0, "Центральный"  # Заглушка
            
            # Проверяем, есть ли адрес в справочнике (точное + похожее совпадение)
            addr_info = get_address_info(manual_address)
            
            # 🔥 НОВОЕ: Проверка на похожие адреса (если точного нет)
            if not addr_info:
                # Получаем все адреса из справочника
                try:
                    all_addresses = sprav.col_values(1)[1:]  # Пропускаем заголовок
                    norm_manual = normalize_text(manual_address)
                    
                    # Ищем похожие адреса
                    for existing in all_addresses:
                        norm_existing = normalize_text(existing)
                        
                        # Точное совпадение после нормализации
                        if norm_manual == norm_existing:
                            logging.info(f"🔄 Адрес '{manual_address}' уже есть как '{existing}'")
                            addr_info = get_address_info(existing)
                            break
                        
                        # Похожие адреса (отличаются только буквой А/Б/В)
                        import re
                        base_manual = re.sub(r'[а-яa-z]$', '', norm_manual)
                        base_existing = re.sub(r'[а-яa-z]$', '', norm_existing)
                        if base_manual == base_existing and base_manual and len(base_manual) > 3:
                            logging.info(f"🔄 Адрес '{manual_address}' похож на '{existing}'")
                            addr_info = get_address_info(existing)
                            break
                except Exception as e:
                    logging.warning(f"⚠️ Ошибка проверки похожих адресов: {e}")
            
            if not addr_info:
                # Добавляем новый адрес
                try:
                    # 🔥 БЕЗОПАСНО: Определяем следующую строку и добавляем ТОЛЬКО в A:I
                    all_rows = sprav.get_all_values()
                    next_row = len(all_rows) + 1
                    
                    # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно (защита от "Out of rows")
                    ensure_sheet_has_enough_rows(sprav, next_row)
                    
                    new_row = [
                        manual_address,
                        addr_district,
                        "",
                        "",
                        "",
                        "",
                        "🔴 Не был",
                        str(addr_lat) if addr_lat != 0.0 else "",  # Пустая строка если нет координат
                        str(addr_lng) if addr_lng != 0.0 else ""
                    ]
                    
                    # ✅ БЕЗОПАСНЫЙ МЕТОД: Явно указываем диапазон A:I
                    range_name = f"A{next_row}:I{next_row}"
                    sprav.update(values=[new_row], range_name=range_name)
                    
                    logging.info(f"✅ Адрес '{manual_address}' добавлен в строку {next_row}: ({addr_lat}, {addr_lng}, {addr_district})")
                    user_state[user_id]["just_added_address"] = True
                    user_state[user_id]["address_bonus_multiplier"] = 1.10
                except Exception as e:
                    logging.error(f"❌ Ошибка добавления адреса: {e}")
                # Перечитываем адрес из справочника
                addr_info = get_address_info(manual_address)
            if addr_info:
                # ✅ Адрес готов к работе!
                addr = addr_info[0] if len(addr_info) > 0 else manual_address
                lat = addr_info[1] if len(addr_info) > 1 else (str(addr_lat) if addr_lat != 0.0 else "0")
                lng = addr_info[2] if len(addr_info) > 2 else (str(addr_lng) if addr_lng != 0.0 else "0")
                district = addr_info[3] if len(addr_info) > 3 else addr_district
                status_card = addr_info[4] if len(addr_info) > 4 else "🔴 Не был"
                last_promoter = addr_info[5] if len(addr_info) > 5 else ""
                last_visit = addr_info[6] if len(addr_info) > 6 else ""
                
                # Инициализируем user_state[user_id] если не существует
                if user_id not in user_state:
                    user_state[user_id] = {}
                user_state[user_id]["selected_address"] = addr
                user_state[user_id]["address_info"] = addr_info
                user_state[user_id]["state"] = None
                
                keyboard = [
                    ["🎯 ✅ Я на месте!"],
                    ["Вернуться в меню"]
                ]
                
                distance_text = "—"
                if user_id in user_state and "current_location" in user_state[user_id]:
                    try:
                        user_lat, user_lng = user_state[user_id]["current_location"]
                        if lat and lng and float(lat) != 0.0 and float(lng) != 0.0:
                            distance = get_walking_distance(user_lat, user_lng, float(lat), float(lng)) or haversine_distance(user_lat, user_lng, float(lat), float(lng))
                            distance_text = f"{int(distance)} м" if distance <= 1000 else f"{distance/1000:.1f} км"
                    except Exception:
                        pass
                
                route_url = f"https://yandex.ru/maps/?text={addr.replace(' ', '%20')}"
                
                # 🔥 УЛУЧШЕННЫЙ UX: Позитивное сообщение вместо "не найден"
                await update.message.reply_text(
                    f"✅ Адрес готов к работе!\n\n"
                    f"📍 <b>{addr}</b>\n"
                    f"🔑 Расстояние до входа: {distance_text}\n\n"
                    f"🪧 Статус: {status_card}\n"
                    f"🗺️ <a href='{route_url}'>Маршрут на Яндекс.Картах</a>",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                )
            else:
                # Крайний случай - даже после добавления не нашли
                await update.message.reply_text(
                    f"❌ Не удалось добавить адрес \"{manual_address}\".\n\n"
                    f"🔄 Попробуй ещё раз.",
                    reply_markup=get_main_menu_keyboard()
                )
                user_state[user_id]["state"] = None
        elif text == "📦 Запросить листовки":
            # Выбор количества листовок
            keyboard = [["500","1000","1500"],["📦 Отменить заявку"]]
            await update.message.reply_text(
                "📦 Выбери количество листовок для заявки:",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            user_state[user_id]["state"] = "awaiting_flyer_request"
        elif user_state.get(user_id, {}).get("state") == "awaiting_flyer_request" and text in ["500","1000","1500"]:
            qty = int(text)
            name = (update.effective_user.full_name or update.effective_user.first_name or "Без имени")
            date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            try:
                if flyer_requests_sheet:
                    flyer_requests_sheet.append_row([str(user_id), name, date_str, str(qty), "В ожидании", ""])
                await update.message.reply_text(
                    "✅ Заявка отправлена. Подготовка листовок займёт 1–3 дня.",
                    reply_markup=get_main_menu_keyboard()
                )
            except Exception as e:
                logging.error(f"❌ Ошибка создания заявки на листовки: {e}")
                await update.message.reply_text(
                    "⚠️ Не удалось создать заявку. Попробуй позже.",
                    reply_markup=get_main_menu_keyboard()
                )
            user_state[user_id]["state"] = None
        elif text == "📦 Отменить заявку":
            # Отмена последней заявки со статусом 'В ожидании'
            try:
                if flyer_requests_sheet:
                    values = flyer_requests_sheet.get_all_values()
                    # Поиск снизу вверх
                    for idx in range(len(values)-1, 0, -1):
                        row = values[idx]
                        if len(row) >= 5 and row[0] == str(user_id) and row[4] == "В ожидании":
                            flyer_requests_sheet.update_cell(idx+1, 5, "Отменена")
                            await update.message.reply_text("🛑 Заявка отменена.")
                            
                            # 🔧 ИСПРАВЛЕНО: Уведомляем админа об отмене
                            user_name = update.effective_user.full_name or update.effective_user.first_name or "Неизвестный"
                            quantity = row[3] if len(row) > 3 else "Неизвестно"
                            for admin_id in ADMIN_IDS:
                                try:
                                    await context.bot.send_message(
                                        chat_id=admin_id,
                                        text=f"⚠️ **Промоутер отменил заявку на листовки!**\n\n"
                                             f"👤 Промоутер: {user_name} (ID: {user_id})\n"
                                             f"📦 Количество: {quantity} шт\n"
                                             f"📊 Статус: **Отменена**",
                                        parse_mode="Markdown"
                                    )
                                except Exception as e:
                                    logging.warning(f"⚠️ Не удалось уведомить админа {admin_id}: {e}")
                            break
                    else:
                        await update.message.reply_text("ℹ️ Нет активных заявок для отмены.")
                else:
                    await update.message.reply_text("⚠️ Лист заявок недоступен.")
            except Exception as e:
                logging.error(f"❌ Ошибка отмены заявки: {e}")
                await update.message.reply_text("⚠️ Не удалось отменить заявку. Попробуй позже.")
            user_state[user_id]["state"] = None
        elif text == "📍 Добавить адрес":
            # 🔥 UX: Оставляем кнопку отмены!
            keyboard = [["❌ Отмена"]]
            try:
                # 📸 Отправляем фото примера (Чкалова 49Б)
                await update.message.reply_photo(
                    photo="https://i.ibb.co/4mZ9Tb3/address-example.jpg",
                    caption=(
                        "📍 Напиши адрес в формате:\n\n"
                        "📌 <b>Улица Номер</b> (например: <i>\"Чкалова 49Б\"</i>)\n\n"
                        "🔍 Я найду его на карте и добавлю в справочник, если нужно."
                    ),
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить фото примера: {e}")
                # Фолбэк: только текст
                await update.message.reply_text(
                    "📍 Напиши адрес в формате:\n\n"
                    "📌 <b>Улица Номер</b> (например: <i>\"Чкалова 49Б\"</i>)\n\n"
                    "🔍 Я найду его на карте и добавлю в справочник, если нужно.",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
            user_state[user_id]["state"] = "awaiting_manual_address"

        # Обработка ввода адреса
        else:
            # Проверяем, ожидаем ли мы ручной ввод адреса
            if user_id in user_state and user_state[user_id].get("state") == "awaiting_manual_address":
                # Пользователь ввёл адрес вручную
                manual_address = text.strip()
                logging.info(f"📝 Пользователь {user_id} ввёл адрес вручную: '{manual_address}'")
                
                # Геокодируем адрес
                await update.message.reply_text("✨ Подготавливаю информацию... Чуть-чуть!")
                result = geocode_address(manual_address)
                
                if result:
                    # Координаты найдены - отлично!
                    addr_lat, addr_lng, addr_district = result
                    addr_district = ensure_real_district(manual_address, addr_lat, addr_lng, addr_district)
                else:
                    # Координаты НЕ найдены - всё равно добавляем, админ потом поправит
                    logging.warning(f"⚠️ Координаты для '{manual_address}' не найдены, добавляем без координат")
                    addr_lat, addr_lng, addr_district = 0.0, 0.0, "Центральный"  # Заглушка
                
                # Проверяем, есть ли адрес в справочнике (точное + похожее совпадение)
                addr_info = get_address_info(manual_address)
                
                # 🔥 НОВОЕ: Проверка на похожие адреса (если точного нет)
                if not addr_info:
                    try:
                        all_addresses = sprav.col_values(1)[1:]  # Пропускаем заголовок
                        norm_manual = normalize_text(manual_address)
                        
                        # Ищем похожие адреса
                        for existing in all_addresses:
                            norm_existing = normalize_text(existing)
                            
                            # Точное совпадение после нормализации
                            if norm_manual == norm_existing:
                                logging.info(f"🔄 Адрес '{manual_address}' уже есть как '{existing}'")
                                addr_info = get_address_info(existing)
                                break
                            
                            # Похожие адреса (отличаются только буквой А/Б/В)
                            import re
                            base_manual = re.sub(r'[а-яa-z]$', '', norm_manual)
                            base_existing = re.sub(r'[а-яa-z]$', '', norm_existing)
                            if base_manual == base_existing and base_manual and len(base_manual) > 3:
                                logging.info(f"🔄 Адрес '{manual_address}' похож на '{existing}'")
                                addr_info = get_address_info(existing)
                                break
                    except Exception as e:
                        logging.warning(f"⚠️ Ошибка проверки похожих адресов: {e}")
                
                if not addr_info:
                    # Добавляем новый адрес
                    try:
                        # 🔥 БЕЗОПАСНО: Определяем следующую строку и добавляем ТОЛЬКО в A:I
                        all_rows = sprav.get_all_values()
                        next_row = len(all_rows) + 1
                        
                        # 🛡️ КРИТИЧНО: Расширяем таблицу если нужно
                        ensure_sheet_has_enough_rows(sprav, next_row)
                        
                        new_row = [
                            manual_address,       # A: Адрес
                            addr_district,        # B: Район (из OSM/Yandex!) ✅
                            "",                   # C: Промоутер
                            "",                   # D: Фото
                            "",                   # E: Посещение
                            "",                   # F: Статус листовок
                            "🔴 Не был",          # G: Статус карты
                            str(addr_lat) if addr_lat != 0.0 else "",  # H: Широта (lat)
                            str(addr_lng) if addr_lng != 0.0 else ""   # I: Долгота (lng)
                        ]
                        
                        # ✅ БЕЗОПАСНЫЙ МЕТОД: Явно указываем диапазон A:I
                        range_name = f"A{next_row}:I{next_row}"
                        sprav.update(values=[new_row], range_name=range_name)
                        
                        logging.info(f"✅ Адрес '{manual_address}' добавлен в строку {next_row}: ({addr_lat}, {addr_lng}, {addr_district})")
                        # 🔥 Бонус: адресс только что добавлен вручную → +10% к доходу по фото
                        user_state[user_id]["just_added_address"] = True
                        user_state[user_id]["address_bonus_multiplier"] = 1.10
                    except Exception as e:
                        logging.error(f"❌ Ошибка добавления адреса: {e}")
                    # Повторно читаем данные
                    addr_info = get_address_info(manual_address)
                
                if addr_info:
                    # ✅ Адрес готов к работе!
                    # Безопасная распаковка с fallback значениями
                    addr = addr_info[0] if len(addr_info) > 0 else manual_address
                    lat = addr_info[1] if len(addr_info) > 1 else (str(addr_lat) if addr_lat != 0.0 else "0")
                    lng = addr_info[2] if len(addr_info) > 2 else (str(addr_lng) if addr_lng != 0.0 else "0")
                    district = addr_info[3] if len(addr_info) > 3 else addr_district
                    status_card = addr_info[4] if len(addr_info) > 4 else "🔴 Не был"
                    last_promoter = addr_info[5] if len(addr_info) > 5 else ""
                    last_visit = addr_info[6] if len(addr_info) > 6 else ""
                    
                    # Сохраняем выбранный адрес
                    user_state[user_id]["selected_address"] = addr
                    user_state[user_id]["address_info"] = addr_info
                    
                    # Проверяем, подтверждено ли уже местоположение
                    if user_state[user_id].get("state") == "awaiting_access_answer":
                        # Местоположение уже подтверждено, показываем кнопки доступа
                        keyboard = [
                            ["🎯 ✅ Я на месте!"],
                            ["Вернуться в меню"]
                        ]
                        
                        # Вычисляем расстояние до входа
                        distance_text = "—"
                        if user_id in user_state and "current_location" in user_state[user_id]:
                            try:
                                user_lat, user_lng = user_state[user_id]["current_location"]
                                if lat and lng and float(lat) != 0.0 and float(lng) != 0.0:
                                    distance = get_walking_distance(user_lat, user_lng, float(lat), float(lng)) or haversine_distance(user_lat, user_lng, float(lat), float(lng))
                                    distance_text = f"{int(distance)} м"
                            except Exception:
                                pass
                        
                        # 🔥 Создаём гиперссылку на Яндекс.Карты
                        route_url = f"https://yandex.ru/maps/?text={addr.replace(' ', '%20')}"
                        
                        await update.message.reply_text(
                            f"📍 <b>{addr}</b>\n"
                            f"🔑 Расстояние до входа: {distance_text}\n\n"
                            f"🪧 Статус: {status_card}\n"
                            f"🗺️ <a href='{route_url}'>Маршрут на Яндекс.Картах</a>",
                            parse_mode="HTML",
                            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                        )
                        return
                    
                    user_state[user_id]["state"] = None
                    
                    # Показываем карточку адреса
                    keyboard = [
                        ["🎯 ✅ Я на месте!"],
                        ["Вернуться в меню"]
                    ]
                    
                    # Вычисляем расстояние до входа (если есть геолокация)
                    distance_text = "—"
                    if user_id in user_state and "current_location" in user_state[user_id]:
                        try:
                            user_lat, user_lng = user_state[user_id]["current_location"]
                            if lat and lng and float(lat) != 0.0 and float(lng) != 0.0:
                                distance = get_walking_distance(user_lat, user_lng, float(lat), float(lng)) or haversine_distance(user_lat, user_lng, float(lat), float(lng))
                                distance_text = f"{int(distance)} м" if distance <= 1000 else f"{distance/1000:.1f} км"
                        except Exception:
                            pass
                    
                    # 🔥 Создаём гиперссылку на Яндекс.Карты
                    route_url = f"https://yandex.ru/maps/?text={addr.replace(' ', '%20')}"
                    
                    await update.message.reply_text(
                        f"✅ Адрес готов к работе!\n\n"
                        f"📍 <b>{addr}</b>\n"
                        f"🔑 Расстояние до входа: {distance_text}\n\n"
                        f"🪧 Статус: {status_card}\n"
                        f"🗺️ <a href='{route_url}'>Маршрут на Яндекс.Картах</a>",
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    )
                else:
                    # Крайний случай - даже после добавления не нашли
                    await update.message.reply_text(
                        f"❌ Не удалось добавить адрес \"{manual_address}\".\n\n"
                        f"🔄 Попробуй ещё раз.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    user_state[user_id]["state"] = None
            else:
                # 🔧 ИСПРАВЛЕНО: Если пользователь в состоянии awaiting_access_answer - игнорируем любой текст кроме кнопок
                current_state = user_state.get(user_id, {}).get("state")
                if current_state == "awaiting_access_answer":
                    selected_address = user_state.get(user_id, {}).get("selected_address", "Адрес")
                    await update.message.reply_text(
                        f"📍 Ты уже выбрал адрес: {selected_address}\n\n"
                        "🗺️ Открой ссылку 'Маршрут на Яндекс.Картах' в карточке выше и доберись до подъезда.\n\n"
                        "🎯 Когда будешь на месте — нажми кнопку '🎯 ✅ Я на месте!'.\n\n"
                        "🔙 Или нажми 'Вернуться в меню' чтобы выбрать другой адрес.",
                        reply_markup=ReplyKeyboardMarkup([["🎯 ✅ Я на месте!"], ["Вернуться в меню"]], resize_keyboard=True)
                    )
                    return
                
                # Пробуем найти адрес в справочнике
                # ВАЖНО: Очищаем текст от эмодзи статусов, расстояния и подъезда
                clean_text = text
                
                # Удаляем эмодзи статусов в начале
                for emoji in ["🟢", "🟡", "🔴", "📍"]:
                    if clean_text.startswith(emoji):
                        clean_text = clean_text[len(emoji):].strip()
                        break
                
                # Удаляем расстояние в скобках в конце (например, "(18 м)")
                import re
                clean_text = re.sub(r'\s*\(\d+\s*м\)\s*$', '', clean_text).strip()
                
                # Удаляем подъезд (например, "— подъезд 1")
                clean_text = re.sub(r'\s*[—–-]\s*подъезд\s*\d+', '', clean_text, flags=re.IGNORECASE).strip()
                
                # Логируем для отладки
                logging.info(f"🔍 Пользователь {user_id} выбрал адрес: '{text}' → очищено: '{clean_text}'")
                
                # Проверяем адрес после очистки
                if not clean_text or len(clean_text) < 4:
                    await update.message.reply_text(
                        "❌ Это не похоже на адрес. Напиши, например: Еловая 40.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return
                
                # 🎭 🔥 ИСПРАВЛЕНО: Показываем loading-сообщение ТОЛЬКО ОДИН РАЗ
                loading_emojis = [
                    "🎯 Подготавливаю адрес... Момент!",
                    "🚀 Загружаю данные... Сейчас будет!",
                    "⚡ Подготавливаю адрес... Секундочку!",
                    "🎨 Формирую карточку... Почти готово!",
                    "✨ Подготавливаю информацию... Чуть-чуть!",
                    "🔥 Проверяю статус... Секунду!",
                    "💫 Загружаю детали... Уже скоро!",
                ]
                import random
                loading_message = await update.message.reply_text(
                    random.choice(loading_emojis),
                    reply_markup=ReplyKeyboardMarkup([["Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
                )
                
                addr_info = get_address_info(clean_text)
                if addr_info:
                    # ЗАЩИТА: Проверяем длину перед распаковкой
                    if len(addr_info) != 7:
                        logging.error(f"❌ addr_info имеет неправильную длину: {len(addr_info)}")
                        # 🗑️ Удаляем loading-сообщение
                        try:
                            await loading_message.delete()
                        except Exception:
                            pass
                        await update.message.reply_text(
                            f"❌ Ошибка данных адреса.",
                            reply_markup=get_main_menu_keyboard()
                        )
                        return
                    # ИСПРАВЛЕНО: Распаковываем все 7 значений
                    addr, lat, lng, district, status_card, last_promoter, last_visit = addr_info
                    
                    # 📍 Сохраняем выбранный адрес
                    if user_id not in user_state:
                        user_state[user_id] = {}
                    user_state[user_id]["selected_address"] = addr
                    user_state[user_id]["address_info"] = addr_info
                    
                    # 🚦 Устанавливаем состояние ожидания подтверждения местоположения
                    user_state[user_id]["state"] = "awaiting_access_answer"
                    
                    # 🎯 Показываем информацию об адресе
                    keyboard = [
                        ["🎯 ✅ Я на месте!"],
                        ["Вернуться в меню"]
                    ]
                    
                    # Дополняем карточку адреса фактами
                    last_visit = addr_info[6] if len(addr_info) > 6 and addr_info[6] else "—"
                    
                    # Вычисляем расстояние до входа (если есть геолокация)
                    distance_text = "—"
                    if user_id in user_state and "current_location" in user_state[user_id]:
                        user_lat, user_lng = user_state[user_id]["current_location"]
                        distance = get_walking_distance(user_lat, user_lng, float(lat), float(lng)) or haversine_distance(user_lat, user_lng, float(lat), float(lng))
                        distance_text = f"{int(distance)} м" if distance <= 1000 else f"{distance/1000:.1f} км"
                    
                    # 🔥 Создаём гиперссылку на Яндекс.Карты
                    route_url = f"https://yandex.ru/maps/?text={addr.replace(' ', '%20')}"
                    
                    # 🗑️ Удаляем заглушку
                    try:
                        await loading_message.delete()
                    except Exception:
                        pass
                    
                    await update.message.reply_text(
                        f"📍 <b>{addr}</b>\n"
                        f"🔑 Расстояние до входа: {distance_text}\n\n"
                        f"🪧 Статус: {status_card}\n"
                        f"🗺️ <a href='{route_url}'>Маршрут на Яндекс.Картах</a>",
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                    )
                else:
                    # 📍 Пытаемся распознать введённый адрес и добавить в Справочник (без геолокации)
                    import re
                    if re.search(r'\d', clean_text):
                        result = geocode_address(clean_text)
                        if result:
                            addr_lat, addr_lng, addr_district = result
                            try:
                                new_row = [
                                    clean_text,                # A: АДРЕС
                                    addr_district,            # B: РАЙОН
                                    "",                       # C: ПРОМОУТЕР
                                    str(DEFAULT_FREQUENCY_DAYS),  # D: ЧАСТОТА
                                    "",                       # E: ПОСЛЕДНЕЕ ПОСЕЩЕНИЕ
                                    "🔴 Не был",              # F: СТАТУС РЕКЛАМЫ
                                    "🔴 Не был",              # G: СТАТУС КАРТЫ
                                    str(addr_lat),            # H: ШИРОТА
                                    str(addr_lng)             # I: ДОЛГОТА
                                ]
                                sprav.append_row(new_row)
                                logging.info(f"✅ Добавлен адрес вручную: {clean_text} ({addr_district})")
                                # Повторно читаем данные
                                addr_info = get_address_info(clean_text)
                            except Exception as e:
                                logging.error(f"❌ Ошибка добавления адреса вручную: {e}")
                    
                    if addr_info:
                        # ЗАЩИТА: Проверяем длину перед распаковкой
                        if len(addr_info) != 7:
                            await update.message.reply_text(
                                f"❌ Ошибка данных адреса.",
                                reply_markup=get_main_menu_keyboard()
                            )
                            return
                        addr, lat, lng, district, status_card, last_promoter, last_visit = addr_info
                        # 📍 Сохраняем выбранный адрес
                        if user_id not in user_state:
                            user_state[user_id] = {}
                        user_state[user_id]["selected_address"] = addr
                        user_state[user_id]["address_info"] = addr_info
                        
                        # 🚦 Устанавливаем состояние ожидания подтверждения местоположения
                        user_state[user_id]["state"] = "awaiting_access_answer"
                        user_state[user_id]["just_added_address"] = True  # 🎉 Бонус для первопроходца
                        
                        # 🎯 Показываем информацию об адресе
                        keyboard = [["🎯 ✅ Я на месте!"],["Вернуться в меню"]]
                        distance_text = "—"
                        if user_id in user_state and "current_location" in user_state[user_id]:
                            user_lat, user_lng = user_state[user_id]["current_location"]
                            distance = get_walking_distance(user_lat, user_lng, float(lat), float(lng)) or haversine_distance(user_lat, user_lng, float(lat), float(lng))
                            distance_text = f"{int(distance)} м" if distance <= 1000 else f"{distance/1000:.1f} км"
                        route_url = f"https://yandex.ru/maps/?text={addr.replace(' ', '%20')}"
                        await update.message.reply_text(
                            f"<b>{addr}</b>\n"
                            f"🔑 Расстояние до входа: {distance_text}\n\n"
                            f"🪧 Статус: {status_card}\n"
                            f"🗺️ <a href='{route_url}'>Маршрут на Яндекс.Картах</a>",
                            parse_mode="HTML",
                            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                        )
                    else:
                        # Адрес не найден - предлагаем ближайшие адреса
                        if user_id in user_state and "current_location" in user_state[user_id]:
                            user_lat = user_state[user_id]["current_location"][0]
                            user_lng = user_state[user_id]["current_location"][1]
                            
                            # Ищем ближайшие адреса и автоматически добавляем новые в Справочник
                            nearby_addresses = get_or_create_nearby_addresses(user_lat, user_lng, exclude_address="", limit=MAX_NEARBY_ADDRESSES)
                            
                            if nearby_addresses:
                                # Формируем список доступных адресов
                                address_list = []
                                for i, (addr, addr_lat, addr_lng, distance, status_icon) in enumerate(nearby_addresses, 1):
                                    address_list.append(f"{status_icon} {addr} ({int(distance)} м)")
                                
                                result_text = (
                                    f"❌ Адрес \"{text}\" не найден в Справочнике.\n\n"
                                    f"📍 **Ближайшие доступные адреса:**\n\n"
                                )
                                result_text += "\n".join(address_list)
                                result_text += "\n\n💬 Выбери адрес из списка или введи другой."
                                
                                # Кнопки с адресами
                                keyboard = []
                                # Кнопка добавления своего адреса - всегда первая
                                keyboard.append(["📍 Добавить адрес"])
                                
                                if nearby_addresses:
                                    keyboard.append(["🎯 Выбрать ближайшую точку"])
                                for addr, _, _, distance, status_icon in nearby_addresses:
                                    keyboard.append([f"{status_icon} {addr} ({int(distance)} м)"])
                                
                                keyboard.append(["Вернуться в меню"])
                                
                                await update.message.reply_text(
                                    result_text,
                                    parse_mode="Markdown",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                                )
                            else:
                                await update.message.reply_text(
                                    f"❌ Адрес \"{text}\" не найден.\n\n"
                                    f"📍 Сначала отправь свою геолокацию для поиска ближайших адресов!",
                                    reply_markup=get_main_menu_keyboard()
                                )
                        else:
                            user_state.setdefault(user_id, {})["state"] = "awaiting_manual_address"
                            await update.message.reply_text(
                                f"❌ Адрес \"{text}\" не найден.\n\n"
                                f"🧭 Давай добавим его вместе! Это займёт меньше минуты.\n\n"
                                f"1) Напиши название улицы (например: Еловая)\n"
                                f"2) Потом укажи номер дома (например: 40)\n\n"
                                f"💡 Формат итогового адреса: \"Еловая 40\"\n"
                                f"📍 Если удобнее — сначала отправь геолокацию, и я предложу ближайшие варианты.",
                                reply_markup=ReplyKeyboardMarkup([["↩️ Вернуться в меню"]], resize_keyboard=True, one_time_keyboard=False)
                            )

    except Exception as e:
        logging.error(f"❌ Ошибка в handle_text_message(): {e}")
        # 🔥 ИСПРАВЛЕНО: Проверяем что update.message существует перед reply
        if update and update.message:
            await update.message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже."
            )


# ============================
# 🚀 MAIN APPLICATION
# ============================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    try:
        error_str = str(context.error)
        
        # 🔥 НОВОЕ: Игнорируем сетевые ошибки (они обрабатываются автоматически)
        if "httpx.ReadError" in error_str or "httpx.ConnectError" in error_str or "httpx.TimeoutException" in error_str:
            logging.warning(f"⚠️ Сетевая ошибка (автоматическое переподключение): {error_str}")
            return  # Не сообщаем пользователю о временных проблемах с сетью
        
        logging.error(f"❌ Ошибка: {error_str}")
        user_id = None
        chat_id = None
        if update and hasattr(update, "effective_user") and update.effective_user:
            user_id = update.effective_user.id
        if update and hasattr(update, "effective_chat") and update.effective_chat:
            chat_id = update.effective_chat.id
        state = user_state.get(user_id, {}).get("state") if (user_id in user_state) else None
        # Подбираем понятные кнопки для продолжения + кнопка отчета об ошибке
        if state == "awaiting_photos":
            keyboard = ReplyKeyboardMarkup([["📸 Зафиксировать листовку","📤 Добавить несколько фото"],["📘 Краткая инструкция","💾 Сохранить"],["🆘 Сообщить о проблеме"]], resize_keyboard=True)
            message = "❌ Произошла ошибка, но работа продолжается.\n\n📸 Отправь фото электрощита или используй кнопки ниже.\n\n💡 Если проблема повторяется — нажми '🆘 Сообщить о проблеме'"
        elif state == "awaiting_access_answer":
            keyboard = ReplyKeyboardMarkup([["✅ Да!"],
                            ["🚪 Нет доступа"],["Вернуться в меню"],["🆘 Сообщить о проблеме"]], resize_keyboard=True, one_time_keyboard=False)
            message = "❌ Произошла ошибка.\n\n🚪 Есть ли доступ в подъезд?\n\n💡 Если проблема повторяется — нажми '🆘 Сообщить о проблеме'"
        elif state == "awaiting_door_photo":
            keyboard = ReplyKeyboardMarkup([["❌ Отмена"],["🆘 Сообщить о проблеме"]], resize_keyboard=True)
            message = "❌ Произошла ошибка.\n\n📸 Отправь фото входной двери с визиткой Балтсеть³⁹.\n\n💡 Если проблема повторяется — нажми '🆘 Сообщить о проблеме'"
        elif state == "awaiting_exit_door_photo":
            keyboard = ReplyKeyboardMarkup([["❌ Отмена"],["🆘 Сообщить о проблеме"]], resize_keyboard=True)
            message = "❌ Произошла ошибка.\n\n📸 Отправь обязательное фото входной двери с визиткой Балтсеть³⁹.\n\n💡 Если проблема повторяется — нажми '🆘 Сообщить о проблеме'"
        else:
            keyboard = ReplyKeyboardMarkup([["📍 Добавить адрес"], ["🔍 Сканировать район"], ["🆘 Сообщить о проблеме"]], resize_keyboard=True, one_time_keyboard=False)
            message = "❌ Произошла ошибка.\n\nВыбери действие для продолжения.\n\n💡 Если проблема повторяется — нажми '🆘 Сообщить о проблеме'"
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)
    except Exception as e:
        logging.error(f"❌ Ошибка внутри error_handler: {e}")


# ============================
# 👑 АДМИН-КОМАНДЫ
# ============================
# ADMIN_IDS уже определён в начале файла (строка ~54)

async def approve_flyers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    🎉 НОВОЕ: Админ-команда для одобрения заявок на листовки
    Использование: /approve <user_id> <количество>
    Пример: /approve 1668456209 1000
    """
    user_id = update.effective_user.id
    
    # 🔒 Проверка прав админа
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У тебя нет прав администратора!")
        return
    
    try:
        # Парсим аргументы
        if len(context.args) != 2:
            await update.message.reply_text(
                "❌ Неправильный формат!\n\n"
                "📝 Использование: <code>/approve &lt;user_id&gt; &lt;количество&gt;</code>\n"
                "💡 Пример: <code>/approve 1668456209 1000</code>",
                parse_mode="HTML"
            )
            return
        
        promoter_id = int(context.args[0])
        quantity = int(context.args[1])
        
        if quantity <= 0:
            await update.message.reply_text("❌ Количество должно быть > 0!")
            return
        
        # Находим заявку в Google Sheets
        all_values = flyer_requests_sheet.get_all_values()
        request_found = False
        
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= 5 and str(row[0]) == str(promoter_id) and row[4] == "⏳ Ожидает":
                # Нашли ожидающую заявку
                promoter_name = row[1]
                request_date = row[2]
                
                # Обновляем статус заявки
                from datetime import datetime
                approval_date = datetime.now().strftime("%d.%m.%Y %H:%M")
                flyer_requests_sheet.update_cell(i, 5, "✅ Одобрено")  # Статус
                flyer_requests_sheet.update_cell(i, 6, approval_date)  # Дата одобрения
                
                # Добавляем листовки промоутеру
                current_balance = get_flyer_balance(promoter_id)
                new_balance = current_balance + quantity
                
                # Обновляем баланс в листе "Балансы" (колонка C)
                balances_values = balances_sheet.get_all_values()
                user_found = False
                
                for j, balance_row in enumerate(balances_values[1:], start=2):
                    if len(balance_row) > 0 and str(balance_row[0]) == str(promoter_id):
                        balances_sheet.update_cell(j, 3, str(new_balance))  # Колонка C = 3
                        user_found = True
                        break
                
                # Если пользователя нет в "Балансы" - логируем предупреждение
                if not user_found:
                    logging.warning(f"⚠️ Промоутер {promoter_id} не найден в 'Балансы', листовки не обновлены!")
                
                request_found = True
                
                # 🔔 НОВОЕ: Уведомляем промоутера об одобрении
                try:
                    await context.bot.send_message(
                        chat_id=promoter_id,
                        text=(
                            f"🎉 **ЗАЯВКА ОДОБРЕНА!**\n\n"
                            f"📦 Получено: **{quantity} листовок**\n"
                            f"💼 Новый баланс: **{new_balance} шт**\n\n"
                            f"🚀 Теперь можешь начать работу!\n"
                            f"✅ Нажми '🚀 Начать работу'"
                        ),
                        parse_mode="Markdown"
                    )
                    logging.info(f"✅ Промоутер {promoter_id} уведомлён об одобрении")
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось уведомить промоутера {promoter_id}: {e}")
                
                await update.message.reply_text(
                    f"✅ Заявка одобрена!\n\n"
                    f"👤 Промоутер: {promoter_name} (ID: {promoter_id})\n"
                    f"📦 Количество: {quantity} листовок\n"
                    f"💰 Новый баланс: {new_balance}\n"
                    f"📅 Заявка от: {request_date}\n"
                    f"✅ Одобрено: {approval_date}"
                )
                
                logging.info(f"✅ Админ {user_id} одобрил заявку: {promoter_id} - {quantity} листовок")
                break
        
        if not request_found:
            await update.message.reply_text(
                f"❌ Не найдено ожидающих заявок для промоутера ID: {promoter_id}\n\n"
                f"💡 Проверь лист 'Заявки' в Google Sheets."
            )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неправильный формат!\n\n"
            "📝 user_id и количество должны быть числами!"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка в approve_flyers_command: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def start_expense_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    💸 Админ: быстро добавить расход (печать визиток по прайсу или внеплановый расход)
    Команда: /expense
    """
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ У тебя нет прав администратора!")
        return
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    # Кнопки выбора
    keyboard = [
        [InlineKeyboardButton("🖨️ Печать 1 сторона", callback_data="expense_print_1s_menu"), InlineKeyboardButton("🖨️ Печать 2 стороны", callback_data="expense_print_2s_menu")],
        [InlineKeyboardButton("💸 Другой расход", callback_data="expense_other")]
    ]
    await update.message.reply_text(
        "Выберите вид расхода:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_expense_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик inline-кнопок расходов:
    - expense_print_1s_menu / expense_print_2s_menu: показать варианты количества
    - expense_print_{1s|2s}_{qty}: записать расход
    - expense_other: запрос суммы
    """
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if user_id not in ADMIN_IDS:
        await query.edit_message_text("❌ Нет прав администратора")
        return
    data = query.data or ""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    # Меню 1 сторона
    if data == "expense_print_1s_menu":
        rows = []
        for qty in [120,216,312,504,1008,2016,3000]:
            rows.append([InlineKeyboardButton(f"{qty} шт • {PRICE_TABLE_PRINT_ONE_SIDE.get(qty)}₽", callback_data=f"expense_print_1s_{qty}")])
        rows.append([InlineKeyboardButton("↩️ Назад", callback_data="expense_back")])
        await query.edit_message_text("Выберите тираж (1 сторона):", reply_markup=InlineKeyboardMarkup(rows))
        return
    # Меню 2 стороны
    if data == "expense_print_2s_menu":
        rows = []
        for qty in [120,216,312,504,1008,2016,3000]:
            rows.append([InlineKeyboardButton(f"{qty} шт • {PRICE_TABLE_PRINT_TWO_SIDES.get(qty)}₽", callback_data=f"expense_print_2s_{qty}")])
        rows.append([InlineKeyboardButton("↩️ Назад", callback_data="expense_back")])
        await query.edit_message_text("Выберите тираж (2 стороны):", reply_markup=InlineKeyboardMarkup(rows))
        return
    # Запись расхода печати
    if data.startswith("expense_print_"):
        try:
            _, _, sides, qty_str = data.split("_", 3)
        except ValueError:
            await query.edit_message_text("❌ Неверный формат кнопки")
            return
        try:
            qty = int(qty_str)
        except Exception:
            await query.edit_message_text("❌ Неверное количество")
            return
        if sides == "1s":
            amount = float(PRICE_TABLE_PRINT_ONE_SIDE.get(qty, 0))
            category = "Печать визиток 1 сторона"
        else:
            amount = float(PRICE_TABLE_PRINT_TWO_SIDES.get(qty, 0))
            category = "Печать визиток 2 стороны"
        if amount <= 0:
            await query.edit_message_text("❌ Неизвестный тираж")
            return
        unit_price = amount / qty
        # Запись в Финансы (общий расход, без адреса/района)
        ok = record_finance_entry(user_id, "", "Общий", "Расход", category, qty, unit_price, amount, "Закупка визиток")
        if ok:
            await query.edit_message_text(f"✅ Расход записан: {category} — {qty} шт, {amount:.2f}₽")
        else:
            await query.edit_message_text("❌ Не удалось записать расход")
        return
    # Внеплановый расход (свободная сумма)
    if data == "expense_other":
        # Просим категорию расхода
        user_state[user_id] = user_state.get(user_id, {})
        user_state[user_id]["state"] = "awaiting_expense_category"
        await query.edit_message_text("📝 Введите категорию расхода (например: Логистика, Инструменты, Аренда).")
        return
    # Назад
    if data == "expense_back":
        keyboard = [
            [InlineKeyboardButton("🖨️ Печать 1 сторона", callback_data="expense_print_1s_menu"), InlineKeyboardButton("🖨️ Печать 2 стороны", callback_data="expense_print_2s_menu")],
            [InlineKeyboardButton("💸 Другой расход", callback_data="expense_other")]
        ]
        await query.edit_message_text("Выберите вид расхода:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

async def handle_request_flyers_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    🔔 Обработчик inline-кнопок промоутера для заявки на листовки
    Обрабатывает: request_flyers_{user_id}_{500|1000|1500|custom}, cancel_flyers_{user_id}
    """
    try:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        data = query.data or ""
        
        # Отмена заявки
        if data.startswith("cancel_flyers_"):
            promoter_id = int(data.split("_")[2])
            if promoter_id != user_id:
                await query.answer("❌ Это не твоя заявка")
                return
            # Обновляем статус в Google Sheets
            try:
                rows = flyer_requests_sheet.get_all_values()
                for i, row in enumerate(rows[1:], start=2):
                    if len(row) >= 5 and str(row[0]) == str(promoter_id) and row[4] == "⏳ Ожидает":
                        flyer_requests_sheet.update_cell(i, 5, "❌ Отменено")
                        break
            except Exception as e:
                logging.warning(f"⚠️ Ошибка отмены заявки: {e}")
            
            # Открепляем у промоутера и убираем кнопку отмены
            try:
                msg_id = pinned_promoter_request_messages.get(promoter_id)
                if msg_id:
                    await context.bot.unpin_chat_message(chat_id=promoter_id, message_id=msg_id)
                    # Скрываем кнопку отмены у промоутера
                    try:
                        await context.bot.edit_message_reply_markup(chat_id=promoter_id, message_id=msg_id, reply_markup=None)
                        await context.bot.edit_message_text(chat_id=promoter_id, message_id=msg_id, text="❌ Заявка отменена.\n\n🏠 Возвращаюсь в главное меню.")
                    except Exception:
                        pass
                    del pinned_promoter_request_messages[promoter_id]
            except Exception as e:
                logging.warning(f"⚠️ Не удалось открепить у промоутера: {e}")
            
            # Открепляем у админов и убираем кнопки
            for admin_id in ADMIN_IDS:
                try:
                    key = (admin_id, promoter_id)
                    msg_id = pinned_admin_request_messages.get(key)
                    if msg_id:
                        await context.bot.unpin_chat_message(chat_id=admin_id, message_id=msg_id)
                        # Скрываем кнопки у админа и помечаем как отменено
                        try:
                            await context.bot.edit_message_reply_markup(chat_id=admin_id, message_id=msg_id, reply_markup=None)
                            await context.bot.edit_message_text(chat_id=admin_id, message_id=msg_id, text=f"❌ Заявка от пользователя отменена.")
                        except Exception:
                            pass
                        del pinned_admin_request_messages[key]
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось открепить у админа {admin_id}: {e}")
            
            await query.edit_message_text(
                "❌ Заявка отменена.\n\n"
                "🏠 Возвращаюсь в главное меню."
            )
            return
        
        if not data.startswith("request_flyers_"):
            return
        # 🔥 Правильный парсинг: request_flyers_{user_id}_{choice}
        parts = data.split("_")
        if len(parts) < 4:  # request + flyers + user_id + choice
            logging.error(f"❌ Неправильный формат callback_data: {data}")
            return
        promoter_id = int(parts[2])  # request_flyers_{USER_ID}_choice
        choice = parts[3]  # request_flyers_user_id_{CHOICE}
        if promoter_id != user_id:
            await query.answer("❌ Это не твоя заявка")
            return
        
        # Свой объём — показываем калькулятор
        if choice == "custom":
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            keyboard = [
                [InlineKeyboardButton("1", callback_data=f"req_num_{user_id}_1"), InlineKeyboardButton("2", callback_data=f"req_num_{user_id}_2"), InlineKeyboardButton("3", callback_data=f"req_num_{user_id}_3")],
                [InlineKeyboardButton("4", callback_data=f"req_num_{user_id}_4"), InlineKeyboardButton("5", callback_data=f"req_num_{user_id}_5"), InlineKeyboardButton("6", callback_data=f"req_num_{user_id}_6")],
                [InlineKeyboardButton("7", callback_data=f"req_num_{user_id}_7"), InlineKeyboardButton("8", callback_data=f"req_num_{user_id}_8"), InlineKeyboardButton("9", callback_data=f"req_num_{user_id}_9")],
                [InlineKeyboardButton("0", callback_data=f"req_num_{user_id}_0"), InlineKeyboardButton("00", callback_data=f"req_num_{user_id}_00"), InlineKeyboardButton("⬅️ Удалить", callback_data=f"req_num_{user_id}_del")],
                [InlineKeyboardButton("✅ Отправить", callback_data=f"req_confirm_{user_id}"), InlineKeyboardButton("❌ Отмена", callback_data=f"req_cancel_custom_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Сохраняем состояние
            if user_id not in user_state:
                user_state[user_id] = {}
            user_state[user_id]["req_custom_qty"] = ""
            await query.edit_message_text(
                "💯 **Введи количество листовок:**\n\n📦 Количество: **0**\n\n⌨️ Используй калькулятор ниже:",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        
        # Фиксированный объём
        quantity = int(choice)
        user_name = get_user_name_from_balances(user_id) or query.from_user.first_name or "Промоутер"
        success = create_flyer_request(user_id, user_name, quantity)
        if not success:
            await query.answer("⚠️ Уже есть ожидающая заявка")
            return
        
        # Уведомляем админов (с кнопкой связи) и закрепляем
        try:
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            global _pending_admin_notification
            if _pending_admin_notification:
                # 🔥 Кнопки для админа: конкретное кол-во из заявки + своё кол-во + чат + отклонить
                requested_qty = _pending_admin_notification['quantity']
                adm_kb = [
                    [InlineKeyboardButton(f"📦 {requested_qty} шт (как запрошено)", callback_data=f"approve_{user_id}_{requested_qty}")],
                    [InlineKeyboardButton("💯 Своё кол-во", callback_data=f"approve_{user_id}_custom")],
                    [InlineKeyboardButton("💬 Чат с промоутером", url=f"tg://user?id={user_id}")],
                    [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_request_{user_id}")]
                ]
                adm_markup = InlineKeyboardMarkup(adm_kb)
                admin_message = (
                    f"🆕 **НОВАЯ ЗАЯВКА НА ЛИСТОВКИ**\n\n"
                    f"👤 Промоутер: {_pending_admin_notification['user_name']} (ID: `{_pending_admin_notification['user_id']}`)\n"
                    f"📦 Запрошено: **{requested_qty} листовок**\n"
                    f"⏰ Дата: {_pending_admin_notification['request_date']}\n\n"
                    f"⚡ Выбери действие:"
                )
                for admin_id in ADMIN_IDS:
                    try:
                        admin_msg = await context.bot.send_message(chat_id=admin_id, text=admin_message, parse_mode="Markdown", reply_markup=adm_markup)
                        pinned_admin_request_messages[(admin_id, user_id)] = admin_msg.message_id
                        await context.bot.pin_chat_message(chat_id=admin_id, message_id=admin_msg.message_id, disable_notification=False)
                    except Exception as e:
                        logging.warning(f"⚠️ Ошибка уведомления админа {admin_id}: {e}")
        except Exception as e:
            logging.warning(f"⚠️ Ошибка подготовки уведомлений админам: {e}")
        
        # Сообщение промоутеру и закрепление
        try:
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            # 🔧 ИСПРАВЛЕНО: Кнопка отмены только если заявка в статусе "⏳ Ожидает"
            # Проверяем статус заявки
            has_pending_request = False
            try:
                all_values = flyer_requests_sheet.get_all_values()
                for row in all_values[1:]:
                    if len(row) >= 5 and str(row[0]) == str(user_id) and row[4] == "⏳ Ожидает":
                        has_pending_request = True
                        break
            except Exception as e:
                logging.warning(f"⚠️ Ошибка проверки статуса заявки: {e}")
                has_pending_request = True  # Показываем кнопку на всякий случай
            
            if has_pending_request:
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отменить заявку", callback_data=f"cancel_flyers_{user_id}")]])
            else:
                kb = None  # Нет кнопок
            
            pm_msg = await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"📦 **Заявка отправлена!**\n\n"
                    f"📦 Количество: **{quantity} шт**\n"
                    f"⏳ Статус: **Ожидает одобрения админа**\n\n"
                    f"🛠️ Изготовление занимает **1–3 дня**\n"
                    f"🔔 Уведомлю, как только админ примет решение."
                ),
                parse_mode="Markdown",
                reply_markup=kb
            )
            pinned_promoter_request_messages[user_id] = pm_msg.message_id
            await context.bot.pin_chat_message(chat_id=user_id, message_id=pm_msg.message_id, disable_notification=False)
        except Exception as e:
            logging.warning(f"⚠️ Не удалось отправить или закрепить сообщение промоутеру: {e}")
        
        await query.edit_message_text(f"✅ Выбрано: {quantity} шт. Заявка создана и отправлена администратору.")
    except Exception as e:
        # Телеграм может вернуть BadRequest: Message is not modified — в этом случае просто игнорируем обновление
        msg = str(e)
        if "Message is not modified" in msg:
            logging.warning("⚠️ Message is not modified — пропускаю обновление текста заявки")
            return
        logging.error(f"❌ Ошибка в handle_request_flyers_callback: {e}")

async def handle_existing_flyers_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🔥 НОВОЕ: Обработчик inline-кнопок с количеством уже наклеенных листовок"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        
        # Подтверждаем нажатие кнопки
        await query.answer()
        
        # Получаем данные
        exit_stats = user_state.get(user_id, {}).get("exit_stats", {})
        photos_uploaded = exit_stats.get("photos_uploaded", 0)
        total_amount = exit_stats.get("total_amount", 0)
        selected_address = exit_stats.get("selected_address", "Неизвестный адрес")
        stats = get_session_stats(user_id)
        
        # Обрабатываем ответ
        if query.data.startswith("existing_flyers_"):
            if query.data == "existing_flyers_skip":
                existing_count = None
                logging.info(f"👤 Пользователь {user_id} пропустил вопрос о листовках")
            else:
                existing_count = int(query.data.split("_")[2])
                logging.info(f"📊 Пользователь {user_id}: уже было {existing_count} щитов с нашими листовками на {selected_address}")
                
                # 🎯 НОВОЕ: Сохраняем данные в Google Sheets (колонка J - ЛИСТОВКИ ДО)
                try:
                    if sprav:
                        all_values = sprav.get_all_values()
                        normalized_input = normalize_text(selected_address)
                        
                        for i, row in enumerate(all_values[1:], start=2):
                            if len(row) >= 1:
                                addr = row[0]
                                if normalize_text(addr) == normalized_input:
                                    # Обновляем столбец J (Листовки до)
                                    sprav.update_cell(i, 10, str(existing_count))  # Столбец J (10)
                                    logging.info(f"✅ Данные сохранены: {selected_address} → {existing_count} листовок до (столбец J)")
                                    break
                except Exception as e:
                    logging.error(f"❌ Ошибка сохранения данных в справочник: {e}")
        
        # Очищаем состояние
        user_state[user_id]["state"] = None
        user_state[user_id]["photos_uploaded"] = 0
        user_state[user_id]["exit_stats"] = {}
        
        # Показываем ближайшие адреса (НЕ возвращаем в меню!)
        if "current_location" in user_state.get(user_id, {}):
            user_lat = user_state[user_id]["current_location"][0]
            user_lng = user_state[user_id]["current_location"][1]
            
            # Ищем ближайшие адреса (исключаем текущий) в радиусе 1 км
            nearby_addresses = get_or_create_nearby_addresses(user_lat, user_lng, exclude_address=selected_address, limit=MAX_NEARBY_ADDRESSES)
            
            if nearby_addresses:
                # Формируем сообщение
                result_text = (
                    f"✅ **Работа завершена!**\n\n"
                    f"💰 Начислено: **{total_amount:.2f}₽** ({photos_uploaded} фото)\n"
                    f"📦 Списано листовок: {photos_uploaded} шт\n\n"
                    f"📈 **Сессия:** {stats['addresses']} адресов | {stats['photos']} фото | {stats['earnings']}₽\n\n"
                    f"🎯 **Вот ближайшие адреса для продолжения:**\n\n"
                )
                
                address_list = []
                for i, (addr, addr_lat, addr_lng, distance, status_icon) in enumerate(nearby_addresses, 1):
                    address_list.append(f"{status_icon} **{addr}** ({int(distance)} м)")
                
                result_text += "\n".join(address_list)
                result_text += "\n\n👇 Выбери следующий адрес:"
                
                # Кнопки с адресами
                keyboard = []
                # Кнопка добавления своего адреса - всегда первая
                keyboard.append(["📍 Добавить адрес"])
                
                for addr, _, _, distance, status_icon in nearby_addresses:
                    keyboard.append([f"{status_icon} {addr} ({int(distance)} м)"])
                
                keyboard.append(["Вернуться в меню"])
                
                await query.edit_message_text(
                    result_text,
                    parse_mode="Markdown"
                )
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text="👇 Выбери следующий адрес:",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                )
            else:
                # Нет ближайших адресов
                # KeyboardButton импортируется на уровне модуля
                keyboard = [
                    [KeyboardButton("🔍 Сканировать район", request_location=True)],
                    ["📍 Добавить адрес"],
                    ["Вернуться в меню"]
                ]
                
                await query.edit_message_text(
                    f"✅ **Работа завершена!**\n\n"
                    f"💰 Начислено: **{total_amount:.2f}₽** ({photos_uploaded} фото)\n"
                    f"📦 Списано листовок: {photos_uploaded} шт\n\n"
                    f"📈 **Сессия:** {stats['addresses']} адресов | {stats['photos']} фото | {stats['earnings']}₽\n\n"
                    f"👏 Отличная работа! Переместись в другое место или вернись в меню.",
                    parse_mode="Markdown"
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text="📡 Отправь геолокацию для сканирования района или добавь новый адрес!",
                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                )
        else:
            # Нет геолокации
            keyboard = [
                ["📍 Добавить адрес"],
                ["Вернуться в меню"]
            ]
                        
            await query.edit_message_text(
                f"✅ **Работа завершена!**\n\n"
                f"💰 Начислено: **{total_amount:.2f}₽** ({photos_uploaded} фото)\n"
                f"📦 Списано листовок: {photos_uploaded} шт\n\n"
                f"📈 **Сессия:** {stats['addresses']} адресов | {stats['photos']} фото | {stats['earnings']}₽\n\n"
                f"👏 Отличная работа!\n\n"
                f"📍 Добавь новый адрес для продолжения работы!",
                parse_mode="Markdown"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text="📍 Добавь новый адрес для продолжения работы!",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            )
            
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_existing_flyers_callback: {e}")


async def handle_entrance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик inline-кнопок с номером подъезда"""
    try:
        query = update.callback_query
        user_id = query.from_user.id
        
        # Подтверждаем нажатие кнопки
        await query.answer()
        
        if query.data.startswith("entrance_"):
            entrance_num = int(query.data.split("_")[1])
            
            # Сохраняем номер подъезда
            user_state[user_id]["entrance_number"] = entrance_num
            user_state[user_id]["session_target_photos"] = min(15, entrance_num * 3)
            user_state[user_id]["photos_uploaded"] = 0
            user_state[user_id]["state"] = "awaiting_photos"
            
            session_target = user_state[user_id]["session_target_photos"]
            
            # Редактируем сообщение с прогресс-баром
            filled = 0
            progress_bar = "░" * 10
            
            # Для первого фото скрываем информацию о прогрессе
            message_text = f"✅ Подъезд №{entrance_num} — поехали!\n\n"
            message_text += f"📸 Загружай фото электрощитов с листовками!\n\n"
            message_text += f"💡 Приоритет — на многоэтажки!"
            
            await query.edit_message_text(message_text)
            
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_entrance_callback: {e}")


async def handle_coords_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Админский обработчик подтверждения/отклонения координат"""
    try:
        query = update.callback_query
        admin_id = query.from_user.id
        await query.answer()
        if admin_id not in ADMIN_IDS:
            await query.answer("❌ Нет прав админа")
            return
        data = query.data or ""
        if data.startswith("coord_approve_"):
            promoter_id = int(data.split("_")[2])
            # Снимаем закрепы
            try:
                msg_id = pinned_admin_coord_messages.get((admin_id, promoter_id))
                if msg_id:
                    await context.bot.unpin_chat_message(chat_id=admin_id, message_id=msg_id)
                    del pinned_admin_coord_messages[(admin_id, promoter_id)]
            except Exception:
                pass
            try:
                pm_msg_id = pinned_promoter_coord_messages.get(promoter_id)
                if pm_msg_id:
                    await context.bot.unpin_chat_message(chat_id=promoter_id, message_id=pm_msg_id)
                    del pinned_promoter_coord_messages[promoter_id]
            except Exception:
                pass
            # Начисляем бонусы до конца дня
            us = user_state.get(promoter_id, {})
            temp_mult = float(us.get("address_bonus_multiplier", 1.0)) + 0.10
            if promoter_id not in user_state:
                user_state[promoter_id] = {}
            user_state[promoter_id]["address_bonus_multiplier"] = temp_mult
            # Временная надбавка до конца дня
            user_state[promoter_id]["day_bonus_temp_increment"] = 0.10
            # Установка срока действия (конец дня локального времени)
            expires = datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)
            user_state[promoter_id]["day_bonus_expires_at"] = expires
            # Уведомляем админа и промоутера
            await query.edit_message_text("✅ Координаты подтверждены. Промоутер уведомлён.")
            try:
                await context.bot.send_message(
                    chat_id=promoter_id,
                    text=(
                        "✅ Координаты подтверждены администратором!\n\n"
                        "🎁 Спасибо за сотрудничество — вознаграждение начислено.\n"
                        "🔥 Активность: +10% к премии до конца дня."
                    )
                )
            except Exception:
                pass
        elif data.startswith("coord_reject_"):
            promoter_id = int(data.split("_")[2])
            # Снимаем закрепы
            try:
                msg_id = pinned_admin_coord_messages.get((admin_id, promoter_id))
                if msg_id:
                    await context.bot.unpin_chat_message(chat_id=admin_id, message_id=msg_id)
                    del pinned_admin_coord_messages[(admin_id, promoter_id)]
            except Exception:
                pass
            try:
                pm_msg_id = pinned_promoter_coord_messages.get(promoter_id)
                if pm_msg_id:
                    await context.bot.unpin_chat_message(chat_id=promoter_id, message_id=pm_msg_id)
                    del pinned_promoter_coord_messages[promoter_id]
            except Exception:
                pass
            await query.edit_message_text("❌ Координаты отклонены.")
            try:
                await context.bot.send_message(chat_id=promoter_id, text=("❌ Администратор отклонил обновление координат.\n💬 Попробуй ещё раз, убедившись, что стоишь у входа."))
            except Exception:
                pass
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_coords_admin_callback: {e}")
        return

async def handle_void_address_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    👑 Админ: аннулировать оплату полностью по адресу (не по конкретному фото)
    callback_data варианты:
    - void_addr_idx_{row_idx}: взять адрес из строки в 'Отчёты' и аннулировать все записи по этому адресу
    """
    try:
        query = update.callback_query
        admin_id = query.from_user.id
        if admin_id not in ADMIN_IDS:
            await query.answer("❌ Нет прав")
            return
        await query.answer()
        data = query.data or ""
        address = None
        promoter_ids_to_adjust: Dict[int, float] = {}
        if data.startswith("void_addr_idx_"):
            try:
                row_idx = int(data.replace("void_addr_idx_", ""))
            except ValueError:
                await query.message.reply_text("❌ Неверный параметр")
                return
            rows = otchety.get_all_values()
            if row_idx <= 1 or row_idx > len(rows):
                await query.message.reply_text("❌ Неверный номер строки")
                return
            row = rows[row_idx - 1]
            address = row[2] if len(row) > 2 else None
        if not address:
            await query.message.reply_text("❌ Адрес не найден")
            return
        # 1) Отмечаем ВСЕ записи по адресу в 'Отчёты' как ОТКЛОНЕНО
        try:
            rows = otchety.get_all_values()
            void_reports = 0
            for i, r in enumerate(rows[1:], start=2):
                if len(r) < 3:
                    continue
                r_address = r[2]
                status = r[9] if len(r) > 9 else ""
                if normalize_text(r_address) == normalize_text(address) and status != "ОТКЛОНЕНО":
                    try:
                        otchety.update_cell(i, 10, "ОТКЛОНЕНО")
                        void_reports += 1
                    except Exception:
                        pass
        except Exception as e:
            logging.warning(f"⚠️ Ошибка аннулирования отчётов по адресу '{address}': {e}")
        # 2) Аннулируем доходы по адресу в 'Финансы' и собираем суммы для коррекции баланса
        void_income_total = 0.0
        void_fin_rows = 0
        try:
            if finance_sheet:
                fin_rows = finance_sheet.get_all_values()
                # Убедимся, что есть колонка K: Статус
                try:
                    finance_sheet.update(values=[["Статус"]], range_name="K1")
                except Exception:
                    pass
                for i, frow in enumerate(fin_rows[1:], start=2):
                    if len(frow) < 10:
                        continue
                    f_date, f_promoter, f_address, f_district, f_type, f_cat, f_qty, f_unit, f_amount, f_comment = frow[:10]
                    f_status = frow[10] if len(frow) >= 11 else ""
                    if f_status == "VOID":
                        continue
                    if normalize_text(f_address) == normalize_text(address):
                        # VOID запись
                        try:
                            finance_sheet.update_cell(i, 11, "VOID")
                            void_fin_rows += 1
                        except Exception:
                            pass
                        # Корректируем только доходы
                        try:
                            amt = float(f_amount)
                        except Exception:
                            amt = 0.0
                        if f_type == "Доход" and amt > 0:
                            void_income_total += amt
                            try:
                                pid = int(f_promoter)
                                promoter_ids_to_adjust[pid] = promoter_ids_to_adjust.get(pid, 0.0) + amt
                            except Exception:
                                pass
        except Exception as e:
            logging.warning(f"⚠️ Ошибка аннулирования финансов по адресу '{address}': {e}")
        # 3) Корректируем баланс каждому промоутеру
        adjusted_users = []
        for pid, amt in promoter_ids_to_adjust.items():
            if amt > 0:
                try:
                    update_balance(pid, -amt)
                    adjusted_users.append((pid, amt))
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось скорректировать баланс промоутера {pid}: {e}")
        # Ответ администратору
        lines = [
            f"✅ Аннулирование по адресу: {address}",
            f"📄 Отклонено записей в 'Отчёты': {void_reports}",
            f"📒 Помечено VOID в 'Финансы': {void_fin_rows}",
            f"💸 Возврат всего: {void_income_total:.2f}₽"
        ]
        if adjusted_users:
            lines.append("\n👥 Коррекция баланса:")
            for pid, amt in adjusted_users:
                lines.append(f"• Пользователь {pid}: -{amt:.2f}₽")
        await query.message.reply_text("\n".join(lines))
    except Exception as e:
        logging.error(f"❌ Ошибка handle_void_address_callback: {e}")
        try:
            await update.callback_query.answer("❌ Ошибка")
        except Exception:
            pass


async def handle_promoter_calculator_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    🧮 Обработчик калькулятора промоутера: req_num_{user_id}_{digit}, req_confirm_{user_id}, req_cancel_custom_{user_id}
    """
    try:
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        data = query.data or ""
        
        # Отмена
        if data.startswith("req_cancel_custom_"):
            await query.edit_message_text(
                "❌ Отмена ввода количества.\n\n"
                "🏠 Возвращаюсь в главное меню."
            )
            return
        
        # Цифры
        if data.startswith("req_num_"):
            parts = data.split("_")
            target_id = int(parts[2])
            digit = parts[3]
            if target_id != user_id:
                await query.answer("❌ Это не твоя заявка")
                return
            current = user_state.get(user_id, {}).get("req_custom_qty", "")
            if digit == "del":
                current = current[:-1]
            else:
                if len(current) < 6:
                    current += digit
            if user_id not in user_state:
                user_state[user_id] = {}
            user_state[user_id]["req_custom_qty"] = current
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            keyboard = [
                [InlineKeyboardButton("1", callback_data=f"req_num_{user_id}_1"), InlineKeyboardButton("2", callback_data=f"req_num_{user_id}_2"), InlineKeyboardButton("3", callback_data=f"req_num_{user_id}_3")],
                [InlineKeyboardButton("4", callback_data=f"req_num_{user_id}_4"), InlineKeyboardButton("5", callback_data=f"req_num_{user_id}_5"), InlineKeyboardButton("6", callback_data=f"req_num_{user_id}_6")],
                [InlineKeyboardButton("7", callback_data=f"req_num_{user_id}_7"), InlineKeyboardButton("8", callback_data=f"req_num_{user_id}_8"), InlineKeyboardButton("9", callback_data=f"req_num_{user_id}_9")],
                [InlineKeyboardButton("0", callback_data=f"req_num_{user_id}_0"), InlineKeyboardButton("00", callback_data=f"req_num_{user_id}_00"), InlineKeyboardButton("⬅️ Удалить", callback_data=f"req_num_{user_id}_del")],
                [InlineKeyboardButton("✅ Отправить", callback_data=f"req_confirm_{user_id}"), InlineKeyboardButton("❌ Отмена", callback_data=f"req_cancel_custom_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            display = current if current else "0"
            await query.edit_message_text(
                f"💯 **Введи количество листовок:**\n\n📦 Количество: **{display}**\n\n⌨️ Используй калькулятор ниже:",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        
        # Подтверждение
        if data.startswith("req_confirm_"):
            target_id = int(data.split("_")[2])
            if target_id != user_id:
                await query.answer("❌ Это не твоя заявка")
                return
            qty_str = user_state.get(user_id, {}).get("req_custom_qty", "")
            if not qty_str or not qty_str.isdigit() or int(qty_str) <= 0:
                await query.answer("❌ Введи корректное количество!")
                return
            quantity = int(qty_str)
            user_name = get_user_name_from_balances(user_id) or query.from_user.first_name or "Промоутер"
            success = create_flyer_request(user_id, user_name, quantity)
            if not success:
                await query.answer("⚠️ Уже есть ожидающая заявка")
                return
            # Аналогично отправляем админам и закрепляем (как в handle_request_flyers_callback)
            try:
                # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
                global _pending_admin_notification
                if _pending_admin_notification:
                    # 🔥 Кнопки для админа: конкретное кол-во из заявки + своё кол-во + чат + отклонить
                    requested_qty = _pending_admin_notification['quantity']
                    adm_kb = [
                        [InlineKeyboardButton(f"📦 {requested_qty} шт (как запрошено)", callback_data=f"approve_{user_id}_{requested_qty}")],
                        [InlineKeyboardButton("💯 Своё кол-во", callback_data=f"approve_{user_id}_custom")],
                        [InlineKeyboardButton("💬 Чат с промоутером", url=f"tg://user?id={user_id}")],
                        [InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_request_{user_id}")]
                    ]
                    adm_markup = InlineKeyboardMarkup(adm_kb)
                    admin_message = (
                        f"🆕 **НОВАЯ ЗАЯВКА НА ЛИСТОВКИ**\n\n"
                        f"👤 Промоутер: {_pending_admin_notification['user_name']} (ID: `{_pending_admin_notification['user_id']}`)\n"
                        f"📦 Запрошено: **{requested_qty} листовок**\n"
                        f"⏰ Дата: {_pending_admin_notification['request_date']}\n\n"
                        f"⚡ Выбери действие:"
                    )
                    for admin_id in ADMIN_IDS:
                        try:
                            admin_msg = await context.bot.send_message(chat_id=admin_id, text=admin_message, parse_mode="Markdown", reply_markup=adm_markup)
                            pinned_admin_request_messages[(admin_id, user_id)] = admin_msg.message_id
                            await context.bot.pin_chat_message(chat_id=admin_id, message_id=admin_msg.message_id, disable_notification=False)
                        except Exception as e:
                            logging.warning(f"⚠️ Ошибка уведомления админа {admin_id}: {e}")
            except Exception as e:
                logging.warning(f"⚠️ Ошибка подготовки уведомлений админам: {e}")
            # Сообщение промоутеру и закрепление
            try:
                # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
                # 🔧 ИСПРАВЛЕНО: Кнопка отмены только если заявка в статусе "⏳ Ожидает"
                has_pending_request = False
                try:
                    all_values_check = flyer_requests_sheet.get_all_values()
                    for row in all_values_check[1:]:
                        if len(row) >= 5 and str(row[0]) == str(user_id) and row[4] == "⏳ Ожидает":
                            has_pending_request = True
                            break
                except Exception as e:
                    logging.warning(f"⚠️ Ошибка проверки статуса заявки: {e}")
                    has_pending_request = True  # Показываем кнопку на всякий случай
                
                if has_pending_request:
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отменить заявку", callback_data=f"cancel_flyers_{user_id}")]])
                else:
                    kb = None  # Нет кнопок
                
                pm_msg = await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"📦 **Заявка отправлена!**\n\n"
                        f"📦 Количество: **{quantity} шт**\n"
                        f"⏳ Статус: **Ожидает одобрения админа**\n\n"
                        f"🛠️ Изготовление занимает **1–3 дня**\n"
                        f"🔔 Уведомлю, как только админ примет решение."
                    ),
                    parse_mode="Markdown",
                    reply_markup=kb
                )
                pinned_promoter_request_messages[user_id] = pm_msg.message_id
                await context.bot.pin_chat_message(chat_id=user_id, message_id=pm_msg.message_id, disable_notification=False)
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить или закрепить сообщение промоутеру: {e}")
            await query.edit_message_text(f"✅ Выбрано: {quantity} шт. Заявка создана и отправлена администратору.")
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_promoter_calculator_callback: {e}")
    """
    🧮 НОВОЕ: Обработчик калькулятора для ввода количества листовок
    Обрабатывает: num_{promoter_id}_{digit}, confirm_approve_{promoter_id}, cancel_custom_{promoter_id}
    """
    try:
        query = update.callback_query
        admin_id = query.from_user.id
        
        if admin_id not in ADMIN_IDS:
            await query.answer("❌ У тебя нет прав администратора!")
            return
        
        await query.answer()
        
        # 🔢 Цифровые кнопки
        if query.data.startswith("num_"):
            parts = query.data.split("_")
            promoter_id = int(parts[1])
            action = parts[2]
            
            # Получаем текущее значение
            current = user_state.get(admin_id, {}).get("custom_quantity", "")
            
            # Обработка действий
            if action == "del":
                current = current[:-1]  # Удаляем последнюю цифру
            else:
                # Добавляем цифру (максимум 6 символов)
                if len(current) < 6:
                    current += action
            
            # Сохраняем
            if admin_id not in user_state:
                user_state[admin_id] = {}
            user_state[admin_id]["custom_quantity"] = current
            
            # Обновляем сообщение
            # InlineKeyboardButton, InlineKeyboardMarkup импортируются на уровне модуля
            keyboard = [
                [InlineKeyboardButton("1", callback_data=f"num_{promoter_id}_1"), InlineKeyboardButton("2", callback_data=f"num_{promoter_id}_2"), InlineKeyboardButton("3", callback_data=f"num_{promoter_id}_3")],
                [InlineKeyboardButton("4", callback_data=f"num_{promoter_id}_4"), InlineKeyboardButton("5", callback_data=f"num_{promoter_id}_5"), InlineKeyboardButton("6", callback_data=f"num_{promoter_id}_6")],
                [InlineKeyboardButton("7", callback_data=f"num_{promoter_id}_7"), InlineKeyboardButton("8", callback_data=f"num_{promoter_id}_8"), InlineKeyboardButton("9", callback_data=f"num_{promoter_id}_9")],
                [InlineKeyboardButton("0", callback_data=f"num_{promoter_id}_0"), InlineKeyboardButton("00", callback_data=f"num_{promoter_id}_00"), InlineKeyboardButton("⬅️ Удалить", callback_data=f"num_{promoter_id}_del")],
                [InlineKeyboardButton("✅ Одобрить", callback_data=f"confirm_approve_{promoter_id}"), InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_custom_{promoter_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            display_value = current if current else "0"
            await query.edit_message_text(
                f"💯 **Введи количество листовок:**\n\n"
                f"👤 Промоутер ID: `{promoter_id}`\n"
                f"📦 Количество: **{display_value}**\n\n"
                f"⌨️ Используй калькулятор ниже:",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        
        # ✅ Подтверждение
        elif query.data.startswith("confirm_approve_"):
            promoter_id = int(query.data.split("_")[2])
            custom_quantity = user_state.get(admin_id, {}).get("custom_quantity", "")
            
            if not custom_quantity or int(custom_quantity) <= 0:
                await query.answer("❌ Введи корректное количество!")
                return
            
            quantity = int(custom_quantity)
            
            # Выполняем одобрение
            success = await process_approval(promoter_id, quantity, context)
            
            # Очищаем состояние
            user_state[admin_id]["custom_quantity"] = ""
            
            if success:
                # 🔥 ОТКРЕПЛЯЕМ сообщение
                try:
                    await context.bot.unpin_chat_message(
                        chat_id=admin_id,
                        message_id=query.message.message_id
                    )
                    logging.info(f"📍 Сообщение с заявкой откреплено после одобрения")
                except Exception as unpin_error:
                    logging.warning(f"⚠️ Не удалось открепить: {unpin_error}")
                
                await query.edit_message_text(
                    f"✅ **ЗАЯВКА ОДОБРЕНА!**\n\n"
                    f"👤 Промоутер ID: `{promoter_id}`\n"
                    f"📦 Количество: **{quantity} шт**\n\n"
                    f"✅ Промоутер уведомлён!",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    f"❌ **ОШИБКА!**\n\n"
                    f"⚠️ Не найдено ожидающих заявок.",
                    parse_mode="Markdown"
                )
        
        # ❌ Отмена
        elif query.data.startswith("cancel_custom_"):
            # Очищаем состояние
            if admin_id in user_state:
                user_state[admin_id]["custom_quantity"] = ""
            
            await query.edit_message_text(
                "❌ Отменено.\n\n"
                "💡 Заявка осталась в статусе '⏳ Ожидает'.\n\n"
                "🏠 Возвращаюсь в главное меню.",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_calculator_callback: {e}")
        try:
            await query.answer("❌ Произошла ошибка!")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось отправить ответ на callback: {e}")


async def process_approval(promoter_id: int, quantity: int, context) -> bool:
    """
    📦 НОВОЕ: Общая логика одобрения заявки
    Возвращает True при успехе, False при ошибке
    """
    try:
        # Находим заявку в Google Sheets
        all_values = flyer_requests_sheet.get_all_values()
        
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) >= 5 and str(row[0]) == str(promoter_id) and row[4] == "⏳ Ожидает":
                promoter_name = row[1]
                
                # Обновляем статус заявки
                from datetime import datetime
                approval_date = datetime.now().strftime("%d.%m.%Y %H:%M")
                flyer_requests_sheet.update_cell(i, 5, "✅ Одобрено")
                flyer_requests_sheet.update_cell(i, 6, approval_date)
                
                # Добавляем листовки
                current_balance = get_flyer_balance(promoter_id)
                new_balance = current_balance + quantity
                
                # Обновляем баланс в листе "Балансы" (колонка C)
                balances_values = balances_sheet.get_all_values()
                user_found = False
                
                for j, balance_row in enumerate(balances_values[1:], start=2):
                    if len(balance_row) > 0 and str(balance_row[0]) == str(promoter_id):
                        balances_sheet.update_cell(j, 3, str(new_balance))  # Колонка C = 3
                        user_found = True
                        break
                
                if not user_found:
                    logging.warning(f"⚠️ Промоутер {promoter_id} не найден в 'Балансы', листовки не обновлены!")
                
                # 🔥 НОВОЕ: Открепляем сообщения у промоутера и админов
                try:
                    # Открепляем у промоутера
                    if promoter_id in pinned_promoter_request_messages:
                        pm_msg_id = pinned_promoter_request_messages[promoter_id]
                        try:
                            await context.bot.unpin_chat_message(chat_id=promoter_id, message_id=pm_msg_id)
                            logging.info(f"📍 Откреплено сообщение у промоутера {promoter_id}")
                            del pinned_promoter_request_messages[promoter_id]
                        except Exception as unpin_error:
                            logging.warning(f"⚠️ Не удалось открепить у промоутера: {unpin_error}")
                    
                    # Открепляем у всех админов
                    for admin_id in ADMIN_IDS:
                        if (admin_id, promoter_id) in pinned_admin_request_messages:
                            admin_msg_id = pinned_admin_request_messages[(admin_id, promoter_id)]
                            try:
                                await context.bot.unpin_chat_message(chat_id=admin_id, message_id=admin_msg_id)
                                logging.info(f"📍 Откреплено сообщение у админа {admin_id}")
                                del pinned_admin_request_messages[(admin_id, promoter_id)]
                            except Exception as unpin_error:
                                logging.warning(f"⚠️ Не удалось открепить у админа: {unpin_error}")
                except Exception as e:
                    logging.warning(f"⚠️ Ошибка открепления сообщений: {e}")
                
                # Уведомляем промоутера
                try:
                    # Получаем текущий streak для отображения мотивационного сообщения
                    streak_days = get_work_streak(promoter_id)
                    activity_multiplier = min(1.0 + 0.10 * streak_days, 1.5)
                    effective_panel_rate = 3.0 * activity_multiplier * user_state.get(promoter_id, {}).get("address_bonus_multiplier", 1.0)
                    
                    # 💰 Рассчитываем потенциальный заработок С УЧЁТОМ ЕЖЕДНЕВНЫХ БОНУСОВ
                    # Пример: 1000 листовок = ~1000 фото (если 1 листовка = 1 фото)
                    # Заработок за фото + ежедневные бонусы (70/100/150 фото)
                    estimated_photos = quantity  # Примерное кол-во фото
                    photo_earnings = estimated_photos * effective_panel_rate
                    
                    # Ежедневные бонусы (с учётом activity_multiplier)
                    # Пример: 70 фото = 500₽, 100 фото = 700₽, 150 фото = 1000₽
                    daily_bonus = 0
                    if estimated_photos >= 150:
                        daily_bonus = 1000 * activity_multiplier
                    elif estimated_photos >= 100:
                        daily_bonus = 700 * activity_multiplier
                    elif estimated_photos >= 70:
                        daily_bonus = 500 * activity_multiplier
                    
                    potential_earnings = photo_earnings + daily_bonus
                    
                    # Формируем текст бонуса
                    bonus_percent = int((activity_multiplier - 1.0)*100)
                    if bonus_percent > 0:
                        bonus_text = f"🔥 Активность: +{bonus_percent}% ({streak_days} дн. подряд)"
                    else:
                        bonus_text = "🔥 Активность: 0% (начни работать ежедневно!)"
                    
                    await context.bot.send_message(
                        chat_id=promoter_id,
                        text=(
                            f"🎉 **ЗАЯВКА ОДОБРЕНА!**\n\n"
                            f"📦 Получено: **{quantity} листовок**\n\n"
                            f"💰 Потенциальный заработок: **{potential_earnings:.0f}₽**\n"
                            f"   • За фото: {photo_earnings:.0f}₽ (по {effective_panel_rate:.1f}₽ +{int((activity_multiplier - 1.0)*100)}%)\n"
                            f"   • Ежедневные бонусы: {daily_bonus:.0f}₽\n\n"
                            f"{bonus_text}\n\n"
                            f"🚀 Теперь можешь начать работу!\n"
                            f"✅ Нажми '🚀 Начать работу'"
                        ),
                        parse_mode="Markdown"
                    )
                    logging.info(f"✅ Промоутер {promoter_id} уведомлён об одобрении")
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось уведомить промоутера {promoter_id}: {e}")
                
                logging.info(f"✅ Заявка одобрена: {promoter_id} - {quantity} листовок")
                return True
        
        # Не нашли заявку
        logging.warning(f"⚠️ Не найдена ожидающая заявка для {promoter_id}")
        return False
        
    except Exception as e:
        logging.error(f"❌ Ошибка в process_approval: {e}")
        return False


async def handle_feedback_idea(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        await query.message.reply_text("💡 Напиши идею ответным сообщением — мы передадим её администратору.")
        if user_id not in user_state:
            user_state[user_id] = {}
        user_state[user_id]["state"] = "awaiting_feedback_idea"
    except Exception as e:
        logging.warning(f"⚠️ Ошибка обработки идеи: {e}")

async def handle_create_route_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки '🗺️ Создать свой маршрут'"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # 🔥 ИСПРАВЛЕНО: Простое сообщение с кнопкой "Добавить адрес"
        instruction_text = (
            "🗺️ **Создание личного маршрута**\n\n"
            "🎯 Как это работает:\n\n"
            "1️⃣ Подойди к любому дому в Калининграде\n"
            "2️⃣ Нажми '📍 Добавить адрес' или напиши адрес в чат\n"
            "3️⃣ Я сохраню адрес и покажу его на карте\n"
            "4️⃣ Повтори для других адресов на твоём маршруте\n"
            "5️⃣ По каждому адресу получишь маршрут на Яндекс.Картах\n\n"
            "💡 **Полезные советы:**\n"
            "• Можно добавлять адреса в любом порядке\n"
            "• Формируй маршрут по своему усмотрению\n"
            "• Контролируй свой район или улицу\n\n"
            "✨ Удачной работы!"
        )
        
        # Кнопки для быстрого действия
        from telegram import ReplyKeyboardMarkup
        keyboard = [
            ["📍 Добавить адрес"],
            ["← Вернуться в меню"]
        ]
        
        # 🔥 ИСПРАВЛЕНО: Используем context.bot.send_message вместо query.message.reply_text
        await context.bot.send_message(
            chat_id=user_id,
            text=instruction_text,
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        
        logging.info(f"🗺️ Пользователь {user_id} открыл инструкцию по созданию маршрута")
        
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_create_route_callback: {e}")
        # 🔥 Дополнительная защита: уведомляем пользователя об ошибке
        try:
            if update and update.callback_query:
                await context.bot.send_message(
                    chat_id=update.callback_query.from_user.id,
                    text="❌ Произошла ошибка. Попробуй нажать '📍 Добавить адрес' в меню."
                )
        except Exception:
            pass

async def handle_start_work_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки '🚀 Начать работу' (из inline-кнопки)"""
    try:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        # Проверяем баланс листовок
        flyer_balance = get_flyer_balance(user_id)
        if flyer_balance <= 0:
            await query.message.reply_text(
                "❗ У тебя нет листовок.\n\n"
                "Нажми «📦 Запросить листовки» и дождись подтверждения от админа.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Листовки есть - запрашиваем геолокацию для сканирования
        keyboard = [
            [KeyboardButton("🔍 Сканировать район", request_location=True)],
            ["Вернуться в меню"]
        ]
        try:
            await query.message.reply_photo(
                photo="https://disk.yandex.ru/i/6DjXrMN5aH5p-Q",
                caption=(
                    "📍 Добавить можно любой адрес в Калининграде, например: ул. Дадаева 55\n\n"
                    "💬 Напишите адрес в чат, я сохраню его!"
                ),
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            )
        except Exception as e:
            logging.warning(f"⚠️ Не удалось отправить фото при старте работы: {e}")
            await query.message.reply_text(
                "📍 Добавить можно любой адрес в Калининграде, например: ул. Дадаева 55\n\n"
                "💬 Напишите адрес в чат, я сохраню его!",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
            )
        
        logging.info(f"🚀 Пользователь {user_id} нажал 'Начать работу' из inline-кнопки")
        
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_start_work_callback: {e}")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """🔥 НОВОЕ: Обработчик видео - подсказка отправить фото"""
    try:
        user_id = update.effective_user.id
        
        # Проверяем, в каком состоянии пользователь
        state = user_state.get(user_id, {}).get("state")
        
        if state in ["awaiting_photos", "awaiting_door_photo", "awaiting_exit_door_photo"]:
            # Пользователь ожидает загрузки фото - подсказываем
            await update.message.reply_text(
                "❌ Видео не подходит.\n\n"
                "📸 Пожалуйста, отправь **фото** электрощита или двери.",
                parse_mode="Markdown"
            )
        else:
            # Не ожидаем фото - общая подсказка
            await update.message.reply_text(
                "🎬 Видео не принимается.\n\n"
                "ℹ️ Для работы нужны только **фотографии**.\n\n"
                "🚀 Нажми 'Начать работу 🚀' чтобы начать.",
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard(user_id)
            )
        
        logging.info(f"🎬 Пользователь {user_id} отправил видео (состояние: {state})")
        
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_video: {e}")


def main() -> None:
    """Главная функция запуска бота"""
    global scheduler
    try:
        # Инициализация Google Sheets
        logging.info("🔧 Инициализация Google Sheets...")
        init_sheets()
        
        # 🔥 ЗАГРУЗКА НАСТРОЕК: Инициализируем глобальную переменную SETTINGS
        logging.info("⚙️ Загрузка настроек...")
        try:
            load_settings(force=True)  # Принудительно загружаем настройки при старте
            logging.info(f"✅ Настройки загружены: {len(SETTINGS)} параметров")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось загрузить настройки: {e}")
        
        # Проверка обязательной конфигурации
        if not BOT_TOKEN:
            logging.critical("❌ ОШИБКА: Не установлен TELEGRAM_TOKEN. Установите переменную окружения TELEGRAM_TOKEN.")
            raise ValueError("Missing required environment variable: TELEGRAM_TOKEN")
        
        if not SPREADSHEET_URL:
            logging.critical("❌ ОШИБКА: Не установлен SPREADSHEET_URL. Установите переменную окружения SPREADSHEET_URL.")
            raise ValueError("Missing required environment variable: SPREADSHEET_URL")
        
        if ADMIN_TELEGRAM_ID == 0:
            logging.warning("⚠️ ПРЕДУПРЕЖДЕНИЕ: ADMIN_CHAT_ID не установлен. Админ-функции могут не работать.")
        
        # Загрузка хешей фото для проверки дубликатов
        logging.info("📸 Загрузка хешей фото...")
        load_photo_hashes()

        # Создание приложения с увеличенными таймаутами
        logging.info("🚀 Запуск Telegram бота...")
        # 🔥 НОВОЕ: Увеличены таймауты для предотвращения httpx.ReadError
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .read_timeout(30)  # Увеличено с 5 до 30 секунд
            .write_timeout(30)
            .connect_timeout(30)
            .pool_timeout(30)
            .get_updates_read_timeout(42)  # Telegram long polling timeout
            .build()
        )

        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("profile", profile_command))
        
        application.add_handler(CommandHandler("reject", reject_report_command))
        # 🔧 ИСПРАВЛЕНО: pattern=r\"ˆreject_\\d+$\" чтобы НЕ срабатывало на reject_request_ (заявки на листовки)
        application.add_handler(CallbackQueryHandler(handle_reject_callback, pattern=r"^reject_\d+$"))
        
        # ⚡ НОВОЕ: Админ-команда для заполнения координат
        application.add_handler(CommandHandler("fillcoords", fillcoords_command))
        
        # 🎉 НОВОЕ: Админ-команды
        application.add_handler(CommandHandler("approve", approve_flyers_command))
        application.add_handler(CommandHandler("expense", start_expense_command))
        application.add_handler(CallbackQueryHandler(handle_expense_callback, pattern="^expense_"))

        # 💯 НОВОЕ: Inline-кнопки для админа (одобрение заявок)
        # CallbackQueryHandler уже импортирован наверху
        application.add_handler(CallbackQueryHandler(handle_admin_approve_callback, pattern="^(approve_|reject_request_)"))
        application.add_handler(CallbackQueryHandler(handle_coords_admin_callback, pattern="^(coord_approve_|coord_reject_)"))
        # Legacy calculator handler removed
        application.add_handler(CallbackQueryHandler(handle_feedback_idea, pattern="^feedback_idea$"))
        application.add_handler(CallbackQueryHandler(handle_create_route_callback, pattern="^create_route$"))
        application.add_handler(CallbackQueryHandler(handle_start_work_callback, pattern="^start_work$"))
        application.add_handler(CallbackQueryHandler(handle_void_address_callback, pattern="^void_addr_"))
        
        # 🔥 Промоутер: выбор количества листовок и отмена
        application.add_handler(CallbackQueryHandler(handle_request_flyers_callback, pattern="^(request_flyers_|cancel_flyers_)"))
        application.add_handler(CallbackQueryHandler(handle_promoter_calculator_callback, pattern="^(req_num_|req_confirm_|req_cancel_custom_)"))
        
        # 🔥 НОВОЕ: Inline-кнопки для промоутера (количество уже наклеенных листовок)
        application.add_handler(CallbackQueryHandler(handle_existing_flyers_callback, pattern="^existing_flyers_"))
        
        # Обработчик inline-кнопок (выбор подъезда)
        application.add_handler(CallbackQueryHandler(handle_entrance_callback, pattern="^entrance_"))

        # Обработчик контакта (регистрация через телефон)
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))

        # Обработчик геолокации (сканирование местности)
        application.add_handler(MessageHandler(filters.LOCATION, handle_location))

        # Обработчик текстовых сообщений (кнопки меню)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

        # Обработчик фото (электрощиты и дверь)
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # 🔥 НОВОЕ: Обработчик видео (подсказка отправить фото)
        application.add_handler(MessageHandler(filters.VIDEO, handle_video))

        # Обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Запуск APScheduler для автоматической смены статусов и push-уведомлений
        # ВАЖНО: Запускаем ЧЕРЕЗ post_init, чтобы был event loop
        async def post_init_scheduler(app: Application) -> None:
            global scheduler
            if SCHEDULER_AVAILABLE:
                try:
                    # 🛡️ КРИТИЧНО: Проверяем, что планировщик ещё НЕ запущен (защита от дублей!)
                    if scheduler is not None and scheduler.running:
                        logging.warning("⚠️ APScheduler УЖЕ запущен! Пропускаем повторную инициализацию.")
                        return
                    
                    # 🔥 КРИТИЧНО: УКАЗЫВАЕМ ТАЙМЗОНУ Europe/Moscow (МСК, UTC+3)
                    moscow_tz = pytz.timezone('Europe/Moscow')
                    scheduler = AsyncIOScheduler(timezone=moscow_tz)
                    
                    logging.info(f"✅ APScheduler инициализирован с таймзоной: {moscow_tz}")
                    
                    # Каждые 6 часов проверяем статусы
                    scheduler.add_job(
                        auto_update_statuses,
                        'interval',
                        hours=6,
                        id='auto_status_update',
                        name='Автоматическое обновление статусов'
                    )
                    
                    # Утреннее напоминание в 10:00 (МСК)
                    scheduler.add_job(
                        send_morning_reminder,
                        'cron',
                        hour=10,
                        minute=0,
                        args=[app],
                        id='morning_reminder',
                        name='Утреннее напоминание промоутерам',
                        misfire_grace_time=60,
                        coalesce=True,
                        max_instances=1
                    )
                    
                    # Предупреждение об очистке чата в 21:00 (МСК)
                    scheduler.add_job(
                        send_cleanup_warning,
                        'cron',
                        hour=21,
                        minute=0,
                        args=[app],
                        id='cleanup_warning_21',
                        name='Предупреждение об очистке чата в 21:00',
                        misfire_grace_time=60,  # 🔥 НОВОЕ: игнорировать задачу если опоздала > 60 сек
                        coalesce=True,  # 🔥 НОВОЕ: объединять пропущенные запуски в один
                        max_instances=1  # 🔥 НОВОЕ: только один экземпляр одновременно
                    )
                    
                    # Утренний отчёт ROI в 09:00 (МСК)
                    scheduler.add_job(
                        send_daily_roi_summary,
                        'cron',
                        hour=9,
                        minute=0,
                        args=[app],
                        id='daily_roi_summary',
                        name='Ежедневный отчёт ROI',
                        misfire_grace_time=60,
                        coalesce=True,
                        max_instances=1
                    )
                    
                    # Авто-очистка чата в 07:00 (МСК)
                    scheduler.add_job(
                        perform_chat_cleanup,
                        'cron',
                        hour=7,
                        minute=0,
                        args=[app],
                        id='cleanup_07',
                        name='Авто-очистка чата в 07:00',
                        misfire_grace_time=60,  # 🔥 НОВОЕ: игнорировать задачу если опоздала > 60 сек
                        coalesce=True,  # 🔥 НОВОЕ: объединять пропущенные запуски в один
                        max_instances=1  # 🔥 НОВОЕ: только один экземпляр одновременно
                    )

                    # Ночной агрегатор ROI в 23:55 (МСК)
                    scheduler.add_job(
                        compute_daily_roi,
                        'cron',
                        hour=23,
                        minute=55,
                        id='daily_roi',
                        name='Ежедневная агрегация ROI'
                    )

                    scheduler.start()
                    logging.info(
                        "✅ APScheduler запущен:\n"
                        "   - Автоматическое обновление статусов каждые 6 часов\n"
                        "   - Утреннее напоминание в 10:00\n"
                        "   - Предупреждение об очистке в 21:00\n"
                        "   - Авто-очистка чата в 07:00\n"
                        "   - ROI-отчёт в 09:00\n"
                        "   - Агрегация ROI в 23:55"
                    )
                except Exception as e:
                    logging.error(f"❌ Ошибка запуска APScheduler: {e}")
            else:
                logging.warning("⚠️ APScheduler не установлен. Авто-обновление статусов и push-уведомления отключены")
        
        # Регистрируем post_init callback
        application.post_init = post_init_scheduler

        # Запуск бота
        logging.info("✅ Бот успешно запущен!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logging.critical(f"❌ ФАТАЛЬНАЯ ОШИБКА: {e}")
        raise


def send_daily_roi_summary(app: Application) -> None:
    """
    📣 НОВОЕ: Утренний отчёт по ROI за вчера — админам в Telegram
    Содержит: суммарный доход/расход, средний ROI, топ-3 промоутера по ROI, анти-топ-3 районов.
    """
    try:
        if not roi_sheet:
            return
        rows = roi_sheet.get_all_values()
        if not rows or len(rows) <= 1:
            return
        yday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        total_income = 0.0
        total_expense = 0.0
        promoter_roi: Dict[str, float] = {}
        district_roi: Dict[str, float] = {}
        for row in rows[1:]:
            if len(row) < 8:
                continue
            date, district, promoter, income_s, expense_s, roi_s, addrs_s, photos_s = row[:8]
            if date != yday:
                continue
            try:
                income = float(income_s)
            except Exception:
                income = 0.0
            try:
                expense = float(expense_s)
            except Exception:
                expense = 0.0
            try:
                roi_val = float(roi_s)
            except Exception:
                roi_val = 0.0
            total_income += income
            total_expense += expense
            if promoter:
                promoter_roi[promoter] = roi_val
            if district:
                district_roi[district] = roi_val
        avg_roi = (total_income - total_expense) / (total_expense if total_expense > 0 else 1.0)
        def top_n(d: Dict[str, float], n: int, reverse: bool = True) -> List[tuple[str, float]]:
            return sorted(d.items(), key=lambda kv: kv[1], reverse=reverse)[:n]
        top_promoters = top_n(promoter_roi, 3, True)
        worst_districts = top_n(district_roi, 3, False)
        summary = [
            f"📅 Отчёт за {yday}",
            f"💰 Доход: {total_income:.2f}₽",
            f"💸 Расход: {total_expense:.2f}₽",
            f"📈 ROI: {avg_roi:.2f}",
            "",
            "🏆 Топ-3 промоутера по ROI:",
        ]
        if top_promoters:
            for i, (p, r) in enumerate(top_promoters, 1):
                summary.append(f"{i}. {p}: ROI {r:.2f}")
        else:
            summary.append("— Нет данных")
        summary.extend(["", "⚠️ Анти-топ-3 районов по ROI:"])
        if worst_districts:
            for i, (d, r) in enumerate(worst_districts, 1):
                summary.append(f"{i}. {d}: ROI {r:.2f}")
        else:
            summary.append("— Нет данных")
        text = "\n".join(summary)
        for admin_id in ADMIN_IDS:
            try:
                app.bot.send_message(chat_id=admin_id, text=text)
            except Exception as e:
                logging.warning(f"⚠️ Не удалось отправить ROI-отчёт админу {admin_id}: {e}")
    except Exception as e:
        logging.error(f"❌ Ошибка отправки утреннего ROI-отчёта: {e}")

def get_spreadsheet_id_from_url(url: str) -> Optional[str]:
    try:
        if "/d/" in url:
            part = url.split("/d/")[1]
            return part.split("/")[0]
        return None
    except Exception:
        return None


def ensure_roi_dashboard_and_charts() -> None:
    try:
        if not roi_sheet or not config_sheet:
            return
        
        # 🔧 ИСПРАВЛЕНО: Расширяем лист до 20 колонок если нужно
        try:
            current_cols = roi_sheet.col_count
            if current_cols < 20:
                roi_sheet.resize(rows=roi_sheet.row_count, cols=20)
                logging.info(f"✅ Лист 'ROI' расширен до 20 колонок (было {current_cols})")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось расширить лист ROI: {e}")
        
        # Сводная область J1:M
        headers = ["Дата", "Доход (₽)", "Расход (₽)", "ROI"]
        try:
            roi_sheet.update(values=[headers], range_name="J1:M1")  # 🔧 ИСПРАВЛЕНО: порядок аргументов
            formula = '=QUERY(A2:H, "select A, sum(D), sum(E), avg(F) group by A order by A label sum(D) \"Доход\", sum(E) \"Расход\", avg(F) \"ROI\"", 0)'
            roi_sheet.update(values=[[formula]], range_name="J2", value_input_option="USER_ENTERED")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось создать сводную область ROI: {e}")
        # Компактный Dashboard N1:S3
        try:
            roi_sheet.update(values=[["Показатель","Дата","Доход (₽)","Расход (₽)","ROI","Листовки (шт.)"]], range_name="N1:S1")  # 🔧 ИСПРАВЛЕНО
            yday_date_formula = '=TEXT(TODAY()-1, "dd.mm.yyyy")'
            income_yday_formula = '=IFERROR(INDEX(K:K, MATCH(TEXT(TODAY()-1, "dd.mm.yyyy"), J:J, 0)), 0)'
            expense_yday_formula = '=IFERROR(INDEX(L:L, MATCH(TEXT(TODAY()-1, "dd.mm.yyyy"), J:J, 0)), 0)'
            roi_yday_formula = '=IFERROR(INDEX(M:M, MATCH(TEXT(TODAY()-1, "dd.mm.yyyy"), J:J, 0)), 0)'
            flyers_yday_formula = '=IFERROR(SUM(FILTER(H:H, A:A = TEXT(TODAY()-1, "dd.mm.yyyy"))), 0)'
            week_income_formula = '=IFERROR(SUM(FILTER(K:K, DATEVALUE(J:J) >= TODAY()-7, DATEVALUE(J:J) <= TODAY()-1)), 0)'
            week_expense_formula = '=IFERROR(SUM(FILTER(L:L, DATEVALUE(J:J) >= TODAY()-7, DATEVALUE(J:J) <= TODAY()-1)), 0)'
            week_roi_formula = '=(P3-Q3)/IF(Q3>0,Q3,1)'
            week_flyers_formula = '=IFERROR(SUM(FILTER(H:H, DATEVALUE(A:A) >= TODAY()-7, DATEVALUE(A:A) <= TODAY()-1)), 0)'
            roi_sheet.update(values=[["Вчера", yday_date_formula, income_yday_formula, expense_yday_formula, roi_yday_formula, flyers_yday_formula]], range_name="N2:S2", value_input_option="USER_ENTERED")  # 🔧 ИСПРАВЛЕНО
            roi_sheet.update(values=[["Неделя (посл. 7 дней)", "", week_income_formula, week_expense_formula, week_roi_formula, week_flyers_formula]], range_name="N3:S3", value_input_option="USER_ENTERED")  # 🔧 ИСПРАВЛЕНО
        except Exception as e:
            logging.warning(f"⚠️ Не удалось создать компактный Dashboard: {e}")
        # Проверка флага настроек
        created = False
        row_index = None
        try:
            rows = config_sheet.get_all_values()
            for i, row in enumerate(rows[1:], start=2):
                if len(row) >= 2 and row[0] == "ROI_CHARTS_CREATED":
                    row_index = i
                    created = (row[1] == "1")
                    break
        except Exception as e:
            logging.warning(f"⚠️ Не удалось прочитать настройки ROI_CHARTS_CREATED: {e}")
        if created:
            return
        if not SHEETS_API_AVAILABLE:
            logging.warning("⚠️ Авто-графики отключены: нет google-api-python-client")
            return
        # Sheets API
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds2 = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scope)
        try:
            service = build('sheets', 'v4', credentials=creds2)
        except Exception as e:
            logging.warning(f"⚠️ Не удалось инициализировать Sheets API: {e}")
            return
        spreadsheet_id = get_spreadsheet_id_from_url(SPREADSHEET_URL)
        if not spreadsheet_id:
            logging.warning("⚠️ Не удалось извлечь spreadsheetId из URL")
            return
        sheet_id = roi_sheet.id
        # Диапазон строк для графиков
        try:
            total_rows = len(roi_sheet.get_all_values())
        except Exception:
            total_rows = 1000
        start_row = 1  # J2 (0-based)
        end_row = max(start_row + 1, total_rows)
        requests = [
            {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "Доход/Расход по дням",
                            "basicChart": {
                                "chartType": "LINE",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "Дата"},
                                    {"position": "LEFT_AXIS", "title": "Сумма (₽)"}
                                ],
                                "domains": [
                                    {"domain": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 9, "endColumnIndex": 10}]}}}
                                ],
                                "series": [
                                    {"series": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 10, "endColumnIndex": 11}]}}, "targetAxis": "LEFT_AXIS"},
                                    {"series": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 11, "endColumnIndex": 12}]}}, "targetAxis": "LEFT_AXIS"}
                                ]
                            }
                        },
                        "position": {"overlayPosition": {"anchorCell": {"sheetId": sheet_id, "rowIndex": 0, "columnIndex": 9}}}
                    }
                }
            },
            {
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "ROI по дням",
                            "basicChart": {
                                "chartType": "LINE",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "Дата"},
                                    {"position": "LEFT_AXIS", "title": "ROI"}
                                ],
                                "domains": [
                                    {"domain": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 9, "endColumnIndex": 10}]}}}
                                ],
                                "series": [
                                    {"series": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": 12, "endColumnIndex": 13}]}}, "targetAxis": "LEFT_AXIS"}
                                ]
                            }
                        },
                        "position": {"overlayPosition": {"anchorCell": {"sheetId": sheet_id, "rowIndex": 15, "columnIndex": 9}}}
                    }
                }
            }
        ]
        # Дополнительный компактный бар‑график по Dashboard N2:N3
        try:
            requests.append({
                "addChart": {
                    "chart": {
                        "spec": {
                            "title": "Вчера vs Неделя: Доход/Расход",
                            "basicChart": {
                                "chartType": "COLUMN",
                                "legendPosition": "BOTTOM_LEGEND",
                                "axis": [
                                    {"position": "BOTTOM_AXIS", "title": "Период"},
                                    {"position": "LEFT_AXIS", "title": "Сумма (₽)"}
                                ],
                                "domains": [
                                    {"domain": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 3, "startColumnIndex": 13, "endColumnIndex": 14}]}}}
                                ],
                                "series": [
                                    {"series": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 3, "startColumnIndex": 15, "endColumnIndex": 16}]}} , "targetAxis": "LEFT_AXIS"},
                                    {"series": {"sourceRange": {"sources": [{"sheetId": sheet_id, "startRowIndex": 1, "endRowIndex": 3, "startColumnIndex": 16, "endColumnIndex": 17}]}} , "targetAxis": "LEFT_AXIS"}
                                ]
                            }
                        },
                        "position": {"overlayPosition": {"anchorCell": {"sheetId": sheet_id, "rowIndex": 30, "columnIndex": 13}}}
                    }
                }
            })
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": requests}).execute()
            logging.info("✅ Авто-графики ROI созданы на листе 'ROI'")
            if row_index:
                config_sheet.update_cell(row_index, 2, "1")
            else:
                config_sheet.append_row(["ROI_CHARTS_CREATED", "1", "Авто-графики ROI созданы"])
        except Exception as e:
            logging.warning(f"⚠️ Не удалось создать графики: {e}")
    except Exception as e:
        logging.warning(f"⚠️ Ошибка ensure_roi_dashboard_and_charts: {e}")

async def handle_reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик inline-кнопок отклонения отчётов и создания маршрута"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    
    # Обработка создания маршрута
    if data == "create_route":
        user_state[user_id]["state"] = "awaiting_manual_address"
        
        # 📸 Отправляем мини-инструкцию с фото примера
        try:
            await query.message.reply_photo(
                photo="https://i.ibb.co/4mZ9Tb3/address-example.jpg",
                caption=(
                    "🗺️ <b>Создание своего маршрута</b>\n\n"
                    "📝 <b>Как добавить адрес:</b>\n"
                    "1️⃣ Напиши адрес в формате: <i>Улица Номер</i>\n"
                    "    Пример: <code>Чкалова 49Б</code>\n\n"
                    "2️⃣ Я найду его на карте и добавлю в справочник\n\n"
                    "3️⃣ После добавления ты сможешь начать работу\n\n"
                    "💡 <b>Подсказка:</b> Можно вводить адреса прямо в чат в любой момент!"
                ),
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup([["📍 Добавить адрес"], ["Вернуться в меню"]], resize_keyboard=True)
            )
        except Exception as e:
            logging.warning(f"⚠️ Не удалось отправить фото инструкции: {e}")
            # Фолбэк: только текст
            await query.message.reply_text(
                "🗺️ <b>Создание своего маршрута</b>\n\n"
                "📝 <b>Как добавить адрес:</b>\n"
                "1️⃣ Напиши адрес в формате: <i>Улица Номер</i>\n"
                "    Пример: <code>Чкалова 49Б</code>\n\n"
                "2️⃣ Я найду его на карте и добавлю в справочник\n\n"
                "3️⃣ После добавления ты сможешь начать работу\n\n"
                "💡 <b>Подсказка:</b> Можно вводить адреса прямо в чат в любой момент!",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup([["📍 Добавить адрес"], ["Вернуться в меню"]], resize_keyboard=True)
            )
        return
    
    # Обработка отклонения отчёта
    if user_id not in ADMIN_IDS:
        await query.message.reply_text("❌ Нет прав.")
        return
    
    # 🔧 ИСПРАВЛЕНО: Проверка уже не нужна, т.к. pattern изменён на r\"^reject_\\d+$\"
    
    try:
        row_idx = int(data.replace("reject_", ""))
        # Убедимся, что есть столбец 'Статус' в 'Отчёты'
        try:
            otchety.update(values=[["Статус"]], range_name="J1")
        except Exception:
            pass
        rows = otchety.get_all_values()
        if row_idx <= 1 or row_idx > len(rows):
            await query.message.reply_text("❌ Неверный номер строки.")
            return
        row = rows[row_idx - 1]
        # Ставим статус 'ОТКЛОНЕНО' в J-колонке
        try:
            otchety.update_cell(row_idx, 10, "ОТКЛОНЕНО")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось обновить статус отчёта: {e}")
        # Подготовка к аннулированию финансов
        date = row[0] if len(row) > 0 else ""
        promoter = row[1] if len(row) > 1 else ""
        address = row[2] if len(row) > 2 else ""
        void_income_total = 0.0
        void_count = 0
        try:
            # Проверка наличия finance_sheet
            if not finance_sheet:
                logging.warning("⚠️ finance_sheet не инициализирован")
                await query.message.reply_text("✅ Отчёт отклонён (без коррекции финансов)")
                return
            # Убедимся, что есть столбец 'Статус' в 'Финансы'
            try:
                finance_sheet.update(values=[["Статус"]], range_name="K1")
            except Exception:
                pass
            fin_rows = finance_sheet.get_all_values()
            for i, frow in enumerate(fin_rows[1:], start=2):
                if len(frow) < 10:
                    continue
                f_date, f_promoter, f_address, f_district, f_type, f_cat, f_qty, f_unit, f_amount, f_comment = frow[:10]
                f_status = frow[10] if len(frow) >= 11 else ""
                if f_status == "VOID":
                    continue
                if f_date == date and f_promoter == promoter and f_address == address and f_cat.startswith("Фото"):
                    try:
                        amt = float(f_amount)
                    except Exception:
                        amt = 0.0
                    # Обновляем статус VOID
                    try:
                        finance_sheet.update_cell(i, 11, "VOID")
                    except Exception as e:
                        logging.warning(f"⚠️ Не удалось проставить VOID в Финансы (строка {i}): {e}")
                    void_count += 1
                    if f_type == "Доход":
                        void_income_total += amt
            # Корректируем баланс (минус доход)
            if void_income_total > 0:
                try:
                    update_balance(int(promoter), -void_income_total)
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось скорректировать баланс: {e}")
        except Exception as e:
            logging.warning(f"⚠️ Ошибка аннулирования финансов: {e}")
        # UX-текст в стиле Дональда Нормана: ясно, что произошло и что делать дальше
        if void_count > 0:
            await query.message.reply_text(
                f"✅ **Отчёт #{row_idx} отклонён**\n\n"
                f"📊 Аннулировано записей: {void_count}\n"
                f"💸 Возвращено со счёта: {void_income_total:.2f}₽\n\n"
                f"ℹ️ Баланс промоутера обновлён.",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text(
                f"✅ **Отчёт #{row_idx} отклонён**\n\n"
                f"ℹ️ Финансовые записи не найдены (возможно, уже аннулированы).",
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"❌ Ошибка handle_reject_callback: {e}")
        await query.message.reply_text("❌ Ошибка отклонения.")

async def handle_admin_approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    👑 НОВОЕ: Обработчик inline-кнопок одобрения заявок админом
    Обрабатывает: approve_{user_id}_{quantity}, approve_{user_id}_custom, reject_request_{user_id}
    """
    try:
        query = update.callback_query
        admin_id = query.from_user.id
        
        # 🔒 Проверка прав админа
        if admin_id not in ADMIN_IDS:
            await query.answer("❌ У тебя нет прав администратора!")
            return
        
        await query.answer()
        
        # 📦 Одобрение заявки
        if query.data.startswith("approve_"):
            parts = query.data.split("_")
            promoter_id = int(parts[1])
            quantity_param = parts[2]
            
            # 💯 Своё количество - просим ввести
            if quantity_param == "custom":
                keyboard = [
                    [InlineKeyboardButton("1", callback_data=f"num_{promoter_id}_1"), InlineKeyboardButton("2", callback_data=f"num_{promoter_id}_2"), InlineKeyboardButton("3", callback_data=f"num_{promoter_id}_3")],
                    [InlineKeyboardButton("4", callback_data=f"num_{promoter_id}_4"), InlineKeyboardButton("5", callback_data=f"num_{promoter_id}_5"), InlineKeyboardButton("6", callback_data=f"num_{promoter_id}_6")],
                    [InlineKeyboardButton("7", callback_data=f"num_{promoter_id}_7"), InlineKeyboardButton("8", callback_data=f"num_{promoter_id}_8"), InlineKeyboardButton("9", callback_data=f"num_{promoter_id}_9")],
                    [InlineKeyboardButton("0", callback_data=f"num_{promoter_id}_0"), InlineKeyboardButton("00", callback_data=f"num_{promoter_id}_00"), InlineKeyboardButton("⬅️ Удалить", callback_data=f"num_{promoter_id}_del")],
                    [InlineKeyboardButton("✅ Одобрить", callback_data=f"confirm_approve_{promoter_id}"), InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_custom_{promoter_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if admin_id not in user_state:
                    user_state[admin_id] = {}
                user_state[admin_id]["custom_quantity"] = ""
                user_state[admin_id]["custom_promoter_id"] = promoter_id
                await query.edit_message_text(
                    f"💯 **Введи количество листовок:**\n\n"
                    f"👤 Промоутер ID: `{promoter_id}`\n"
                    f"📦 Количество: **0**\n\n"
                    f"⌨️ Используй калькулятор ниже:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                return
            
            # 📦 Одобрение с фиксированным количеством
            quantity = int(quantity_param)
            success = await process_approval(promoter_id, quantity, context)
            if success:
                try:
                    await context.bot.unpin_chat_message(chat_id=admin_id, message_id=query.message.message_id)
                except Exception:
                    pass
                await query.edit_message_text(
                    f"✅ **ЗАЯВКА ОДОБРЕНА!**\n\n"
                    f"👤 Промоутер ID: `{promoter_id}`\n"
                    f"📦 Количество: **{quantity} шт**\n\n"
                    f"✅ Промоутер уведомлён!",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    f"❌ **ОШИБКА!**\n\n"
                    f"⚠️ Не найдено ожидающих заявок для промоутера ID: {promoter_id}\n\n"
                    f"💡 Проверь лист 'Заявки'.",
                    parse_mode="Markdown"
                )
        elif query.data.startswith("reject_request_"):
            parts = query.data.split("_")
            if len(parts) < 3 or not parts[2]:
                await query.answer("❌ Неверный формат запроса")
                return
            promoter_id = int(parts[2])
            await query.edit_message_text(
                f"❌ **ЗАЯВКА ОТКЛОНЕНА**\n\n"
                f"👤 Промоутер ID: `{promoter_id}`",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logging.error(f"❌ Ошибка в handle_admin_approve_callback: {e}")
        try:
            await query.answer("❌ Произошла ошибка!")
        except Exception:
            pass

async def fillcoords_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    ⚡ НОВОЕ: Админ-команда для заполнения координат адресов в фоновом режиме
    
    Использование: /fillcoords [макс_количество]
    Пример: /fillcoords 10  (заполнит 10 адресов)
    """
    try:
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Нет прав.")
            return
        
        # Парсим лимит
        text = (update.message.text or "").strip()
        parts = text.split()
        limit = 50  # По умолчанию
        if len(parts) > 1 and parts[1].isdigit():
            limit = int(parts[1])
        
        await update.message.reply_text(
            f"🔄 Запуск геокодирования адресов...\n"
            f"🎯 Максимум: {limit} адресов\n\n"
            f"⏳ Это может занять до 2-3 минут..."
        )
        
        # Загружаем все записи
        all_records = sprav.get_all_records()
        filled_count = 0
        skipped_count = 0
        error_count = 0
        
        for r in all_records:
            if filled_count >= limit:
                break
            
            addr = str(r.get("АДРЕС", "")).strip()
            if not addr:
                continue
            
            # Проверяем, есть ли координаты
            try:
                lat = float(r.get("ШИРОТА", 0) or 0)
                lng = float(r.get("ДОЛГОТА", 0) or 0)
            except (ValueError, TypeError):
                lat, lng = 0.0, 0.0
            
            if lat and lng:
                skipped_count += 1
                continue  # Уже есть координаты
            
            # Геокодируем
            try:
                coords = geocode_address(addr)
                if coords:
                    g_lat, g_lng, district = coords
                    # Обновляем таблицу
                    try:
                        cell = sprav.find(addr, in_column=1)
                        district_fixed = ensure_real_district(addr, g_lat, g_lng, district)
                        sprav.update_cell(cell.row, 8, str(g_lat))  # ШИРОТА
                        sprav.update_cell(cell.row, 9, str(g_lng))  # ДОЛГОТА
                        sprav.update_cell(cell.row, 2, district_fixed)  # РАЙОН
                        filled_count += 1
                        logging.info(f"✅ Заполнены координаты: {addr} -> {g_lat}, {g_lng} ({district_fixed})")
                    except Exception as e:
                        logging.error(f"❌ Ошибка обновления '{addr}': {e}")
                        error_count += 1
                else:
                    logging.warning(f"⚠️ Не удалось геокодировать '{addr}'")
                    error_count += 1
            except Exception as e:
                logging.error(f"❌ Ошибка геокодирования '{addr}': {e}")
                error_count += 1
        
        # Отчёт
        await update.message.reply_text(
            f"✅ **Геокодирование завершено!**\n\n"
            f"✅ Заполнено: {filled_count}\n"
            f"⏭️ Пропущено (есть координаты): {skipped_count}\n"
            f"❌ Ошибок: {error_count}\n\n"
            f"ℹ️ Теперь сканирование будет работать быстрее!",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"❌ Ошибка команды /fillcoords: {e}")
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def reject_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_id = update.effective_user.id
        if user_id not in ADMIN_IDS:
            await update.message.reply_text("❌ Нет прав.")
            return
        text = (update.message.text or "").strip()
        parts = text.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await update.message.reply_text("ℹ️ Использование: /reject <номер_строки_в_Отчётах>")
            return
        row_idx = int(parts[1])
        # Убедимся, что есть столбец 'Статус' в 'Отчёты'
        try:
            otchety.update(values=[["Статус"]], range_name="J1")
        except Exception:
            pass
        rows = otchety.get_all_values()
        if row_idx <= 1 or row_idx > len(rows):
            await update.message.reply_text("❌ Неверный номер строки.")
            return
        row = rows[row_idx - 1]
        # Ставим статус 'ОТКЛОНЕНО' в J-колонке
        try:
            otchety.update_cell(row_idx, 10, "ОТКЛОНЕНО")
        except Exception as e:
            logging.warning(f"⚠️ Не удалось обновить статус отчёта: {e}")
        # Подготовка к аннулированию финансов
        date = row[0] if len(row) > 0 else ""
        promoter = row[1] if len(row) > 1 else ""
        address = row[2] if len(row) > 2 else ""
        void_income_total = 0.0
        void_count = 0
        try:
            # Проверка наличия finance_sheet
            if not finance_sheet:
                logging.warning("⚠️ finance_sheet не инициализирован")
                await update.message.reply_text("✅ Отчёт отклонён (без коррекции финансов)")
                return
            # Убедимся, что есть столбец 'Статус' в 'Финансы'
            try:
                finance_sheet.update(values=[["Статус"]], range_name="K1")
            except Exception:
                pass
            fin_rows = finance_sheet.get_all_values()
            for i, frow in enumerate(fin_rows[1:], start=2):
                if len(frow) < 10:
                    continue
                f_date, f_promoter, f_address, f_district, f_type, f_cat, f_qty, f_unit, f_amount, f_comment = frow[:10]
                f_status = frow[10] if len(frow) >= 11 else ""
                if f_status == "VOID":
                    continue
                if f_date == date and f_promoter == promoter and f_address == address and f_cat.startswith("Фото"):
                    try:
                        amt = float(f_amount)
                    except Exception:
                        amt = 0.0
                    # Обновляем статус VOID
                    try:
                        finance_sheet.update_cell(i, 11, "VOID")
                    except Exception as e:
                        logging.warning(f"⚠️ Не удалось проставить VOID в Финансы (строка {i}): {e}")
                    void_count += 1
                    if f_type == "Доход":
                        void_income_total += amt
            # Корректируем баланс (минус доход)
            if void_income_total > 0:
                try:
                    update_balance(int(promoter), -void_income_total)
                except Exception as e:
                    logging.warning(f"⚠️ Не удалось скорректировать баланс: {e}")
        except Exception as e:
            logging.warning(f"⚠️ Ошибка аннулирования финансов: {e}")
        # UX-текст в стиле Дональда Нормана: ясно, что произошло и что делать дальше
        if void_count > 0:
            await update.message.reply_text(
                f"✅ **Отчёт #{row_idx} отклонён**\n\n"
                f"📊 Аннулировано записей: {void_count}\n"
                f"💸 Возвращено со счёта: {void_income_total:.2f}₽\n\n"
                f"ℹ️ Баланс промоутера обновлён.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✅ **Отчёт #{row_idx} отклонён**\n\n"
                f"ℹ️ Финансовые записи не найдены (возможно, уже аннулированы).",
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"❌ Ошибка команды /reject: {e}")

def compute_daily_roi() -> None:
    """
    💹 НОВОЕ: Агрегирует доход/расход/ROI за вчера по району и промоутеру и пишет в лист 'ROI'
    ROI = (Доход - Расход) / max(Расход, 1)
    Также считает количество уникальных адресов и фото.
    """
    try:
        if not finance_sheet or not roi_sheet:
            return
        rows = finance_sheet.get_all_values()
        if not rows or len(rows) <= 1:
            return
        from collections import defaultdict
        yday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        # Ключ: (district, promoter)
        agg_income = defaultdict(float)
        agg_expense = defaultdict(float)
        addr_count = defaultdict(set)
        photo_count = defaultdict(int)
        for row in rows[1:]:
            if len(row) < 10:
                continue
            date, promoter, address, district, entry_type, category, qty, unit_price, amount, comment = row[:10]
            status = row[10] if len(row) >= 11 else ""
            if status == "VOID":
                continue
            if date != yday:
                continue
            key = (district or "Неизвестный", promoter or "")
            try:
                amt = float(amount)
            except Exception:
                amt = 0.0
            # Доход/Расход
            if entry_type == "Доход":
                agg_income[key] += amt
                # Считаем фото по категориям
                if category.startswith("Фото"):
                    photo_count[key] += int(qty) if qty.isdigit() else 1
            elif entry_type == "Расход":
                agg_expense[key] += amt
            # Уникальные адреса
            if address:
                addr_count[key].add(address)
        # Пишем результаты
        data = []
        for key in agg_income.keys() | agg_expense.keys():
            district, promoter = key
            income = agg_income.get(key, 0.0)
            expense = agg_expense.get(key, 0.0)
            roi = (income - expense) / (expense if expense > 0 else 1.0)
            data.append([
                yday, district, promoter, f"{income:.2f}", f"{expense:.2f}", f"{roi:.2f}", str(len(addr_count[key])), str(photo_count.get(key, 0))
            ])
        if data:
            # Найдём последнюю строку и допишем
            existing = roi_sheet.get_all_values()
            start_row = len(existing) + 1 if existing else 2
            roi_sheet.update(values=data, range_name=f"A{start_row}:H{start_row + len(data) - 1}")
            logging.info(f"✅ ROI за {yday} записан: {len(data)} строк")
    except Exception as e:
        logging.error(f"❌ Ошибка агрегации ROI: {e}")
    """
    Начисляет призовой фонд за прошедший день и записывает транзакцию в лист 'Балансы'.
    Сумма призового фонда масштабируется активностью (до +50%).
    """
    try:
        if not balances_sheet:
            return
        load_settings()
        all_values = balances_sheet.get_all_values()
        user_ids: list[int] = []
        if all_values and len(all_values) > 1:
            for row in all_values[1:]:
                if row and row[0]:
                    try:
                        user_ids.append(int(row[0]))
                    except ValueError:
                        continue
        now = datetime.now()
        for uid in user_ids:
            try:
                # ВАЖНО: должен учитывать только фото электрощитов за вчера
                panel_count = 0
                try:
                    if otchety:
                        rows = otchety.get_all_values()
                        if len(rows) > 1:
                            yday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
                            for row in rows[1:]:
                                if len(row) >= 4:
                                    date = row[0]
                                    promoter = row[1]
                                    address = row[2]
                                    photos = row[3]
                                    comment = row[7] if len(row) > 7 else ""
                                    if date == yday and str(promoter) == str(uid):
                                        if "входной двери" in comment.lower() or "фото двери" in comment.lower():
                                            continue
                                        if "БОНУС" in address:
                                            continue
                                        try:
                                            panel_count += int(photos)
                                        except ValueError:
                                            continue
                except Exception:
                    panel_count = 0
                tier = None
                for t in reversed(BONUS_TIERS):
                    if panel_count >= t["threshold"]:
                        tier = t
                        break
                if not tier:
                    continue
                streak_days = get_work_streak(uid)
                activity_multiplier = min(1.0 + 0.10 * streak_days, 1.5)
                amount = float(tier["bonus"]) * activity_multiplier
                balances_sheet.append_row([
                    str(uid),
                    now.strftime("%d.%m.%Y %H:%M"),
                    "Призовой фонд",
                    tier["name"],
                    f"{amount:.2f}"
                ])
            except Exception:
                continue
    except Exception as e:
        logging.error(f"❌ Ошибка начисления призового фонда: {e}")

def ensure_balances_headers():
    try:
        if not balances_sheet:
            return
        rows = balances_sheet.get_all_values()
        expected = ["ПромоутерID","Дата","Тип","Листовки (шт)","Фото двери (шт)","Фото щитов (шт)","Оплата дверь (₽)","Оплата щиты базовая (₽)","Премия активность (₽)","Итого (₽)"]
        if not rows or len(rows) == 0:
            balances_sheet.update("A1:J1", [expected])
        else:
            headers = rows[0]
            if len(headers) < len(expected) or any(h != expected[i] for i,h in enumerate(headers[:len(expected)])):
                balances_sheet.update("A1:J1", [expected])
    except Exception as e:
        logging.warning(f"⚠️ Не удалось обновить заголовки 'Балансы': {e}")

def settle_daily_summary(app: Application) -> None:
    """
    Формирует дневную сводку по листовкам и оплатам в листе 'Балансы'.
    Поля: [ПромоутерID, Дата, Тип, Листовки (шт), Фото двери (шт), Фото щитов (шт), Оплата дверь (₽), Оплата щиты базовая (₽), Премия активность (₽), Итого (₽)]
    """
    try:
        if not balances_sheet or not otchety:
            return
        ensure_balances_headers()
        # Собираем всех промоутеров из 'Балансы'
        all_bal = balances_sheet.get_all_values()
        user_ids: list[int] = []
        if all_bal and len(all_bal) > 1:
            for row in all_bal[1:]:
                if row and row[0]:
                    try:
                        user_ids.append(int(row[0]))
                    except ValueError:
                        continue
        # Заголовок при необходимости
        try:
            if not all_bal or len(all_bal) == 0:
                balances_sheet.update("A1:J1", [[
                    "ПромоутерID","Дата","Тип","Листовки (шт)","Фото двери (шт)","Фото щитов (шт)",
                    "Оплата дверь (₽)","Оплата щиты базовая (₽)","Премия активность (₽)","Итого (₽)"
                ]])
                all_bal = balances_sheet.get_all_values()
        except Exception:
            pass
        # Читаем 'Отчёты' за вчера
        rows = otchety.get_all_values()
        if not rows or len(rows) <= 1:
            return
        yday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        # Для каждого промоутера считаем дневные показатели
        for uid in user_ids:
            door_photos = 0
            panel_photos = 0
            door_earnings = 0.0
            panel_base_earnings = 0.0
            for row in rows[1:]:
                if len(row) >= 7:
                    date = row[0]
                    promoter = row[1]
                    address = row[2]
                    photos_str = row[3]
                    sum_str = row[4]
                    time_str = row[6]
                    comment = row[7] if len(row) > 7 else ""
                    if date != yday or str(promoter) != str(uid):
                        continue
                    # Фото двери
                    is_door = ("входной двери" in comment.lower()) or ("фото двери" in comment.lower())
                    # Фото электрощитов (исключая бонусные строки)
                    is_bonus = ("БОНУС" in address)
                    try:
                        photos = int(photos_str)
                    except ValueError:
                        photos = 0
                    if is_door:
                        door_photos += photos
                        # Расчёт ставки двери по времени
                        try:
                            hour = int(time_str.split(":")[0])
                        except Exception:
                            hour = 12
                        rate = 0.5 if (hour >= 21 or hour < 7) else 1.0
                        door_earnings += rate * photos
                    elif not is_bonus:
                        panel_photos += photos
                        # Базовая ставка щита без активности
                        panel_base_earnings += 3.0 * photos
            # Премия за активность (только на щиты)
            streak_days = get_work_streak(uid)
            activity_multiplier = min(1.0 + 0.10 * streak_days, 1.5)
            activity_premium = panel_base_earnings * (activity_multiplier - 1.0)
            total = door_earnings + panel_base_earnings + activity_premium
            # Затраченные листовки = фото щитов
            flyers_used = panel_photos
            # Записываем строку сводки в 'Балансы'
            balances_sheet.append_row([
                str(uid),
                yday,
                "Дневной итог",
                str(flyers_used),
                str(door_photos),
                str(panel_photos),
                f"{door_earnings:.2f}",
                f"{panel_base_earnings:.2f}",
                f"{activity_premium:.2f}",
                f"{total:.2f}"
            ])
    except Exception as e:
        logging.error(f"❌ Ошибка дневной сводки: {e}")

if __name__ == "__main__":
    main()
