# CycloneAI — Member 2: ML Prediction Service (`ml-prediction`)

AI/ML spatiotemporal forecasting microservice for tropical cyclone track (latitude/longitude) and intensity (sustained wind speed and central pressure) prediction in the North Indian Ocean (Bay of Bengal and Arabian Sea), designed for the Ministry of Earth Sciences (MoES) and India Meteorological Department (IMD).

---

## 1. Overview

Member 2 owns the data engineering, kinematic feature extraction, sequence modeling, track & intensity forecasting, uncertainty estimation, and standalone REST API for CycloneAI.

### Key Capabilities
- **Multi-Horizon Forecasts**: Predicts positions and intensities at **+6h, +12h, +24h, and +48h**.
- **Dual-Target Independence**: Track (displacement vector) and intensity (wind/pressure tendencies) are independently generated, validated, and evaluable.
- **Defensible Uncertainty Estimation**: Monte Carlo Dropout (MCDO) generates a 95% spatial confidence cone (error radius in km) and a calibrated confidence score $[0.0, 1.0]$ that decays realistically with lead time.
- **Data Leakage Safeguards**: Strict storm-level event partitioning (`split_cyclones_by_event`) guarantees zero temporal or storm leakage between train, validation, and test sets.
- **Persistence Baseline Included**: Constant-velocity / Last-Known-Motion (LKM) benchmark against which all ML models are evaluated.

---

## 2. Directory Structure

```text
member2-prediction/
├── data/
│   ├── download_ibtracs.py        # Automated IBTrACS North Indian Ocean downloader
│   ├── cleaner.py                 # Data validation & 6-hour synoptic regularization
│   ├── features.py                # Kinematic feature engineering (Haversine, bearing, velocity)
│   ├── dataset.py                 # PyTorch sequence dataset & event-based splitter
│   └── benchmark_sample.csv       # Verified historical NIO benchmark dataset
├── models/
│   ├── baseline.py                # Persistence / Last-Known-Motion baseline
│   ├── recurrent_track_model.py   # Multi-task GRU sequence-to-sequence neural network
│   ├── uncertainty.py             # Monte Carlo Dropout variance & confidence decay
│   └── model_registry.py          # Weight checkpointing & model loader
├── training/
│   ├── train.py                   # Model training script
│   └── evaluate.py                # Comparative evaluation harness (Haversine MTE, MAE, skill)
├── api/
│   ├── main.py                    # FastAPI application entrypoint
│   ├── schemas.py                 # Pydantic schemas conforming to docs/SCHEMA.md
│   └── routes.py                  # API endpoints (/health, /forecast, /track, /intensity)
├── checkpoints/
│   └── track_model_v1.pt          # Serialized trained model weights
├── tests/
│   ├── test_data_validation.py
│   ├── test_feature_engineering.py
│   ├── test_sequences.py
│   ├── test_baseline.py
│   ├── test_model_inference.py
│   └── test_api.py
├── Dockerfile                     # Production container (port 8002)
├── .dockerignore
├── requirements.txt
├── README.md                      # This documentation
└── MEMBER2_HANDOFF.md             # Integration document for Member 3
```

---

## 3. Quick Start (Local Setup)

### Setup Environment
```bash
cd member2-prediction
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Train Model
Train the multi-task GRU on the benchmark dataset with strict event-based splitting:
```bash
python training/train.py --epochs 40
```

### Run Comparative Evaluation
Benchmark the trained ML model against the Persistence Baseline:
```bash
python training/evaluate.py
```

### Run Tests
Execute the unit and integration test suite:
```bash
pytest tests/ -v
```

### Start API Server
Launch the FastAPI microservice on port 8002:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8002
```

Interactive API documentation will be available at:
`http://localhost:8002/docs`

---

## 4. Docker Deployment

### Build Container
```bash
docker build -t cyclone-ml-prediction -f Dockerfile .
```

### Run Container
```bash
docker run -d --name ml-prediction -p 8002:8002 cyclone-ml-prediction
```

### Test Health Endpoint
```bash
curl http://localhost:8002/health
```

---

## 5. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status, active model version, and compute device |
| `POST` | `/forecast` | Joint track & intensity forecast with uncertainty cone and confidence |
| `POST` | `/track` | Dedicated track trajectory forecast (coordinates, error radius, confidence) |
| `POST` | `/intensity` | Dedicated intensity forecast (wind speed, central pressure, confidence) |
