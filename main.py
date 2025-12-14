"""
AI Service Platform - FastAPI Backend
Оптимизировано для Timeweb App Platform
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import os
import json
import sqlite3
from pathlib import Path

# Google интеграция
try:
    from google_sync import init_google_integration, sync_order_to_google
    GOOGLE_SYNC_AVAILABLE = True
except ImportError:
    GOOGLE_SYNC_AVAILABLE = False
    print("⚠️ Google интеграция недоступна (установите: pip install google-api-python-client)")

# Калькулятор цен
try:
    from price_calculator import estimate_from_description, PriceCalculator, PriceFactors, ServiceCategory, Urgency, District
    PRICE_CALCULATOR_AVAILABLE = True
except ImportError:
    PRICE_CALCULATOR_AVAILABLE = False
    print("⚠️ Калькулятор цен недоступен")

# MVP Modules
try:
    from conversation_manager import ConversationManager, ConversationType, ConversationChannel
    from job_file_generator import JobFileGenerator
    from schedule_manager import ScheduleManager
    from notification_service import NotificationService, NotificationType
    MVP_MODULES_AVAILABLE = True
except ImportError as e:
    MVP_MODULES_AVAILABLE = False
    print(f"⚠️ MVP модули недоступны: {e}")

# ==================== КОНФИГУРАЦИЯ ====================

# Переменные окружения
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/ai_service.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ==================== ИНИЦИАЛИЗАЦИЯ БД ====================

def init_database():
    """Инициализация SQLite базы данных"""
    db_dir = Path(DATABASE_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Таблица мастеров
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS masters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            telegram_id INTEGER UNIQUE,
            specializations TEXT NOT NULL,
            city TEXT NOT NULL,
            preferred_channel TEXT DEFAULT 'telegram',
            rating REAL DEFAULT 5.0,
            is_active BOOLEAN DEFAULT 1,
            terminal_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- MVP Enhancement fields
            schedule_json TEXT,
            terminal_type TEXT DEFAULT 'smartphone',
            terminal_id TEXT,
            onboarding_conversation_id TEXT,
            last_schedule_confirmation TIMESTAMP
        )
    """)
    
    # Таблица заказов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            client_phone TEXT NOT NULL,
            category TEXT NOT NULL,
            problem_description TEXT NOT NULL,
            address TEXT NOT NULL,
            estimated_price REAL,
            status TEXT DEFAULT 'pending',
            master_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- НОВЫЕ ПОЛЯ ДЛЯ ОТСЛЕЖИВАНИЯ
            master_departed_at TIMESTAMP,
            master_arrived_at TIMESTAMP,
            client_phone_revealed BOOLEAN DEFAULT 0,
            master_location_lat REAL,
            master_location_lon REAL,
            route_screenshot_url TEXT,
            google_calendar_event_id TEXT,
            google_task_id TEXT,
            
            -- MVP Enhancement fields
            conversation_id TEXT,
            ai_diagnosis TEXT,
            work_instructions_json TEXT,
            job_file_url TEXT,
            media_urls TEXT,
            estimated_duration INTEGER,
            urgency_level TEXT DEFAULT 'standard',
            
            FOREIGN KEY (master_id) REFERENCES masters(id)
        )
    """)
    
    # Таблица транзакций
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            platform_fee REAL,
            master_earnings REAL,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- MVP Enhancement fields
            terminal_id TEXT,
            payment_gateway_response TEXT,
            commission_breakdown_json TEXT,
            
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    # Таблица разговоров (новая)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            channel TEXT NOT NULL,
            participant_name TEXT,
            participant_phone TEXT,
            messages_json TEXT,
            transcript TEXT,
            audio_url TEXT,
            status TEXT DEFAULT 'active',
            extracted_data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    
    # Таблица инструкций (новая)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_instructions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            problem_diagnosis TEXT NOT NULL,
            tools_required TEXT,
            consumables_required TEXT,
            parts_required TEXT,
            step_by_step TEXT,
            safety_notes TEXT,
            estimated_time INTEGER,
            difficulty_level TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    # Таблица уведомлений (новая)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_id TEXT NOT NULL,
            recipient_type TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            channel TEXT NOT NULL,
            title TEXT,
            message TEXT NOT NULL,
            data_json TEXT,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    
    # Миграция: добавить telegram_id если его нет
    cursor.execute("PRAGMA table_info(masters)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'telegram_id' not in columns:
        print("🔄 Добавляю колонку telegram_id в таблицу masters...")
        cursor.execute("ALTER TABLE masters ADD COLUMN telegram_id INTEGER UNIQUE")
        conn.commit()
        print("✅ Миграция завершена!")
    
    conn.close()

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="AI Service Platform",
    description="Автоматизированная платформа для связи мастеров и клиентов",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - Монтируем только если папка существует
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ Static files монтированы через /static")
else:
    print("⚠️ Static files НЕ монтированы (папка не найдена)")

# ==================== КРАСИВЫЕ URL ДЛЯ СТРАНИЦ ====================

# Главная страница
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Сервисные страницы с красивыми URL
@app.get("/services/usb-rozetki")
@app.get("/services/usb-rozetki.html")
async def usb_rozetki():
    return FileResponse("static/services/usb-rozetki.html")

@app.get("/services/smart-home")
@app.get("/services/smart-home.html")
async def smart_home():
    return FileResponse("static/services/smart-home.html")

@app.get("/services/emergency")
@app.get("/services/emergency.html")
async def emergency():
    return FileResponse("static/services/emergency.html")

@app.get("/services/seasonal-packages")
@app.get("/services/seasonal-packages.html")
async def seasonal_packages():
    return FileResponse("static/services/seasonal-packages.html")

# Существующие сервисные страницы
@app.get("/services/elektroschit")
@app.get("/services/elektroschit.html")
async def elektroschit():
    return FileResponse("static/services/elektroschit.html")

@app.get("/services/osveshchenie")
@app.get("/services/osveshchenie.html")
async def osveshchenie():
    return FileResponse("static/services/osveshchenie.html")

@app.get("/services/pod-klyuch")
@app.get("/services/pod-klyuch.html")
async def pod_klyuch():
    return FileResponse("static/services/pod-klyuch.html")

@app.get("/services/provodka")
@app.get("/services/provodka.html")
async def provodka():
    return FileResponse("static/services/provodka.html")

@app.get("/services/remont-elektriki")
@app.get("/services/remont-elektriki.html")
async def remont_elektriki():
    return FileResponse("static/services/remont-elektriki.html")

@app.get("/services/rozetki")
@app.get("/services/rozetki.html")
async def rozetki():
    return FileResponse("static/services/rozetki.html")

# Блог с красивыми URL
@app.get("/blog/kak-vybrat-usb-rozetki-dlya-doma")
@app.get("/blog/kak-vybrat-usb-rozetki-dlya-doma.html")
async def blog_usb_rozetki():
    return FileResponse("static/blog/kak-vybrat-usb-rozetki-dlya-doma.html")

# Основные страницы
@app.get("/calculator")
@app.get("/calculator.html")
async def calculator():
    return FileResponse("static/calculator.html")

# Интегрированный калькулятор с функционалом React
@app.get("/calculator-integrated")
@app.get("/calculator-integrated.html")
async def calculator_integrated():
    return FileResponse("static/calculator-integrated.html")

@app.get("/catalog")
@app.get("/catalog.html")
async def catalog():
    return FileResponse("static/catalog.html")

@app.get("/services")
@app.get("/services.html")
async def services():
    return FileResponse("static/services.html")

@app.get("/reviews")
@app.get("/reviews.html")
async def reviews():
    return FileResponse("static/reviews.html")

@app.get("/portfolio")
@app.get("/portfolio.html")
async def portfolio():
    return FileResponse("static/portfolio.html")

@app.get("/high-conversion-landing")
@app.get("/high-conversion-landing.html")
async def high_conversion_landing():
    return FileResponse("static/high-conversion-landing.html")

# Sitemap и robots.txt
@app.get("/sitemap.xml")
async def sitemap():
    return FileResponse("static/sitemap.xml", media_type="application/xml")

@app.get("/robots.txt")
async def robots():
    return FileResponse("static/robots.txt", media_type="text/plain")

# React Build - Монтируем если есть dist/
if Path("electric-service-automation-main/dist").exists():
    app.mount("/assets", StaticFiles(directory="electric-service-automation-main/dist/assets"), name="assets")
    print("✅ React assets монтированы через /assets")
else:
    print("⚠️ React build НЕ найден (соберите: npm run build)")

# Инициализация БД при старте
@app.on_event("startup")
async def startup_event():
    import os
    from pathlib import Path
    
    print("="*60)
    print("🔍 ДИАГНОСТИКА ОКРУЖЕНИЯ:")
    print(f"📂 Current working directory: {os.getcwd()}")
    print(f"📂 Files in current dir: {os.listdir('.')}")
    
    # Проверка static/
    static_path = Path("static")
    if static_path.exists():
        print(f"✅ static/ exists")
        print(f"   Files: {list(static_path.glob('*'))}")
    else:
        print(f"❌ static/ folder NOT FOUND!")
        print(f"   Expected path: {static_path.absolute()}")
        
        # Попытка найти HTML файлы в других местах
        print("🔍 Searching for HTML files...")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.html'):
                    print(f"   Found: {os.path.join(root, file)}")
    
    print("="*60)
    
    init_database()
    
    # Инициализация Google интеграции
    if GOOGLE_SYNC_AVAILABLE:
        try:
            init_google_integration()
            print("✅ Google Calendar и Tasks синхронизация активна")
        except Exception as e:
            print(f"⚠️ Google интеграция недоступна: {e}")
    
    print(f"🚀 AI Service Platform запущен (Environment: {ENVIRONMENT})")

# ==================== МОДЕЛИ ДАННЫХ ====================

class MasterRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r'^\+\d{10,15}$')
    specializations: List[str] = Field(..., min_items=1)
    city: str = Field(..., min_length=2, max_length=50)
    preferred_channel: str = Field(default="telegram")

class ClientRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r'^\+\d{10,15}$')
    category: str
    problem_description: str = Field(..., min_length=10)
    address: str = Field(..., min_length=5)
    photos: Optional[List[str]] = None

class JobStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r'^(pending|accepted|in_progress|completed|cancelled)$')

class PaymentProcess(BaseModel):
    job_id: int
    payment_method: str = Field(..., pattern=r'^(cash|card|sbp)$')
    amount: float = Field(..., gt=0)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_db_connection():
    """Получить подключение к БД"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_pricing(category: str, description: str) -> float:
    """Расчёт цены на основе категории и описания"""
    
    # 🔥 ИСПОЛЬЗОВАТЬ ПРОДВИНУТЫЙ КАЛЬКУЛЯТОР
    if PRICE_CALCULATOR_AVAILABLE:
        try:
            result = estimate_from_description(description, category)
            print(f"✅ Автоматический расчёт: {result['total_price']}₽")
            print(f"   Детали: {result['breakdown']}")
            return result['total_price']
        except Exception as e:
            print(f"⚠️ Ошибка калькулятора: {e}")
    
    # Базовый расчёт (если калькулятор недоступен)
    base_prices = {
        "electrical": 1500,
        "plumbing": 1800,
        "appliance": 2000,
        "general": 1200
    }
    
    base_price = base_prices.get(category, 1500)
    
    # Увеличение цены за срочность или сложность
    if "срочно" in description.lower() or "urgent" in description.lower():
        base_price *= 1.3
    
    if len(description) > 200:  # Сложная задача
        base_price *= 1.2
    
    return round(base_price, 2)

def find_available_master(category: str, city: str) -> Optional[int]:
    """Найти доступного мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ищем мастера по специализации и городу
    cursor.execute("""
        SELECT id FROM masters 
        WHERE is_active = 1 
        AND terminal_active = 1
        AND city = ?
        AND specializations LIKE ?
        ORDER BY rating DESC
        LIMIT 1
    """, (city, f'%{category}%'))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['id'] if result else None

def calculate_platform_fee(amount: float) -> Dict[str, float]:
    """Расчёт комиссий платформы"""
    payment_gateway_fee = amount * 0.02  # 2% платёжный шлюз
    remaining = amount - payment_gateway_fee
    platform_commission = remaining * 0.25  # 25% комиссия платформы
    master_earnings = remaining - platform_commission
    
    return {
        "total": amount,
        "payment_gateway_fee": round(payment_gateway_fee, 2),
        "platform_commission": round(platform_commission, 2),
        "master_earnings": round(master_earnings, 2)
    }

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Главная страница - отдаём статичный HTML из /static если есть"""
    # Проверяем static/index.html (старая версия что работала)
    static_index = Path("static/index.html")
    if static_index.exists():
        return FileResponse(static_index)
    
    # Fallback - встроенный HTML
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Услуги электрика в Калининграде | Быстрый вызов мастера</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            :root {
                --primary: #1a1a1a;
                --primary-light: #333;
                --accent: #10b981;
                --accent-dark: #059669;
                --bg: #ffffff;
                --bg-alt: #f9fafb;
                --text: #1a1a1a;
                --text-muted: #6b7280;
                --border: #e5e7eb;
                --shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg);
                color: var(--text);
                line-height: 1.6;
            }
            
            /* Header */
            header {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(10px);
                border-bottom: 1px solid var(--border);
                position: sticky;
                top: 0;
                z-index: 50;
            }
            
            .header-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 1rem 1.5rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 2rem;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                text-decoration: none;
                color: var(--primary);
                font-size: 1.25rem;
                font-weight: 700;
            }
            
            .logo-icon {
                width: 32px;
                height: 32px;
                background: linear-gradient(135deg, var(--accent), var(--accent-dark));
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.25rem;
            }
            
            nav {
                display: flex;
                gap: 2rem;
            }
            
            nav a {
                text-decoration: none;
                color: var(--text-muted);
                font-size: 0.95rem;
                transition: color 0.2s;
            }
            
            nav a:hover {
                color: var(--primary);
            }
            
            .header-btn {
                padding: 0.625rem 1.25rem;
                background: var(--accent);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 0.95rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                text-decoration: none;
                display: inline-block;
            }
            
            .header-btn:hover {
                background: var(--accent-dark);
                transform: translateY(-1px);
            }
            
            /* Hero Section */
            .hero {
                background: linear-gradient(135deg, #f9fafb 0%, #e5e7eb 100%);
                padding: 4rem 1.5rem;
                position: relative;
                overflow: hidden;
            }
            
            .hero::before {
                content: '';
                position: absolute;
                right: -5%;
                top: -10%;
                width: 400px;
                height: 400px;
                border-radius: 50%;
                border: 8px solid rgba(16, 185, 129, 0.1);
            }
            
            .hero-container {
                max-width: 1200px;
                margin: 0 auto;
                text-align: center;
                position: relative;
                z-index: 1;
            }
            
            .hero-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                background: rgba(16, 185, 129, 0.1);
                border-radius: 100px;
                color: var(--accent);
                font-size: 0.875rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
            }
            
            h1 {
                font-size: clamp(2rem, 5vw, 3.5rem);
                font-weight: 800;
                margin-bottom: 1rem;
                line-height: 1.2;
            }
            
            .hero h1 span {
                color: var(--accent);
                display: block;
            }
            
            .hero-subtitle {
                font-size: 1.125rem;
                color: var(--text-muted);
                max-width: 600px;
                margin: 0 auto 2rem;
            }
            
            .hero-actions {
                display: flex;
                gap: 1rem;
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .btn {
                padding: 1rem 2rem;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, var(--accent), var(--accent-dark));
                color: white;
                box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
            }
            
            .btn-outline {
                background: white;
                color: var(--primary);
                border: 2px solid var(--border);
            }
            
            .btn-outline:hover {
                border-color: var(--accent);
                color: var(--accent);
            }
            
            /* Services Section */
            .services {
                padding: 4rem 1.5rem;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .section-header {
                text-align: center;
                margin-bottom: 3rem;
            }
            
            .section-badge {
                color: var(--accent);
                font-weight: 600;
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
            }
            
            .section-title {
                font-size: 2.5rem;
                font-weight: 800;
                margin-bottom: 0.75rem;
            }
            
            .section-subtitle {
                color: var(--text-muted);
                font-size: 1.125rem;
            }
            
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
            }
            
            .service-card {
                background: white;
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 2rem;
                transition: all 0.3s;
                cursor: pointer;
            }
            
            .service-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border-color: var(--accent);
            }
            
            .service-icon {
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2rem;
                margin-bottom: 1.5rem;
            }
            
            .service-card h3 {
                font-size: 1.25rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }
            
            .service-card p {
                color: var(--text-muted);
                font-size: 0.95rem;
                line-height: 1.6;
            }
            
            /* How it works */
            .how-it-works {
                padding: 4rem 1.5rem;
                background: var(--bg-alt);
            }
            
            .steps {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 2rem;
                margin-top: 3rem;
            }
            
            .step {
                text-align: center;
            }
            
            .step-number {
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, var(--accent), var(--accent-dark));
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                font-weight: 700;
                margin: 0 auto 1.5rem;
            }
            
            .step h3 {
                font-size: 1.125rem;
                margin-bottom: 0.5rem;
            }
            
            .step p {
                color: var(--text-muted);
                font-size: 0.95rem;
            }
            
            /* CTA Section */
            .cta {
                padding: 4rem 1.5rem;
                background: linear-gradient(135deg, var(--primary), var(--primary-light));
                color: white;
                text-align: center;
            }
            
            .cta h2 {
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
            
            .cta p {
                font-size: 1.125rem;
                opacity: 0.9;
                margin-bottom: 2rem;
            }
            
            .cta .btn-primary {
                background: white;
                color: var(--primary);
            }
            
            .cta .btn-primary:hover {
                background: var(--bg-alt);
            }
            
            /* Footer */
            footer {
                padding: 2rem 1.5rem;
                background: var(--bg-alt);
                border-top: 1px solid var(--border);
                text-align: center;
                color: var(--text-muted);
                font-size: 0.875rem;
            }
            
            @media (max-width: 768px) {
                nav { display: none; }
                .hero-actions { flex-direction: column; }
                .btn { width: 100%; justify-content: center; }
            }
        </style>
    </head>
    <body>
        <!-- Header -->
        <header>
            <div class="header-container">
                <a href="/" class="logo">
                    <div class="logo-icon">⚡</div>
                    <span>Услуги Мастера</span>
                </a>
                <nav>
                    <a href="/services">Услуги</a>
                    <a href="/calculator">Калькулятор</a>
                    <a href="#how-it-works">Как работает</a>
                </nav>
                <a href="/admin" class="header-btn">Админ</a>
            </div>
        </header>

        <!-- Hero Section -->
        <section class="hero">
            <div class="hero-container">
                <div class="hero-badge">
                    ⚡ Быстрая помощь в Калининграде
                </div>
                <h1>
                    Вызов мастера
                    <span>онлайн за 2 минуты</span>
                </h1>
                <p class="hero-subtitle">
                    Электрики, сантехники, мастера по бытовой технике. Прозрачные цены, гарантия качества.
                </p>
                <div class="hero-actions">
                    <button class="btn btn-primary" onclick="scrollToServices()">
                        🔧 Выбрать услугу
                    </button>
                    <a href="/calculator" class="btn btn-outline" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none;">
                        💡 Калькулятор стоимости
                    </a>
                    <a href="/master" class="btn btn-outline">
                        👨‍🔧 Для мастеров
                    </a>
                </div>
            </div>
        </section>

        <!-- Services Section -->
        <section class="services" id="services">
            <div class="container">
                <div class="section-header">
                    <div class="section-badge">Услуги</div>
                    <h2 class="section-title">Что мы предлагаем</h2>
                    <p class="section-subtitle">Широкий спектр услуг для дома и офиса</p>
                </div>
                <div class="services-grid">
                    <div class="service-card" onclick="openOrderForm('electrical')">
                        <div class="service-icon">⚡</div>
                        <h3>Электрика</h3>
                        <p>Замена розеток, выключателей, монтаж освещения, электропроводка</p>
                    </div>
                    <div class="service-card" onclick="openOrderForm('plumbing')">
                        <div class="service-icon">🚰</div>
                        <h3>Сантехника</h3>
                        <p>Ремонт кранов, установка сантехники, прочистка труб</p>
                    </div>
                    <div class="service-card" onclick="openOrderForm('appliance')">
                        <div class="service-icon">🔌</div>
                        <h3>Бытовая техника</h3>
                        <p>Ремонт холодильников, стиральных машин, микроволновок</p>
                    </div>
                    <div class="service-card" onclick="openOrderForm('general')">
                        <div class="service-icon">🔨</div>
                        <h3>Общие работы</h3>
                        <p>Мелкий ремонт, сборка мебели, навес полок</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- How it Works -->
        <section class="how-it-works" id="how-it-works">
            <div class="container">
                <div class="section-header">
                    <div class="section-badge">Процесс</div>
                    <h2 class="section-title">Как это работает</h2>
                    <p class="section-subtitle">Простые шаги до выполненной работы</p>
                </div>
                <div class="steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <h3>Оставьте заявку</h3>
                        <p>Выберите услугу и опишите проблему</p>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <h3>Получите оценку</h3>
                        <p>Автоматический расчёт стоимости</p>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <h3>Мастер выезжает</h3>
                        <p>Опытный специалист приедет в удобное время</p>
                    </div>
                    <div class="step">
                        <div class="step-number">4</div>
                        <h3>Готово!</h3>
                        <p>Оплата после выполнения работы</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- CTA -->
        <section class="cta">
            <div class="container">
                <h2>Готовы вызвать мастера?</h2>
                <p>Начните прямо сейчас — это займёт всего 2 минуты</p>
                <button class="btn btn-primary" onclick="scrollToServices()">
                    ✨ Оформить заказ
                </button>
            </div>
        </section>

        <!-- Footer -->
        <footer>
            <p>&copy; 2025 Услуги Мастера. Все права защищены.</p>
            <p style="margin-top: 0.5rem;">
                <a href="/docs" style="color: var(--accent); text-decoration: none;">API Документация</a> • 
                <a href="/admin" style="color: var(--accent); text-decoration: none;">Админ-панель</a> • 
                <a href="/master" style="color: var(--accent); text-decoration: none;">Для мастеров</a>
            </p>
        </footer>

        <script>
            function scrollToServices() {
                document.getElementById('services').scrollIntoView({ behavior: 'smooth' });
            }
            
            function openOrderForm(category) {
                // Редирект на страницу заказа с категорией
                window.location.href = `/order?category=${category}`;
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/form")
async def form_page():
    """Простая форма для клиентов"""
    html_path = Path("static/index.html")
    if not html_path.exists():
        raise HTTPException(status_code=500, detail=f"HTML file not found: {html_path.absolute()}")
    return FileResponse(html_path)

@app.get("/order")
async def order_page(category: str = "electrical"):
    """Страница оформления заказа"""
    from fastapi.responses import HTMLResponse
    
    categories_ru = {
        "electrical": "Электрика",
        "plumbing": "Сантехника",
        "appliance": "Бытовая техника",
        "general": "Общие работы"
    }
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Заказ мастера - {categories_ru.get(category, "Услуга")}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            :root {{
                --primary: #1a1a1a;
                --accent: #10b981;
                --accent-dark: #059669;
                --bg: #ffffff;
                --bg-alt: #f9fafb;
                --text: #1a1a1a;
                --text-muted: #6b7280;
                --border: #e5e7eb;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg-alt);
                color: var(--text);
                line-height: 1.6;
                padding: 2rem 1rem;
            }}
            
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 2.5rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }}
            
            .back-btn {{
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-muted);
                text-decoration: none;
                margin-bottom: 1.5rem;
                font-size: 0.9rem;
                transition: color 0.2s;
            }}
            
            .back-btn:hover {{
                color: var(--primary);
            }}
            
            h1 {{
                font-size: 2rem;
                margin-bottom: 0.5rem;
                color: var(--primary);
            }}
            
            .subtitle {{
                color: var(--text-muted);
                margin-bottom: 2rem;
                font-size: 1rem;
            }}
            
            .category-badge {{
                display: inline-block;
                padding: 0.5rem 1rem;
                background: rgba(16, 185, 129, 0.1);
                color: var(--accent);
                border-radius: 100px;
                font-weight: 600;
                font-size: 0.9rem;
                margin-bottom: 2rem;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            label {{
                display: block;
                margin-bottom: 0.5rem;
                color: var(--primary);
                font-weight: 600;
                font-size: 0.95rem;
            }}
            
            .required {{
                color: #ef4444;
            }}
            
            input, select, textarea {{
                width: 100%;
                padding: 0.875rem;
                border: 2px solid var(--border);
                border-radius: 10px;
                font-size: 1rem;
                transition: all 0.2s;
                font-family: inherit;
            }}
            
            input:focus, select:focus, textarea:focus {{
                outline: none;
                border-color: var(--accent);
                box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
            }}
            
            textarea {{
                resize: vertical;
                min-height: 120px;
            }}
            
            .btn {{
                width: 100%;
                padding: 1rem;
                background: linear-gradient(135deg, var(--accent), var(--accent-dark));
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                margin-top: 1rem;
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
            }}
            
            .btn:active {{
                transform: translateY(0);
            }}
            
            .success {{
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                display: none;
            }}
            
            .success h3 {{
                margin-bottom: 0.5rem;
                font-size: 1.25rem;
            }}
            
            .success p {{
                opacity: 0.95;
                font-size: 0.95rem;
            }}
            
            .price-estimate {{
                background: var(--bg-alt);
                padding: 1.25rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                border-left: 4px solid var(--accent);
                display: none;
            }}
            
            .price-estimate h4 {{
                color: var(--primary);
                margin-bottom: 0.5rem;
            }}
            
            .price-estimate .price {{
                font-size: 2rem;
                font-weight: 700;
                color: var(--accent);
            }}
            
            @media (max-width: 640px) {{
                .container {{
                    padding: 1.5rem;
                }}
                h1 {{
                    font-size: 1.5rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Назад</a>
            
            <div class="category-badge">{categories_ru.get(category, "Услуга")}</div>
            
            <h1>Оформление заказа</h1>
            <p class="subtitle">Заполните форму, и мы найдём лучшего мастера</p>
            
            <div id="successMessage" class="success">
                <h3>✅ Заказ принят!</h3>
                <p id="orderDetails"></p>
            </div>
            
            <div id="priceEstimate" class="price-estimate">
                <h4>Примерная стоимость:</h4>
                <div class="price" id="estimatedPrice">0 ₽</div>
            </div>
            
            <form id="orderForm">
                <input type="hidden" name="category" value="{category}">
                
                <div class="form-group">
                    <label>👤 Ваше имя <span class="required">*</span></label>
                    <input type="text" name="name" required placeholder="Иван Иванов">
                </div>
                
                <div class="form-group">
                    <label>📱 Телефон <span class="required">*</span></label>
                    <input type="tel" name="phone" required placeholder="+7 (900) 123-45-67">
                </div>
                
                <div class="form-group">
                    <label>📍 Адрес <span class="required">*</span></label>
                    <input type="text" name="address" required placeholder="ул. Пушкина, д. 10, кв. 5">
                </div>
                
                <div class="form-group">
                    <label>📝 Описание проблемы <span class="required">*</span></label>
                    <textarea name="problem_description" required placeholder="Опишите что нужно сделать..."></textarea>
                </div>
                
                <div class="form-group">
                    <label>🗓️ Желаемая дата и время</label>
                    <input type="datetime-local" name="preferred_time">
                </div>
                
                <button type="submit" class="btn">✨ Оформить заказ</button>
            </form>
        </div>
        
        <script>
            const form = document.getElementById('orderForm');
            const success = document.getElementById('successMessage');
            const priceEstimate = document.getElementById('priceEstimate');
            const orderDetails = document.getElementById('orderDetails');
            const estimatedPrice = document.getElementById('estimatedPrice');
            
            form.addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const formData = new FormData(form);
                const data = {{
                    name: formData.get('name'),
                    phone: formData.get('phone'),
                    category: formData.get('category'),
                    problem_description: formData.get('problem_description'),
                    address: formData.get('address'),
                    preferred_time: formData.get('preferred_time') || null
                }};
                
                try {{
                    const response = await fetch('/api/v1/ai/web-form', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        // Показываем успех
                        success.style.display = 'block';
                        priceEstimate.style.display = 'block';
                        
                        orderDetails.textContent = `Заказ #${{result.job_id}} принят в обработку. Мастер свяжется с вами в ближайшее время.`;
                        estimatedPrice.textContent = `${{result.estimated_price}} ₽`;
                        
                        form.reset();
                        
                        // Прокручиваем к сообщению
                        success.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        
                        // Через 5 секунд редирект на главную
                        setTimeout(() => {{
                            window.location.href = '/';
                        }}, 5000);
                    }}
                }} catch (error) {{
                    alert('❌ Ошибка отправки. Проверьте интернет-соединение.');
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.get("/admin")
async def admin_panel():
    """Админ-панель - управление заказами и мастерами"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Админ-панель | Управление платформой</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            :root {
                --primary: #1a1a1a;
                --accent: #10b981;
                --accent-dark: #059669;
                --bg: #f9fafb;
                --text: #1a1a1a;
                --text-muted: #6b7280;
                --border: #e5e7eb;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg);
                color: var(--text);
                line-height: 1.6;
            }
            
            header {
                background: white;
                border-bottom: 1px solid var(--border);
                padding: 1.5rem;
            }
            
            .header-content {
                max-width: 1400px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--primary);
            }
            
            .nav-links {
                display: flex;
                gap: 1.5rem;
            }
            
            .nav-links a {
                color: var(--text-muted);
                text-decoration: none;
                transition: color 0.2s;
            }
            
            .nav-links a:hover {
                color: var(--accent);
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem 1.5rem;
            }
            
            h1 {
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            
            .subtitle {
                color: var(--text-muted);
                margin-bottom: 2rem;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            
            .stat-card {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid var(--border);
            }
            
            .stat-card h3 {
                color: var(--text-muted);
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.75rem;
            }
            
            .stat-value {
                font-size: 2.5rem;
                font-weight: 700;
                color: var(--accent);
            }
            
            .card {
                background: white;
                border-radius: 12px;
                padding: 2rem;
                border: 1px solid var(--border);
                margin-bottom: 1.5rem;
            }
            
            .card h2 {
                font-size: 1.5rem;
                margin-bottom: 1.5rem;
            }
            
            .api-links {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem;
            }
            
            .api-link {
                display: block;
                padding: 1rem 1.5rem;
                background: var(--bg);
                border-radius: 8px;
                text-decoration: none;
                color: var(--text);
                transition: all 0.2s;
                border: 1px solid var(--border);
            }
            
            .api-link:hover {
                border-color: var(--accent);
                background: white;
            }
            
            .api-link strong {
                color: var(--accent);
                display: block;
                margin-bottom: 0.25rem;
            }
            
            .api-link span {
                font-size: 0.875rem;
                color: var(--text-muted);
            }
        </style>
    </head>
    <body>
        <header>
            <div class="header-content">
                <div class="logo">⚙️ Админ-панель</div>
                <nav class="nav-links">
                    <a href="/">Главная</a>
                    <a href="/docs">API Docs</a>
                    <a href="/master">Мастера</a>
                </nav>
            </div>
        </header>
        
        <div class="container">
            <h1>Панель управления</h1>
            <p class="subtitle">Статистика, заказы и мастера</p>
            
            <!-- Статистика -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📊 Всего заказов</h3>
                    <div class="stat-value" id="totalJobs">0</div>
                </div>
                <div class="stat-card">
                    <h3>✅ Выполнено</h3>
                    <div class="stat-value" id="completedJobs">0</div>
                </div>
                <div class="stat-card">
                    <h3>👨‍🔧 Активных мастеров</h3>
                    <div class="stat-value" id="activeMasters">0</div>
                </div>
                <div class="stat-card">
                    <h3>💰 Доход</h3>
                    <div class="stat-value" id="revenue">0 ₽</div>
                </div>
            </div>
            
            <!-- API Эндпоинты -->
            <div class="card">
                <h2>🔌 API Эндпоинты</h2>
                <div class="api-links">
                    <a href="/docs" class="api-link">
                        <strong>📚 Swagger UI</strong>
                        <span>Интерактивная документация API</span>
                    </a>
                    <a href="/api/v1/jobs" class="api-link">
                        <strong>📝 GET /api/v1/jobs</strong>
                        <span>Список всех заказов</span>
                    </a>
                    <a href="/api/v1/masters" class="api-link">
                        <strong>👨‍🔧 GET /api/v1/masters</strong>
                        <span>Список всех мастеров</span>
                    </a>
                    <a href="/api/v1/stats" class="api-link">
                        <strong>📊 GET /api/v1/stats</strong>
                        <span>Общая статистика платформы</span>
                    </a>
                </div>
            </div>
        </div>
        
        <script>
            // Загрузка статистики
            async function loadStats() {
                try {
                    const response = await fetch('/api/v1/stats');
                    const stats = await response.json();
                    
                    document.getElementById('totalJobs').textContent = stats.total_jobs || 0;
                    document.getElementById('completedJobs').textContent = stats.completed_jobs || 0;
                    document.getElementById('activeMasters').textContent = stats.active_masters || 0;
                    document.getElementById('revenue').textContent = (stats.total_revenue || 0) + ' ₽';
                } catch (error) {
                    console.error('Ошибка загрузки статистики:', error);
                }
            }
            
            // Загрузка данных при загрузке страницы
            loadStats();
            
            // Обновление каждые 30 секунд
            setInterval(loadStats, 30000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/calculator.html")
@app.get("/calculator")
async def calculator():
    """Калькулятор стоимости электромонтажных работ"""
    from fastapi.responses import FileResponse
    return FileResponse("static/calculator.html")

@app.get("/services")
@app.get("/services.html")
async def services():
    """Каталог услуг электрика - SEO-оптимизированная страница"""
    from fastapi.responses import FileResponse
    return FileResponse("static/services.html")

@app.get("/robots.txt")
async def robots():
    """Файл robots.txt для поисковых роботов"""
    from fastapi.responses import FileResponse
    return FileResponse("static/robots.txt", media_type="text/plain")

@app.get("/sitemap.xml")
async def sitemap():
    """XML-карта сайта для SEO"""
    from fastapi.responses import FileResponse
    return FileResponse("static/sitemap.xml", media_type="application/xml")

@app.get("/master")
async def master_dashboard():
    """Личный кабинет мастера"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Личный кабинет мастера</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            :root {
                --primary: #1a1a1a;
                --accent: #10b981;
                --accent-dark: #059669;
                --bg: #f9fafb;
                --text: #1a1a1a;
                --text-muted: #6b7280;
                --border: #e5e7eb;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg);
                color: var(--text);
                line-height: 1.6;
            }
            
            header {
                background: white;
                border-bottom: 1px solid var(--border);
                padding: 1.5rem;
            }
            
            .header-content {
                max-width: 1400px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--primary);
            }
            
            .nav-links {
                display: flex;
                gap: 1.5rem;
            }
            
            .nav-links a {
                color: var(--text-muted);
                text-decoration: none;
                transition: color 0.2s;
            }
            
            .nav-links a:hover {
                color: var(--accent);
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem 1.5rem;
            }
            
            h1 {
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            
            .subtitle {
                color: var(--text-muted);
                margin-bottom: 2rem;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            
            .stat-card {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                border: 1px solid var(--border);
            }
            
            .stat-card h3 {
                color: var(--text-muted);
                font-size: 0.875rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.75rem;
            }
            
            .stat-value {
                font-size: 2rem;
                font-weight: 700;
                color: var(--accent);
            }
            
            .card {
                background: white;
                border-radius: 12px;
                padding: 2rem;
                border: 1px solid var(--border);
                margin-bottom: 1.5rem;
            }
            
            .card h2 {
                font-size: 1.5rem;
                margin-bottom: 1.5rem;
            }
            
            .job-item {
                padding: 1rem;
                border: 1px solid var(--border);
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            
            .job-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.75rem;
            }
            
            .job-id {
                font-weight: 700;
                color: var(--accent);
            }
            
            .status {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 100px;
                font-size: 0.875rem;
                font-weight: 600;
            }
            
            .status-pending {
                background: #fef3c7;
                color: #92400e;
            }
            
            .status-active {
                background: #d1fae5;
                color: #065f46;
            }
            
            .btn {
                padding: 0.5rem 1rem;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s;
                text-decoration: none;
                display: inline-block;
            }
            
            .btn-primary {
                background: var(--accent);
                color: white;
            }
            
            .btn-primary:hover {
                background: var(--accent-dark);
            }
            
            .info-box {
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
                padding: 1.5rem;
                border-radius: 12px;
                border-left: 4px solid var(--accent);
            }
            
            .info-box h3 {
                margin-bottom: 0.75rem;
                color: var(--primary);
            }
            
            .info-box ul {
                list-style: none;
                padding: 0;
            }
            
            .info-box li {
                padding: 0.5rem 0;
                color: var(--text-muted);
            }
        </style>
    </head>
    <body>
        <header>
            <div class="header-content">
                <div class="logo">👨‍🔧 Кабинет Мастера</div>
                <nav class="nav-links">
                    <a href="/">Главная</a>
                    <a href="/docs">API Docs</a>
                    <a href="/admin">Админ</a>
                </nav>
            </div>
        </header>
        
        <div class="container">
            <h1>Личный кабинет</h1>
            <p class="subtitle">Ваши заказы и статистика</p>
            
            <!-- Статистика -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📊 Всего заказов</h3>
                    <div class="stat-value" id="totalJobs">0</div>
                </div>
                <div class="stat-card">
                    <h3>✅ Выполнено</h3>
                    <div class="stat-value" id="completedJobs">0</div>
                </div>
                <div class="stat-card">
                    <h3>💰 Заработано</h3>
                    <div class="stat-value" id="earnings">0 ₽</div>
                </div>
                <div class="stat-card">
                    <h3>⭐ Рейтинг</h3>
                    <div class="stat-value" id="rating">5.0</div>
                </div>
            </div>
            
            <!-- Текущие заказы -->
            <div class="card">
                <h2>📝 Текущие заказы</h2>
                <div id="jobsList">
                    <p style="color: var(--text-muted); text-align: center; padding: 2rem;">
                        Загрузка заказов...
                    </p>
                </div>
            </div>
            
            <!-- Интеграции -->
            <div class="card">
                <h2>🔌 Интеграции</h2>
                <div class="info-box">
                    <h3>✨ Доступные интеграции</h3>
                    <ul>
                        <li>📅 <strong>Google Calendar</strong> - Синхронизация заказов с календарём</li>
                        <li>☑️ <strong>Google Tasks</strong> - Мобильный виджет для Android</li>
                        <li>📧 <strong>Telegram Mini App</strong> - Доступ через бота</li>
                        <li>📊 <strong>API</strong> - Полный доступ к данным</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <script>
            // Загрузка статистики мастера
            async function loadMasterStats() {
                try {
                    // TODO: Заменить на реальный telegram_id
                    const masterId = '1668456209'; // Пример
                    const response = await fetch(`/api/v1/masters/${masterId}`);
                    
                    if (response.ok) {
                        const master = await response.json();
                        document.getElementById('totalJobs').textContent = master.total_jobs || 0;
                        document.getElementById('completedJobs').textContent = master.completed_jobs || 0;
                        document.getElementById('earnings').textContent = (master.total_earnings || 0) + ' ₽';
                        document.getElementById('rating').textContent = (master.rating || 5.0).toFixed(1);
                    }
                } catch (error) {
                    console.error('Ошибка загрузки статистики:', error);
                }
            }
            
            // Загрузка заказов
            async function loadJobs() {
                try {
                    const response = await fetch('/api/v1/jobs?status=pending,assigned,in_progress');
                    const jobs = await response.json();
                    
                    const jobsList = document.getElementById('jobsList');
                    
                    if (jobs.length === 0) {
                        jobsList.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">Нет текущих заказов</p>';
                        return;
                    }
                    
                    jobsList.innerHTML = jobs.map(job => `
                        <div class="job-item">
                            <div class="job-header">
                                <span class="job-id">#${job.job_id}</span>
                                <span class="status status-${job.status}">${getStatusText(job.status)}</span>
                            </div>
                            <p><strong>${job.category || 'Общие работы'}</strong></p>
                            <p>${job.problem_description || 'Нет описания'}</p>
                            <p style="color: var(--text-muted); font-size: 0.875rem; margin-top: 0.5rem;">
                                📍 ${job.address || 'Адрес не указан'}
                            </p>
                            <p style="margin-top: 0.5rem;"><strong>${job.estimated_price || 0} ₽</strong></p>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Ошибка загрузки заказов:', error);
                }
            }
            
            function getStatusText(status) {
                const statuses = {
                    'pending': 'Ожидает',
                    'assigned': 'Назначен',
                    'in_progress': 'В работе',
                    'completed': 'Выполнен'
                };
                return statuses[status] || status;
            }
            
            // Загрузка данных
            loadMasterStats();
            loadJobs();
            
            // Обновление каждые 30 секунд
            setInterval(() => {
                loadMasterStats();
                loadJobs();
            }, 30000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@app.get("/track")
async def track_master():
    """Отслеживание мастера для клиента"""
    html_path = Path("static/track.html")
    if not html_path.exists():
        raise HTTPException(status_code=500, detail=f"HTML file not found: {html_path.absolute()}")
    return FileResponse(html_path)

@app.get("/api")
async def api_info():
    """Информация об API"""
    return {
        "service": "AI Service Platform",
        "version": "1.0.0",
        "status": "running",
        "environment": ENVIRONMENT,
        "features": {
            "google_calendar": GOOGLE_SYNC_AVAILABLE,
            "google_tasks": GOOGLE_SYNC_AVAILABLE,
            "advanced_pricing": PRICE_CALCULATOR_AVAILABLE,
            "telegram_mini_app": True
        },
        "docs": "/docs"
    }

@app.post("/api/v1/price-estimate")
async def estimate_price(data: dict):
    """
    Автоматическая оценка стоимости услуги
    
    Body:
        {
            "category": "electrical",
            "description": "Описание проблемы",
            "urgency": "normal",  // normal, urgent, emergency
            "district": "center",
            "outlets": 0,
            "switches": 0,
            "time_of_day": "day"  // morning, day, evening, night
        }
    """
    if not PRICE_CALCULATOR_AVAILABLE:
        # Базовый расчёт
        price = calculate_pricing(
            data.get('category', 'electrical'),
            data.get('description', '')
        )
        return {
            "estimated_price": price,
            "breakdown": {"base_price": price},
            "calculator": "basic"
        }
    
    try:
        # Продвинутый расчёт
        result = estimate_from_description(
            data.get('description', ''),
            data.get('category', 'electrical')
        )
        
        return {
            "estimated_price": result['total_price'],
            "breakdown": result['breakdown'],
            "discount": result['discount'],
            "multipliers": result['multipliers'],
            "calculator": "advanced"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка расчёта: {str(e)}")

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    import os
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "cwd": os.getcwd(),
        "static_exists": os.path.exists("static"),
        "master_html_exists": os.path.exists("static/master-dashboard.html")
    }

# ==================== МАСТЕРА ====================

@app.post("/api/v1/masters/register")
async def register_master(master: MasterRegister):
    """Регистрация нового мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO masters (full_name, phone, specializations, city, preferred_channel)
            VALUES (?, ?, ?, ?, ?)
        """, (
            master.full_name,
            master.phone,
            json.dumps(master.specializations),
            master.city,
            master.preferred_channel
        ))
        
        conn.commit()
        master_id = cursor.lastrowid
        
        return {
            "success": True,
            "master_id": master_id,
            "message": f"Мастер {master.full_name} успешно зарегистрирован",
            "terminal_url": f"/terminal/{master_id}"
        }
    
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")
    finally:
        conn.close()

@app.post("/api/v1/masters/{master_id}/activate-terminal")
async def activate_terminal(master_id: int):
    """Активация терминала мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE masters SET terminal_active = 1 WHERE id = ?", (master_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Мастер не найден")
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "Терминал активирован",
        "terminal_url": f"/terminal/{master_id}"
    }

@app.get("/api/v1/masters/available/{category}")
async def get_available_masters(category: str, city: Optional[str] = None):
    """Получить список доступных мастеров"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT id, full_name, specializations, city, rating
        FROM masters
        WHERE is_active = 1 AND terminal_active = 1
        AND specializations LIKE ?
    """
    params = [f'%{category}%']
    
    if city:
        query += " AND city = ?"
        params.append(city)
    
    query += " ORDER BY rating DESC"
    
    cursor.execute(query, params)
    masters = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"count": len(masters), "masters": masters}

@app.get("/api/v1/masters/{telegram_id}")
async def get_master_by_telegram(telegram_id: int):
    """Получить информацию о мастере по Telegram ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, full_name, phone, telegram_id, specializations, city, rating, is_active, terminal_active
        FROM masters
        WHERE telegram_id = ?
    """, (telegram_id,))
    
    master = cursor.fetchone()
    conn.close()
    
    if not master:
        raise HTTPException(status_code=404, detail="Мастер не найден")
    
    master_dict = dict(master)
    master_dict['specializations'] = json.loads(master_dict['specializations'])
    return master_dict

@app.patch("/api/v1/masters/{master_id}/terminal")
async def update_terminal_status(master_id: int, data: dict):
    """Обновить статус терминала мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    terminal_active = data.get('terminal_active', False)
    
    cursor.execute("""
        UPDATE masters SET terminal_active = ? WHERE id = ?
    """, (1 if terminal_active else 0, master_id))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "terminal_active": terminal_active}

@app.patch("/api/v1/masters/{master_id}")
async def update_master(master_id: int, data: dict):
    """Обновить данные мастера (включая telegram_id)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Поддерживаемые поля для обновления
    allowed_fields = ['telegram_id', 'phone', 'full_name', 'city', 'specializations', 'terminal_active', 'is_active']
    updates = []
    params = []
    
    for field in allowed_fields:
        if field in data:
            updates.append(f"{field} = ?")
            if field == 'specializations' and isinstance(data[field], list):
                params.append(json.dumps(data[field]))
            else:
                params.append(data[field])
    
    if not updates:
        raise HTTPException(status_code=400, detail="Нет полей для обновления")
    
    params.append(master_id)
    query = f"UPDATE masters SET {', '.join(updates)} WHERE id = ?"
    
    cursor.execute(query, params)
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Мастер не найден")
    
    conn.close()
    return {"success": True, "message": "Данные обновлены"}

@app.get("/api/v1/masters/{master_id}/statistics")
async def get_master_statistics(master_id: int):
    """Получить статистику мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Общая статистика
    cursor.execute("""
        SELECT 
            COUNT(*) as completed_jobs,
            COALESCE(SUM(t.master_earnings), 0) as total_earnings
        FROM jobs j
        LEFT JOIN transactions t ON j.id = t.job_id
        WHERE j.master_id = ? AND j.status = 'completed'
    """, (master_id,))
    
    stats = dict(cursor.fetchone())
    
    # За сегодня
    cursor.execute("""
        SELECT 
            COUNT(*) as today_jobs,
            COALESCE(SUM(t.master_earnings), 0) as today_earnings
        FROM jobs j
        LEFT JOIN transactions t ON j.id = t.job_id
        WHERE j.master_id = ? 
        AND DATE(j.created_at) = DATE('now')
        AND j.status = 'completed'
    """, (master_id,))
    
    today = dict(cursor.fetchone())
    stats.update(today)
    
    # За месяц
    cursor.execute("""
        SELECT 
            COUNT(*) as month_jobs,
            COALESCE(SUM(t.master_earnings), 0) as month_earnings
        FROM jobs j
        LEFT JOIN transactions t ON j.id = t.job_id
        WHERE j.master_id = ? 
        AND strftime('%Y-%m', j.created_at) = strftime('%Y-%m', 'now')
        AND j.status = 'completed'
    """, (master_id,))
    
    month = dict(cursor.fetchone())
    stats.update(month)
    
    # Средний рейтинг
    cursor.execute("SELECT rating FROM masters WHERE id = ?", (master_id,))
    master = cursor.fetchone()
    stats['average_rating'] = master['rating'] if master else 5.0
    
    conn.close()
    
    return stats

@app.get("/api/v1/jobs")
async def get_jobs(status: Optional[str] = None, city: Optional[str] = None):
    """Получить список заказов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    jobs = [dict(row) for row in cursor.fetchall()]
    
    # Добавляем читабельное название категории
    category_names = {
        "electrical": "⚡ Электрика",
        "plumbing": "🚰 Сантехника",
        "appliance": "🔌 Бытовая техника",
        "general": "🔨 Общие работы"
    }
    
    for job in jobs:
        job['category_name'] = category_names.get(job.get('category'), job.get('category'))
    
    conn.close()
    
    return jobs

@app.get("/api/v1/masters/{master_id}/jobs")
async def get_master_jobs_all(master_id: int):
    """Получить все заказы мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM jobs 
        WHERE master_id = ? 
        ORDER BY created_at DESC
    """, (master_id,))
    
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jobs

@app.post("/api/v1/jobs/{job_id}/assign")
async def assign_job_to_master(job_id: int, data: dict):
    """Назначить заказ мастеру"""
    master_id = data.get('master_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE jobs 
        SET master_id = ?, status = 'accepted'
        WHERE id = ? AND status = 'pending'
    """, (master_id, job_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Заказ уже назначен или не найден")
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Заказ принят"}

@app.patch("/api/v1/jobs/{job_id}/status")
async def update_job_status(job_id: int, data: dict):
    """Обновить статус заказа"""
    new_status = data.get('status')
    
    if new_status not in ['pending', 'accepted', 'in_progress', 'completed', 'cancelled']:
        raise HTTPException(status_code=400, detail="Неверный статус")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE jobs SET status = ? WHERE id = ?
    """, (new_status, job_id))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "status": new_status}

# ==================== КЛИЕНТЫ (AI) ====================

@app.post("/api/v1/ai/web-form")
async def process_client_request(request: ClientRequest):
    """Обработка заявки от клиента через веб-форму"""
    
    # Расчёт цены
    estimated_price = calculate_pricing(request.category, request.problem_description)
    
    # Поиск мастера
    master_id = find_available_master(request.category, "Москва")  # Пока по умолчанию Москва
    
    # Создание заказа
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO jobs (client_name, client_phone, category, problem_description, address, estimated_price, master_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.name,
        request.phone,
        request.category,
        request.problem_description,
        request.address,
        estimated_price,
        master_id,
        'accepted' if master_id else 'pending'
    ))
    
    conn.commit()
    job_id = cursor.lastrowid
    conn.close()
    
    # 🔥 СИНХРОНИЗАЦИЯ С GOOGLE CALENDAR И TASKS
    google_sync_result = {'calendar_event_id': None, 'task_id': None}
    if GOOGLE_SYNC_AVAILABLE and master_id:
        try:
            order_data = {
                'id': job_id,
                'client_name': request.name,
                'client_phone': request.phone,
                'category_name': {
                    'electrical': '⚡ Электрика',
                    'plumbing': '🚠 Сантехника',
                    'appliance': '🔌 Бытовая техника',
                    'general': '🔨 Общие работы'
                }.get(request.category, request.category),
                'problem_description': request.problem_description,
                'address': request.address,
                'estimated_price': estimated_price,
                'preferred_date': datetime.now().strftime('%Y-%m-%d'),
                'preferred_time': '09:00'
            }
            google_sync_result = sync_order_to_google(order_data)
            if google_sync_result['calendar_event_id']:
                print(f"✅ Заказ #{job_id} синхронизирован с Google Calendar")
            if google_sync_result['task_id']:
                print(f"✅ Заказ #{job_id} добавлен в Google Tasks")
        except Exception as e:
            print(f"⚠️ Ошибка синхронизации с Google: {e}")
    
    response = {
        "success": True,
        "job_id": job_id,
        "estimated_price": estimated_price,
        "message": "Заявка принята и обрабатывается AI"
    }
    
    if master_id:
        response["master_assigned"] = True
        response["master_id"] = master_id
        response["message"] = f"Заявка принята! Мастер #{master_id} назначен."
    else:
        response["master_assigned"] = False
        response["message"] = "Заявка принята. Ищем подходящего мастера..."
    
    return response

# ==================== ТЕРМИНАЛ МАСТЕРА ====================

@app.get("/api/v1/terminal/jobs/{master_id}")
async def get_master_jobs(master_id: int, status: Optional[str] = None):
    """Получить заказы мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM jobs WHERE master_id = ?"
    params = [master_id]
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"count": len(jobs), "jobs": jobs}

@app.get("/api/v1/terminal/jobs/{master_id}/active")
async def get_active_job(master_id: int):
    """Получить активный заказ мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM jobs 
        WHERE master_id = ? AND status IN ('accepted', 'in_progress')
        ORDER BY created_at DESC LIMIT 1
    """, (master_id,))
    
    job = cursor.fetchone()
    conn.close()
    
    if not job:
        return {"active_job": None}
    
    return {"active_job": dict(job)}

@app.patch("/api/v1/terminal/jobs/{master_id}/status/{job_id}")
async def update_job_status(master_id: int, job_id: int, update: JobStatusUpdate):
    """Обновить статус заказа"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE jobs SET status = ?
        WHERE id = ? AND master_id = ?
    """, (update.status, job_id, master_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    conn.commit()
    conn.close()
    
    return {"success": True, "status": update.status}

@app.post("/api/v1/terminal/payment/process")
async def process_payment(payment: PaymentProcess):
    """Обработка платежа"""
    
    # Расчёт комиссий
    fees = calculate_platform_fee(payment.amount)
    
    # Сохранение транзакции
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions (job_id, amount, payment_method, platform_fee, master_earnings)
        VALUES (?, ?, ?, ?, ?)
    """, (
        payment.job_id,
        payment.amount,
        payment.payment_method,
        fees['platform_commission'],
        fees['master_earnings']
    ))
    
    # Обновление статуса заказа
    cursor.execute("UPDATE jobs SET status = 'completed' WHERE id = ?", (payment.job_id,))
    
    conn.commit()
    transaction_id = cursor.lastrowid
    conn.close()
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "breakdown": fees,
        "message": f"Оплата {payment.amount}₽ принята. Мастер получит {fees['master_earnings']}₽"
    }

@app.get("/api/v1/terminal/earnings/{master_id}")
async def get_master_earnings(master_id: int):
    """Получить заработок мастера"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_jobs,
            COALESCE(SUM(t.master_earnings), 0) as total_earnings,
            COALESCE(SUM(t.amount), 0) as total_revenue
        FROM jobs j
        LEFT JOIN transactions t ON j.id = t.job_id
        WHERE j.master_id = ? AND j.status = 'completed'
    """, (master_id,))
    
    result = dict(cursor.fetchone())
    conn.close()
    
    return {
        "master_id": master_id,
        "total_jobs": result['total_jobs'],
        "total_earnings": round(result['total_earnings'], 2),
        "total_revenue": round(result['total_revenue'], 2)
    }

# ==================== СТАТИСТИКА ====================

@app.post("/api/v1/master/depart/{job_id}")
async def master_depart(job_id: int, data: dict):
    """
    🚗 Мастер выехал к клиенту
    Сохранить время выезда и маршрут для клиента
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    location = data.get('location', {})
    route_url = data.get('route_screenshot_url', '')
    
    cursor.execute("""
        UPDATE jobs 
        SET master_departed_at = CURRENT_TIMESTAMP,
            master_location_lat = ?,
            master_location_lon = ?,
            route_screenshot_url = ?,
            status = 'on-the-way'
        WHERE id = ?
    """, (
        location.get('lat'),
        location.get('lon'),
        route_url,
        job_id
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": "Выезд зафиксирован. Клиент получил уведомление с маршрутом.",
        "route_url": route_url
    }

@app.post("/api/v1/master/arrive/{job_id}")
async def master_arrive(job_id: int):
    """
    ✅ Мастер нажал "Я НА МЕСТЕ"
    Открыть контакт клиента + обновить Google Calendar
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получить данные заказа
    cursor.execute("""
        SELECT id, client_name, client_phone, google_calendar_event_id
        FROM jobs
        WHERE id = ?
    """, (job_id,))
    
    job = cursor.fetchone()
    if not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    job_dict = dict(job)
    
    # Обновить статус в БД
    cursor.execute("""
        UPDATE jobs 
        SET master_arrived_at = CURRENT_TIMESTAMP,
            client_phone_revealed = 1,
            status = 'arrived'
        WHERE id = ?
    """, (job_id,))
    
    conn.commit()
    conn.close()
    
    # 🔥 ОТКРЫТЬ КОНТАКТ В GOOGLE CALENDAR
    if GOOGLE_SYNC_AVAILABLE and job_dict.get('google_calendar_event_id'):
        try:
            from google_sync import google_integration
            if google_integration:
                google_integration.reveal_client_contact(
                    job_dict['google_calendar_event_id'],
                    job_dict['client_name'],
                    job_dict['client_phone']
                )
        except Exception as e:
            print(f"⚠️ Ошибка обновления Google Calendar: {e}")
    
    return {
        "success": True,
        "message": "Контакт клиента открыт!",
        "client_phone": job_dict['client_phone'],
        "client_name": job_dict['client_name']
    }

@app.get("/api/v1/client/track/{job_id}")
async def track_master(job_id: int):
    """
    📍 Клиент отслеживает мастера
    Показать маршрут и статус
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            status,
            master_departed_at,
            master_arrived_at,
            master_location_lat,
            master_location_lon,
            route_screenshot_url,
            estimated_price
        FROM jobs
        WHERE id = ?
    """, (job_id,))
    
    job = cursor.fetchone()
    conn.close()
    
    if not job:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    job_dict = dict(job)
    
    return {
        "status": job_dict['status'],
        "departed": bool(job_dict['master_departed_at']),
        "arrived": bool(job_dict['master_arrived_at']),
        "location": {
            "lat": job_dict['master_location_lat'],
            "lon": job_dict['master_location_lon']
        } if job_dict['master_location_lat'] else None,
        "route_url": job_dict['route_screenshot_url'],
        "estimated_price": job_dict['estimated_price']
    }

# ==================== СТАТИСТИКА ====================

@app.get("/api/v1/stats")
async def get_statistics():
    """Общая статистика платформы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Количество мастеров
    cursor.execute("SELECT COUNT(*) as count FROM masters WHERE is_active = 1")
    masters_count = cursor.fetchone()['count']
    
    # Количество заказов
    cursor.execute("SELECT COUNT(*) as count FROM jobs")
    jobs_count = cursor.fetchone()['count']
    
    # Заказы по статусам
    cursor.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
    jobs_by_status = {row['status']: row['count'] for row in cursor.fetchall()}
    
    # Общий доход
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM transactions")
    total_revenue = cursor.fetchone()['total']
    
    conn.close()
    
    return {
        "masters": {"active": masters_count},
        "jobs": {
            "total": jobs_count,
            "by_status": jobs_by_status
        },
        "revenue": {
            "total": round(total_revenue, 2)
        }
    }

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
