# CycloneAI Schema

## Cyclone
```json
{"id":"string","name":"string|null","basin":"string|null","start_time":"datetime|null","end_time":"datetime|null"}
```

## Observation
```json
{"id":"string","cyclone_id":"string","timestamp":"datetime","latitude":"float","longitude":"float","wind_speed":"float|null","pressure":"float|null","classification":"string|null","source":"string"}
```

## Satellite Image Metadata
```json
{"id":"string","timestamp":"datetime","satellite":"string","sensor":"string","channel":"string","file_path":"string"}
```

## Detection
```json
{"image_id":"string","detected":"boolean","latitude":"float|null","longitude":"float|null","confidence":"float","model_version":"string"}
```

## Classification
```json
{"image_id":"string","classification":"string","confidence":"float","model_version":"string"}
```

## Forecast
```json
{"cyclone_id":"string","forecast_time":"datetime","target_time":"datetime","latitude":"float","longitude":"float","predicted_wind_speed":"float|null","predicted_pressure":"float|null","confidence":"float","model_version":"string"}
```
