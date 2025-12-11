-- ============================================
-- Supabase Schema for Vinyl Marketplace
-- ============================================
-- Схема базы данных для винилового маркетплейса
-- Выполните этот скрипт в Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Table: profiles
-- ============================================
-- Профили пользователей, связанные с Telegram ID

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username TEXT,
    full_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table: records
-- ============================================
-- Каталог виниловых пластинок

CREATE TABLE records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    genre TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year >= 1900 AND year <= 2100),
    label TEXT,
    country TEXT NOT NULL,
    condition TEXT NOT NULL,
    price NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    description TEXT,
    image_url TEXT,
    custom_image BOOLEAN DEFAULT FALSE,
    custom_description BOOLEAN DEFAULT FALSE,
    status TEXT DEFAULT 'available',
    seller_telegram_id BIGINT,
    import_source TEXT DEFAULT 'manual',
    google_sheets_row INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table: import_logs
-- ============================================
-- Логи импорта из Google Sheets

CREATE TABLE import_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    errors TEXT,
    admin_telegram_id BIGINT NOT NULL,
    duration_seconds NUMERIC
);

-- ============================================
-- Indexes for Performance
-- ============================================

CREATE INDEX idx_records_genre ON records(genre);
CREATE INDEX idx_records_year ON records(year);
CREATE INDEX idx_records_status ON records(status);
CREATE INDEX idx_records_artist ON records(artist);
CREATE INDEX idx_records_title ON records(title);
CREATE INDEX idx_records_composite ON records(genre, year, status);
CREATE INDEX idx_profiles_telegram_id ON profiles(telegram_id);

-- ============================================
-- Triggers
-- ============================================

-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применяем триггер к таблицам
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_records_updated_at
    BEFORE UPDATE ON records
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Row-Level Security Policies
-- ============================================

-- Включаем RLS для всех таблиц
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE records ENABLE ROW LEVEL SECURITY;
ALTER TABLE import_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Policies for profiles table
-- ============================================

-- Публичное чтение профилей
CREATE POLICY "public_read_profiles" ON profiles
    FOR SELECT USING (true);

-- Пользователь может обновлять свой профиль
CREATE POLICY "user_update_own_profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Админ может делать всё с профилями
CREATE POLICY "admin_all_profiles" ON profiles
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================
-- Policies for records table
-- ============================================

-- Публичное чтение доступных записей
CREATE POLICY "public_read_available_records" ON records
    FOR SELECT USING (status = 'available');

-- Аутентифицированные пользователи видят все записи
CREATE POLICY "authenticated_read_all_records" ON records
    FOR SELECT USING (auth.role() = 'authenticated');

-- Только админ может создавать записи
CREATE POLICY "admin_insert_records" ON records
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Админ может обновлять любые записи
CREATE POLICY "admin_update_records" ON records
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- Владелец может обновлять кастомные поля своих записей
CREATE POLICY "owner_update_custom_fields" ON records
    FOR UPDATE USING (
        seller_telegram_id IN (
            SELECT telegram_id FROM profiles WHERE id = auth.uid()
        )
    );

-- Только админ может удалять записи
CREATE POLICY "admin_delete_records" ON records
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================
-- Policies for import_logs table
-- ============================================

-- Только админ имеет доступ к логам импорта
CREATE POLICY "admin_all_import_logs" ON import_logs
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE id = auth.uid() AND is_admin = true
        )
    );

-- ============================================
-- Initial Data (Optional)
-- ============================================

-- Вы можете добавить тестовые данные здесь
-- Например:
-- INSERT INTO records (title, artist, genre, year, country, condition, price, status)
-- VALUES ('The Dark Side of the Moon', 'Pink Floyd', 'Progressive Rock', 1973, 'UK', 'Near Mint', 4500.00, 'available');

-- ============================================
-- Comments for Documentation
-- ============================================

COMMENT ON TABLE profiles IS 'Профили пользователей, связанные с Telegram ID';
COMMENT ON TABLE records IS 'Каталог виниловых пластинок';
COMMENT ON TABLE import_logs IS 'Логи импорта данных из Google Sheets';

COMMENT ON COLUMN records.custom_image IS 'Флаг ручного редактирования изображения (защита от перезаписи при импорте)';
COMMENT ON COLUMN records.custom_description IS 'Флаг ручного редактирования описания (защита от AI генерации)';
COMMENT ON COLUMN records.import_source IS 'Источник записи: manual, sheets_import';
COMMENT ON COLUMN records.google_sheets_row IS 'Номер строки в Google Sheets для синхронизации';
