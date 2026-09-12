-- 01-init-postgis.sql: Initialize PostGIS extensions and baseline schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS postgis;

-- Cyclones Registry
CREATE TABLE IF NOT EXISTS cyclones (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(100),
    basin VARCHAR(50) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Official & Sensor Ground-Truth Observations (Never mix with predictions)
CREATE TABLE IF NOT EXISTS observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cyclone_id VARCHAR(64) REFERENCES cyclones(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    geom GEOMETRY(Point, 4326),
    wind_speed DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    classification VARCHAR(50),
    source VARCHAR(50) NOT NULL DEFAULT 'IMD_OFFICIAL',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Satellite Image Metadata (Image rasters stored on disk volume, never directly in SQL)
CREATE TABLE IF NOT EXISTS satellite_images (
    id VARCHAR(64) PRIMARY KEY,
    cyclone_id VARCHAR(64) REFERENCES cyclones(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    satellite VARCHAR(50) NOT NULL,
    sensor VARCHAR(50) NOT NULL,
    channel VARCHAR(30) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    resolution_km DOUBLE PRECISION DEFAULT 4.0,
    min_lat DOUBLE PRECISION,
    min_lon DOUBLE PRECISION,
    max_lat DOUBLE PRECISION,
    max_lon DOUBLE PRECISION,
    bbox_geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detection Results (Member 1 Output)
CREATE TABLE IF NOT EXISTS detection_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id VARCHAR(64) REFERENCES satellite_images(id) ON DELETE CASCADE,
    detected BOOLEAN NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    center_geom GEOMETRY(Point, 4326),
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    bbox_coordinates JSONB,
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Classification Results (Member 1 Output)
CREATE TABLE IF NOT EXISTS classification_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    image_id VARCHAR(64) REFERENCES satellite_images(id) ON DELETE CASCADE,
    cyclone_id VARCHAR(64) REFERENCES cyclones(id) ON DELETE SET NULL,
    classification VARCHAR(50) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    estimated_wind_speed DOUBLE PRECISION,
    class_probabilities JSONB,
    explainability_file_path VARCHAR(512),
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Forecasts (Member 2 Output - Strictly Separated from Observations)
CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cyclone_id VARCHAR(64) REFERENCES cyclones(id) ON DELETE CASCADE,
    forecast_time TIMESTAMPTZ NOT NULL,
    target_time TIMESTAMPTZ NOT NULL,
    lead_hours INTEGER NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    point_geom GEOMETRY(Point, 4326),
    predicted_wind_speed DOUBLE PRECISION,
    predicted_pressure DOUBLE PRECISION,
    uncertainty_radius_km DOUBLE PRECISION DEFAULT 30.0,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model Registry & Performance Metrics
CREATE TABLE IF NOT EXISTS models (
    id VARCHAR(64) PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    metrics JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial & Temporal Indexes
CREATE INDEX IF NOT EXISTS idx_observations_geom ON observations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_observations_cyclone_time ON observations (cyclone_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_satellite_images_bbox ON satellite_images USING GIST (bbox_geom);
CREATE INDEX IF NOT EXISTS idx_forecasts_point_geom ON forecasts USING GIST (point_geom);
CREATE INDEX IF NOT EXISTS idx_forecasts_cyclone_target ON forecasts (cyclone_id, target_time);
