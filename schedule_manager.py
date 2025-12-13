"""
Schedule Manager - Master availability and schedule management
Управление расписанием и доступностью мастеров
"""
import json
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TimeSlot:
    """Временной слот"""
    start: time
    end: time
    
    def __contains__(self, check_time: time) -> bool:
        """Проверка, входит ли время в слот"""
        return self.start <= check_time <= self.end
    
    def to_dict(self) -> Dict:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat()
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'TimeSlot':
        return TimeSlot(
            start=time.fromisoformat(data["start"]),
            end=time.fromisoformat(data["end"])
        )


@dataclass
class DaySchedule:
    """Расписание на день"""
    date: datetime
    available: bool
    time_slot: Optional[TimeSlot]
    booked_jobs: List[int]  # ID заказов
    
    def is_available_at(self, check_time: time) -> bool:
        """Проверка доступности в определенное время"""
        if not self.available:
            return False
        
        if not self.time_slot:
            return False
        
        return check_time in self.time_slot
    
    def to_dict(self) -> Dict:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "available": self.available,
            "time_slot": self.time_slot.to_dict() if self.time_slot else None,
            "booked_jobs": self.booked_jobs
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'DaySchedule':
        return DaySchedule(
            date=datetime.strptime(data["date"], "%Y-%m-%d"),
            available=data["available"],
            time_slot=TimeSlot.from_dict(data["time_slot"]) if data.get("time_slot") else None,
            booked_jobs=data.get("booked_jobs", [])
        )


class ScheduleManager:
    """Менеджер расписания мастеров"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._update_masters_table()
    
    def _update_masters_table(self):
        """Обновить таблицу мастеров (добавить поля расписания)"""
        cursor = self.db.cursor()
        
        # Проверяем, есть ли уже колонка schedule_json
        cursor.execute("PRAGMA table_info(masters)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "schedule_json" not in columns:
            cursor.execute("ALTER TABLE masters ADD COLUMN schedule_json TEXT")
        
        if "terminal_type" not in columns:
            cursor.execute("ALTER TABLE masters ADD COLUMN terminal_type TEXT DEFAULT 'smartphone'")
        
        if "terminal_id" not in columns:
            cursor.execute("ALTER TABLE masters ADD COLUMN terminal_id TEXT")
        
        if "onboarding_conversation_id" not in columns:
            cursor.execute("ALTER TABLE masters ADD COLUMN onboarding_conversation_id TEXT")
        
        if "last_schedule_confirmation" not in columns:
            cursor.execute("ALTER TABLE masters ADD COLUMN last_schedule_confirmation TIMESTAMP")
        
        self.db.commit()
    
    def set_master_schedule(
        self,
        master_id: int,
        schedule: Dict[str, DaySchedule]
    ):
        """Установить расписание мастера"""
        schedule_json = json.dumps(
            {date: day.to_dict() for date, day in schedule.items()},
            ensure_ascii=False
        )
        
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE masters SET schedule_json = ? WHERE id = ?",
            (schedule_json, master_id)
        )
        self.db.commit()
    
    def get_master_schedule(self, master_id: int) -> Dict[str, DaySchedule]:
        """Получить расписание мастера"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT schedule_json FROM masters WHERE id = ?",
            (master_id,)
        )
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return {}
        
        schedule_data = json.loads(row[0])
        return {
            date: DaySchedule.from_dict(day_data)
            for date, day_data in schedule_data.items()
        }
    
    def update_day_schedule(
        self,
        master_id: int,
        date: datetime,
        available: bool,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """Обновить расписание на конкретный день"""
        schedule = self.get_master_schedule(master_id)
        date_key = date.strftime("%Y-%m-%d")
        
        time_slot = None
        if available and start_time and end_time:
            time_slot = TimeSlot(
                start=time.fromisoformat(start_time),
                end=time.fromisoformat(end_time)
            )
        
        schedule[date_key] = DaySchedule(
            date=date,
            available=available,
            time_slot=time_slot,
            booked_jobs=schedule.get(date_key, DaySchedule(date, False, None, [])).booked_jobs
        )
        
        self.set_master_schedule(master_id, schedule)
    
    def is_master_available(
        self,
        master_id: int,
        date: datetime,
        check_time: Optional[time] = None
    ) -> bool:
        """Проверка доступности мастера на дату/время"""
        schedule = self.get_master_schedule(master_id)
        date_key = date.strftime("%Y-%m-%d")
        
        if date_key not in schedule:
            return False
        
        day_schedule = schedule[date_key]
        
        if check_time:
            return day_schedule.is_available_at(check_time)
        else:
            return day_schedule.available
    
    def get_available_masters(
        self,
        specialization: str,
        city: str,
        date: datetime,
        check_time: Optional[time] = None
    ) -> List[int]:
        """Получить список доступных мастеров"""
        cursor = self.db.cursor()
        
        # Получить всех активных мастеров с нужной специализацией и городом
        cursor.execute("""
            SELECT id FROM masters
            WHERE is_active = 1
            AND city = ?
            AND specializations LIKE ?
        """, (city, f'%{specialization}%'))
        
        all_masters = [row[0] for row in cursor.fetchall()]
        
        # Отфильтровать по доступности
        available_masters = []
        for master_id in all_masters:
            if self.is_master_available(master_id, date, check_time):
                available_masters.append(master_id)
        
        return available_masters
    
    def book_master_for_job(
        self,
        master_id: int,
        job_id: int,
        date: datetime
    ):
        """Забронировать мастера на заказ"""
        schedule = self.get_master_schedule(master_id)
        date_key = date.strftime("%Y-%m-%d")
        
        if date_key in schedule:
            schedule[date_key].booked_jobs.append(job_id)
            self.set_master_schedule(master_id, schedule)
    
    def confirm_daily_schedule(self, master_id: int) -> bool:
        """Подтвердить расписание на сегодня"""
        cursor = self.db.cursor()
        cursor.execute(
            "UPDATE masters SET last_schedule_confirmation = ? WHERE id = ?",
            (datetime.now().isoformat(), master_id)
        )
        self.db.commit()
        return True
    
    def needs_schedule_confirmation(self, master_id: int) -> bool:
        """Проверка, нужно ли подтверждение расписания"""
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT last_schedule_confirmation FROM masters WHERE id = ?",
            (master_id,)
        )
        row = cursor.fetchone()
        
        if not row or not row[0]:
            return True
        
        last_confirmation = datetime.fromisoformat(row[0])
        # Подтверждение нужно если последнее было больше 12 часов назад
        return (datetime.now() - last_confirmation) > timedelta(hours=12)
    
    def create_weekly_schedule(
        self,
        master_id: int,
        default_start: str = "08:00",
        default_end: str = "20:00",
        working_days: List[int] = None
    ):
        """Создать расписание на неделю вперед"""
        if working_days is None:
            working_days = [0, 1, 2, 3, 4]  # Пн-Пт
        
        schedule = {}
        today = datetime.now().date()
        
        for i in range(7):
            date = datetime.combine(today + timedelta(days=i), datetime.min.time())
            weekday = date.weekday()
            
            available = weekday in working_days
            time_slot = None
            
            if available:
                time_slot = TimeSlot(
                    start=time.fromisoformat(default_start),
                    end=time.fromisoformat(default_end)
                )
            
            date_key = date.strftime("%Y-%m-%d")
            schedule[date_key] = DaySchedule(
                date=date,
                available=available,
                time_slot=time_slot,
                booked_jobs=[]
            )
        
        self.set_master_schedule(master_id, schedule)
    
    def get_master_workload(self, master_id: int, date: datetime) -> int:
        """Получить количество заказов мастера на дату"""
        schedule = self.get_master_schedule(master_id)
        date_key = date.strftime("%Y-%m-%d")
        
        if date_key not in schedule:
            return 0
        
        return len(schedule[date_key].booked_jobs)
    
    def find_best_available_master(
        self,
        specialization: str,
        city: str,
        date: datetime,
        check_time: Optional[time] = None
    ) -> Optional[int]:
        """Найти лучшего доступного мастера"""
        available_masters = self.get_available_masters(
            specialization, city, date, check_time
        )
        
        if not available_masters:
            return None
        
        # Сортировка по рейтингу и загрузке
        cursor = self.db.cursor()
        master_scores = []
        
        for master_id in available_masters:
            cursor.execute(
                "SELECT rating FROM masters WHERE id = ?",
                (master_id,)
            )
            rating = cursor.fetchone()[0] or 5.0
            workload = self.get_master_workload(master_id, date)
            
            # Балл = рейтинг * 10 - загрузка
            score = (rating * 10) - workload
            master_scores.append((master_id, score))
        
        # Выбрать мастера с наивысшим баллом
        master_scores.sort(key=lambda x: x[1], reverse=True)
        return master_scores[0][0] if master_scores else None
