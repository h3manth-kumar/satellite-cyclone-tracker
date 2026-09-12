# CycloneAI — Member 1: AI/ML Detection, Center Localization & Classification

This subsystem implements the computer vision and deep learning service for **CycloneAI**. It handles satellite imagery preprocessing, cyclone presence detection, cyclone center localization, IMD intensity stage classification, confidence estimation, and Grad-CAM visual explainability.

---

## 🚀 Key Features

* **Satellite Image Preprocessing**: Automatic format validation, channel alignment (IR / Multi-channel RGB), resizing to standard input resolutions (224x224), and normalization.
* **Cyclone Detection**: High-sensitivity binary classification determining cyclone presence with calibrated confidence scores.
* **Center Localization**: Continuous spatial regression mapping normalized pixel center \((x, y) \in [0, 1]\) to geographical coordinates \((\text{Latitude}, \text{Longitude})\) given image bounding boxes.
* **IMD Intensity Classification**: Multi-class categorization aligning with official IMD stages:
  - *No Cyclone / Non-Depression*
  - *Depression*
  - *Deep Depression*
  - *Cyclonic Storm*
  - *Severe Cyclonic Storm*
  - *Very Severe Cyclonic Storm*
  - *Extremely Severe Cyclonic Storm*
  - *Super Cyclonic Storm*
* **Explainability (Grad-CAM)**: Gradient-weighted Class Activation Mapping highlighting spiral rainbands and central dense overcast features, rendered as base64-encoded PNG overlays.
* **FastAPI Inference Service**: Exposing `/health`, `/predict`, `/detect`, `/classify`, and `/explain` with strict Pydantic validation.
* **Dockerized & CPU-Optimized**: Self-contained container running on port `8001` with no external GPU hard-dependencies.

---

## 📁 Subsystem Structure

```text
member1-ml/
├── Dockerfile                   # Standalone CPU-optimized Dockerfile
├── .dockerignore                # Docker ignore rules
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Dev/Test dependencies
├── README.md                    # Setup and usage guide
├── MEMBER1_HANDOFF.md           # Handoff specification for Member 3
├── configs/
│   ├── default_config.yaml      # Service & class configuration
│   └── model_config.yaml        # Architecture hyperparameters
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── app.py               # FastAPI application factory
│   │   ├── routes.py            # API route endpoints
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── preprocessing/
│   │   ├── image_loader.py      # Image validation & loading
│   │   ├── transforms.py        # Normalization & augmentation transforms
│   │   └── geo_utils.py         # Geospatial coordinate conversions
│   ├── models/
│   │   ├── baseline_cnn.py      # Multi-task CNN architecture
│   │   ├── detector.py          # Cyclone presence detector
│   │   ├── classifier.py        # IMD stage classifier
│   │   └── center_locator.py    # Eye center locator
│   ├── explainability/
│   │   └── gradcam.py           # Grad-CAM heatmap generator & overlay
│   ├── inference/
│   │   └── engine.py            # End-to-end inference orchestrator
│   └── training/
│       ├── dataset.py           # Dataset loaders & synthetic fixtures
│       ├── train.py             # Multi-task training script
│       └── evaluate.py          # Precision/Recall/F1/MAE evaluation
├── tests/
│   ├── test_preprocessing.py    # Validation & geo tests
│   ├── test_models.py           # Model forward pass & output bounds
│   ├── test_inference.py        # End-to-end engine tests
│   ├── test_explainability.py   # Grad-CAM saliency tests
│   └── test_api.py              # FastAPI endpoint integration tests
└── artifacts/
    ├── models/                  # Saved checkpoint weights
    └── heatmaps/                # Output heatmaps
```

---

## 💻 Local Setup & Execution

### 1. Installation

```bash
cd member1-ml
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements-dev.txt
```

### 2. Run Baseline Training

```bash
python -m src.training.train --epochs 5 --batch-size 16 --output-dir artifacts/models
```

### 3. Run Test Suite

```bash
pytest tests/ -v
```

### 4. Start the Inference Service

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8001 --reload
```

---

## 🐳 Docker Deployment

### Build Container

```bash
docker build -t cyclone-ml-detection:v1.0.0 .
```

### Run Container

```bash
docker run -d -p 8001:8001 --name ml-detection cyclone-ml-detection:v1.0.0
```

### Test Health in Docker

```bash
curl http://localhost:8001/health
```

---

## 📡 API Reference

### Health Check: `GET /health`
* **Response**: `{"status": "healthy", "service": "ml-detection", "version": "v1.0.0", "model_loaded": true, "device": "cpu", "timestamp": "2026-09-04T12:00:00Z"}`

### Full Analysis: `POST /predict`
* **Form-data**:
  * `image`: Binary file (`.png`, `.jpg`, `.tif`)
  * `bbox` *(optional)*: `'{"min_lat": 10.0, "max_lat": 25.0, "min_lon": 80.0, "max_lon": 95.0}'`
  * `timestamp` *(optional)*: `"2026-09-04T12:00:00Z"`
* **Query param**: `?include_explainability=true`
* **Response**:
```json
{
  "timestamp": "2026-09-04T12:00:00Z",
  "detection": {
    "detected": true,
    "confidence": 0.9412,
    "latitude": 17.84,
    "longitude": 87.21,
    "pixel_center": {"x": 128, "y": 115},
    "normalized_center": {"x": 0.5714, "y": 0.5134}
  },
  "classification": {
    "class": "Severe Cyclonic Storm",
    "confidence": 0.8874,
    "probabilities": {
      "No Cyclone / Non-Depression": 0.0012,
      "Depression": 0.0125,
      "Deep Depression": 0.0341,
      "Cyclonic Storm": 0.0648,
      "Severe Cyclonic Storm": 0.8874,
      "Very Severe Cyclonic Storm": 0.0,
      "Extremely Severe Cyclonic Storm": 0.0,
      "Super Cyclonic Storm": 0.0
    }
  },
  "explainability": {
    "available": true,
    "heatmap_base64": "data:image/png;base64,iVBOR...",
    "heatmap_path": null
  },
  "model": {
    "detection_version": "v1.0.0",
    "classification_version": "v1.0.0",
    "backbone": "CycloneBaselineCNN-v1",
    "weights_loaded": true,
    "inference_latency_ms": 34.2
  }
}
```
