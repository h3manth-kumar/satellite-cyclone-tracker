export interface CycloneSummary {
  id: string;
  name: string | null;
  basin: string;
  start_time: string;
  end_time: string | null;
  is_active: boolean;
  latest_lat: number | null;
  latest_lon: number | null;
  latest_wind_speed: number | null;
  latest_pressure: number | null;
  latest_classification: string | null;
  total_observations: number;
}

export interface Observation {
  id: string;
  cyclone_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  wind_speed: number | null;
  pressure: number | null;
  classification: string | null;
  source: string;
}

export interface ForecastPoint {
  lead_hours: number;
  target_time: string;
  latitude: number;
  longitude: number;
  predicted_wind_speed: number;
  predicted_pressure: number;
  uncertainty_radius_km: number;
  confidence: number;
}

export interface DetectionResult {
  detected: boolean;
  latitude?: number;
  longitude?: number;
  confidence: number;
  bbox?: number[];
  model_version: string;
}

export interface ClassificationResult {
  classification: string;
  confidence: number;
  estimated_wind_speed: number;
  probabilities?: Record<string, number>;
  model_version: string;
  explainability_heatmap_path?: string;
  explainability_heatmap_base64?: string;
}

export interface UnifiedAnalysisResponse {
  timestamp: string;
  status: 'success' | 'partial_success' | 'failed';
  cyclone: {
    id: string;
    name: string | null;
    basin: string;
    is_active: boolean;
  };
  observation?: {
    timestamp: string;
    latitude: number;
    longitude: number;
    wind_speed: number;
    pressure: number;
    classification: string;
    source: string;
    provenance: string;
  };
  detection?: DetectionResult;
  classification?: ClassificationResult;
  forecast: ForecastPoint[];
  models: Record<string, string>;
  warnings: string[];
  disclaimer: string;
}

export interface ServiceStatus {
  status: 'online' | 'degraded' | 'offline';
  url?: string;
  latency_ms?: number;
  error?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  database: {
    status: string;
    latency_ms?: number;
  };
  services: {
    ml_detection: ServiceStatus;
    ml_prediction: ServiceStatus;
  };
}

export interface SatelliteImageMeta {
  id: string;
  cyclone_id: string;
  timestamp: string;
  satellite: string;
  sensor: string;
  channel: string;
  file_path: string;
  resolution_km: number;
  download_url?: string;
}
