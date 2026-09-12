-- Seed Fani, Remal, Mocha, Michaung
INSERT INTO cyclones (id, name, basin, start_time, end_time, is_active) VALUES
('CYC-2024-BOB-REMAL', 'Remal', 'Bay of Bengal', '2024-05-24 00:00:00+00', '2024-05-28 12:00:00+00', false),
('CYC-2023-BOB-MICHAUNG', 'Michaung', 'Bay of Bengal', '2023-12-01 00:00:00+00', '2023-12-06 06:00:00+00', false),
('CYC-2023-BOB-MOCHA', 'Mocha', 'Bay of Bengal', '2023-05-09 00:00:00+00', '2023-05-15 12:00:00+00', false),
('CYC-2019-BOB-FANI', 'Fani', 'Bay of Bengal', '2019-04-26 00:00:00+00', '2019-05-04 18:00:00+00', false)
ON CONFLICT (id) DO NOTHING;

-- Observations for Remal
INSERT INTO observations (cyclone_id, timestamp, latitude, longitude, wind_speed, pressure, classification, source) VALUES
('CYC-2024-BOB-REMAL', '2024-05-24 12:00:00+00', 15.2, 88.5, 25.0, 1002.0, 'Depression', 'IMD_OFFICIAL'),
('CYC-2024-BOB-REMAL', '2024-05-25 00:00:00+00', 16.8, 89.1, 35.0, 996.0, 'Deep Depression', 'IMD_OFFICIAL'),
('CYC-2024-BOB-REMAL', '2024-05-25 18:00:00+00', 18.5, 89.5, 45.0, 990.0, 'Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2024-BOB-REMAL', '2024-05-26 06:00:00+00', 20.2, 89.4, 60.0, 982.0, 'Severe Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2024-BOB-REMAL', '2024-05-26 18:00:00+00', 21.9, 89.2, 65.0, 978.0, 'Severe Cyclonic Storm', 'IMD_OFFICIAL')
ON CONFLICT DO NOTHING;

-- Observations for Fani
INSERT INTO observations (cyclone_id, timestamp, latitude, longitude, wind_speed, pressure, classification, source) VALUES
('CYC-2019-BOB-FANI', '2019-04-27 00:00:00+00', 5.2, 88.5, 25.0, 1004.0, 'Depression', 'IMD_OFFICIAL'),
('CYC-2019-BOB-FANI', '2019-04-28 12:00:00+00', 8.1, 87.2, 40.0, 996.0, 'Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2019-BOB-FANI', '2019-04-30 06:00:00+00', 11.9, 84.8, 75.0, 974.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2019-BOB-FANI', '2019-05-02 00:00:00+00', 15.8, 84.6, 115.0, 938.0, 'Extremely Severe Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2019-BOB-FANI', '2019-05-03 03:00:00+00', 19.8, 85.8, 100.0, 950.0, 'Extremely Severe Cyclonic Storm', 'IMD_OFFICIAL')
ON CONFLICT DO NOTHING;

-- Observations for Mocha
INSERT INTO observations (cyclone_id, timestamp, latitude, longitude, wind_speed, pressure, classification, source) VALUES
('CYC-2023-BOB-MOCHA', '2023-05-09 12:00:00+00', 8.5, 89.0, 25.0, 1004.0, 'Depression', 'IMD_OFFICIAL'),
('CYC-2023-BOB-MOCHA', '2023-05-11 00:00:00+00', 11.5, 88.0, 45.0, 994.0, 'Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2023-BOB-MOCHA', '2023-05-12 12:00:00+00', 14.0, 88.5, 80.0, 966.0, 'Very Severe Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2023-BOB-MOCHA', '2023-05-13 18:00:00+00', 17.5, 91.0, 130.0, 928.0, 'Super Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2023-BOB-MOCHA', '2023-05-14 06:00:00+00', 20.1, 92.8, 115.0, 940.0, 'Extremely Severe Cyclonic Storm', 'IMD_OFFICIAL')
ON CONFLICT DO NOTHING;

-- Observations for Michaung
INSERT INTO observations (cyclone_id, timestamp, latitude, longitude, wind_speed, pressure, classification, source) VALUES
('CYC-2023-BOB-MICHAUNG', '2023-12-01 12:00:00+00', 9.5, 86.0, 25.0, 1004.0, 'Depression', 'IMD_OFFICIAL'),
('CYC-2023-BOB-MICHAUNG', '2023-12-03 00:00:00+00', 12.0, 82.5, 45.0, 996.0, 'Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2023-BOB-MICHAUNG', '2023-12-04 12:00:00+00', 14.5, 80.5, 60.0, 988.0, 'Severe Cyclonic Storm', 'IMD_OFFICIAL'),
('CYC-2023-BOB-MICHAUNG', '2023-12-05 06:00:00+00', 15.8, 80.3, 55.0, 990.0, 'Severe Cyclonic Storm', 'IMD_OFFICIAL')
ON CONFLICT DO NOTHING;
