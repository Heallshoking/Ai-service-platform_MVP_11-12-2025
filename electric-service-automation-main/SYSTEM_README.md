# УСЛУГИ ЭЛЕКТРИКА ORG

Комплексная система управления заявками для электромонтажной компании с автоматизацией через Telegram Web App, Planfix, Google Tasks и WhatsApp.

## 🚀 Быстрый старт

### Что уже работает (MVP):

✅ **База данных PostgreSQL** - полная схема с таблицами заказов, клиентов, исполнителей, услуг  
✅ **Backend API** - 5 cloud functions для работы с заказами  
✅ **Клиентский интерфейс** - каталог услуг, форма заказа, корзина  
✅ **Админ-панель** - управление заказами, фильтры, обновление статусов  

### Доступные URL:

**Frontend:**
- Главная страница: `/`
- Админ-панель: `/admin`

**Backend API:**
- GET Список услуг: `https://functions.poehali.dev/46dcbdcd-c306-4a31-b776-f6e34eba609f`
- POST Создать заказ: `https://functions.poehali.dev/5c3c68df-2e41-4012-81fd-e134547810fb`
- GET Статус заказа: `https://functions.poehali.dev/b875ba9a-3e1c-4e76-807f-0525f61dd331`
- POST Обновить статус: `https://functions.poehali.dev/9fde3ede-6010-4014-95a9-ec4e7388f476`
- POST Planfix Webhook: `https://functions.poehali.dev/49c48648-754a-47d9-a571-dc98222b25bc`

## 📚 Документация

- **[PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md)** - полная архитектура системы, схема БД, API endpoints
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - пошаговые инструкции по интеграции Telegram, Planfix, Google Tasks, WhatsApp

## 🏗️ Архитектура

```
┌─────────────────┐
│  Telegram Bot   │ ─┐
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌──────────────────┐
│   Web Client    │ ─┼───→│  Backend API     │
└─────────────────┘  │    │  (Cloud Funcs)   │
                     │    └──────────────────┘
┌─────────────────┐  │             ↓
│  Admin Panel    │ ─┘    ┌──────────────────┐
└─────────────────┘       │   PostgreSQL     │
                          └──────────────────┘
         ↑                         ↓
         └─────────────────────────┘
              Webhooks & Sync
```

## 📋 База данных

**8 таблиц:**
- `clients` - клиенты с Telegram ID
- `executors` - мастера с рейтингом и геолокацией
- `services` - каталог услуг (6 услуг предустановлено)
- `orders` - заказы с статусами
- `order_services` - связь заказов и услуг
- `order_status_history` - полная история изменений
- `reviews` - отзывы клиентов
- `admin_users` - администраторы

**Статусы заказов:** new → assigned → in_progress → on_way → completed

## 🔌 Интеграции (готовые endpoints)

### ✅ Реализовано:
- REST API для создания и управления заказами
- Webhook приемник для Planfix
- Структура БД для всех интеграций

### 📝 Требует настройки:
- **Telegram Bot** - создать бота через @BotFather, настроить Web App URL
- **Planfix API** - получить API ключ, настроить webhook на наш endpoint
- **Google Tasks** - создать Service Account, выдать доступы
- **WhatsApp Business** - зарегистрировать в Meta Business, создать шаблоны сообщений

Подробные инструкции: [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)

## 🛠️ Технологии

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS
- Vite
- shadcn/ui компоненты

**Backend:**
- Python 3.11
- Cloud Functions (serverless)
- PostgreSQL
- psycopg2 для работы с БД

**Интеграции:**
- Telegram Bot API
- Planfix REST API
- Google Tasks API
- WhatsApp Business API

## 🎯 Сценарии использования

### 1. Клиент заказывает услугу
```
Telegram Web App → POST /create-order → БД
→ Webhook Planfix → Создание задачи
→ Автоназначение мастера → Уведомление клиенту
```

### 2. Мастер работает с заказом
```
Google Tasks виджет → Получение задачи
→ Обновление статуса → POST /update-order-status
→ БД + история → Уведомление клиенту
```

### 3. Админ управляет заказами
```
/admin → Список заказов с фильтрами
→ Изменение статуса → POST /update-order-status
→ Просмотр деталей → Назначение мастера
```

## 📊 KPI и мониторинг

Готовые метрики для отслеживания:
- Количество заказов по статусам
- Среднее время обработки
- Рейтинги исполнителей
- История изменений (полный аудит)

## 🚀 Развертывание на Timeweb

1. Скачать код проекта
2. Настроить переменные окружения (DATABASE_URL, API ключи)
3. Применить миграции: `db_migrations/V0001__initial_schema_orders_system.sql`
4. Развернуть backend функции (уже задеплоены в Cloud)
5. Собрать frontend: `npm run build`
6. Загрузить на хостинг

Все функции уже работают в облаке poehali.dev и готовы к использованию!

## 📞 Контакты

- Telegram: @konigelectric
- Телефон: +7 (4012) 52-07-25
- Калининград

## 🗺️ Дорожная карта

### MVP ✅ (Готово)
- [x] Схема БД с миграциями
- [x] Backend API (5 функций)
- [x] Веб-интерфейс клиента
- [x] Админ-панель
- [x] Webhook для Planfix

### Этап 2 (Следующий)
- [ ] Подключение Telegram Bot
- [ ] Интеграция Planfix API
- [ ] Интеграция Google Tasks
- [ ] WhatsApp уведомления
- [ ] Автораспределение мастеров

### Этап 3 (Будущее)
- [ ] Геолокация и карты
- [ ] Мобильное приложение
- [ ] Система лояльности
- [ ] Расширенная аналитика
- [ ] Multi-тенантность (несколько компаний)

---

**Система готова к интеграциям!** Все базовые компоненты работают, осталось подключить внешние сервисы.
