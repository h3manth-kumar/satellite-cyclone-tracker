# CycloneAI Technical Requirements

## Stack
- Python 3.10+
- PyTorch
- NumPy/Pandas/scikit-learn
- FastAPI/Pydantic
- React/TypeScript
- PostgreSQL/PostGIS
- Leaflet or MapLibre
- Docker/Docker Compose

## Final repository concept

```text
cyclone-ai/
├── docs/
├── member1-ml/
├── member2-prediction/
├── member3-platform/
├── integration/
└── README.md
```

## Final Compose

```text
frontend
backend
ml-detection
ml-prediction
postgres
```

## Target startup

```bash
docker compose up --build
```

## Service ports
- frontend: 3000
- backend: 8000
- ml-detection: 8001
- ml-prediction: 8002
- postgres: 5432

Ports may be changed through environment variables.

## Requirements
- health endpoints
- structured JSON
- model versioning
- dataset versioning
- error handling
- tests
- no secrets
- reproducible Docker builds
