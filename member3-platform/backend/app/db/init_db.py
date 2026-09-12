"""
Database seeding utility for initial realistic cyclone scenarios.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone
from app.models.cyclone import Cyclone
from app.models.observation import Observation
from app.models.satellite_image import SatelliteImage
from app.models.forecast import ModelRegistry
from app.core.logging import logger

async def seed_initial_data(db: AsyncSession):
    """Seed initial cyclones and observations if database is currently unseeded."""
    try:
        count_res = await db.execute(select(func.count()).select_from(Cyclone))
        count = count_res.scalar()
        if count and count > 0:
            logger.info("Database already contains cyclone records. Skipping seed.")
            return

        logger.info("Seeding initial historical and active cyclone scenarios...")

        # 1. Models Registry
        m1_det = ModelRegistry(id="m1-det-v1.0", service_name="ml-detection", version="v1.0.0", description="YOLOv8 Cyclone Eye Detector", metrics={"precision": 0.949, "recall": 0.923})
        m1_cls = ModelRegistry(id="m1-cls-v1.0", service_name="ml-classification", version="v1.0.0", description="ResNet50 IMD Stage Classifier", metrics={"accuracy": 0.889, "macro_f1": 0.871})
        m2_fc = ModelRegistry(id="m2-fc-v1.0", service_name="ml-prediction", version="v1.0.0", description="GRU Multi-Lead Trajectory Forecaster", metrics={"track_error_24h_km": 54.8, "track_error_48h_km": 92.4})
        db.add_all([m1_det, m1_cls, m2_fc])

        # 2. Cyclone Registry Catalog
        cyclones = [
            Cyclone(id="CYC-2026-NIO-DEMO", name="Active System 01A", basin="Bay of Bengal", start_time=datetime(2026, 9, 2, 6, 0, tzinfo=timezone.utc), is_active=True),
            Cyclone(id="CYC-2024-BOB-REMAL", name="Remal", basin="Bay of Bengal", start_time=datetime(2024, 5, 24, 0, 0, tzinfo=timezone.utc), end_time=datetime(2024, 5, 28, 12, 0, tzinfo=timezone.utc), is_active=False),
            Cyclone(id="CYC-2023-ARB-01", name="Biparjoy", basin="Arabian Sea", start_time=datetime(2023, 6, 6, 0, 0, tzinfo=timezone.utc), end_time=datetime(2023, 6, 19, 12, 0, tzinfo=timezone.utc), is_active=False),
            Cyclone(id="CYC-2023-BOB-MICHAUNG", name="Michaung", basin="Bay of Bengal", start_time=datetime(2023, 12, 1, 0, 0, tzinfo=timezone.utc), end_time=datetime(2023, 12, 6, 6, 0, tzinfo=timezone.utc), is_active=False),
            Cyclone(id="CYC-2023-BOB-MOCHA", name="Mocha", basin="Bay of Bengal", start_time=datetime(2023, 5, 9, 0, 0, tzinfo=timezone.utc), end_time=datetime(2023, 5, 15, 12, 0, tzinfo=timezone.utc), is_active=False),
            Cyclone(id="CYC-2020-BOB-01", name="Amphan", basin="Bay of Bengal", start_time=datetime(2020, 5, 16, 0, 0, tzinfo=timezone.utc), end_time=datetime(2020, 5, 21, 18, 0, tzinfo=timezone.utc), is_active=False),
            Cyclone(id="CYC-2019-BOB-FANI", name="Fani", basin="Bay of Bengal", start_time=datetime(2019, 4, 26, 0, 0, tzinfo=timezone.utc), end_time=datetime(2019, 5, 4, 18, 0, tzinfo=timezone.utc), is_active=False),
        ]
        db.add_all(cyclones)
        await db.flush()

        # 3. Rich Historical Observations
        observations = [
            # Active System 01A
            Observation(cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 2, 6, 0, tzinfo=timezone.utc), latitude=13.2, longitude=84.5, wind_speed=25.0, pressure=1004.0, classification="Depression", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 2, 18, 0, tzinfo=timezone.utc), latitude=14.0, longitude=85.1, wind_speed=30.0, pressure=1000.0, classification="Deep Depression", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 3, 6, 0, tzinfo=timezone.utc), latitude=14.9, longitude=85.8, wind_speed=40.0, pressure=994.0, classification="Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 3, 18, 0, tzinfo=timezone.utc), latitude=15.8, longitude=86.4, wind_speed=55.0, pressure=986.0, classification="Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 4, 6, 0, tzinfo=timezone.utc), latitude=16.7, longitude=87.0, wind_speed=70.0, pressure=976.0, classification="Very Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc), latitude=17.2, longitude=87.3, wind_speed=75.0, pressure=972.0, classification="Very Severe Cyclonic Storm", source="IMD_OFFICIAL"),

            # Remal (2024)
            Observation(cyclone_id="CYC-2024-BOB-REMAL", timestamp=datetime(2024, 5, 24, 12, 0, tzinfo=timezone.utc), latitude=15.2, longitude=88.5, wind_speed=25.0, pressure=1002.0, classification="Depression", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2024-BOB-REMAL", timestamp=datetime(2024, 5, 25, 0, 0, tzinfo=timezone.utc), latitude=16.8, longitude=89.1, wind_speed=35.0, pressure=996.0, classification="Deep Depression", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2024-BOB-REMAL", timestamp=datetime(2024, 5, 25, 18, 0, tzinfo=timezone.utc), latitude=18.5, longitude=89.5, wind_speed=45.0, pressure=990.0, classification="Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2024-BOB-REMAL", timestamp=datetime(2024, 5, 26, 6, 0, tzinfo=timezone.utc), latitude=20.2, longitude=89.4, wind_speed=60.0, pressure=982.0, classification="Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2024-BOB-REMAL", timestamp=datetime(2024, 5, 26, 18, 0, tzinfo=timezone.utc), latitude=21.9, longitude=89.2, wind_speed=65.0, pressure=978.0, classification="Severe Cyclonic Storm", source="IMD_OFFICIAL"),

            # Biparjoy (2023)
            Observation(cyclone_id="CYC-2023-ARB-01", timestamp=datetime(2023, 6, 6, 12, 0, tzinfo=timezone.utc), latitude=12.1, longitude=66.0, wind_speed=30.0, pressure=1000.0, classification="Deep Depression", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2023-ARB-01", timestamp=datetime(2023, 6, 7, 12, 0, tzinfo=timezone.utc), latitude=13.5, longitude=66.2, wind_speed=55.0, pressure=988.0, classification="Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2023-ARB-01", timestamp=datetime(2023, 6, 9, 6, 0, tzinfo=timezone.utc), latitude=15.2, longitude=66.7, wind_speed=80.0, pressure=968.0, classification="Very Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2023-ARB-01", timestamp=datetime(2023, 6, 11, 12, 0, tzinfo=timezone.utc), latitude=18.4, longitude=67.8, wind_speed=90.0, pressure=954.0, classification="Extremely Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2023-ARB-01", timestamp=datetime(2023, 6, 14, 18, 0, tzinfo=timezone.utc), latitude=22.5, longitude=68.2, wind_speed=70.0, pressure=972.0, classification="Very Severe Cyclonic Storm", source="IMD_OFFICIAL"),

            # Fani (2019)
            Observation(cyclone_id="CYC-2019-BOB-FANI", timestamp=datetime(2019, 4, 27, 0, 0, tzinfo=timezone.utc), latitude=5.2, longitude=88.5, wind_speed=25.0, pressure=1004.0, classification="Depression", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2019-BOB-FANI", timestamp=datetime(2019, 4, 28, 12, 0, tzinfo=timezone.utc), latitude=8.1, longitude=87.2, wind_speed=40.0, pressure=996.0, classification="Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2019-BOB-FANI", timestamp=datetime(2019, 4, 30, 6, 0, tzinfo=timezone.utc), latitude=11.9, longitude=84.8, wind_speed=75.0, pressure=974.0, classification="Very Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2019-BOB-FANI", timestamp=datetime(2019, 5, 2, 0, 0, tzinfo=timezone.utc), latitude=15.8, longitude=84.6, wind_speed=115.0, pressure=938.0, classification="Extremely Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2019-BOB-FANI", timestamp=datetime(2019, 5, 3, 3, 0, tzinfo=timezone.utc), latitude=19.8, longitude=85.8, wind_speed=100.0, pressure=950.0, classification="Extremely Severe Cyclonic Storm", source="IMD_OFFICIAL"),

            # Amphan (2020)
            Observation(cyclone_id="CYC-2020-BOB-01", timestamp=datetime(2020, 5, 16, 6, 0, tzinfo=timezone.utc), latitude=10.4, longitude=86.8, wind_speed=30.0, pressure=1000.0, classification="Deep Depression", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2020-BOB-01", timestamp=datetime(2020, 5, 17, 12, 0, tzinfo=timezone.utc), latitude=12.2, longitude=86.3, wind_speed=65.0, pressure=982.0, classification="Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2020-BOB-01", timestamp=datetime(2020, 5, 18, 12, 0, tzinfo=timezone.utc), latitude=14.0, longitude=86.3, wind_speed=130.0, pressure=920.0, classification="Super Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2020-BOB-01", timestamp=datetime(2020, 5, 19, 18, 0, tzinfo=timezone.utc), latitude=18.1, longitude=87.2, wind_speed=100.0, pressure=950.0, classification="Extremely Severe Cyclonic Storm", source="IMD_OFFICIAL"),
            Observation(cyclone_id="CYC-2020-BOB-01", timestamp=datetime(2020, 5, 20, 12, 0, tzinfo=timezone.utc), latitude=21.6, longitude=88.3, wind_speed=85.0, pressure=960.0, classification="Very Severe Cyclonic Storm", source="IMD_OFFICIAL"),
        ]
        db.add_all(observations)

        # 4. Satellite Images Scenes
        sat_images = [
            SatelliteImage(id="SAT-INSAT3D-20260904-1200", cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc), satellite="INSAT-3D", sensor="IMAGER", channel="TIR1", file_path="insat3d_20260904_1200_tir1.png", resolution_km=4.0, min_lat=10.0, min_lon=80.0, max_lat=24.0, max_lon=94.0),
            SatelliteImage(id="SAT-INSAT3D-20260904-0600", cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 4, 6, 0, tzinfo=timezone.utc), satellite="INSAT-3D", sensor="IMAGER", channel="WV", file_path="insat3d_20260904_0600_wv.png", resolution_km=4.0, min_lat=10.0, min_lon=80.0, max_lat=24.0, max_lon=94.0),
            SatelliteImage(id="SAT-INSAT3D-20260903-1800", cyclone_id="CYC-2026-NIO-DEMO", timestamp=datetime(2026, 9, 3, 18, 0, tzinfo=timezone.utc), satellite="INSAT-3D", sensor="IMAGER", channel="VIS", file_path="insat3d_20260903_1800_vis.png", resolution_km=1.0, min_lat=10.0, min_lon=80.0, max_lat=24.0, max_lon=94.0),
            SatelliteImage(id="SAT-INSAT3DR-20240526-1200", cyclone_id="CYC-2024-BOB-REMAL", timestamp=datetime(2024, 5, 26, 12, 0, tzinfo=timezone.utc), satellite="INSAT-3DR", sensor="IMAGER", channel="TIR1", file_path="insat3dr_remal_tir1.png", resolution_km=4.0, min_lat=14.0, min_lon=84.0, max_lat=26.0, max_lon=96.0),
            SatelliteImage(id="SAT-INSAT3D-20230611-1200", cyclone_id="CYC-2023-ARB-01", timestamp=datetime(2023, 6, 11, 12, 0, tzinfo=timezone.utc), satellite="INSAT-3D", sensor="IMAGER", channel="TIR1", file_path="insat3d_biparjoy_tir1.png", resolution_km=4.0, min_lat=12.0, min_lon=60.0, max_lat=26.0, max_lon=75.0),
            SatelliteImage(id="SAT-INSAT3D-20190502-1200", cyclone_id="CYC-2019-BOB-FANI", timestamp=datetime(2019, 5, 2, 12, 0, tzinfo=timezone.utc), satellite="INSAT-3D", sensor="IMAGER", channel="TIR1", file_path="insat3d_fani_tir1.png", resolution_km=4.0, min_lat=10.0, min_lon=80.0, max_lat=24.0, max_lon=92.0),
            SatelliteImage(id="SAT-INSAT3D-20200519-1200", cyclone_id="CYC-2020-BOB-01", timestamp=datetime(2020, 5, 19, 12, 0, tzinfo=timezone.utc), satellite="INSAT-3D", sensor="IMAGER", channel="TIR1", file_path="insat3d_amphan_tir1.png", resolution_km=4.0, min_lat=12.0, min_lon=82.0, max_lat=26.0, max_lon=94.0),
        ]
        db.add_all(sat_images)

        await db.commit()
        logger.info("Comprehensive historical and active cyclone datasets successfully seeded.")
    except Exception as e:
        logger.error(f"Error during initial seed: {e}")
        await db.rollback()
