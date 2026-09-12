# CycloneAI Design

## Architecture

```text
Satellite/Meteorological Data
            ↓
       Data Pipeline
            ↓
     ┌──────┴──────┐
     ↓             ↓
Member 1        Member 2
Detection       Track +
Classification  Intensity
     └──────┬──────┘
            ↓
       FastAPI Backend
            ↓
      React Dashboard
            ↓
      PostgreSQL/PostGIS
```

## Container Architecture

```text
frontend
backend
ml-detection
ml-prediction
postgres
```

## Integration
The backend is the integration layer. The frontend must not directly call ML services.
