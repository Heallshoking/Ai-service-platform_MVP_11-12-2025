"""
Google Calendar и Tasks интеграция для AI Service Platform
Автоматическая синхронизация заказов с Google сервисами
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
import pickle
from typing import Dict, Optional, List

# Права доступа для Google API
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]

class GoogleIntegration:
    """Интеграция с Google Calendar и Google Tasks"""
    
    def __init__(self):
        self.creds = None
        self.calendar_service = None
        self.tasks_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Авторизация в Google API"""
        # Проверка существующих токенов
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        
        # Обновление токенов если истекли
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                # Первая авторизация
                if os.path.exists('credentials.json'):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)
                else:
                    print("⚠️ credentials.json не найден! Создайте через Google Cloud Console")
                    return
            
            # Сохранение токенов
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)
        
        # Инициализация сервисов
        if self.creds:
            self.calendar_service = build('calendar', 'v3', credentials=self.creds)
            self.tasks_service = build('tasks', 'v1', credentials=self.creds)
    
    def create_calendar_event(self, order: Dict) -> Optional[str]:
        """
        Создать событие в Google Calendar
        
        Args:
            order: Данные заказа (dict)
            
        Returns:
            event_id: ID созданного события или None
        """
        if not self.calendar_service:
            return None
        
        try:
            # Подготовка времени
            date_str = order.get('preferred_date', datetime.now().strftime('%Y-%m-%d'))
            time_str = order.get('preferred_time', '09:00')
            
            start_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            end_datetime = start_datetime + timedelta(hours=2)  # 2 часа на работу
            
            # 🔥 ФОРМАТ НАЗВАНИЯ: "Дата, Адрес, Время" (БЕЗ ИКОНОК И НОМЕРА)
            event_title = f"{date_str}, {order.get('address', 'Адрес')}, {time_str}"
            
            # Формирование события
            event = {
                'summary': event_title,
                'location': order.get('address', 'Адрес не указан'),
                'description': f"""
📋 Заказ #{order['id']}

🔧 Категория: {order.get('category_name', 'Общие работы')}
📝 Описание: {order.get('problem_description', 'Нет описания')}

💰 Стоимость: {order.get('estimated_price', 0)} ₽
💵 Ваш заработок (75%): {order.get('estimated_price', 0) * 0.75} ₽

⚠️ КОНТАКТ КЛИЕНТА ОТКРОЕТСЯ ПОСЛЕ НАЖАТИЯ "Я НА МЕСТЕ"
                """.strip(),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/Kaliningrad',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/Kaliningrad',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},  # За час
                        {'method': 'popup', 'minutes': 15},  # За 15 минут
                    ],
                },
                'colorId': '9',  # Синий цвет для рабочих заказов
            }
            
            # Создание события
            event = self.calendar_service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            print(f"✅ Событие создано в Google Calendar: {event.get('htmlLink')}")
            return event['id']
            
        except Exception as e:
            print(f"❌ Ошибка создания события в Calendar: {e}")
            return None
    
    def create_task(self, order: Dict) -> Optional[str]:
        """
        Создать задачу в Google Tasks
        
        Args:
            order: Данные заказа (dict)
            
        Returns:
            task_id: ID созданной задачи или None
        """
        if not self.tasks_service:
            return None
        
        try:
            # Получение списка задач (или создание нового)
            tasklists = self.tasks_service.tasklists().list().execute()
            
            # Найти или создать список "Заказы"
            tasklist_id = None
            for tasklist in tasklists.get('items', []):
                if tasklist['title'] == 'Заказы':
                    tasklist_id = tasklist['id']
                    break
            
            if not tasklist_id:
                # Создать новый список
                new_tasklist = self.tasks_service.tasklists().insert(
                    body={'title': 'Заказы'}
                ).execute()
                tasklist_id = new_tasklist['id']
            
            # Формирование задачи в нужном формате
            time_str = order.get('preferred_time', '09:00')
            address = order.get('address', 'Адрес не указан')
            price = order.get('estimated_price', 0) * 0.75  # 75% мастеру
            
            task = {
                'title': f"{time_str}, {address}, {price:.0f}₽",
                'notes': f"""
Заказ #{order['id']}

Клиент: {order.get('client_name', 'Не указан')}
Телефон: {order.get('client_phone', 'Не указан')}

Категория: {order.get('category_name', 'Общие работы')}
Описание: {order.get('problem_description', 'Нет описания')}

Общая сумма: {order.get('estimated_price', 0)} ₽
Ваш заработок: {price:.0f} ₽
                """.strip(),
                'due': f"{order.get('preferred_date', datetime.now().strftime('%Y-%m-%d'))}T23:59:59.000Z"
            }
            
            # Создание задачи
            result = self.tasks_service.tasks().insert(
                tasklist=tasklist_id,
                body=task
            ).execute()
            
            print(f"✅ Задача создана в Google Tasks: {result.get('title')}")
            return result['id']
            
        except Exception as e:
            print(f"❌ Ошибка создания задачи в Tasks: {e}")
            return None
    
    def update_event(self, event_id: str, order: Dict) -> bool:
        """Обновить событие в календаре"""
        if not self.calendar_service or not event_id:
            return False
        
        try:
            # Получить событие
            event = self.calendar_service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Обновить время если изменилось
            if 'preferred_time' in order:
                date_str = order.get('preferred_date', datetime.now().strftime('%Y-%m-%d'))
                time_str = order['preferred_time']
                
                start_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                end_datetime = start_datetime + timedelta(hours=2)
                
                event['start'] = {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Europe/Kaliningrad',
                }
                event['end'] = {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Europe/Kaliningrad',
                }
            
            # Обновить статус
            if order.get('status') == 'completed':
                event['summary'] = f"✅ {event.get('summary', 'Заказ')}"
                event['colorId'] = '10'  # Зелёный для завершённых
            
            # Сохранить изменения
            updated_event = self.calendar_service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            print(f"✅ Событие обновлено в Google Calendar")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления события: {e}")
            return False
    
    def complete_task(self, task_id: str) -> bool:
        """Отметить задачу как выполненную"""
        if not self.tasks_service or not task_id:
            return False
        
        try:
            # Найти список задач
            tasklists = self.tasks_service.tasklists().list().execute()
            tasklist_id = None
            
            for tasklist in tasklists.get('items', []):
                if tasklist['title'] == 'Заказы':
                    tasklist_id = tasklist['id']
                    break
            
            if not tasklist_id:
                return False
            
            # Обновить статус задачи
            task = self.tasks_service.tasks().get(
                tasklist=tasklist_id,
                task=task_id
            ).execute()
            
            task['status'] = 'completed'
            
            updated_task = self.tasks_service.tasks().update(
                tasklist=tasklist_id,
                task=task_id,
                body=task
            ).execute()
            
            print(f"✅ Задача отмечена выполненной в Google Tasks")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка завершения задачи: {e}")
            return False
    
    def reveal_client_contact(self, event_id: str, client_name: str, client_phone: str) -> bool:
        """
        🔥 ОТКРЫТЬ КОНТАКТ КЛИЕНТА ПОСЛЕ "Я НА МЕСТЕ"
        Обновить событие в Google Calendar - добавить контакты клиента
        """
        if not self.calendar_service or not event_id:
            return False
        
        try:
            # Получить событие
            event = self.calendar_service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            # Обновить описание - добавить контакты
            description = event.get('description', '')
            
            # Добавить контакты в начало
            new_description = f"""
✅ МАСТЕР НА МЕСТЕ!

👤 Клиент: {client_name}
📞 Телефон: {client_phone}

{description}
            """.strip()
            
            event['description'] = new_description
            # 🔥 НЕ МЕНЯЕМ НАЗВАНИЕ - оставляем "Дата, Адрес, Время"
            # Только добавляем галочку в начало
            current_title = event.get('summary', '')
            if not current_title.startswith('✅'):
                event['summary'] = f"✅ {current_title}"
            event['colorId'] = '10'  # Зелёный цвет
            
            # Сохранить
            self.calendar_service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            print(f"✅ Контакт клиента открыт в Google Calendar")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления события: {e}")
            return False
    
    def sync_order(self, order: Dict) -> Dict[str, Optional[str]]:
        """
        Полная синхронизация заказа с Google
        Создаёт событие в Calendar и задачу в Tasks
        
        Returns:
            dict: {'calendar_event_id': str, 'task_id': str}
        """
        result = {
            'calendar_event_id': None,
            'task_id': None
        }
        
        # Создать в Calendar
        calendar_id = self.create_calendar_event(order)
        if calendar_id:
            result['calendar_event_id'] = calendar_id
        
        # Создать в Tasks
        task_id = self.create_task(order)
        if task_id:
            result['task_id'] = task_id
        
        return result


# Глобальный экземпляр для использования в API
google_integration = None

def init_google_integration():
    """Инициализация Google интеграции при старте"""
    global google_integration
    try:
        google_integration = GoogleIntegration()
        print("✅ Google интеграция инициализирована")
    except Exception as e:
        print(f"⚠️ Google интеграция недоступна: {e}")
        print("💡 Для подключения:")
        print("   1. Создайте проект в Google Cloud Console")
        print("   2. Включите Calendar API и Tasks API")
        print("   3. Скачайте credentials.json")
        print("   4. Положите в корень проекта")

def sync_order_to_google(order: Dict) -> Dict:
    """Синхронизировать заказ с Google (используется в API)"""
    if google_integration:
        return google_integration.sync_order(order)
    return {'calendar_event_id': None, 'task_id': None}
