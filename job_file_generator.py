"""
Job File Generator - AI-powered work instructions generator
Генератор файлов заказов с полными инструкциями для мастеров
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class WorkInstructions:
    """Инструкции по выполнению работы"""
    problem_diagnosis: str  # AI-диагноз проблемы
    tools_required: List[str]  # Необходимые инструменты
    consumables_required: List[str]  # Расходные материалы
    parts_required: List[str]  # Запчасти для покупки
    step_by_step: List[str]  # Пошаговая инструкция
    safety_notes: List[str]  # Меры безопасности
    estimated_time: int  # Время в минутах
    difficulty_level: str  # easy, medium, hard
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class JobFile:
    """Полный файл заказа для мастера"""
    job_id: int
    client_name: str
    client_phone: str
    client_address: str
    service_category: str
    problem_description: str
    ai_diagnosis: str
    estimated_price: float
    master_earnings: float
    scheduled_time: Optional[str]
    urgency_level: str
    work_instructions: WorkInstructions
    conversation_transcript: str
    media_urls: List[str]
    special_notes: Optional[str]
    created_at: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def to_text(self) -> str:
        """Текстовое представление для отправки мастеру"""
        text = f"""
🔧 **ЗАКАЗ #{self.job_id}**

📋 **ИНФОРМАЦИЯ О КЛИЕНТЕ:**
Имя: {self.client_name}
Телефон: {self.client_phone}
Адрес: {self.client_address}

⚡ **ПРОБЛЕМА:**
Категория: {self.service_category}
Описание клиента: {self.problem_description}

🔍 **ДИАГНОЗ AI:**
{self.ai_diagnosis}

💰 **ФИНАНСЫ:**
Стоимость для клиента: {self.estimated_price}₽
Ваш заработок: {self.master_earnings}₽

⏰ **ВРЕМЯ:**
Запланировано: {self.scheduled_time or 'Согласовать с клиентом'}
Ожидаемая длительность: {self.work_instructions.estimated_time} минут
Срочность: {self.urgency_level}

🔨 **НЕОБХОДИМЫЕ ИНСТРУМЕНТЫ:**
{self._format_list(self.work_instructions.tools_required)}

📦 **РАСХОДНЫЕ МАТЕРИАЛЫ:**
{self._format_list(self.work_instructions.consumables_required)}

🛒 **ЗАПЧАСТИ ДЛЯ ПОКУПКИ:**
{self._format_list(self.work_instructions.parts_required)}

📝 **ПОШАГОВАЯ ИНСТРУКЦИЯ:**
{self._format_steps(self.work_instructions.step_by_step)}

⚠️ **МЕРЫ БЕЗОПАСНОСТИ:**
{self._format_list(self.work_instructions.safety_notes)}

📊 **СЛОЖНОСТЬ:** {self.work_instructions.difficulty_level.upper()}

{f'📌 **ДОПОЛНИТЕЛЬНО:**\\n{self.special_notes}' if self.special_notes else ''}

---
✅ После выполнения работы примите оплату через терминал.
Ваш заработок {self.master_earnings}₽ будет зачислен на ваш счет.
"""
        return text.strip()
    
    def _format_list(self, items: List[str]) -> str:
        if not items:
            return "Не требуется"
        return "\n".join(f"• {item}" for item in items)
    
    def _format_steps(self, steps: List[str]) -> str:
        if not steps:
            return "Нет детальной инструкции"
        return "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))


class JobFileGenerator:
    """Генератор файлов заказов с AI-инструкциями"""
    
    def __init__(self, db_connection, ai_client=None):
        self.db = db_connection
        self.ai_client = ai_client  # OpenAI/Anthropic/etc клиент
        self._init_work_instructions_table()
    
    def _init_work_instructions_table(self):
        """Инициализация таблицы инструкций"""
        cursor = self.db.cursor()
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
        self.db.commit()
    
    async def generate_job_file(
        self,
        job_id: int,
        conversation_transcript: str,
        problem_description: str,
        category: str,
        client_info: Dict[str, Any]
    ) -> JobFile:
        """Генерация полного файла заказа"""
        
        # 1. AI диагностирует проблему
        ai_diagnosis = await self._diagnose_problem(problem_description, conversation_transcript, category)
        
        # 2. AI генерирует инструкции
        instructions = await self._generate_instructions(ai_diagnosis, category, problem_description)
        
        # 3. Сохранить инструкции в БД
        self._save_instructions(job_id, instructions)
        
        # 4. Получить информацию о заказе из БД
        job_data = self._get_job_data(job_id)
        
        # 5. Создать файл заказа
        job_file = JobFile(
            job_id=job_id,
            client_name=client_info.get("name", "Клиент"),
            client_phone=client_info.get("phone", ""),
            client_address=client_info.get("address", ""),
            service_category=category,
            problem_description=problem_description,
            ai_diagnosis=ai_diagnosis,
            estimated_price=job_data.get("estimated_price", 0),
            master_earnings=job_data.get("master_earnings", 0),
            scheduled_time=job_data.get("scheduled_time"),
            urgency_level=job_data.get("urgency_level", "standard"),
            work_instructions=instructions,
            conversation_transcript=conversation_transcript,
            media_urls=job_data.get("media_urls", []),
            special_notes=job_data.get("special_notes"),
            created_at=datetime.now()
        )
        
        return job_file
    
    async def _diagnose_problem(self, description: str, transcript: str, category: str) -> str:
        """AI диагностирует проблему"""
        
        if self.ai_client:
            # Используем AI для диагностики
            prompt = f"""
Ты - опытный мастер-диагност в категории '{category}'.
На основе описания клиента и разговора, определи техническую проблему.

Описание клиента: {description}

Транскрипт разговора:
{transcript}

Дай точный технический диагноз проблемы на русском языке (2-3 предложения).
"""
            diagnosis = await self._call_ai(prompt)
            return diagnosis
        else:
            # Без AI - возвращаем описание как есть
            return f"Проблема: {description}"
    
    async def _generate_instructions(
        self,
        diagnosis: str,
        category: str,
        problem: str
    ) -> WorkInstructions:
        """AI генерирует пошаговые инструкции"""
        
        if self.ai_client:
            # Используем AI для генерации инструкций
            prompt = f"""
Ты - опытный мастер в категории '{category}'.
Создай подробные инструкции для выполнения работы.

Диагноз: {diagnosis}
Проблема: {problem}

Ответь в JSON формате:
{{
    "tools_required": ["список инструментов"],
    "consumables_required": ["расходные материалы"],
    "parts_required": ["запчасти для покупки"],
    "step_by_step": ["шаг 1", "шаг 2", ...],
    "safety_notes": ["меры безопасности"],
    "estimated_time": минут,
    "difficulty_level": "easy/medium/hard"
}}
"""
            response = await self._call_ai(prompt, json_mode=True)
            data = json.loads(response) if isinstance(response, str) else response
            
            return WorkInstructions(
                problem_diagnosis=diagnosis,
                tools_required=data.get("tools_required", []),
                consumables_required=data.get("consumables_required", []),
                parts_required=data.get("parts_required", []),
                step_by_step=data.get("step_by_step", []),
                safety_notes=data.get("safety_notes", []),
                estimated_time=data.get("estimated_time", 60),
                difficulty_level=data.get("difficulty_level", "medium")
            )
        else:
            # Без AI - базовые инструкции
            return self._generate_basic_instructions(category, diagnosis)
    
    def _generate_basic_instructions(self, category: str, diagnosis: str) -> WorkInstructions:
        """Базовые инструкции без AI (fallback)"""
        
        category_instructions = {
            "electrical": {
                "tools": ["Отвертка", "Мультиметр", "Изолента", "Плоскогубцы"],
                "consumables": ["Изолента", "Клеммы"],
                "parts": [],
                "steps": [
                    "Отключить электропитание",
                    "Проверить отсутствие напряжения мультиметром",
                    "Выполнить ремонт/установку",
                    "Проверить работу",
                    "Включить питание"
                ],
                "safety": ["Отключить электропитание!", "Проверить отсутствие напряжения"],
                "time": 60,
                "difficulty": "medium"
            },
            "plumbing": {
                "tools": ["Гаечный ключ", "Разводной ключ", "ФУМ-лента"],
                "consumables": ["ФУМ-лента", "Прокладки"],
                "parts": [],
                "steps": [
                    "Перекрыть воду",
                    "Слить остатки воды",
                    "Выполнить ремонт",
                    "Проверить на протечки",
                    "Открыть воду"
                ],
                "safety": ["Перекрыть воду!", "Подготовить тряпки на случай протечки"],
                "time": 45,
                "difficulty": "easy"
            },
            "appliance": {
                "tools": ["Отвертка", "Мультиметр"],
                "consumables": [],
                "parts": [],
                "steps": [
                    "Отключить устройство от сети",
                    "Диагностировать неисправность",
                    "Выполнить ремонт/замену",
                    "Провести тестирование"
                ],
                "safety": ["Отключить от сети!", "Дать остыть перед работой"],
                "time": 90,
                "difficulty": "medium"
            }
        }
        
        cat_data = category_instructions.get(category, category_instructions["electrical"])
        
        return WorkInstructions(
            problem_diagnosis=diagnosis,
            tools_required=cat_data["tools"],
            consumables_required=cat_data["consumables"],
            parts_required=cat_data["parts"],
            step_by_step=cat_data["steps"],
            safety_notes=cat_data["safety"],
            estimated_time=cat_data["time"],
            difficulty_level=cat_data["difficulty"]
        )
    
    async def _call_ai(self, prompt: str, json_mode: bool = False) -> str:
        """Вызов AI API"""
        # Здесь будет интеграция с OpenAI/Anthropic/etc
        # Пока заглушка
        return prompt  # TODO: Реализовать AI вызов
    
    def _save_instructions(self, job_id: int, instructions: WorkInstructions):
        """Сохранить инструкции в БД"""
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO work_instructions (
                job_id, problem_diagnosis, tools_required, consumables_required,
                parts_required, step_by_step, safety_notes,
                estimated_time, difficulty_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            instructions.problem_diagnosis,
            json.dumps(instructions.tools_required, ensure_ascii=False),
            json.dumps(instructions.consumables_required, ensure_ascii=False),
            json.dumps(instructions.parts_required, ensure_ascii=False),
            json.dumps(instructions.step_by_step, ensure_ascii=False),
            json.dumps(instructions.safety_notes, ensure_ascii=False),
            instructions.estimated_time,
            instructions.difficulty_level
        ))
        self.db.commit()
    
    def _get_job_data(self, job_id: int) -> Dict:
        """Получить данные заказа из БД"""
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if not row:
            return {}
        
        # Рассчитать заработок мастера (75% после вычета 2% шлюза)
        estimated_price = row[6] if len(row) > 6 else 0
        gateway_fee = estimated_price * 0.02
        net = estimated_price - gateway_fee
        master_earnings = net * 0.75
        
        return {
            "estimated_price": estimated_price,
            "master_earnings": round(master_earnings, 2),
            "scheduled_time": None,  # TODO: Из conversations
            "urgency_level": "standard",
            "media_urls": [],
            "special_notes": None
        }
    
    def export_to_pdf(self, job_file: JobFile, output_path: str):
        """Экспорт файла заказа в PDF"""
        # TODO: Реализовать генерацию PDF
        # Можно использовать reportlab или fpdf
        pass
    
    def send_to_master(self, job_file: JobFile, master_id: int, channel: str = "telegram"):
        """Отправить файл заказа мастеру"""
        # TODO: Интеграция с notification_service
        pass
