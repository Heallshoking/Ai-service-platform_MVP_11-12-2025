-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    phone VARCHAR(20),
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Executors (masters) table
CREATE TABLE IF NOT EXISTS executors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    telegram_id BIGINT,
    rating DECIMAL(3,2) DEFAULT 5.0,
    experience_years INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    current_location_lat DECIMAL(10,8),
    current_location_lng DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Services table
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2),
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id),
    executor_id INT REFERENCES executors(id),
    status VARCHAR(50) DEFAULT 'new',
    address TEXT NOT NULL,
    location_lat DECIMAL(10,8),
    location_lng DECIMAL(11,8),
    scheduled_date DATE,
    scheduled_time TIME,
    total_price DECIMAL(10,2),
    client_notes TEXT,
    planfix_task_id VARCHAR(100),
    google_task_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order services (many-to-many)
CREATE TABLE IF NOT EXISTS order_services (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    service_id INT REFERENCES services(id),
    quantity INT DEFAULT 1,
    price DECIMAL(10,2),
    notes TEXT
);

-- Status history
CREATE TABLE IF NOT EXISTS order_status_history (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    status VARCHAR(50) NOT NULL,
    comment TEXT,
    changed_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    executor_id INT REFERENCES executors(id),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin users
CREATE TABLE IF NOT EXISTS admin_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial services
INSERT INTO services (name, description, base_price, category) VALUES
('Установка розетки', 'Установка одной розетки', 500, 'installation'),
('Установка выключателя', 'Установка одного выключателя', 450, 'installation'),
('Установка люстры', 'Установка люстры или светильника', 800, 'installation'),
('Замена электропроводки', 'Полная или частичная замена проводки', 5000, 'wiring'),
('Монтаж щитка', 'Установка электрического щитка', 3000, 'wiring'),
('Установка автомата защиты', 'Монтаж автоматического выключателя', 600, 'installation');

-- Insert test executor
INSERT INTO executors (name, phone, experience_years, rating) VALUES
('Алексей Иванов', '+79991234567', 12, 4.9);
