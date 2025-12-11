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
            specializations TEXT NOT NULL,
            city TEXT NOT NULL,
            preferred_channel TEXT DEFAULT 'telegram',
            rating REAL DEFAULT 5.0,
            is_active BOOLEAN DEFAULT 1,
            terminal_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    """)
    
    conn.commit()
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

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация БД при старте
@app.on_event("startup")
async def startup_event():
    init_database()
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
    """Простой расчёт цены на основе категории"""
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
    """Главная страница - форма для клиентов"""
    return FileResponse("static/index.html")

@app.get("/api")
async def api_info():
    """Информация об API"""
    return {
        "service": "AI Service Platform",
        "version": "1.0.0",
        "status": "running",
        "environment": ENVIRONMENT,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
