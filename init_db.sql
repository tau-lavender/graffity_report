-- Enable PostGIS extension for geography/geometry types
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users table: stores Telegram user data
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Graffiti reports table: main application data
CREATE TABLE IF NOT EXISTS graffiti_reports (
    report_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    location GEOGRAPHY(POINT, 4326),
    fias_id UUID,
    normalized_address TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'declined')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Report photos table: S3/MinIO object keys for uploaded images
CREATE TABLE IF NOT EXISTS report_photos (
    photo_id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES graffiti_reports(report_id),
    s3_key VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

-- Spatial index for efficient location queries
CREATE INDEX IF NOT EXISTS idx_reports_location ON graffiti_reports USING GIST (location);

-- Optional: index for soft-delete filtering
CREATE INDEX IF NOT EXISTS idx_users_active ON users (is_deleted);
CREATE INDEX IF NOT EXISTS idx_reports_active ON graffiti_reports (is_deleted);
CREATE INDEX IF NOT EXISTS idx_photos_active ON report_photos (is_deleted);