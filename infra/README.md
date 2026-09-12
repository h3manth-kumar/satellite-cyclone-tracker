# CycloneAI — Integrated Deployment & Validation Guide

This directory contains the orchestration configuration and end-to-end integration test suite for the **CycloneAI** decision-support platform.

---

## 1. Stack Topology

The platform runs as a coordinated 5-container topology:
- **`frontend:3000`** — React 18 + Vite GIS Dashboard (Nginx Alpine)
- **`backend:8000`** — FastAPI REST API Gateway & Pipeline Orchestrator
- **`ml-detection:8001`** — Member 1: Satellite Preprocessing, CNN Eye Detection, IMD Stage Classification & Grad-CAM
- **`ml-prediction:8002`** — Member 2: GRU Multi-Lead Trajectory & Intensity Forecasting (+6h to +48h)
- **`postgres:5432`** — PostgreSQL 16 + PostGIS 3.4 Spatial Database (mapped to host port `5433`)

---

## 2. Quick Start

### Build and Launch the Complete Stack

```bash
docker compose up -d
```

### Check Container Status & Health

```bash
docker compose ps
```

All 5 containers will start up:
- `cyclone-frontend` (Port 3000)
- `cyclone-backend` (Port 8000 - Healthy)
- `cyclone-ml-detection` (Port 8001 - Healthy)
- `cyclone-ml-prediction` (Port 8002 - Healthy)
- `cyclone-postgres` (Port 5433 - Healthy)

---

## 3. End-to-End Verification

Run the automated integration verification suite:

```bash
python integration/tests/test_e2e_pipeline.py
```

All 7 pipeline stages are tested against live microservices:
1. Healthcheck (`GET /health`)
2. Cyclone Registry (`GET /cyclones`)
3. GeoJSON Track (`GET /cyclones/CYC-2026-NIO-DEMO/track-geojson`)
4. Direct Member 1 Detection (`POST /analysis/detect`)
5. Direct Member 1 Classification (`POST /analysis/classify`)
6. Direct Member 2 Forecasting (`POST /analysis/forecast`)
7. Full End-to-End AI Orchestration (`POST /analysis/full`)

---

## 4. Running Subsystem Unit Tests

```bash
# Member 1 Unit Tests (26/26)
cd member1-ml && python -m pytest tests/ -v

# Member 2 Unit Tests (25/25)
cd member2-prediction && python -m pytest tests/ -v

# Member 3 Backend Tests (9/9)
cd member3-platform/backend && python -m pytest tests/ -v
```

---

## 5. Teardown

```bash
docker compose down
```
