-- Таблица пользователей с ролями
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'client' CHECK (role IN ('client', 'executor', 'admin', 'owner')),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Связь пользователя с исполнителем (если роль executor)
ALTER TABLE executors ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

-- Календарь исполнителя
CREATE TABLE IF NOT EXISTS executor_calendar (
    id SERIAL PRIMARY KEY,
    executor_id INTEGER REFERENCES executors(id),
    date DATE NOT NULL,
    time_slot VARCHAR(10) NOT NULL,
    is_available BOOLEAN DEFAULT true,
    order_id INTEGER REFERENCES orders(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(executor_id, date, time_slot)
);

-- Сообщения между пользователями
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    from_user_id INTEGER REFERENCES users(id),
    to_user_id INTEGER REFERENCES users(id),
    order_id INTEGER REFERENCES orders(id),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Объявления исполнителей
CREATE TABLE IF NOT EXISTS executor_ads (
    id SERIAL PRIMARY KEY,
    executor_id INTEGER REFERENCES executors(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price_from DECIMAL(10,2),
    price_to DECIMAL(10,2),
    is_active BOOLEAN DEFAULT true,
    avito_published BOOLEAN DEFAULT false,
    avito_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Запросы предложений для исполнителей
CREATE TABLE IF NOT EXISTS order_proposals (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    executor_id INTEGER REFERENCES executors(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(order_id, executor_id)
);

-- Настройки доставки материалов
CREATE TABLE IF NOT EXISTS material_delivery_settings (
    id SERIAL PRIMARY KEY,
    executor_id INTEGER REFERENCES executors(id),
    vk_group_url TEXT,
    delivery_address TEXT,
    preferred_suppliers TEXT[],
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_messages_from_user ON messages(from_user_id);
CREATE INDEX IF NOT EXISTS idx_messages_to_user ON messages(to_user_id);
CREATE INDEX IF NOT EXISTS idx_messages_order ON messages(order_id);
CREATE INDEX IF NOT EXISTS idx_calendar_executor ON executor_calendar(executor_id);
CREATE INDEX IF NOT EXISTS idx_calendar_date ON executor_calendar(date);
CREATE INDEX IF NOT EXISTS idx_proposals_order ON order_proposals(order_id);
CREATE INDEX IF NOT EXISTS idx_proposals_executor ON order_proposals(executor_id);