# -*- coding: utf-8 -*-
"""
FastAPI приложение для винилового маркетплейса
REST API для фронтенда и Telegram бота
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from dotenv import load_dotenv

from utils.sheets_client import SheetsClient
from utils.llm.factory import get_adapter, get_fallback_adapter
from utils.supabase_client import SupabaseClient
from utils.auth_service import AuthService
from utils.import_service import ImportService
from utils.static_export import export_catalog_to_json

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to store the background task
background_sync_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background sync task
    global background_sync_task
    background_sync_task = asyncio.create_task(background_sync_worker())
    logger.info("Background sync worker started")
    
    yield
    
    # Shutdown: Cancel background sync task
    if background_sync_task:
        background_sync_task.cancel()
        try:
            await background_sync_task
        except asyncio.CancelledError:
            pass
        logger.info("Background sync worker stopped")

app = FastAPI(
    title="Виниловый маркетплейс API", 
    description="API для управления каталогом виниловых пластинок",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация клиентов
sheets_client = SheetsClient()

# Инициализация Supabase сервисов
try:
    supabase_client = SupabaseClient()
    auth_service = AuthService()
    import_service = ImportService()
    SUPABASE_ENABLED = True
    logger.info("Supabase сервисы успешно инициализированы")
except Exception as e:
    logger.warning(f"Supabase не доступен, работа только с Google Sheets: {e}")
    supabase_client = None
    auth_service = None
    import_service = None
    SUPABASE_ENABLED = False

# Настройка кеша
cache = Cache(Cache.MEMORY, serializer=JsonSerializer())
CACHE_TTL = int(os.getenv('CACHE_TTL', '60'))


# Pydantic модели
class RecordResponse(BaseModel):
    """Модель ответа с записью"""
    id: str
    article_id: str
    title: str
    artist: str
    genre: str
    year: int
    label: Optional[str]
    country: str
    format: Optional[str]
    condition: str
    price: float
    photo_url: Optional[str]
    status: str
    description: Optional[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    stock_count: int


class RecordsListResponse(BaseModel):
    """Модель списка записей"""
    total: int
    records: List[RecordResponse]


class GenerateDescriptionRequest(BaseModel):
    """Модель запроса на генерацию описания"""
    record_id: str
    title: str
    artist: str
    year: int
    genre: str
    label: Optional[str] = None
    country: Optional[str] = None


class GenerateDescriptionResponse(BaseModel):
    """Модель ответа генерации описания"""
    status: str
    description: str
    generated_at: str


# Supabase-specific models

class TelegramAuthRequest(BaseModel):
    """Запрос аутентификации через Telegram"""
    telegram_id: int
    telegram_username: Optional[str] = None
    full_name: Optional[str] = None


class TelegramAuthResponse(BaseModel):
    """Ответ аутентификации"""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    expires_in: int


class ImportSheetsRequest(BaseModel):
    """Запрос импорта из Google Sheets"""
    sheet_name: str = "Справочник"
    update_existing: bool = False
    preserve_custom_fields: bool = True


class ImportSheetsResponse(BaseModel):
    """Ответ импорта"""
    status: str
    timestamp: str
    summary: Dict
    duration_seconds: float


class RecordUpdateRequest(BaseModel):
    """Запрос обновления записи"""
    description: Optional[str] = None
    image_url: Optional[str] = None
    custom_image: Optional[bool] = None
    custom_description: Optional[bool] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    status: Optional[str] = None


class PreorderRequest(BaseModel):
    """Запрос на создание предзаказа с фронтенда"""
    search_query: str
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_telegram: Optional[str] = None


class PreorderResponse(BaseModel):
    """Ответ создания предзаказа"""
    status: str
    article_id: str
    title: str
    artist: str
    message: str
    row_number: int


def calculate_priority_score(record: dict) -> int:
    """
    Расчёт приоритета записи для сортировки
    
    Args:
        record: Запись из Google Sheets
        
    Returns:
        Приоритетный балл
    """
    score = 0
    description = str(record.get('Описание', '')).lower()
    condition = str(record.get('Состояние', '')).lower()
    country = str(record.get('Страна', '')).lower()
    
    # Безопасное преобразование года в int
    try:
        year = int(record.get('Год', 9999))
    except (ValueError, TypeError):
        year = 9999
    
    # Бонусы за ключевые слова в описании
    if 'оригинал' in description:
        score += 50
    if 'пресс 1960' in description or '1960-х' in description:
        score += 40
    
    # Бонусы за состояние
    if 'mint' in condition or 'near mint' in condition:
        score += 30
    
    # Бонусы за страну
    if 'ссср' in country or 'soviet' in country:
        score += 25
    
    # Бонусы за год выпуска
    if year < 1970:
        score += 20
    
    # Бонус за наличие AI-описания (не шаблонного)
    if description and len(description) > 100:
        score += 10
    
    return score


def generate_cache_key(filters: dict) -> str:
    """
    Генерация ключа кеша на основе фильтров
    
    Args:
        filters: Словарь с фильтрами
        
    Returns:
        MD5 хеш параметров
    """
    filter_string = str(sorted(filters.items()))
    return hashlib.md5(filter_string.encode()).hexdigest()


@app.get("/", tags=["Health"])
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "Vinyl Marketplace API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка здоровья сервиса"""
    try:
        # Проверка подключения к Google Sheets
        sheets_client.spreadsheet.title
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "google_sheets": "connected",
                "llm_provider": os.getenv('LLM_PROVIDER', 'qwen')
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/records", response_model=RecordsListResponse, tags=["Records"])
async def get_records(
    search: Optional[str] = Query(None, description="Поиск по названию/исполнителю"),
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    year_min: Optional[int] = Query(None, description="Минимальный год"),
    year_max: Optional[int] = Query(None, description="Максимальный год"),
    condition: Optional[str] = Query(None, description="Фильтр по состоянию"),
    country: Optional[str] = Query(None, description="Фильтр по стране"),
    price_min: Optional[float] = Query(None, description="Минимальная цена"),
    price_max: Optional[float] = Query(None, description="Максимальная цена"),
    limit: int = Query(50, ge=1, le=100, description="Количество результатов"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации")
):
    """
    Получение списка виниловых пластинок с фильтрацией и умной сортировкой
    
    - **genre**: Фильтр по жанру (частичное совпадение)
    - **year_min**: Минимальный год выпуска
    - **year_max**: Максимальный год выпуска
    - **condition**: Фильтр по состоянию
    - **country**: Фильтр по стране производства
    - **price_min**: Минимальная цена
    - **price_max**: Максимальная цена
    - **limit**: Количество записей на странице (по умолчанию 50)
    - **offset**: Смещение для пагинации (по умолчанию 0)
    """
    try:
        # Подготовка фильтров
        filters = {}
        if genre:
            filters['genre'] = genre
        if year_min:
            filters['year_min'] = year_min
        if year_max:
            filters['year_max'] = year_max
        if condition:
            filters['condition'] = condition
        if country:
            filters['country'] = country
        if price_min:
            filters['price_min'] = price_min
        if price_max:
            filters['price_max'] = price_max
        
        # Генерация ключа кеша
        cache_key = f"records_{generate_cache_key(filters)}_{search or ''}_{limit}_{offset}"
        
        # Попытка получить из кеша
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info(f"Возврат данных из кеша: {cache_key}")
            return cached_result
        
        # Получение записей из Google Sheets
        if search:
            # Поиск по запросу
            raw_records = sheets_client.find_records_by_query(search, limit=100)
        else:
            # Все записи с фильтрами
            raw_records = sheets_client.get_all_records(filters if filters else None)
        
        # Расчёт приоритета и сортировка
        records_with_score = []
        for idx, record in enumerate(raw_records):
            score = calculate_priority_score(record)
            records_with_score.append((score, idx, record))
        
        # Сортировка: сначала по приоритету (desc), затем по индексу (новые первыми - desc)
        records_with_score.sort(key=lambda x: (-x[0], -x[1]))
        
        # Пагинация
        paginated_records = records_with_score[offset:offset + limit]
        
        # Формирование ответа
        result_records = []
        for score, idx, record in paginated_records:
            # Безопасное преобразование года
            try:
                year_val = int(record.get('Год', 0))
            except (ValueError, TypeError):
                year_val = 0
            
            # Безопасное преобразование цены
            try:
                price_val = float(record.get('Цена', 0))
            except (ValueError, TypeError):
                price_val = 0.0
            
            # Безопасное преобразование stock
            try:
                stock_val = int(record.get('Stock_Count', 1) or 1)
            except (ValueError, TypeError):
                stock_val = 1
            
            result_records.append(RecordResponse(
                id=f"row_{idx + 2}",
                article_id=record.get('Артикул', ''),
                title=record.get('Название', ''),
                artist=record.get('Исполнитель', ''),
                genre=record.get('Жанр', ''),
                year=year_val,
                label=record.get('Лейбл'),
                country=record.get('Страна', ''),
                format=record.get('Формат'),
                condition=record.get('Состояние', ''),
                price=price_val,
                photo_url=record.get('ФОТО_URL'),
                status=record.get('Статус', ''),
                description=record.get('Описание'),
                seo_title=record.get('SEO_Title'),
                seo_description=record.get('SEO_Description'),
                stock_count=stock_val
            ))
        
        response = RecordsListResponse(
            total=len(records_with_score),
            records=result_records
        )
        
        # Сохранение в кеш
        await cache.set(cache_key, response.dict(), ttl=CACHE_TTL)
        
        logger.info(f"Возвращено {len(result_records)} записей из {len(records_with_score)}")
        return response
        
    except Exception as e:
        logger.error(f"Ошибка получения записей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@app.get("/api/records/{article_id}", response_model=RecordResponse, tags=["Records"])
async def get_record_by_article(article_id: str):
    """
    Получение одной записи по артикулу (VIN-XXXXX)
    
    Используется для динамических страниц продукта в Next.js
    """
    try:
        # Поиск записи по артикулу
        record = sheets_client.find_record_by_article(article_id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        
        # Безопасное преобразование года
        try:
            year_val = int(record.get('Год', 0))
        except (ValueError, TypeError):
            year_val = 0
        
        # Безопасное преобразование цены
        try:
            price_val = float(record.get('Цена', 0))
        except (ValueError, TypeError):
            price_val = 0.0
        
        # Безопасное преобразование stock
        try:
            stock_val = int(record.get('Stock_Count', 1) or 1)
        except (ValueError, TypeError):
            stock_val = 1
        
        row_number = record.get('_row_number', 0)
        
        return RecordResponse(
            id=f"row_{row_number}",
            article_id=record.get('Артикул', ''),
            title=record.get('Название', ''),
            artist=record.get('Исполнитель', ''),
            genre=record.get('Жанр', ''),
            year=year_val,
            label=record.get('Лейбл'),
            country=record.get('Страна', ''),
            format=record.get('Формат'),
            condition=record.get('Состояние', ''),
            price=price_val,
            photo_url=record.get('ФОТО_URL'),
            status=record.get('Статус', ''),
            description=record.get('Описание'),
            seo_title=record.get('SEO_Title'),
            seo_description=record.get('SEO_Description'),
            stock_count=stock_val
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения записи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@app.post("/api/generate-description", response_model=GenerateDescriptionResponse, tags=["AI"])
async def generate_description(request: GenerateDescriptionRequest):
    """
    Генерация AI-описания для виниловой пластинки
    
    Использует настроенный LLM провайдер (Qwen/OpenAI/Claude/Yandex/Custom)
    с автоматическим fallback и шаблонным описанием в случае ошибки.
    """
    try:
        # Подготовка данных для LLM
        record_data = {
            'title': request.title,
            'artist': request.artist,
            'year': request.year,
            'genre': request.genre,
            'label': request.label or 'неизвестен',
            'country': request.country or 'неизвестна'
        }
        
        logger.info(f"Генерация описания для: {request.title} - {request.artist}")
        
        # Получение LLM адаптера
        adapter = get_adapter()
        
        # Генерация описания
        description = adapter.generate_description(record_data)
        
        # Извлечение номера строки из record_id
        if request.record_id.startswith('row_'):
            row_number = int(request.record_id.replace('row_', ''))
            
            # Обновление описания в Google Sheets
            sheets_client.update_description(row_number, description)
            
            # Инвалидация кеша
            await cache.clear()
            
            logger.info(f"Описание успешно сохранено в строку {row_number}")
        
        return GenerateDescriptionResponse(
            status="completed",
            description=description,
            generated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Ошибка генерации описания: {e}")
        
        # Попытка использовать fallback
        try:
            fallback_adapter = get_fallback_adapter()
            if fallback_adapter:
                description = fallback_adapter.generate_description(record_data)
                status = "completed_with_fallback"
            else:
                # Использование шаблонного описания
                adapter = get_adapter()
                description = adapter.generate_template_description(record_data)
                status = "completed_with_template"
            
            return GenerateDescriptionResponse(
                status=status,
                description=description,
                generated_at=datetime.now().isoformat()
            )
            
        except Exception as fallback_error:
            logger.error(f"Ошибка fallback генерации: {fallback_error}")
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать описание")


@app.post("/api/preorder", response_model=PreorderResponse, tags=["Preorders"])
async def create_preorder(request: PreorderRequest):
    """
    Создание предзаказа с фронтенда
    
    Когда пользователь ищет пластинку, которой нет в каталоге,
    автоматически создаётся карточка предзаказа с AI-описанием.
    """
    try:
        search_query = request.search_query.strip()
        
        # Парсим запрос на исполнителя и название
        parts = search_query.split(' - ', 1)
        if len(parts) == 2:
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            title = search_query
            artist = "Уточняется"
        
        logger.info(f"Создание предзаказа: {artist} - {title}")
        
        # Создаём запись в Google Sheets
        record_data = {
            'title': title,
            'artist': artist,
            'genre': '',
            'year': '',
            'label': '',
            'country': '',
            'condition': '',
            'price': 0,
            'photo_url': '',
            'seller_tg_id': 0,
            'stock_count': 0,
            'status': '🟡 Предзаказ'
        }
        
        row_number = sheets_client.add_record(record_data)
        
        # Получаем артикул созданной записи
        worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        article_id = worksheet.cell(row_number, 1).value or f"VIN-{row_number:05d}"
        
        # Запускаем AI-генерацию описания в фоне
        try:
            adapter = get_adapter()
            description = adapter.generate_description({
                'title': title,
                'artist': artist,
                'year': 0,
                'genre': 'Уточняется',
                'label': 'Уточняется',
                'country': 'Уточняется'
            })
            sheets_client.update_description(row_number, description)
            logger.info(f"AI-описание сохранено для строки {row_number}")
        except Exception as ai_error:
            logger.warning(f"Не удалось сгенерировать AI-описание: {ai_error}")
        
        # Инвалидация кеша
        await cache.clear()
        
        return PreorderResponse(
            status="created",
            article_id=article_id,
            title=title,
            artist=artist,
            message=f"Предзаказ '{artist} - {title}' успешно создан! Мы уведомим вас о поступлении.",
            row_number=row_number
        )
        
    except Exception as e:
        logger.error(f"Ошибка создания предзаказа: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка создания предзаказа: {str(e)}")


@app.post("/admin/export-static", tags=["Admin"])
async def export_static_catalog(
    output_dir: str = Query("./static_export", description="Директория для экспорта")
):
    """
    Экспорт каталога в JSON файлы для фронтенда
    
    Создаёт:
    - catalog.json - полный каталог
    - products/{article_id}.json - отдельные файлы товаров
    """
    try:
        start_time = datetime.now()
        
        # Экспорт каталога
        result = export_catalog_to_json(output_dir)
        
        # Инвалидация кеша
        await cache.clear()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Экспорт завершён за {duration:.2f}с")
        
        return {
            "status": "success",
            "message": "Каталог успешно экспортирован",
            "exported_records": result["exported_records"],
            "catalog_path": result["catalog_path"],
            "generated_at": result["generated_at"],
            "duration_seconds": round(duration, 2)
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка экспорта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Получение метрик системы"""
    try:
        # Получение статистики из Google Sheets
        catalog_worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_CATALOG)
        balances_worksheet = sheets_client.spreadsheet.worksheet(sheets_client.SHEET_BALANCES)
        
        total_records = len(catalog_worksheet.get_all_values()) - 1  # -1 для заголовка
        total_users = len(balances_worksheet.get_all_values()) - 1
        
        # Подсчёт записей по статусам
        records = catalog_worksheet.get_all_records()
        available = sum(1 for r in records if '🟢' in str(r.get('Статус', '')))
        reserved = sum(1 for r in records if '🟡' in str(r.get('Статус', '')))
        sold = sum(1 for r in records if '🔴' in str(r.get('Статус', '')))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "records": {
                "total": total_records,
                "available": available,
                "reserved": reserved,
                "sold": sold
            },
            "users": {
                "total": total_users
            },
            "llm": {
                "provider": os.getenv('LLM_PROVIDER', 'qwen'),
                "fallback": os.getenv('LLM_FALLBACK_PROVIDER', 'none')
            },
            "supabase": {
                "enabled": SUPABASE_ENABLED
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения метрик: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения метрик")


# ============================================
# Supabase эндпоинты
# ============================================

@app.post("/auth/telegram", response_model=TelegramAuthResponse, tags=["Authentication"])
async def authenticate_telegram(request: TelegramAuthRequest):
    """
    Аутентификация пользователя через Telegram ID
    
    Создает нового пользователя или возвращает токен существующего
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase не доступен")
    
    try:
        # Валидация telegram_id
        if request.telegram_id <= 0:
            raise HTTPException(status_code=400, detail="Некорректный telegram_id")
        
        # Создание/аутентификация пользователя
        user_data = auth_service.create_user_from_telegram(
            telegram_id=request.telegram_id,
            username=request.telegram_username,
            full_name=request.full_name
        )
        
        return TelegramAuthResponse(
            access_token=user_data['access_token'],
            user_id=user_data['user_id'],
            expires_in=user_data['expires_in']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка аутентификации: {e}")
        raise HTTPException(status_code=500, detail="Ошибка аутентификации")


@app.get("/records", tags=["Records"])
async def get_supabase_records(
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    year_min: Optional[int] = Query(None, description="Минимальный год"),
    year_max: Optional[int] = Query(None, description="Максимальный год"),
    price_min: Optional[float] = Query(None, description="Минимальная цена"),
    price_max: Optional[float] = Query(None, description="Максимальная цена"),
    search: Optional[str] = Query(None, description="Поиск по названию и исполнителю"),
    status: Optional[str] = Query("available", description="Статус записи"),
    limit: int = Query(50, ge=1, le=100, description="Количество результатов"),
    offset: int = Query(0, ge=0, description="Смещение для пагинации")
):
    """
    Получение записей из Supabase с фильтрацией
    
    Использует Supabase REST API для умной фильтрации на уровне SQL
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase не доступен")
    
    try:
        # Подготовка фильтров
        filters = {}
        if genre:
            filters['genre'] = genre
        if year_min:
            filters['year_min'] = year_min
        if year_max:
            filters['year_max'] = year_max
        if price_min:
            filters['price_min'] = price_min
        if price_max:
            filters['price_max'] = price_max
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status
        
        # Получение записей
        records = supabase_client.get_records(filters, limit, offset)
        
        return {
            "total": len(records),
            "records": records
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения записей из Supabase: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных")


@app.get("/records/{record_id}", tags=["Records"])
async def get_record_by_id(record_id: str):
    """Получение записи по ID"""
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase не доступен")
    
    try:
        record = supabase_client.get_record_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        
        return record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения записи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения записи")


@app.patch("/records/{record_id}", tags=["Records"])
async def update_record(record_id: str, updates: RecordUpdateRequest):
    """
    Обновление записи (требуется аутентификация)
    
    Обновляет только переданные поля
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase не доступен")
    
    try:
        # Подготовка обновлений (только непустые поля)
        update_data = {}
        if updates.description is not None:
            update_data['description'] = updates.description
            update_data['custom_description'] = updates.custom_description or True
        if updates.image_url is not None:
            update_data['image_url'] = updates.image_url
            update_data['custom_image'] = updates.custom_image or True
        if updates.price is not None:
            update_data['price'] = updates.price
        if updates.condition is not None:
            update_data['condition'] = updates.condition
        if updates.status is not None:
            update_data['status'] = updates.status
        
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет полей для обновления")
        
        # Обновление записи
        updated_record = supabase_client.update_record(record_id, update_data)
        
        if not updated_record:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        
        return updated_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления записи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления")


@app.post("/admin/import-from-sheets", response_model=ImportSheetsResponse, tags=["Admin"])
async def import_from_sheets(request: ImportSheetsRequest):
    """
    Импорт записей из Google Sheets в Supabase
    
    Требует админских прав
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase не доступен")
    
    try:
        # TODO: Добавить проверку админских прав через Bearer token
        
        # Выполнение импорта
        result = import_service.import_from_sheets(
            sheet_name=request.sheet_name,
            update_existing=request.update_existing,
            preserve_custom_fields=request.preserve_custom_fields,
            admin_telegram_id=int(os.getenv('ADMIN_TELEGRAM_ID', '0'))
        )
        
        return ImportSheetsResponse(**result)
        
    except Exception as e:
        logger.error(f"Ошибка импорта: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


@app.post("/ai/generate-description/{record_id}", tags=["AI"])
async def generate_description_for_record(record_id: str, force_regenerate: bool = False):
    """
    Генерация AI-описания для записи из Supabase
    
    Использует существующую логику LLM генерации
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(status_code=503, detail="Supabase не доступен")
    
    try:
        # Получаем запись
        record = supabase_client.get_record_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        
        # Проверяем необходимость генерации
        if record.get('description') and record.get('custom_description') and not force_regenerate:
            raise HTTPException(
                status_code=400,
                detail="Описание уже существует. Используйте force_regenerate=true"
            )
        
        # Подготовка данных для LLM
        record_data = {
            'title': record['title'],
            'artist': record['artist'],
            'year': record['year'],
            'genre': record['genre'],
            'label': record.get('label', 'неизвестен'),
            'country': record.get('country', 'неизвестна')
        }
        
        logger.info(f"Генерация описания для: {record_data['title']} - {record_data['artist']}")
        
        # Получение LLM адаптера
        adapter = get_adapter()
        
        # Генерация описания
        description = adapter.generate_description(record_data)
        
        # Обновление записи в Supabase
        supabase_client.update_record(record_id, {
            'description': description,
            'custom_description': False  # AI-сгенерированное
        })
        
        logger.info(f"Описание сохранено для записи {record_id}")
        
        return {
            "status": "completed",
            "record_id": record_id,
            "description": description,
            "generated_at": datetime.now().isoformat(),
            "llm_provider": os.getenv('LLM_PROVIDER', 'qwen')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации описания: {e}")
        
        # Попытка использовать fallback
        try:
            fallback_adapter = get_fallback_adapter()
            if fallback_adapter:
                description = fallback_adapter.generate_description(record_data)
                status = "completed_with_fallback"
            else:
                adapter = get_adapter()
                description = adapter.generate_template_description(record_data)
                status = "completed_with_template"
            
            return {
                "status": status,
                "record_id": record_id,
                "description": description,
                "generated_at": datetime.now().isoformat()
            }
        except Exception as fallback_error:
            logger.error(f"Ошибка fallback генерации: {fallback_error}")
            raise HTTPException(status_code=500, detail="Не удалось сгенерировать описание")


async def background_sync_worker():
    """Background worker for automatic sync every 2 minutes"""
    while True:
        try:
            await asyncio.sleep(120)  # 2 minutes for more frequent updates
            
            # Perform sync
            logger.info("Starting automatic sync from Google Sheets...")
            
            # Get all records from sheets to refresh connection
            raw_records = sheets_client.get_all_records()
            logger.info(f"Retrieved {len(raw_records)} records from Google Sheets")
            
            # Force clear cache to ensure fresh data on next request
            await cache.clear()
            logger.info("Cache cleared after sync")
            
            # Also update any Supabase data if enabled
            if SUPABASE_ENABLED and import_service:
                try:
                    import_result = import_service.import_from_sheets(
                        sheet_name="Справочник",
                        update_existing=True,
                        preserve_custom_fields=True
                    )
                    logger.info(f"Supabase sync completed: {import_result}")
                except Exception as e:
                    logger.error(f"Error syncing with Supabase: {e}")
            
        except asyncio.CancelledError:
            logger.info("Background sync worker cancelled")
            break
        except Exception as e:
            logger.error(f"Error in background sync: {e}")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8000'))
    
    logger.info(f"Запуск FastAPI на {host}:{port}")
    uvicorn.run(app, host=host, port=port)
