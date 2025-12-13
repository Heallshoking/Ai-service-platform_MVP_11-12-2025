# Руководство по интеграциям

## 1. Интеграция Telegram Web App

### Шаг 1: Создание бота
1. Напишите @BotFather в Telegram
2. Создайте бота командой `/newbot`
3. Получите TOKEN бота
4. Настройте Web App командой `/newapp`

### Шаг 2: Настройка Web App URL
```
/setmenubutton
Выберите бота
Укажите URL: https://your-domain.com
Название кнопки: Заказать услугу
```

### Шаг 3: Интеграция с API
```javascript
// В вашем Telegram Web App
const tg = window.Telegram.WebApp;

// Получить данные пользователя
const user = tg.initDataUnsafe.user;

// Отправить заказ
const response = await fetch('https://functions.poehali.dev/5c3c68df-2e41-4012-81fd-e134547810fb', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    telegram_id: user.id,
    client_name: `${user.first_name} ${user.last_name}`,
    phone: '+79001234567',
    address: 'ул. Ленина, 10',
    services: [
      { service_id: 1, quantity: 1, price: 500 }
    ]
  })
});

const data = await response.json();
console.log('Order ID:', data.order_id);

// Закрыть Web App
tg.close();
```

## 2. Интеграция Planfix

### Шаг 1: Получение API ключа
1. Войдите в Planfix
2. Настройки → Интеграции → API
3. Создайте новый API токен

### Шаг 2: Создание задачи при новом заказе

```python
import requests

def create_planfix_task(order_id, client_name, address, services):
    api_url = 'https://api.planfix.ru/xml/'
    api_key = 'YOUR_PLANFIX_API_KEY'
    
    task_data = {
        'account': 'your_account',
        'api_key': api_key,
        'task': {
            'title': f'Заказ #{order_id} - {client_name}',
            'description': f'Адрес: {address}\nУслуги: {services}',
            'project': 'Электромонтаж',
            'status': 'Новая'
        }
    }
    
    response = requests.post(api_url, json=task_data)
    return response.json()['task']['id']
```

### Шаг 3: Настройка Webhook от Planfix

**Webhook URL:** https://functions.poehali.dev/49c48648-754a-47d9-a571-dc98222b25bc

В Planfix настройте отправку webhook при:
- Назначении исполнителя
- Изменении статуса задачи

Формат webhook:
```json
{
  "event_type": "task.assigned",
  "task_id": "12345",
  "status": "assigned",
  "assignee": "Алексей Иванов"
}
```

## 3. Интеграция Google Tasks

### Шаг 1: Создание проекта в Google Cloud
1. https://console.cloud.google.com
2. Создайте новый проект
3. Включите Google Tasks API
4. Создайте Service Account
5. Скачайте JSON ключ

### Шаг 2: Создание задачи

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account.json',
    scopes=['https://www.googleapis.com/auth/tasks']
)

service = build('tasks', 'v1', credentials=credentials)

task = {
    'title': f'Заказ #{order_id}',
    'notes': f'Клиент: {client_name}\nАдрес: {address}',
    'status': 'needsAction'
}

result = service.tasks().insert(tasklist='@default', body=task).execute()
print(f"Created task: {result['id']}")
```

### Шаг 3: Виджет для исполнителей

Установите Google Tasks на Android/iOS:
- https://play.google.com/store/apps/details?id=com.google.android.apps.tasks
- https://apps.apple.com/app/google-tasks/id1353634006

## 4. Интеграция WhatsApp Business API

### Шаг 1: Регистрация в Meta Business
1. https://business.facebook.com
2. Создайте Business аккаунт
3. Добавьте WhatsApp Business API

### Шаг 2: Получение токена
1. https://developers.facebook.com
2. Мои приложения → WhatsApp → Токен доступа

### Шаг 3: Отправка уведомлений

```python
import requests

def send_whatsapp_notification(phone, message):
    api_url = 'https://graph.facebook.com/v18.0/YOUR_PHONE_ID/messages'
    headers = {
        'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
        'Content-Type': 'application/json'
    }
    
    data = {
        'messaging_product': 'whatsapp',
        'to': phone,
        'type': 'template',
        'template': {
            'name': 'order_status_update',
            'language': {'code': 'ru'},
            'components': [{
                'type': 'body',
                'parameters': [
                    {'type': 'text', 'text': message}
                ]
            }]
        }
    }
    
    response = requests.post(api_url, json=data, headers=headers)
    return response.json()
```

### Шаблоны сообщений

Создайте в WhatsApp Business Manager:

**Новый заказ:**
```
Здравствуйте! Ваш заказ №{{1}} принят.
Мастер: {{2}}
Дата: {{3}}
Адрес: {{4}}
```

**Мастер выехал:**
```
Мастер {{1}} выехал к вам.
Время прибытия: ~{{2}} минут
Телефон: {{3}}
```

## 5. Автоматизация с помощью Webhooks

### Настройка автоматического распределения

```python
def auto_assign_executor(order_id, address):
    # Получить координаты адреса
    coords = geocode_address(address)
    
    # Найти ближайшего свободного мастера
    query = """
        SELECT id, name, phone 
        FROM executors 
        WHERE is_active = true
        AND id NOT IN (
            SELECT executor_id 
            FROM orders 
            WHERE status IN ('assigned', 'in_progress', 'on_way')
        )
        ORDER BY 
            (current_location_lat - %s)^2 + 
            (current_location_lng - %s)^2 
        LIMIT 1
    """
    
    executor = execute_query(query, (coords['lat'], coords['lng']))
    
    if executor:
        # Назначить исполнителя
        update_order(order_id, executor_id=executor['id'], status='assigned')
        
        # Создать задачу в Planfix/Google Tasks
        create_task(order_id, executor['id'])
        
        # Отправить уведомления
        send_telegram_notification(executor['telegram_id'], f'Новый заказ #{order_id}')
        send_whatsapp_notification(executor['phone'], f'Назначен заказ #{order_id}')
```

## 6. Мониторинг и отладка

### Проверка работы интеграций

```bash
# Тест создания заказа
curl -X POST https://functions.poehali.dev/5c3c68df-2e41-4012-81fd-e134547810fb \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "client_name": "Тест",
    "phone": "+79001234567",
    "address": "ул. Тестовая, 1",
    "services": [{"service_id": 1, "quantity": 1, "price": 500}]
  }'

# Тест получения статуса
curl https://functions.poehali.dev/b875ba9a-3e1c-4e76-807f-0525f61dd331?order_id=1

# Тест обновления статуса
curl -X POST https://functions.poehali.dev/9fde3ede-6010-4014-95a9-ec4e7388f476 \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "status": "in_progress",
    "changed_by": "test"
  }'
```

## 7. Переменные окружения

Создайте `.env` файл:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_SECRET=random_secret_string

# Planfix
PLANFIX_API_KEY=your_planfix_api_key
PLANFIX_ACCOUNT=your_account_name

# Google Tasks
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/credentials.json

# WhatsApp
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_ID=your_phone_number_id
```

## Поддержка

При возникновении проблем с интеграциями:
1. Проверьте логи функций
2. Убедитесь что все переменные окружения установлены
3. Проверьте права доступа к API
4. Свяжитесь с поддержкой: @konigelectric
