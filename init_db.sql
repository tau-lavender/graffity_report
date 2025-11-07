CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS graffiti_reports (
    report_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    location GEOGRAPHY(POINT, 4326),
    fias_id UUID,
    normalized_address TEXT,
    status VARCHAR(20) DEFAULT 'новая' CHECK (status IN ('новая', 'в работе', 'решена')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report_photos (
    photo_id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES graffiti_reports(report_id) ON DELETE CASCADE,
    s3_key VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_location ON graffiti_reports USING GIST (location);