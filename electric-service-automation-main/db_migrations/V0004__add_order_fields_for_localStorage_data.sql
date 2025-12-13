-- Добавляем поля для хранения всех данных заявок из localStorage

-- Контактные данные клиента
ALTER TABLE t_p78209571_electric_service_aut.orders 
ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(50),
ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255);

-- Данные заявки
ALTER TABLE t_p78209571_electric_service_aut.orders
ADD COLUMN IF NOT EXISTS order_uid VARCHAR(100) UNIQUE,
ADD COLUMN IF NOT EXISTS items JSONB,
ADD COLUMN IF NOT EXISTS total_switches INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_outlets INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_points INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS estimated_cable INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS estimated_frames INTEGER DEFAULT 0;

-- Дополнительная информация
ALTER TABLE t_p78209571_electric_service_aut.orders
ADD COLUMN IF NOT EXISTS preferred_date VARCHAR(50),
ADD COLUMN IF NOT EXISTS time_slot VARCHAR(50),
ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(100),
ADD COLUMN IF NOT EXISTS assigned_to_name VARCHAR(255);

-- Статусы оплаты
ALTER TABLE t_p78209571_electric_service_aut.orders
ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'unpaid',
ADD COLUMN IF NOT EXISTS paid_amount NUMERIC(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS payments JSONB;

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_orders_order_uid ON t_p78209571_electric_service_aut.orders(order_uid);
CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON t_p78209571_electric_service_aut.orders(customer_phone);
CREATE INDEX IF NOT EXISTS idx_orders_status ON t_p78209571_electric_service_aut.orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_assigned_to ON t_p78209571_electric_service_aut.orders(assigned_to);
CREATE INDEX IF NOT EXISTS idx_orders_planfix_task_id ON t_p78209571_electric_service_aut.orders(planfix_task_id);

-- Комментарий к таблице
COMMENT ON COLUMN t_p78209571_electric_service_aut.orders.order_uid IS 'Уникальный ID заявки в формате ORD-timestamp';
COMMENT ON COLUMN t_p78209571_electric_service_aut.orders.items IS 'JSON массив услуг: [{name, price, quantity, category, description}]';
COMMENT ON COLUMN t_p78209571_electric_service_aut.orders.payments IS 'JSON массив платежей: [{id, amount, method, status, createdAt}]';
