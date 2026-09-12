# CycloneAI — Member 3 Handoff Documentation
## Platform, Backend, Frontend Dashboard, PostGIS & ML Integration

---

## 1. Owner & Subsystem
* **Member**: Member 3
* **Role**: Platform, Backend, Frontend, GIS & ML Integration Lead
* **Subsystem**: Application Platform, FastAPI Gateway, React Dashboard, PostGIS Spatial Database, ML Service Adapters, and Docker Compose Multi-Container Orchestration.

---

## 2. Target Architecture

The CycloneAI platform employs a decoupled, multi-service architecture where Member 3's backend serves as the sole API Gateway, Orchestrator, and Spatial Data Hub. The React frontend interacts strictly with the backend, which coordinates requests to Member 1 (`ml-detection`) and Member 2 (`ml-prediction`).

```mermaid
graph TD
    subgraph Presentation Tier
        UI["React 18 + TypeScript Console\n(Midnight Cartography / Port 3000)"]
    end

    subgraph Platform Tier [Member 3 Scope]
        API["FastAPI Backend Gateway\n(Port 8000)"]
        ORCH["Analysis Pipeline Orchestrator"]
        ADAPT1["Member 1 Adapter\n(HTTP Client / Circuit Breaker / Mock)"]
        ADAPT2["Member 2 Adapter\n(HTTP Client / Circuit Breaker / Mock)"]
        PG[("PostgreSQL 16 + PostGIS 3.4\n(Spatial DB / Port 5432)")]
        VOL[("Decoupled Volume Storage\n(/app/data/satellite & explainability)")]
    end

    subgraph ML Subsystems [Peer Services]
        M1["Member 1: Detection & Classification\n(ml-detection:8001)"]
        M2["Member 2: Track & Intensity Forecaster\n(ml-prediction:8002)"]
    end

    UI -->|REST / JSON & GeoJSON| API
    API --> ORCH
    ORCH --> ADAPT1
    ORCH --> ADAPT2
    ADAPT1 -->|HTTP POST /detect /classify| M1
    ADAPT2 -->|HTTP POST /forecast| M2
    API -->|Async SQLAlchemy 2.0 + GeoAlchemy2| PG
    API -->|Image Stream / Static Volume Mount| VOL
```

### Core Collaboration Rules Enforced:
1. **Frontend Isolation**: React frontend communicates ONLY with the FastAPI backend.
2. **Docker Internal DNS**: All inter-service calls use Docker service names (`ml-detection:8001`, `ml-prediction:8002`, `postgres:5432`). `localhost` is never hard-coded for inter-container communication.
3. **Data Provenance**: Ground-truth sensor observations (`IMD_OFFICIAL`) and AI predictions are stored in separate tables and visually isolated in the UI.
4. **Anti-Hallucination**: If upstream ML services are offline, the backend reports degradation; it never fabricates synthetic predictions.
5. **Decoupled Satellite Storage**: Massive GeoTIFF/NetCDF/PNG files are kept on Docker volumes (`/app/data/satellite/`); PostgreSQL/PostGIS records only metadata and spatial extents.

---

## 3. Folder Structure

```text
cyclone-ai/
├── HANDOFF.md                             # Master Platform Handoff
├── COMMON.md                              # Shared Instructions
├── 00_INITIAL_PROMPT_ALL_MEMBERS.md
├── docs/                                  # Canonical Team Documentation
│   ├── APPFLOW.md
│   ├── DESIGN.md
│   ├── MAP_DESIGN.md
│   ├── PRD.md
│   ├── RULES.md
│   ├── SCHEMA.md
│   ├── TRACKER.md
│   └── TRD.md
├── member1-ml/                            # Member 1 ML codebase (isolated)
├── member2-prediction/                    # Member 2 Forecasting codebase (isolated)
├── member3-platform/                      # Member 3 Primary Workspace
│   ├── backend/                           # FastAPI Application & Gateway
│   │   ├── app/
│   │   │   ├── api/v1/endpoints/          # RESTful Endpoints (health, cyclones, obs, satellite, analysis)
│   │   │   ├── core/                      # Config (Pydantic v2), Logging, Exceptions
│   │   │   ├── db/                        # Async Engine, Declarative Base, Seeders
│   │   │   ├── models/                    # SQLAlchemy ORM Models (Cyclone, Obs, Satellite, Forecast, etc.)
│   │   │   ├── schemas/                   # Pydantic v2 Validation Models
│   │   │   ├── services/                  # Business Services & Pipeline Orchestrator
│   │   │   ├── adapters/                  # IMember1Adapter & IMember2Adapter (HTTP + Mock)
│   │   │   └── main.py                    # ASGI Application Entrypoint
│   │   ├── alembic/                       # Database Migrations & Versioning
│   │   ├── tests/                         # Pytest Suite (100% Pass)
│   │   ├── Dockerfile                     # Python 3.11 Backend Container
│   │   └── requirements.txt
│   ├── frontend/                          # React 18 + TypeScript Single Page App
│   │   ├── src/
│   │   │   ├── components/                # Map, Telemetry, Dual Provenance, Charts, Satellite Viewer
│   │   │   ├── services/                  # API Client (fetch)
│   │   │   ├── types/                     # TypeScript Domain Models
│   │   │   ├── App.tsx                    # Mission-Control Workspace Layout
│   │   │   └── index.css                  # Mapbox Midnight Theme Tokens
│   │   ├── nginx.conf                     # Production Reverse Proxy
│   │   ├── Dockerfile                     # Multi-stage Node.js + Nginx Container
│   │   └── package.json
│   ├── mocks/                             # Standalone microservice stubs for testing & early integration
│   │   ├── ml_detection_stub/             # Member 1 Reference Service (Port 8001)
│   │   └── ml_prediction_stub/            # Member 2 Reference Service (Port 8002)
│   ├── HANDOFF.md                         # Package Handoff
│   └── README.md
├── integration/                           # Orchestration & Integration Verification
│   ├── docker-compose.yml                 # Master Multi-Container Configuration (5 Services)
│   ├── .env.example                       # Documented Environment Blueprint
│   ├── .env                               # Active Development Configuration
│   ├── init-db/                           # Database Initialization Scripts
│   │   ├── 01-init-postgis.sql            # PostGIS Extension & Normalized Schema
│   │   └── 02-seed-historical.sql         # Seed Historical Cyclones (Biparjoy, Amphan, Active System 01A)
│   └── tests/
│       └── test_e2e_pipeline.py           # End-to-End Pipeline Integration Test Runner
```

---

## 4. Backend Endpoints

Base URL: `http://backend:8000` (internal) / `http://localhost:8000` (host)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check (DB connection latency, M1 & M2 reachability status) |
| `GET` | `/cyclones` | List monitored cyclones (Filters: `basin`, `active_only`, `limit`, `offset`) |
| `GET` | `/cyclones/{id}` | Detailed metadata for a specific cyclone |
| `GET` | `/cyclones/{id}/observations` | Chronological ground-truth observations (`source: IMD_OFFICIAL`) |
| `GET` | `/cyclones/{id}/track-geojson` | RFC 7946 GeoJSON FeatureCollection (Observed track, forecast track, uncertainty cone) |
| `POST` | `/observations` | Ingest new verified ground-truth meteorological observation |
| `GET` | `/satellite/images` | List satellite image metadata (Filter by `cyclone_id`, `channel`) |
| `GET` | `/satellite/images/{id}/file` | Stream raw or enhanced INSAT-3D Thermal IR raster (PNG/WebP) |
| `GET` | `/satellite/explainability/{file}` | Stream Grad-CAM convective attention heatmap generated by Member 1 |
| `POST` | `/analysis/detect` | Call Member 1 Detection endpoint for center localization and bounding box |
| `POST` | `/analysis/classify` | Call Member 1 Classification endpoint for IMD category & estimated wind |
| `POST` | `/analysis/forecast` | Call Member 2 Forecasting endpoint for +6h to +72h trajectory milestones |
| `POST` | `/analysis/full` | Execute unified AI pipeline, persist results to PostGIS, and return unified response |

---

## 5. Database Schema (PostgreSQL 16 + PostGIS 3.4)

### Core Tables & Relationships:
1. `cyclones`: Master registry of tropical cyclones (`id`, `name`, `basin`, `start_time`, `end_time`, `is_active`).
2. `observations`: Ground-truth meteorological observations (`id`, `cyclone_id` FK, `timestamp`, `latitude`, `longitude`, `wind_speed`, `pressure`, `classification`, `source`).
3. `satellite_images`: Satellite metadata (`id`, `cyclone_id` FK, `timestamp`, `satellite`, `sensor`, `channel`, `file_path`, `resolution_km`, `min_lat`, `min_lon`, `max_lat`, `max_lon`).
4. `detection_results`: Member 1 center localization outputs (`id`, `image_id` FK, `detected`, `latitude`, `longitude`, `confidence`, `bbox_coordinates`, `model_version`).
5. `classification_results`: Member 1 IMD classification outputs (`id`, `image_id` FK, `cyclone_id` FK, `classification`, `confidence`, `estimated_wind_speed`, `class_probabilities`, `explainability_file_path`, `model_version`).
6. `forecasts`: Member 2 predicted tracks strictly isolated from observations (`id`, `cyclone_id` FK, `forecast_time`, `target_time`, `lead_hours`, `latitude`, `longitude`, `predicted_wind_speed`, `predicted_pressure`, `uncertainty_radius_km`, `confidence`, `model_version`).
7. `models`: Registry of active neural architectures and validation metrics (`id`, `service_name`, `version`, `description`, `metrics`, `is_active`).

---

## 6. Frontend Pages & Dashboard Components

Adheres strictly to the *"Satellite console at midnight"* aesthetic from `MAP_DESIGN.md`:
* **Colors**: Void Black (`#0e1012`), Deep Charcoal (`#15171b`), Gunmetal (`#1c1f24`), Signal Blue (`#007afc`), Map Green (`#228a56`).
* **Header (`Header.tsx`)**:
  - IMD & MoES Insignia, active cyclone switcher, real-time UTC digital clock.
  - Microservice health badges (`DB`, `M1 Detection`, `M2 Forecasting`).
  - Primary CTA pill button: `⚡ Run AI Pipeline`.
* **Telemetry Quick Bar (`TelemetryBar.tsx`)**:
  - Center coordinates (`17.2°N, 87.3°E`).
  - IMD intensity badge (color-coded for Depression up to Super Cyclonic Storm).
  - Sustained wind speed (knots & km/h) and central barometric pressure (hPa).
* **Interactive GIS Map (`CycloneMap.tsx`)**:
  - Leaflet map with CartoDB Dark Matter tiles.
  - Solid LineString for observed tracks with clickable circular nodes.
  - Dashed LineString for AI predicted trajectories.
  - Dynamic polygonal Cones of Uncertainty expanding with lead time.
  - Pulsing radar eye beacon (`.radar-beacon`) centered on the storm eye.
* **Dual Provenance Card (`OfficialVsAICard.tsx`)**:
  - Side-by-side validation contrasting `[OFFICIAL GROUND TRUTH]` vs `[AI INFERRED ANALYSIS]`.
* **Intensity & Pressure Trend Curve (`IntensityChart.tsx`)**:
  - Multi-lead time SVG curve plotting past observed winds alongside predicted $+6\text{h}$ to $+72\text{h}$ decay curves.
* **Satellite & Explainability Inspector (`SatelliteViewer.tsx`)**:
  - Multi-spectral channel picker (TIR1, WV, VIS).
  - Interactive crossfade slider (0% to 100%) to smoothly blend between raw INSAT-3D Thermal IR and Member 1's Grad-CAM convective attention heatmap.
* **Operational Boundary Banner (`DisclaimerBanner.tsx`)**:
  - Pinned non-official prototype decision-support notice.

---

## 7. Machine Learning Integration Details

Member 3 communicates with Member 1 and Member 2 through decoupled service adapters (`app/adapters/`):

### Member 1 Interface Contract (Port 8001 / Service `ml-detection`):
* `GET /health` $\rightarrow$ `{"status": "ok", "service": "ml-detection", "version": "1.0.0", "model_loaded": true}`
* `POST /detect`:
  - Request: `{"image_id": "string", "image_path": "string", "sensor": "TIR1"}`
  - Response: `{"detected": true, "latitude": 17.25, "longitude": 87.35, "confidence": 0.94, "bbox": [15.0, 85.0, 19.5, 89.7], "model_version": "m1-yolo-v1.0"}`
* `POST /classify`:
  - Request: `{"image_id": "string", "latitude": 17.25, "longitude": 87.35}`
  - Response: `{"classification": "Very Severe Cyclonic Storm", "confidence": 0.88, "estimated_wind_speed": 76.5, "probabilities": {...}, "model_version": "m1-resnet-v1.0", "explainability_heatmap_path": "exp_latest.png"}`

### Member 2 Interface Contract (Port 8002 / Service `ml-prediction`):
* `GET /health` $\rightarrow$ `{"status": "ok", "service": "ml-prediction", "version": "1.0.0", "model_loaded": true}`
* `POST /forecast`:
  - Request:
    ```json
    {
      "cyclone_id": "CYC-2026-NIO-DEMO",
      "history": [
        {"timestamp": "2026-09-04T06:00:00Z", "latitude": 16.7, "longitude": 87.0, "wind_speed": 70.0, "pressure": 976.0},
        {"timestamp": "2026-09-04T12:00:00Z", "latitude": 17.2, "longitude": 87.3, "wind_speed": 75.0, "pressure": 972.0}
      ]
    }
    ```
  - Response:
    ```json
    {
      "cyclone_id": "CYC-2026-NIO-DEMO",
      "forecast_time": "2026-09-04T14:00:00Z",
      "model_version": "m2-tft-transformer-v1.0.0",
      "forecast_points": [
        {"lead_hours": 6, "target_time": "2026-09-04T18:00:00Z", "latitude": 17.7, "longitude": 87.6, "predicted_wind_speed": 80.0, "predicted_pressure": 968.0, "uncertainty_radius_km": 25.0, "confidence": 0.88},
        {"lead_hours": 12, "target_time": "2026-09-05T00:00:00Z", "latitude": 18.3, "longitude": 87.8, "predicted_wind_speed": 83.0, "predicted_pressure": 965.0, "uncertainty_radius_km": 45.0, "confidence": 0.84},
        {"lead_hours": 24, "target_time": "2026-09-05T12:00:00Z", "latitude": 19.4, "longitude": 88.1, "predicted_wind_speed": 78.0, "predicted_pressure": 970.0, "uncertainty_radius_km": 75.0, "confidence": 0.78}
      ]
    }
    ```

---

## 8. Environment Variables (`integration/.env.example`)

```dotenv
# Database Configuration
POSTGRES_USER=cyclone_admin
POSTGRES_PASSWORD=cyclone_secure_dev_password
POSTGRES_DB=cyclone_db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://cyclone_admin:cyclone_secure_dev_password@postgres:5432/cyclone_db
DATABASE_SYNC_URL=postgresql://cyclone_admin:cyclone_secure_dev_password@postgres:5432/cyclone_db

# Backend Configuration
BACKEND_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://frontend:3000
SATELLITE_DATA_DIR=/app/data/satellite

# Machine Learning Service Adapters (Docker Internal DNS)
MEMBER1_URL=http://ml-detection:8001
MEMBER2_URL=http://ml-prediction:8002
ML_TIMEOUT_SECONDS=15.0
USE_MOCK_ML=true

# External Ports for ML Stubs
ML_DETECTION_PORT=8001
ML_PREDICTION_PORT=8002

# Frontend Configuration
FRONTEND_PORT=3000
VITE_API_BASE_URL=http://localhost:8000
```

---

## 9. Docker & Compose Services

The multi-container stack runs via `integration/docker-compose.yml`:

```bash
# Build and run the complete 5-container stack
cd integration
docker compose up --build

# Run in background (detached)
docker compose up -d

# Inspect service health status
docker compose ps

# Stop all containers
docker compose down
```

### Registered Compose Services:
1. `postgres` (`postgis/postgis:16-3.4-alpine`): Exposes port `5432`. Includes persistent volume `postgres_data` and auto-runs `init-db/`.
2. `backend`: FastAPI Gateway exposing port `8000`. Healthcheck checks `http://localhost:8000/health`.
3. `frontend`: Multi-stage Node.js build + Nginx alpine reverse proxy exposing port `3000`.
4. `ml-detection`: Member 1 service stub running on port `8001`.
5. `ml-prediction`: Member 2 service stub running on port `8002`.

---

## 10. Automated Tests & Validation

### Backend Unit & Integration Tests (`pytest`):
```bash
cd member3-platform/backend
python -m pytest tests
```
* **Result**: 9 passed in 2.35s with 0 warnings.
  - `test_health.py`: Verifies `/health` diagnostics and dependency checks.
  - `test_cyclones.py`: Verifies cyclone registry, basin filters, and GeoJSON tracks.
  - `test_analysis.py`: Verifies `/detect`, `/classify`, `/forecast`, and `/full` orchestration.

### End-to-End Stack Verification Script:
```bash
python integration/tests/test_e2e_pipeline.py
```
* Programmatically verifies: Healthcheck $\rightarrow$ Cyclone Registry $\rightarrow$ GeoJSON Generation $\rightarrow$ M1 Detection $\rightarrow$ M1 Classification $\rightarrow$ M2 Forecasting $\rightarrow$ Full PostGIS Persistence $\rightarrow$ Non-official Disclaimer Validation.

---

## 11. Known Limitations & Design Trade-offs

1. **Satellite Band Resolution**: Raw NetCDF scenes are multi-gigabyte. The backend streams web-optimized PNG/WebP representations while preserving spatial bounding box geometry (`min_lat`, `min_lon`, `max_lat`, `max_lon`).
2. **Cold Start Latency**: If Member 1 or Member 2 use large deep-learning models on CPU, initial inference may take 5–15 seconds. The backend employs 15-second timeouts and async non-blocking execution to keep the UI interactive.
3. **Mock Mode Default**: `USE_MOCK_ML=true` is enabled by default so the entire system works immediately for testing and evaluation even before Member 1 and Member 2 models are deployed. Set `USE_MOCK_ML=false` to route calls directly to live ML containers.

---

## 12. Final Integration Instructions for Member 1 & Member 2

When Member 1 and Member 2 finish their subsystems:

1. **Deploy Containers**:
   - Member 1 builds and runs `ml-detection` on port `8001`.
   - Member 2 builds and runs `ml-prediction` on port `8002`.
   - Ensure both containers are attached to the `cyclone-net` Docker network.
2. **Switch to Production Mode**:
   - In `integration/.env`, change:
     ```dotenv
     USE_MOCK_ML=false
     ```
3. **Zero Frontend/Backend Code Changes Required**:
   - Member 3's backend adapters (`HttpMember1Adapter` and `HttpMember2Adapter`) will automatically dispatch HTTP requests to the live containers.
   - The React dashboard contracts remain completely stable.
