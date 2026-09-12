# CycloneAI — Member 3 Platform Subsystem
## Backend, Frontend, GIS Map, Database & ML Integration Platform

### Overview
This subsystem represents Member 3's deliverable for the **CycloneAI** project: a research and decision-support prototype for identifying, classifying, and predicting tropical cyclone patterns in the North Indian Ocean basin (India Meteorological Department / Ministry of Earth Sciences).

Member 3 owns the end-to-end platform:
* **FastAPI Backend Gateway** with Pydantic v2 validation and structured logging.
* **PostgreSQL 16 + PostGIS 3.4** spatial persistence separating observed ground-truth from AI predictions.
* **React 18 + TypeScript Dashboard** styled after the *"Satellite console at midnight"* theme (`MAP_DESIGN.md`).
* **Interactive Leaflet Cyclone Map** with dark CartoDB tiles, solid observed tracks, dashed predicted trajectories, pulsing eye beacons, and uncertainty polygon cones.
* **Multi-Spectral Satellite Viewer** with INSAT-3D Thermal IR and dynamic Grad-CAM attention heatmap overlay slider.
* **Resilient Service Adapters** connecting to Member 1 (`ml-detection:8001`) and Member 2 (`ml-prediction:8002`), with high-fidelity historical mock fallbacks.
* **Multi-Service Docker Compose Orchestration** running 5 isolated containers communicating via internal service names.

---

### Folder Structure
```text
member3-platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/  # Health, Cyclones, Observations, Satellite, Analysis
│   │   ├── core/              # Settings, Logging, Domain Exceptions
│   │   ├── db/                # Async Engine, Declarative Base, Table Seeders
│   │   ├── models/            # SQLAlchemy 2.0 ORM & PostGIS Models
│   │   ├── schemas/           # Pydantic v2 Request/Response Schemas
│   │   ├── services/          # Business logic & Pipeline Orchestrator
│   │   ├── adapters/          # Member 1 & Member 2 HTTP + Mock Adapters
│   │   └── main.py            # ASGI Entrypoint
│   ├── tests/                 # Pytest suite (100% passing)
│   ├── Dockerfile             # Production Python 3.11 Backend
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Map, Telemetry, Dual Provenance, Charts, Satellite
│   │   ├── services/          # API Client
│   │   ├── types/             # TypeScript Models
│   │   ├── App.tsx            # Main Console Workspace
│   │   └── index.css          # Midnight theme design tokens
│   ├── nginx.conf             # Production reverse proxy
│   ├── Dockerfile             # Multi-stage Node + Nginx build
│   └── package.json
└── mocks/
    ├── ml_detection_stub/     # Member 1 microservice stub (Port 8001)
    └── ml_prediction_stub/    # Member 2 microservice stub (Port 8002)
```

---

### Quick Start with Docker Compose

To launch all 5 services simultaneously:

```bash
cd integration
docker compose up --build
```

#### Running Services:
| Service | Container Name | Port | Description |
|---|---|---|---|
| **frontend** | `cyclone-frontend` | `3000` | Mission-control web dashboard |
| **backend** | `cyclone-backend` | `8000` | FastAPI Gateway & Orchestrator |
| **postgres** | `cyclone-postgres` | `5432` | PostgreSQL 16 + PostGIS 3.4 |
| **ml-detection** | `cyclone-ml-detection` | `8001` | Member 1 Detection/Classification |
| **ml-prediction** | `cyclone-ml-prediction` | `8002` | Member 2 Track & Intensity Forecasting |

---

### API Contract Reference

#### 1. System Health
* `GET /health`
  * Reports health of backend, database connectivity, and reachability of `ml-detection` and `ml-prediction`.

#### 2. Cyclones & Spatial Tracking
* `GET /cyclones` (Filter: `basin`, `active_only`, `limit`, `offset`)
* `GET /cyclones/{id}`
* `GET /cyclones/{id}/observations`
* `GET /cyclones/{id}/track-geojson` (RFC 7946 GeoJSON FeatureCollection)

#### 3. Satellite Imagery & Explainability
* `GET /satellite/images?cyclone_id={id}`
* `GET /satellite/images/{id}/file` (Streams raw/enhanced INSAT-3D Thermal IR raster)
* `GET /satellite/explainability/{filename}` (Streams Grad-CAM convective attention heatmap)

#### 4. Machine Learning Inference & Pipeline
* `POST /analysis/detect` $\rightarrow$ Member 1 eye detection & center coordinates
* `POST /analysis/classify` $\rightarrow$ Member 1 IMD intensity classification
* `POST /analysis/forecast` $\rightarrow$ Member 2 $+6\text{h}$ to $+72\text{h}$ track and intensity predictions
* `POST /analysis/full` $\rightarrow$ Orchestrated end-to-end pipeline with PostGIS persistence

---

### Running Automated Tests

#### Backend Pytest Suite:
```bash
cd member3-platform/backend
python -m pytest tests
```
*Expected output: 9 passed with zero warnings.*

#### End-to-End Pipeline Integration Test:
```bash
python integration/tests/test_e2e_pipeline.py
```
*Validates the entire pipeline against running containers or local instances.*

---

### Handoff Notes for Member 1 and Member 2

1. **Member 1 (ML Detection & Classification)**:
   - Expose your container on internal port `8001` (`http://ml-detection:8001`).
   - Implement `POST /detect` returning `{"detected": bool, "latitude": float, "longitude": float, "confidence": float, "bbox": [ymin, xmin, ymax, xmax]}`.
   - Implement `POST /classify` returning `{"classification": str, "confidence": float, "estimated_wind_speed": float, "explainability_heatmap_path": str}`.
   - Member 3's backend already has the adapter ready; no frontend changes are required.

2. **Member 2 (Track & Intensity Forecasting)**:
   - Expose your container on internal port `8002` (`http://ml-prediction:8002`).
   - Implement `POST /forecast` accepting `{"cyclone_id": str, "history": [{"timestamp": str, "latitude": float, "longitude": float, "wind_speed": float, "pressure": float}]}`.
   - Return multi-lead milestones (+6h, +12h, +24h, +48h, +72h) with `predicted_wind_speed`, `predicted_pressure`, and `uncertainty_radius_km`.
