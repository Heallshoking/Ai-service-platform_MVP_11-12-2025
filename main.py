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

@app.get("/api/jobs/all")
async def get_all_jobs():
    """Получить все заказы для Kanban-доски"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT j.*, m.full_name as master_name
        FROM jobs j
        LEFT JOIN masters m ON j.master_id = m.id
        ORDER BY j.created_at DESC
    """)
    
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"jobs": jobs, "count": len(jobs)}

# ==================== HTML ИНТЕРФЕЙСЫ ====================

@app.get("/admin/kanban")
async def admin_kanban():
    """📋 Kanban-доска управления заказами (как на фото)"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Управление заказами | AI Platform</title>
        <style>
            :root {
                --primary: #6366f1; --success: #10b981; --warning: #f59e0b; --danger: #ef4444;
                --bg: #f8fafc; --surface: #fff; --text: #0f172a; --text-muted: #64748b;
                --border: #e2e8f0;
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg); color: var(--text); min-height: 100vh;
            }
            .sidebar {
                position: fixed; left: 0; top: 0; bottom: 0; width: 220px;
                background: #2d3748; color: white; padding: 1.5rem 0;
            }
            .logo { padding: 0 1.5rem; margin-bottom: 2rem; font-size: 1.25rem; font-weight: 700; }
            .nav-item {
                padding: 0.875rem 1.5rem; display: flex; align-items: center; gap: 0.75rem;
                cursor: pointer; transition: all 0.2s; color: rgba(255,255,255,0.7);
            }
            .nav-item:hover, .nav-item.active {
                background: rgba(99,102,241,0.2); color: white;
            }
            .main { margin-left: 220px; padding: 1.5rem; }
            .header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border);
            }
            .header h1 { font-size: 1.5rem; font-weight: 600; }
            .stats-row {
                display: flex; gap: 1rem; margin-bottom: 1.5rem;
            }
            .stat-pill {
                padding: 0.5rem 1.25rem; border-radius: 20px; font-size: 0.875rem;
                font-weight: 600; display: flex; align-items: center; gap: 0.5rem;
            }
            .stat-pill.all { background: #e0e7ff; color: var(--primary); }
            .stat-pill.pending { background: #fef3c7; color: var(--warning); }
            .stat-pill.progress { background: #dbeafe; color: #3b82f6; }
            .stat-pill.payment { background: #fee2e2; color: var(--danger); }
            .stat-pill.done { background: #d1fae5; color: var(--success); }
            .kanban {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1rem; min-height: 70vh;
            }
            .column {
                background: var(--surface); border-radius: 12px; padding: 1rem;
                border: 1px solid var(--border);
            }
            .column-header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border);
            }
            .column-title { font-weight: 600; font-size: 0.875rem; text-transform: uppercase; }
            .column-count {
                background: var(--bg); padding: 0.25rem 0.625rem; border-radius: 12px;
                font-size: 0.75rem; font-weight: 600;
            }
            .card {
                background: white; border: 1px solid var(--border); border-radius: 8px;
                padding: 1rem; margin-bottom: 0.75rem; cursor: pointer;
                transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); transform: translateY(-2px); }
            .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
            .card-client { font-weight: 600; font-size: 0.9rem; }
            .card-tag { font-size: 0.75rem; color: var(--text-muted); }
            .card-info { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }
            .info-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: var(--text-muted); }
            .card-price { font-size: 1.25rem; font-weight: 700; color: var(--success); margin-bottom: 0.75rem; }
            .card-footer { display: flex; gap: 0.5rem; }
            .btn-sm {
                padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.75rem; font-weight: 600;
                border: none; cursor: pointer; transition: all 0.2s;
            }
            .btn-primary { background: var(--primary); color: white; }
            .btn-secondary { background: var(--bg); color: var(--text); border: 1px solid var(--border); }
            .btn-sm:hover { opacity: 0.9; }
            .badge { padding: 0.25rem 0.625rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
            .badge-new { background: #fef3c7; color: var(--warning); }
            .badge-assigned { background: #dbeafe; color: #3b82f6; }
            .badge-work { background: #ddd6fe; color: #7c3aed; }
            .empty-state {
                text-align: center; padding: 2rem; color: var(--text-muted);
                font-size: 0.875rem;
            }
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="logo">⚡ AI Platform</div>
            <div class="nav-item"><span>📊</span>Дашборд</div>
            <div class="nav-item active"><span>📋</span>Заказы</div>
            <div class="nav-item"><span>👥</span>Мастера</span>
            <div class="nav-item"><span>💳</span>Платежи</div>
            <div class="nav-item"><span>📈</span>Аналитика</div>
        </div>
        
        <div class="main">
            <div class="header">
                <h1>Управление заказами</h1>
                <button class="btn-sm btn-primary">+ Новый заказ</button>
            </div>
            
            <div class="stats-row">
                <div class="stat-pill all"><span>📊</span><span id="totalOrders">0</span> Всего</div>
                <div class="stat-pill pending"><span>🆕</span><span id="newOrders">0</span> Новые</div>
                <div class="stat-pill progress"><span>🔄</span><span id="inProgress">0</span> В работе</div>
                <div class="stat-pill payment"><span>💳</span><span id="awaitingPayment">0</span> Оплата</div>
                <div class="stat-pill done"><span>✅</span><span id="completed">0</span> Завершено</div>
            </div>
            
            <div class="kanban">
                <!-- Новые -->
                <div class="column">
                    <div class="column-header">
                        <div class="column-title">🆕 Новые</div>
                        <div class="column-count" id="count-new">0</div>
                    </div>
                    <div id="column-new"></div>
                </div>
                
                <!-- Назначен мастер -->
                <div class="column">
                    <div class="column-header">
                        <div class="column-title">👨‍🔧 Назначен мастер</div>
                        <div class="column-count" id="count-assigned">0</div>
                    </div>
                    <div id="column-assigned"></div>
                </div>
                
                <!-- В работе -->
                <div class="column">
                    <div class="column-header">
                        <div class="column-title">🔧 В работе</div>
                        <div class="column-count" id="count-progress">0</div>
                    </div>
                    <div id="column-progress"></div>
                </div>
                
                <!-- Ожидает оплату -->
                <div class="column">
                    <div class="column-header">
                        <div class="column-title">💳 Ожидает оплату</div>
                        <div class="column-count" id="count-payment">0</div>
                    </div>
                    <div id="column-payment"></div>
                </div>
                
                <!-- Завершено -->
                <div class="column">
                    <div class="column-header">
                        <div class="column-title">✅ Завершено</div>
                        <div class="column-count" id="count-done">0</div>
                    </div>
                    <div id="column-done"></div>
                </div>
            </div>
        </div>
        
        <script>
            const statusMap = {
                'pending': 'new',
                'accepted': 'assigned',
                'in_progress': 'progress',
                'awaiting_payment': 'payment',
                'completed': 'done'
            };
            
            function createCard(job) {
                const masterPart = job.master_id 
                    ? `<div class="info-row">👨‍🔧 Мастер #${job.master_id}</div>` 
                    : '<div class="info-row">⏳ Ищем мастера...</div>';
                    
                return `
                    <div class="card" data-job-id="${job.id}">
                        <div class="card-header">
                            <div class="card-client">${job.client_name}</div>
                            <div class="card-tag">#${job.id}</div>
                        </div>
                        <div class="card-info">
                            <div class="info-row">📍 ${job.address}</div>
                            <div class="info-row">⚡ ${job.category}</div>
                            ${masterPart}
                        </div>
                        <div class="card-price">${Math.round(job.estimated_price || 0)} ₽</div>
                        <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:0.75rem;">
                            ${job.problem_description.substring(0, 60)}...
                        </div>
                        <div class="card-footer">
                            <button class="btn-sm btn-primary" onclick="viewJob(${job.id})">Просмотр</button>
                            <button class="btn-sm btn-secondary">Изменить</button>
                        </div>
                    </div>
                `;
            }
            
            async function loadOrders() {
                try {
                    const res = await fetch('/api/jobs/all');
                    const data = await res.json();
                    const jobs = data.jobs || [];
                    
                    // Очистка колонок
                    ['new', 'assigned', 'progress', 'payment', 'done'].forEach(col => {
                        document.getElementById(`column-${col}`).innerHTML = '';
                    });
                    
                    // Счётчики
                    const counts = { new: 0, assigned: 0, progress: 0, payment: 0, done: 0 };
                    
                    jobs.forEach(job => {
                        const column = statusMap[job.status] || 'new';
                        counts[column]++;
                        document.getElementById(`column-${column}`).innerHTML += createCard(job);
                    });
                    
                    // Обновление счётчиков
                    Object.keys(counts).forEach(key => {
                        document.getElementById(`count-${key}`).textContent = counts[key];
                    });
                    
                    document.getElementById('totalOrders').textContent = jobs.length;
                    document.getElementById('newOrders').textContent = counts.new;
                    document.getElementById('inProgress').textContent = counts.progress;
                    document.getElementById('awaitingPayment').textContent = counts.payment;
                    document.getElementById('completed').textContent = counts.done;
                    
                    // Empty states
                    ['new', 'assigned', 'progress', 'payment', 'done'].forEach(col => {
                        const container = document.getElementById(`column-${col}`);
                        if (!container.innerHTML) {
                            container.innerHTML = '<div class="empty-state">Пусто</div>';
                        }
                    });
                } catch (error) {
                    console.error('Ошибка загрузки:', error);
                }
            }
            
            function viewJob(id) {
                alert(`Просмотр заказа #${id}`);
            }
            
            loadOrders();
            setInterval(loadOrders, 15000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ==================== HTML ИНТЕРФЕЙСЫ ====================

@app.get("/admin")
async def admin_panel():
    """📅 Админ-панель с календарем и карточками мастеров (как на скриншоте)"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Панель управления | AI Service Platform</title>
        <style>
            :root {
                --primary: #10b981; --gray-50: #f9fafb; --gray-100: #f3f4f6;
                --gray-200: #e5e7eb; --gray-300: #d1d5db; --gray-500: #6b7280;
                --gray-700: #374151; --gray-800: #1f2937;
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--gray-50); color: var(--gray-800); font-size: 14px;
            }
            .layout { display: grid; grid-template-columns: 1fr 600px; gap: 1rem; padding: 1rem; height: 100vh; }
            .left-panel { display: flex; gap: 0.75rem; overflow-x: auto; }
            .column {
                min-width: 280px; background: white; border-radius: 12px;
                padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem;
            }
            .column-header {
                display: flex; justify-content: space-between; align-items: center;
                padding: 0.75rem; border-radius: 8px; font-weight: 600; font-size: 13px;
            }
            .col-gray { background: var(--gray-200); color: var(--gray-700); }
            .col-blue { background: #e0f2fe; color: #0369a1; }
            .col-green { background: #d1fae5; color: #065f46; }
            .col-orange { background: #fed7aa; color: #9a3412; }
            .col-success { background: #bbf7d0; color: #14532d; }
            .create-btn {
                background: var(--gray-100); color: var(--gray-500); padding: 0.625rem;
                border: 1px dashed var(--gray-300); border-radius: 6px; text-align: center;
                cursor: pointer; font-size: 12px; transition: all 0.2s;
            }
            .create-btn:hover { background: var(--gray-200); }
            .master-card {
                background: white; border: 1px solid var(--gray-200); border-radius: 8px;
                padding: 0.75rem; cursor: pointer; transition: all 0.2s;
            }
            .master-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); transform: translateY(-2px); }
            .master-name { font-weight: 600; font-size: 13px; color: #0891b2; margin-bottom: 0.25rem; }
            .master-spec { font-size: 12px; color: var(--gray-500); }
            .calendar-panel {
                background: var(--primary); border-radius: 12px; padding: 1.5rem;
                color: white; overflow-y: auto;
            }
            .calendar-header {
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 1.5rem;
            }
            .calendar-title { font-size: 16px; font-weight: 600; }
            .nav-btn {
                background: rgba(255,255,255,0.2); border: none; color: white;
                width: 32px; height: 32px; border-radius: 6px; cursor: pointer;
                display: flex; align-items: center; justify-content: center;
            }
            .nav-btn:hover { background: rgba(255,255,255,0.3); }
            .calendar-grid {
                display: grid; grid-template-columns: repeat(7, 1fr);
                gap: 4px; margin-top: 1rem;
            }
            .day-header {
                text-align: center; font-size: 12px; font-weight: 600;
                padding: 0.5rem; opacity: 0.8;
            }
            .day-cell {
                aspect-ratio: 1; background: rgba(255,255,255,0.1);
                border-radius: 6px; display: flex; align-items: center;
                justify-content: center; font-size: 13px; cursor: pointer;
                transition: all 0.2s;
            }
            .day-cell:hover { background: rgba(255,255,255,0.2); }
            .day-cell.today { background: #f59e0b; font-weight: 700; }
            .day-cell.empty { opacity: 0.3; }
        </style>
    </head>
    <body>
        <div class="layout">
            <div class="left-panel">
                <!-- Не запланировано -->
                <div class="column">
                    <div class="column-header col-gray">
                        <span>Не запланировано</span>
                        <span id="count-unplanned">0</span>
                    </div>
                    <div class="create-btn">Создать</div>
                    <div id="col-unplanned"></div>
                </div>
                
                <!-- Ожидает выезда -->
                <div class="column">
                    <div class="column-header col-blue">
                        <span>Ожидает выезда</span>
                        <span id="count-pending">0</span>
                    </div>
                    <div class="create-btn">Создать</div>
                    <div id="col-pending"></div>
                </div>
                
                <!-- В работе -->
                <div class="column">
                    <div class="column-header col-green">
                        <span>В работе</span>
                        <span id="count-progress">0</span>
                    </div>
                    <div class="create-btn">Создать</div>
                    <div id="col-progress"></div>
                </div>
                
                <!-- На проверке у руководителя -->
                <div class="column">
                    <div class="column-header col-orange">
                        <span>На проверке</span>
                        <span id="count-review">0</span>
                    </div>
                    <div class="create-btn">Создать</div>
                    <div id="col-review"></div>
                </div>
                
                <!-- Выполненная -->
                <div class="column">
                    <div class="column-header col-success">
                        <span>Выполненная</span>
                        <span id="count-completed">0</span>
                    </div>
                    <div class="create-btn">Создать</div>
                    <div id="col-completed"></div>
                </div>
            </div>
            
            <!-- Календарь -->
            <div class="calendar-panel">
                <div class="calendar-header">
                    <button class="nav-btn" onclick="changeMonth(-1)">‹</button>
                    <div class="calendar-title" id="monthTitle">Декабрь 2025</div>
                    <button class="nav-btn" onclick="changeMonth(1)">›</button>
                </div>
                
                <div style="font-size:12px;opacity:0.9;margin-bottom:1rem;">Календарь полный</div>
                
                <div class="calendar-grid">
                    <div class="day-header">Пн</div>
                    <div class="day-header">Вт</div>
                    <div class="day-header">Ср</div>
                    <div class="day-header">Чт</div>
                    <div class="day-header">Пт</div>
                    <div class="day-header">Сб</div>
                    <div class="day-header">Вс</div>
                </div>
                
                <div id="calendar"></div>
            </div>
        </div>
        
        <script>
            const statusMap = {
                'pending': 'unplanned',
                'accepted': 'pending',
                'in_progress': 'progress',
                'awaiting_payment': 'review',
                'completed': 'completed'
            };
            
            let currentMonth = new Date();
            
            function renderCalendar() {
                const year = currentMonth.getFullYear();
                const month = currentMonth.getMonth();
                
                document.getElementById('monthTitle').textContent = 
                    new Date(year, month).toLocaleDateString('ru', { month: 'long', year: 'numeric' });
                
                const firstDay = new Date(year, month, 1).getDay();
                const daysInMonth = new Date(year, month + 1, 0).getDate();
                const today = new Date();
                
                let html = '<div class="calendar-grid">';
                
                // Пустые ячейки в начале
                const startDay = firstDay === 0 ? 6 : firstDay - 1;
                for (let i = 0; i < startDay; i++) {
                    html += '<div class="day-cell empty"></div>';
                }
                
                // Дни месяца
                for (let day = 1; day <= daysInMonth; day++) {
                    const isToday = today.getDate() === day && 
                                    today.getMonth() === month && 
                                    today.getFullYear() === year;
                    html += `<div class="day-cell ${isToday ? 'today' : ''}">${day}</div>`;
                }
                
                html += '</div>';
                document.getElementById('calendar').innerHTML = html;
            }
            
            function changeMonth(delta) {
                currentMonth.setMonth(currentMonth.getMonth() + delta);
                renderCalendar();
            }
            
            function createMasterCard(job) {
                const masterName = job.master_name || 'Не назначен';
                const spec = job.category || 'Общие работы';
                return `
                    <div class="master-card" onclick="viewJob(${job.id})">
                        <div class="master-name">${job.client_name}</div>
                        <div class="master-spec">${spec}, ${masterName}</div>
                    </div>
                `;
            }
            
            async function loadJobs() {
                try {
                    const res = await fetch('/api/jobs/all');
                    const data = await res.json();
                    const jobs = data.jobs || [];
                    
                    // Очистка колонок
                    ['unplanned', 'pending', 'progress', 'review', 'completed'].forEach(col => {
                        document.getElementById(`col-${col}`).innerHTML = '';
                    });
                    
                    const counts = { unplanned: 0, pending: 0, progress: 0, review: 0, completed: 0 };
                    
                    jobs.forEach(job => {
                        const col = statusMap[job.status] || 'unplanned';
                        counts[col]++;
                        document.getElementById(`col-${col}`).innerHTML += createMasterCard(job);
                    });
                    
                    Object.keys(counts).forEach(key => {
                        document.getElementById(`count-${key}`).textContent = counts[key];
                    });
                } catch (error) {
                    console.error('Ошибка загрузки:', error);
                }
            }
            
            function viewJob(id) {
                window.location.href = `/admin/kanban`;
            }
            
            renderCalendar();
            loadJobs();
            setInterval(loadJobs, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/master")
async def master_terminal(master_id: int = 1):
    """🎨 Премиум терминал мастера - Mobile-first + Norman UX"""
    from fastapi.responses import HTMLResponse
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
        <title>Терминал мастера</title>
        <style>
            :root {{
                --primary: #10b981; --primary-dark: #059669; --primary-light: #d1fae5;
                --danger: #ef4444; --warning: #f59e0b; --info: #3b82f6;
                --bg: #0f172a; --surface: #1e293b; --surface-hover: #334155;
                --text: #f8fafc; --text-muted: #94a3b8; --border: #334155;
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg); color: var(--text); min-height: 100vh;
                padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
            }}
            .header {{
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                padding: 1.5rem 1rem; position: sticky; top: 0; z-index: 10;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }}
            .header-content {{ max-width: 600px; margin: 0 auto; }}
            .header h1 {{ font-size: 1.5rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem; }}
            .header-stats {{ display: flex; gap: 1rem; margin-top: 1rem; }}
            .stat {{ flex: 1; background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
                     padding: 0.75rem; border-radius: 12px; text-align: center; }}
            .stat-value {{ font-size: 1.5rem; font-weight: 700; }}
            .stat-label {{ font-size: 0.75rem; opacity: 0.9; margin-top: 0.25rem; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 1rem; }}
            .section-title {{ font-size: 1.125rem; font-weight: 600; margin: 1.5rem 0 1rem;
                             display: flex; align-items: center; gap: 0.5rem; }}
            .job-card {{
                background: var(--surface); border-radius: 16px; padding: 1.25rem;
                margin-bottom: 1rem; border: 1px solid var(--border);
                transition: all 0.2s ease; cursor: pointer; position: relative; overflow: hidden;
            }}
            .job-card::before {{
                content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
                background: linear-gradient(180deg, var(--primary), var(--primary-dark));
            }}
            .job-card:active {{ transform: scale(0.98); background: var(--surface-hover); }}
            .job-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }}
            .job-category {{ font-size: 1.125rem; font-weight: 600; color: var(--primary); }}
            .badge {{
                padding: 0.375rem 0.75rem; border-radius: 20px; font-size: 0.75rem;
                font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
            }}
            .badge-pending {{ background: var(--warning); color: #000; }}
            .badge-accepted {{ background: var(--info); color: #fff; }}
            .job-info {{ display: flex; flex-direction: column; gap: 0.625rem; margin-bottom: 1rem; }}
            .info-row {{ display: flex; align-items: flex-start; gap: 0.625rem; color: var(--text-muted); font-size: 0.9rem; }}
            .info-icon {{ flex-shrink: 0; width: 20px; text-align: center; }}
            .job-price {{ font-size: 1.75rem; font-weight: 700; color: var(--primary);
                         margin: 1rem 0; display: flex; align-items: baseline; gap: 0.25rem; }}
            .job-price small {{ font-size: 0.875rem; font-weight: 400; color: var(--text-muted); }}
            .btn-group {{ display: grid; gap: 0.75rem; grid-template-columns: 1fr 1fr; }}
            .btn {{
                border: none; padding: 1rem; border-radius: 12px; font-size: 1rem; font-weight: 600;
                cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center;
                justify-content: center; gap: 0.5rem; touch-action: manipulation;
            }}
            .btn-primary {{ background: linear-gradient(135deg, var(--primary), var(--primary-dark)); color: #fff; grid-column: 1 / -1; }}
            .btn-primary:active {{ transform: scale(0.97); box-shadow: inset 0 4px 8px rgba(0,0,0,0.3); }}
            .btn-secondary {{ background: var(--surface-hover); color: var(--text); border: 1px solid var(--border); }}
            .btn-secondary:active {{ background: var(--border); }}
            .empty-state {{
                text-align: center; padding: 3rem 1rem; color: var(--text-muted);
            }}
            .empty-icon {{ font-size: 4rem; margin-bottom: 1rem; opacity: 0.5; }}
            .loading {{
                display: flex; justify-content: center; align-items: center; padding: 2rem;
                flex-direction: column; gap: 1rem; color: var(--text-muted);
            }}
            .spinner {{
                width: 40px; height: 40px; border: 3px solid var(--border);
                border-top-color: var(--primary); border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }}
            @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
            .toast {{
                position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
                background: var(--surface); color: var(--text); padding: 1rem 1.5rem;
                border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                display: none; align-items: center; gap: 0.75rem; z-index: 100;
                border: 1px solid var(--border); max-width: 90%; animation: slideUp 0.3s ease;
            }}
            @keyframes slideUp {{ from {{ transform: translateX(-50%) translateY(100px); opacity: 0; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1><span>⚡</span>Терминал мастера</h1>
                <div class="header-stats">
                    <div class="stat">
                        <div class="stat-value" id="activeCount">-</div>
                        <div class="stat-label">Активных</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="todayCount">-</div>
                        <div class="stat-label">Сегодня</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" id="earningsToday">-</div>
                        <div class="stat-label">Заработано</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="container">
            <div class="section-title">
                <span>🔔</span>Новые заказы
            </div>
            <div id="jobs-list">
                <div class="loading">
                    <div class="spinner"></div>
                    <div>Загрузка заказов...</div>
                </div>
            </div>
        </div>
        
        <div class="toast" id="toast"></div>
        
        <script>
            const masterId = {master_id};
            let jobs = [];
            
            function showToast(message, icon = '✅') {{
                const toast = document.getElementById('toast');
                toast.innerHTML = `<span style="font-size:1.5rem">${{icon}}</span><span>${{message}}</span>`;
                toast.style.display = 'flex';
                setTimeout(() => toast.style.display = 'none', 3000);
            }}
            
            async function loadJobs() {{
                try {{
                    const response = await fetch(`/api/jobs/master/${{masterId}}?status=pending,accepted`);
                    const data = await response.json();
                    jobs = data.jobs || [];
                    
                    // Update stats
                    document.getElementById('activeCount').textContent = jobs.length;
                    document.getElementById('todayCount').textContent = jobs.filter(j => 
                        new Date(j.created_at).toDateString() === new Date().toDateString()
                    ).length;
                    document.getElementById('earningsToday').textContent = 
                        Math.round(jobs.reduce((sum, j) => sum + (j.estimated_price || 0), 0) * 0.75) + '₽';
                    
                    const container = document.getElementById('jobs-list');
                    
                    if (jobs.length > 0) {{
                        container.innerHTML = jobs.map(job => `
                            <div class="job-card" onclick="viewJob(${{job.id}})">
                                <div class="job-header">
                                    <div class="job-category">${{job.category}}</div>
                                    <span class="badge badge-${{job.status}}">${{job.status}}</span>
                                </div>
                                <div class="job-info">
                                    <div class="info-row">
                                        <span class="info-icon">📍</span>
                                        <span>${{job.address}}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-icon">👤</span>
                                        <span>${{job.client_name}} • ${{job.client_phone}}</span>
                                    </div>
                                    <div class="info-row">
                                        <span class="info-icon">📝</span>
                                        <span>${{job.problem_description}}</span>
                                    </div>
                                </div>
                                <div class="job-price">
                                    ${{Math.round(job.estimated_price)}} ₽
                                    <small>≈ ${{Math.round(job.estimated_price * 0.75)}}₽ вам</small>
                                </div>
                                <div class="btn-group">
                                    ${{job.status === 'pending' ? `
                                        <button class="btn btn-primary" onclick="event.stopPropagation(); acceptJob(${{job.id}})">
                                            ✓ Принять заказ
                                        </button>
                                    ` : `
                                        <button class="btn btn-secondary" onclick="event.stopPropagation(); startJob(${{job.id}})">
                                            🚀 Начать работу
                                        </button>
                                        <button class="btn btn-secondary" onclick="event.stopPropagation(); cancelJob(${{job.id}})">
                                            ✕ Отменить
                                        </button>
                                    `}}
                                </div>
                            </div>
                        `).join('');
                    }} else {{
                        container.innerHTML = `
                            <div class="empty-state">
                                <div class="empty-icon">📭</div>
                                <div style="font-size:1.125rem;margin-bottom:0.5rem;">Нет активных заказов</div>
                                <div style="font-size:0.875rem;">Новые заказы появятся здесь автоматически</div>
                            </div>
                        `;
                    }}
                }} catch (error) {{
                    console.error('Ошибка загрузки:', error);
                    document.getElementById('jobs-list').innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon">⚠️</div>
                            <div>Ошибка загрузки заказов</div>
                        </div>
                    `;
                }}
            }}
            
            async function acceptJob(jobId) {{
                try {{
                    const res = await fetch(`/api/jobs/master/${{masterId}}/${{jobId}}/status`, {{
                        method: 'PUT',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ status: 'accepted' }})
                    }});
                    if (res.ok) {{
                        showToast('Заказ принят! Свяжитесь с клиентом', '✅');
                        loadJobs();
                    }}
                }} catch (e) {{ showToast('Ошибка при принятии заказа', '❌'); }}
            }}
            
            function viewJob(id) {{
                const job = jobs.find(j => j.id === id);
                if (job) showToast(`Заказ #${{id}}: ${{job.category}}`, '👁️');
            }}
            
            loadJobs();
            setInterval(loadJobs, 10000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/ai-chat")
async def ai_chat():
    """AI-чат с клиентом"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Чат</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f9fafb;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .chat-container {
                flex: 1;
                max-width: 800px;
                margin: 0 auto;
                width: 100%;
                padding: 1rem;
            }
            h1 { margin-bottom: 1rem; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h1>💬 AI Помощник</h1>
            <p>Чат с AI для обработки заказов</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/track")
async def track_order():
    """Отслеживание заказа"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Отслеживание заказа</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f9fafb;
                padding: 2rem;
            }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { margin-bottom: 1.5rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📍 Отслеживание заказа</h1>
            <p>Введите номер заказа для отслеживания</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
