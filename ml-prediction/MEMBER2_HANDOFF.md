# Member Handoff: Member 2 (ML Prediction & Data Pipeline)

Use this document for integrating Member 2's `ml-prediction` service into the CycloneAI platform.

## Owner
Member: Member 2 (Multi-Source Data, Track Prediction & Intensity Prediction)

## Component
: `ml-prediction` (Spatiotemporal Trajectory & Intensity Forecasting Microservice)

## Branch
: `member2-prediction`

## Run

```bash
cd member2-prediction
python -m venv .venv
.venv\Scripts\activate   # or source .venv/bin/activate on Linux
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8002
```

## Docker

```bash
cd member2-prediction
docker build -t cyclone-ml-prediction -f Dockerfile .
docker run -d --name ml-prediction -p 8002:8002 cyclone-ml-prediction
```

## Port
: `8002`

## Health Endpoint
: `GET http://ml-prediction:8002/health`

Response:
```json
{
  "status": "ok",
  "service": "ml-prediction",
  "model_version": "track-model-v1.0",
  "device": "cpu"
}
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service health status and active model version |
| `POST` | `/forecast` | Joint track & intensity multi-horizon forecast (+6h, +12h, +24h, +48h) |
| `POST` | `/track` | Dedicated track prediction (lat, lon, error cone radius, confidence) |
| `POST` | `/intensity` | Dedicated intensity prediction (wind speed, central pressure, confidence) |

## Input Schema (`POST /forecast`, `POST /track`, `POST /intensity`)

```json
{
  "cyclone_id": "CY001",
  "observations": [
    {
      "timestamp": "2024-05-25T00:00:00Z",
      "latitude": 14.2,
      "longitude": 86.5,
      "wind_speed": 45.0,
      "pressure": 996.0
    },
    {
      "timestamp": "2024-05-25T06:00:00Z",
      "latitude": 14.9,
      "longitude": 86.8,
      "wind_speed": 55.0,
      "pressure": 990.0
    },
    {
      "timestamp": "2024-05-25T12:00:00Z",
      "latitude": 15.6,
      "longitude": 87.1,
      "wind_speed": 65.0,
      "pressure": 984.0
    },
    {
      "timestamp": "2024-05-25T18:00:00Z",
      "latitude": 16.3,
      "longitude": 87.3,
      "wind_speed": 75.0,
      "pressure": 976.0
    }
  ]
}
```

## Output Schema (`POST /forecast`)

```json
{
  "cyclone_id": "CY001",
  "forecast_time": "2024-05-25T18:00:00Z",
  "predictions": [
    {
      "hours": 6,
      "target_time": "2024-05-26T00:00:00Z",
      "latitude": 17.02,
      "longitude": 87.51,
      "predicted_wind_speed": 82.4,
      "predicted_pressure": 968.2,
      "confidence": 0.91,
      "error_radius_km": 38.5
    },
    {
      "hours": 12,
      "target_time": "2024-05-26T06:00:00Z",
      "latitude": 17.78,
      "longitude": 87.68,
      "predicted_wind_speed": 88.0,
      "predicted_pressure": 962.0,
      "confidence": 0.84,
      "error_radius_km": 68.2
    },
    {
      "hours": 24,
      "target_time": "2024-05-26T18:00:00Z",
      "latitude": 19.35,
      "longitude": 88.05,
      "predicted_wind_speed": 92.5,
      "predicted_pressure": 956.1,
      "confidence": 0.72,
      "error_radius_km": 122.4
    },
    {
      "hours": 48,
      "target_time": "2024-05-27T18:00:00Z",
      "latitude": 22.10,
      "longitude": 88.85,
      "predicted_wind_speed": 70.0,
      "predicted_pressure": 978.0,
      "confidence": 0.53,
      "error_radius_km": 215.0
    }
  ],
  "model": {
    "name": "CycloneTrackGRU",
    "version": "track-model-v1.0"
  }
}
```

## Model Version
: `track-model-v1.0` (Multi-Task Recurrent Sequence-to-Sequence with Monte Carlo Dropout uncertainty estimation)

## Dataset Version
: NOAA/WMO `IBTrACS.NI.v04r01` & Curated NIO Historical Cyclone Benchmark Catalog `v1.0`

## Metrics

Evaluated on unseen test partition using great-circle Haversine distance and MAE:

| Horizon (hours) | Baseline MTE (km) | ML Model MTE (km) | Track Skill (%) | ML Wind MAE (kt) | ML Pressure MAE (hPa) |
|---|---|---|---|---|---|
| **+6h** | 9.4 | 22.8 | -142.7% (inertia-dominated) | 5.9 | 4.2 |
| **+12h** | 24.7 | 41.0 | -66.1% | 14.7 | 10.0 |
| **+24h** | 73.7 | 56.9 | **+22.8%** | 29.6 | 22.7 |
| **+48h** | 244.7 | 157.6 | **+35.6%** | 49.9 | 38.6 |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8002` | Port to expose the FastAPI service |
| `CHECKPOINT_PATH` | `/app/checkpoints/track_model_v1.pt` | Path to PyTorch model weights checkpoint |
| `DEVICE` | `cpu` | Hardware accelerator (`cpu` or `cuda`) |

## Files Other Members Need

- `member2-prediction/api/schemas.py`: Pydantic models for request/response serialization in Member 3's backend.
- `member2-prediction/Dockerfile`: Standalone Docker container configuration for Docker Compose.
- `member2-prediction/MEMBER2_HANDOFF.md`: This integration contract.

## Known Limitations

- **Minimum History**: Requires at least 2 chronological observations. For < 4 observations, front-padding is applied.
- **Landfall Dissipation**: Extended +48h forecasts for storms hitting the coast model kinematic slowdown and pressure filling, but extreme inland terrain interaction may increase variance.
- **Decision Support Notice**: AI predictions are research decision-support outputs and do not substitute official IMD cyclone warnings.

## Integration Notes

- **Docker Compose Service Name**: Use `http://ml-prediction:8002` in Member 3's backend orchestration calls.
- **Resilience Policy**: If `ml-prediction` is temporarily unreachable, Member 3 should return existing confirmed observations and a graceful service notification (`"ML prediction service temporarily offline"`) rather than inventing simulated coordinates.

## Tests Passed

- [x] Unit (`test_data_validation.py`, `test_feature_engineering.py`, `test_baseline.py`)
- [x] Integration (`test_sequences.py`, `test_model_inference.py`)
- [x] Docker (`Dockerfile` multi-stage, non-root user, healthcheck configured)
- [x] API (`test_api.py` validating `/health`, `/forecast`, `/track`, `/intensity`)
