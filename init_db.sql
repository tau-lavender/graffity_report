-- Enable PostGIS extension for geography/geometry types
CREATE EXTENSION IF NOT EXISTS postgis;

-- Users table: stores Telegram user data
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Graffiti reports table: main application data
CREATE TABLE IF NOT EXISTS graffiti_reports (
    report_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    location GEOGRAPHY(POINT, 4326),
    fias_id UUID,
    normalized_address TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'declined')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Report photos table: S3/MinIO object keys for uploaded images
CREATE TABLE IF NOT EXISTS report_photos (
    photo_id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES graffiti_reports(report_id) ON DELETE CASCADE,
    s3_key VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Spatial index for efficient location queries
CREATE INDEX IF NOT EXISTS idx_reports_location ON graffiti_reports USING GIST (location);
