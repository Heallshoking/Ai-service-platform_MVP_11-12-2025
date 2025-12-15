"""
Google Sheets Integration для BALT-SET.RU
Все заявки сохраняются в Google Таблицу
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Dict, List, Optional

load_dotenv()

# Настройки Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "credentials.json")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "BALT-SET Заявки")

class GoogleSheetsManager:
    """Управление Google Sheets для заявок"""
    
    def __init__(self):
        """Инициализация подключения к Google Sheets"""
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                GOOGLE_SHEETS_CREDENTIALS_FILE, 
                scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open(SPREADSHEET_NAME)
            self.init_worksheets()
        except Exception as e:
            print(f"⚠️ Ошибка подключения к Google Sheets: {e}")
            self.client = None
    
    def init_worksheets(self):
        """Инициализация листов таблицы"""
        try:
            # Лист "Заявки"
            try:
                self.orders_sheet = self.spreadsheet.worksheet("Заявки")
            except:
                self.orders_sheet = self.spreadsheet.add_worksheet(
                    title="Заявки", 
                    rows="1000", 
                    cols="15"
                )
                # Заголовки
                headers = [
                    "ID", "Дата/Время", "Источник", "Имя", "Телефон", 
                    "Категория", "Проблема", "Адрес", "Статус", 
                    "Мастер", "Цена", "Комиссия 30%", "Дата выполнения", 
                    "Оценка", "Комментарий"
                ]
                self.orders_sheet.append_row(headers)
            
            # Лист "Мастера"
            try:
                self.masters_sheet = self.spreadsheet.worksheet("Мастера")
            except:
                self.masters_sheet = self.spreadsheet.add_worksheet(
                    title="Мастера", 
                    rows="100", 
                    cols="10"
                )
                headers = [
                    "ID", "Telegram ID", "Имя", "Телефон", "Специализация",
                    "Рейтинг", "Заказов выполнено", "Заработано", 
                    "Статус", "Дата регистрации"
                ]
                self.masters_sheet.append_row(headers)
            
            # Лист "Статистика"
            try:
                self.stats_sheet = self.spreadsheet.worksheet("Статистика")
            except:
                self.stats_sheet = self.spreadsheet.add_worksheet(
                    title="Статистика", 
                    rows="50", 
                    cols="5"
                )
                headers = ["Метрика", "Значение", "Период", "Обновлено", "Примечание"]
                self.stats_sheet.append_row(headers)
                
        except Exception as e:
            print(f"⚠️ Ошибка инициализации листов: {e}")
    
    def add_order(self, order_data: Dict) -> Optional[int]:
        """
        Добавить заявку в Google Sheets
        
        Args:
            order_data: {
                "source": "telegram" | "website",
                "name": str,
                "phone": str,
                "category": str,
                "problem": str,
                "address": str
            }
        
        Returns:
            ID заявки или None
        """
        if not self.client:
            print("⚠️ Google Sheets не подключен")
            return None
        
        try:
            # Генерируем ID
            all_rows = self.orders_sheet.get_all_values()
            order_id = len(all_rows)  # ID = номер строки
            
            # Текущая дата/время
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Формируем строку
            row = [
                order_id,                           # ID
                now,                                # Дата/Время
                order_data.get("source", "unknown"), # Источник
                order_data.get("name", ""),         # Имя
                order_data.get("phone", ""),        # Телефон
                order_data.get("category", ""),     # Категория
                order_data.get("problem", ""),      # Проблема
                order_data.get("address", ""),      # Адрес
                "Новая",                            # Статус
                "",                                 # Мастер (пусто)
                "",                                 # Цена (пусто)
                "",                                 # Комиссия (пусто)
                "",                                 # Дата выполнения (пусто)
                "",                                 # Оценка (пусто)
                ""                                  # Комментарий (пусто)
            ]
            
            # Добавляем в таблицу
            self.orders_sheet.append_row(row)
            
            # Обновляем статистику
            self.update_stats()
            
            print(f"✅ Заявка #{order_id} добавлена в Google Sheets")
            return order_id
            
        except Exception as e:
            print(f"❌ Ошибка добавления заявки: {e}")
            return None
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        """
        Получить список заявок
        
        Args:
            status: Фильтр по статусу ("Новая", "В работе", "Выполнена", etc.)
        
        Returns:
            Список заявок
        """
        if not self.client:
            return []
        
        try:
            all_rows = self.orders_sheet.get_all_values()
            headers = all_rows[0]
            orders = []
            
            for row in all_rows[1:]:  # Пропускаем заголовок
                order = dict(zip(headers, row))
                
                # Фильтр по статусу
                if status and order.get("Статус") != status:
                    continue
                
                orders.append(order)
            
            return orders
            
        except Exception as e:
            print(f"❌ Ошибка получения заявок: {e}")
            return []
    
    def assign_master(self, order_id: int, master_name: str) -> bool:
        """
        Назначить мастера на заявку
        
        Args:
            order_id: ID заявки
            master_name: Имя мастера
        
        Returns:
            True если успешно
        """
        if not self.client:
            return False
        
        try:
            # Находим строку заявки (ID + 1, т.к. есть заголовок)
            row_num = order_id + 1
            
            # Обновляем колонку "Мастер" (10-я колонка)
            self.orders_sheet.update_cell(row_num, 10, master_name)
            
            # Обновляем статус на "В работе"
            self.orders_sheet.update_cell(row_num, 9, "В работе")
            
            print(f"✅ Мастер {master_name} назначен на заявку #{order_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка назначения мастера: {e}")
            return False
    
    def complete_order(self, order_id: int, price: float, rating: int = 5) -> bool:
        """
        Завершить заявку
        
        Args:
            order_id: ID заявки
            price: Стоимость работы
            rating: Оценка (1-5)
        
        Returns:
            True если успешно
        """
        if not self.client:
            return False
        
        try:
            row_num = order_id + 1
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Комиссия 30%
            commission = price * 0.30
            
            # Обновляем данные
            self.orders_sheet.update_cell(row_num, 9, "Выполнена")      # Статус
            self.orders_sheet.update_cell(row_num, 11, str(price))       # Цена
            self.orders_sheet.update_cell(row_num, 12, str(commission))  # Комиссия
            self.orders_sheet.update_cell(row_num, 13, now)              # Дата выполнения
            self.orders_sheet.update_cell(row_num, 14, str(rating))      # Оценка
            
            # Обновляем статистику
            self.update_stats()
            
            print(f"✅ Заявка #{order_id} завершена. Цена: {price}₽, Комиссия: {commission}₽")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка завершения заявки: {e}")
            return False
    
    def add_master(self, master_data: Dict) -> Optional[int]:
        """
        Добавить мастера
        
        Args:
            master_data: {
                "telegram_id": int,
                "name": str,
                "phone": str,
                "specialization": str
            }
        
        Returns:
            ID мастера или None
        """
        if not self.client:
            return None
        
        try:
            all_rows = self.masters_sheet.get_all_values()
            master_id = len(all_rows)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row = [
                master_id,
                str(master_data.get("telegram_id", "")),
                master_data.get("name", ""),
                master_data.get("phone", ""),
                master_data.get("specialization", "Электрик"),
                "5.0",                               # Рейтинг начальный
                "0",                                 # Заказов выполнено
                "0",                                 # Заработано
                "Активен",                           # Статус
                now                                  # Дата регистрации
            ]
            
            self.masters_sheet.append_row(row)
            
            print(f"✅ Мастер {master_data.get('name')} добавлен (ID: {master_id})")
            return master_id
            
        except Exception as e:
            print(f"❌ Ошибка добавления мастера: {e}")
            return None
    
    def get_masters(self, status: str = "Активен") -> List[Dict]:
        """Получить список мастеров"""
        if not self.client:
            return []
        
        try:
            all_rows = self.masters_sheet.get_all_values()
            headers = all_rows[0]
            masters = []
            
            for row in all_rows[1:]:
                master = dict(zip(headers, row))
                
                if status and master.get("Статус") != status:
                    continue
                
                masters.append(master)
            
            return masters
            
        except Exception as e:
            print(f"❌ Ошибка получения мастеров: {e}")
            return []
    
    def update_stats(self):
        """Обновить статистику"""
        if not self.client:
            return
        
        try:
            orders = self.get_orders()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Считаем метрики
            total_orders = len(orders)
            new_orders = len([o for o in orders if o.get("Статус") == "Новая"])
            in_progress = len([o for o in orders if o.get("Статус") == "В работе"])
            completed = len([o for o in orders if o.get("Статус") == "Выполнена"])
            
            # Подсчёт выручки и комиссии
            total_revenue = sum([float(o.get("Цена", 0) or 0) for o in orders if o.get("Цена")])
            total_commission = sum([float(o.get("Комиссия 30%", 0) or 0) for o in orders if o.get("Комиссия 30%")])
            
            # Обновляем лист статистики
            stats = [
                ["Всего заявок", str(total_orders), "Все время", now, ""],
                ["Новых заявок", str(new_orders), "Сейчас", now, "Требуют назначения"],
                ["В работе", str(in_progress), "Сейчас", now, ""],
                ["Выполнено", str(completed), "Все время", now, ""],
                ["Общая выручка", f"{total_revenue}₽", "Все время", now, ""],
                ["Наша комиссия (30%)", f"{total_commission}₽", "Все время", now, ""],
            ]
            
            # Очищаем и записываем
            self.stats_sheet.clear()
            self.stats_sheet.append_row(["Метрика", "Значение", "Период", "Обновлено", "Примечание"])
            for stat in stats:
                self.stats_sheet.append_row(stat)
            
        except Exception as e:
            print(f"⚠️ Ошибка обновления статистики: {e}")


# Глобальный экземпляр
sheets_manager = GoogleSheetsManager()


# ========== Вспомогательные функции ==========

def save_order_from_bot(name: str, phone: str, category: str, problem: str, address: str, source: str = "telegram"):
    """Сохранить заявку из бота"""
    order_data = {
        "source": source,
        "name": name,
        "phone": phone,
        "category": category,
        "problem": problem,
        "address": address
    }
    
    order_id = sheets_manager.add_order(order_data)
    return order_id


def save_order_from_website(name: str, phone: str, category: str, problem: str, address: str):
    """Сохранить заявку с сайта"""
    return save_order_from_bot(name, phone, category, problem, address, source="website")


if __name__ == "__main__":
    # Тест
    print("🧪 Тестирование Google Sheets Integration...")
    
    # Тестовая заявка
    test_order = save_order_from_bot(
        name="Иван Тестовый",
        phone="+79001234567",
        category="⚡ Электрика",
        problem="Не работает розетка в гостиной",
        address="ул. Ленина, 10"
    )
    
    if test_order:
        print(f"✅ Тестовая заявка #{test_order} создана!")
        
        # Назначаем мастера
        sheets_manager.assign_master(test_order, "Петров Пётр")
        
        # Завершаем
        sheets_manager.complete_order(test_order, price=2000, rating=5)
    
    print("\n📊 Статистика:")
    orders = sheets_manager.get_orders()
    print(f"Всего заявок: {len(orders)}")
