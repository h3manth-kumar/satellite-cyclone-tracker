# CycloneAI App Flow

```text
Open Dashboard
    ↓
Select cyclone/region
    ↓
Load satellite/observation data
    ↓
Run detection
    ↓
Run classification
    ↓
Generate track/intensity forecast
    ↓
Display current + historical + predicted state
    ↓
Show confidence and explainability
```

## Failure Flow

```text
ML service unavailable
        ↓
Show clear service error
        ↓
Continue showing valid stored/latest observations
        ↓
Never invent a prediction
```
