-- 02-seed-historical.sql: Seed initial realistic historical cyclone scenarios

-- Seed Model Registry
INSERT INTO models (id, service_name, version, description, metrics, is_active)
VALUES
    ('m1-det-v1.0', 'ml-detection', 'v1.0.0', 'YOLOv8-based Tropical Cyclone Center Detector', '{"precision": 0.93, "recall": 0.91, "f1": 0.92, "center_error_km": 28.5}', TRUE),
    ('m1-cls-v1.0', 'ml-classification', 'v1.0.0', 'ResNet50 + Dvorak Guided Intensity Classifier', '{"accuracy": 0.88, "macro_f1": 0.86, "mae_knots": 6.8}', TRUE),
    ('m2-fc-v1.0', 'ml-prediction', 'v1.0.0', 'Temporal Fusion Transformer (TFT) Multi-lead Forecaster', '{"track_error_24h_km": 68.2, "track_error_48h_km": 124.5, "intensity_mae_knots": 8.1}', TRUE)
ON CONFLICT (id) DO NOTHING;

-- Seed Cyclone Biparjoy (Arabian Sea, June 2023)
INSERT INTO cyclones (id, name, basin, start_time, end_time, is_active)
VALUES
    ('CYC-2023-ARB-01', 'Biparjoy', 'Arabian Sea', '2023-06-06 00:00:00+00', '2023-06-19 12:00:00+00', FALSE),
    ('CYC-2020-BOB-01', 'Amphan', 'Bay of Bengal', '2020-05-16 00:00:00+00', '2020-05-21 18:00:00+00', FALSE),
    ('CYC-2026-NIO-DEMO', 'Active System 01A', 'Bay of Bengal', '2026-09-02 06:00:00+00', NULL, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Seed Observations for Biparjoy (Sample observed track)
INSERT INTO observations (cyclone_id, timestamp, latitude, longitude, geom, wind_speed, pressure, classification, source)
VALUES
    ('CYC-2023-ARB-01', '2023-06-06 06:00:00+00', 11.5, 66.0, ST_SetSRID(ST_MakePoint(66.0, 11.5), 4326), 35.0, 1000.0, 'Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2023-ARB-01', '2023-06-07 00:00:00+00', 12.6, 66.2, ST_SetSRID(ST_MakePoint(66.2, 12.6), 4326), 50.0, 992.0, 'Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2023-ARB-01', '2023-06-08 00:00:00+00', 14.0, 66.0, ST_SetSRID(ST_MakePoint(66.0, 14.0), 4326), 75.0, 978.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2023-ARB-01', '2023-06-09 06:00:00+00', 15.1, 66.5, ST_SetSRID(ST_MakePoint(66.5, 15.1), 4326), 85.0, 970.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2023-ARB-01', '2023-06-11 00:00:00+00', 18.0, 67.8, ST_SetSRID(ST_MakePoint(67.8, 18.0), 4326), 90.0, 966.0, 'Extremely Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2023-ARB-01', '2023-06-12 12:00:00+00', 19.4, 67.7, ST_SetSRID(ST_MakePoint(67.7, 19.4), 4326), 85.0, 970.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2023-ARB-01', '2023-06-14 00:00:00+00', 21.8, 66.6, ST_SetSRID(ST_MakePoint(66.6, 21.8), 4326), 75.0, 978.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2023-ARB-01', '2023-06-15 12:00:00+00', 23.2, 68.3, ST_SetSRID(ST_MakePoint(68.3, 23.2), 4326), 65.0, 982.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL');

-- Seed Observations for Active System 01A
INSERT INTO observations (cyclone_id, timestamp, latitude, longitude, geom, wind_speed, pressure, classification, source)
VALUES
    ('CYC-2026-NIO-DEMO', '2026-09-02 06:00:00+00', 13.2, 84.5, ST_SetSRID(ST_MakePoint(84.5, 13.2), 4326), 25.0, 1004.0, 'Depression', 'IMD_OFFICIAL'),
    ('CYC-2026-NIO-DEMO', '2026-09-02 18:00:00+00', 14.0, 85.1, ST_SetSRID(ST_MakePoint(85.1, 14.0), 4326), 30.0, 1000.0, 'Deep Depression', 'IMD_OFFICIAL'),
    ('CYC-2026-NIO-DEMO', '2026-09-03 06:00:00+00', 14.9, 85.8, ST_SetSRID(ST_MakePoint(85.8, 14.9), 4326), 40.0, 994.0, 'Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2026-NIO-DEMO', '2026-09-03 18:00:00+00', 15.8, 86.4, ST_SetSRID(ST_MakePoint(86.4, 15.8), 4326), 55.0, 986.0, 'Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2026-NIO-DEMO', '2026-09-04 06:00:00+00', 16.7, 87.0, ST_SetSRID(ST_MakePoint(87.0, 16.7), 4326), 70.0, 976.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL'),
    ('CYC-2026-NIO-DEMO', '2026-09-04 12:00:00+00', 17.2, 87.3, ST_SetSRID(ST_MakePoint(87.3, 17.2), 4326), 75.0, 972.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL');

-- Seed Satellite Images
INSERT INTO satellite_images (id, cyclone_id, timestamp, satellite, sensor, channel, file_path, resolution_km, bbox_geom)
VALUES
    ('SAT-INSAT3D-20260904-1200', 'CYC-2026-NIO-DEMO', '2026-09-04 12:00:00+00', 'INSAT-3D', 'IMAGER', 'TIR1', 'insat3d_20260904_1200_tir1.png', 4.0, ST_MakeEnvelope(80.0, 10.0, 94.0, 24.0, 4326)),
    ('SAT-INSAT3D-20260904-0600', 'CYC-2026-NIO-DEMO', '2026-09-04 06:00:00+00', 'INSAT-3D', 'IMAGER', 'TIR1', 'insat3d_20260904_0600_tir1.png', 4.0, ST_MakeEnvelope(80.0, 10.0, 94.0, 24.0, 4326)),
    ('SAT-INSAT3D-20230612-1200', 'CYC-2023-ARB-01', '2023-06-12 12:00:00+00', 'INSAT-3D', 'IMAGER', 'TIR1', 'insat3d_biparjoy_tir1.png', 4.0, ST_MakeEnvelope(60.0, 12.0, 75.0, 26.0, 4326))
ON CONFLICT (id) DO NOTHING;
