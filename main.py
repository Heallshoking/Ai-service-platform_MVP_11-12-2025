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

# ==================== HTML ИНТЕРФЕЙСЫ ====================

@app.get("/admin")
async def admin_panel():
    """📈 Премиум админ-панель с графиками"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Админ-панель | AI Service Platform</title>
        <style>
            :root {
                --primary: #6366f1; --primary-dark: #4f46e5; --primary-light: #e0e7ff;
                --success: #10b981; --danger: #ef4444; --warning: #f59e0b;
                --bg: #f8fafc; --surface: #fff; --text: #0f172a; --text-muted: #64748b;
                --border: #e2e8f0; --shadow: rgba(15, 23, 42, 0.08);
            }
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--bg); color: var(--text); line-height: 1.6;
            }
            .header {
                background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
                color: white; padding: 2rem 1.5rem; box-shadow: 0 4px 6px var(--shadow);
            }
            .header-content { max-width: 1400px; margin: 0 auto; }
            .header h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; }
            .header-subtitle { opacity: 0.9; font-size: 0.9rem; }
            .container { max-width: 1400px; margin: 0 auto; padding: 2rem 1.5rem; }
            .stats-grid {
                display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem; margin-bottom: 2rem;
            }
            .stat-card {
                background: var(--surface); border-radius: 16px; padding: 1.5rem;
                border: 1px solid var(--border); position: relative; overflow: hidden;
                box-shadow: 0 1px 3px var(--shadow); transition: all 0.2s ease;
            }
            .stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 16px var(--shadow); }
            .stat-card::before {
                content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
            }
            .stat-card.success::before { background: linear-gradient(90deg, var(--success), #34d399); }
            .stat-card.warning::before { background: linear-gradient(90deg, var(--warning), #fbbf24); }
            .stat-card.primary::before { background: linear-gradient(90deg, var(--primary), #818cf8); }
            .stat-card.danger::before { background: linear-gradient(90deg, var(--danger), #f87171); }
            .stat-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
            .stat-icon { font-size: 2rem; opacity: 0.5; }
            .stat-label { font-size: 0.875rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
            .stat-value { font-size: 2.5rem; font-weight: 700; margin: 0.5rem 0; }
            .stat-change { font-size: 0.875rem; }
            .stat-change.up { color: var(--success); }
            .stat-change.down { color: var(--danger); }
            .card {
                background: var(--surface); border-radius: 16px; padding: 2rem;
                border: 1px solid var(--border); box-shadow: 0 1px 3px var(--shadow);
                margin-bottom: 1.5rem;
            }
            .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
            .card-title { font-size: 1.25rem; font-weight: 600; }
            .chart-container { position: relative; height: 300px; }
            .chart-bar { display: flex; align-items: flex-end; height: 100%; gap: 1rem; }
            .bar { flex: 1; background: linear-gradient(180deg, var(--primary-light), var(--primary)); border-radius: 8px 8px 0 0; position: relative; transition: all 0.3s ease; }
            .bar:hover { filter: brightness(1.1); }
            .bar-label { position: absolute; bottom: -1.5rem; left: 50%; transform: translateX(-50%); font-size: 0.75rem; color: var(--text-muted); }
            .bar-value { position: absolute; top: -1.75rem; left: 50%; transform: translateX(-50%); font-size: 0.875rem; font-weight: 600; }
            .quick-actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
            .action-btn {
                display: flex; align-items: center; gap: 0.75rem; padding: 1rem 1.25rem;
                background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
                cursor: pointer; transition: all 0.2s ease; text-decoration: none; color: var(--text);
            }
            .action-btn:hover { background: var(--primary-light); border-color: var(--primary); }
            .action-icon { font-size: 1.5rem; }
            .recent-list { display: flex; flex-direction: column; gap: 0.75rem; }
            .list-item {
                display: flex; justify-content: space-between; align-items: center;
                padding: 1rem; background: var(--bg); border-radius: 8px;
            }
            .item-info { display: flex; align-items: center; gap: 0.75rem; }
            .item-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--primary-light); display: flex; align-items: center; justify-content: center; font-weight: 600; color: var(--primary); }
            .badge { padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
            .badge-success { background: #d1fae5; color: var(--success); }
            .badge-warning { background: #fef3c7; color: var(--warning); }
            .badge-danger { background: #fee2e2; color: var(--danger); }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>⚡ Админ-панель</h1>
                <div class="header-subtitle">Управление платформой AI Service Platform</div>
            </div>
        </div>
        
        <div class="container">
            <!-- Статистика -->
            <div class="stats-grid">
                <div class="stat-card success">
                    <div class="stat-header">
                        <div>
                            <div class="stat-label">Всего заказов</div>
                            <div class="stat-value" id="totalJobs">0</div>
                            <div class="stat-change up">▲ 12% за неделю</div>
                        </div>
                        <div class="stat-icon">📊</div>
                    </div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-header">
                        <div>
                            <div class="stat-label">Активных мастеров</div>
                            <div class="stat-value" id="activeMasters">0</div>
                            <div class="stat-change up">▲ 5 новых</div>
                        </div>
                        <div class="stat-icon">👨‍🔧</div>
                    </div>
                </div>
                <div class="stat-card primary">
                    <div class="stat-header">
                        <div>
                            <div class="stat-label">Доход платформы</div>
                            <div class="stat-value" id="revenue">0 ₽</div>
                            <div class="stat-change up">▲ 18% за месяц</div>
                        </div>
                        <div class="stat-icon">💰</div>
                    </div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-header">
                        <div>
                            <div class="stat-label">Средний чек</div>
                            <div class="stat-value" id="avgCheck">0 ₽</div>
                            <div class="stat-change down">▼ 3% за неделю</div>
                        </div>
                        <div class="stat-icon">📈</div>
                    </div>
                </div>
            </div>
            
            <!-- График заказов -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">📈 Заказы по дням</div>
                </div>
                <div class="chart-container">
                    <div class="chart-bar" id="chart"></div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <!-- Быстрые действия -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">⚡ Быстрые действия</div>
                    </div>
                    <div class="quick-actions">
                        <a href="/docs" class="action-btn">
                            <span class="action-icon">📖</span>
                            <span>API Docs</span>
                        </a>
                        <a href="/health" class="action-btn">
                            <span class="action-icon">❤️</span>
                            <span>Health Check</span>
                        </a>
                        <a href="/api/stats" class="action-btn">
                            <span class="action-icon">📊</span>
                            <span>Статистика</span>
                        </a>
                        <a href="/master" class="action-btn">
                            <span class="action-icon">🔧</span>
                            <span>Терминал</span>
                        </a>
                    </div>
                </div>
                
                <!-- Последние заказы -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">🕒 Последние заказы</div>
                    </div>
                    <div class="recent-list" id="recentJobs">
                        <div class="list-item">
                            <div class="item-info">
                                <div class="item-avatar">-</div>
                                <div>Загрузка...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            async function loadStats() {
                try {
                    const res = await fetch('/api/stats');
                    const data = await res.json();
                    
                    document.getElementById('totalJobs').textContent = data.jobs?.total || 0;
                    document.getElementById('activeMasters').textContent = data.masters?.active || 0;
                    document.getElementById('revenue').textContent = (data.revenue?.total || 0).toFixed(0) + ' ₽';
                    document.getElementById('avgCheck').textContent = 
                        ((data.revenue?.total || 0) / Math.max(data.jobs?.total || 1, 1)).toFixed(0) + ' ₽';
                    
                    // График (мок-данные для примера)
                    const chartData = [
                        { label: 'Пн', value: Math.random() * 100 },
                        { label: 'Вт', value: Math.random() * 100 },
                        { label: 'Ср', value: Math.random() * 100 },
                        { label: 'Чт', value: Math.random() * 100 },
                        { label: 'Пт', value: Math.random() * 100 },
                        { label: 'Сб', value: Math.random() * 100 },
                        { label: 'Вс', value: Math.random() * 100 }
                    ];
                    const maxValue = Math.max(...chartData.map(d => d.value));
                    
                    document.getElementById('chart').innerHTML = chartData.map(d => `
                        <div class="bar" style="height: ${(d.value / maxValue) * 100}%">
                            <div class="bar-value">${Math.round(d.value)}</div>
                            <div class="bar-label">${d.label}</div>
                        </div>
                    `).join('');
                    
                    // Последние заказы (мок-данные)
                    document.getElementById('recentJobs').innerHTML = [
                        { name: 'Электрика', status: 'success', time: '5 мин назад' },
                        { name: 'Сантехника', status: 'warning', time: '15 мин назад' },
                        { name: 'Ремонт', status: 'success', time: '1 час назад' }
                    ].map(item => `
                        <div class="list-item">
                            <div class="item-info">
                                <div class="item-avatar">${item.name[0]}</div>
                                <div>
                                    <div style="font-weight:600">${item.name}</div>
                                    <div style="font-size:0.875rem;color:var(--text-muted)">${item.time}</div>
                                </div>
                            </div>
                            <span class="badge badge-${item.status}">${item.status === 'success' ? 'Готов' : 'В работе'}</span>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Ошибка загрузки:', error);
                }
            }
            
            loadStats();
            setInterval(loadStats, 30000);
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
