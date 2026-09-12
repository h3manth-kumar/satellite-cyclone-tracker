import {
  CycloneSummary,
  Observation,
  UnifiedAnalysisResponse,
  HealthResponse,
  SatelliteImageMeta
} from '../types/cyclone';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCyclones(basin?: string, activeOnly?: boolean): Promise<CycloneSummary[]> {
  const params = new URLSearchParams();
  if (basin) params.append('basin', basin);
  if (activeOnly) params.append('active_only', 'true');

  const res = await fetch(`${API_BASE}/cyclones?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to load cyclones: ${res.statusText}`);
  return res.json();
}

export async function fetchCycloneObservations(cycloneId: string): Promise<Observation[]> {
  const res = await fetch(`${API_BASE}/cyclones/${cycloneId}/observations`);
  if (!res.ok) throw new Error(`Failed to load observations: ${res.statusText}`);
  return res.json();
}

export async function fetchTrackGeoJSON(cycloneId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cyclones/${cycloneId}/track-geojson`);
  if (!res.ok) throw new Error(`Failed to load GeoJSON track: ${res.statusText}`);
  return res.json();
}

export async function fetchSatelliteImages(cycloneId?: string): Promise<SatelliteImageMeta[]> {
  const params = new URLSearchParams();
  if (cycloneId) params.append('cyclone_id', cycloneId);

  const res = await fetch(`${API_BASE}/satellite/images?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to load satellite images: ${res.statusText}`);
  return res.json();
}

export async function runFullAnalysis(cycloneId: string, satelliteImageId?: string): Promise<UnifiedAnalysisResponse> {
  const res = await fetch(`${API_BASE}/analysis/full`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      cyclone_id: cycloneId,
      satellite_image_id: satelliteImageId,
      persist_results: true
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Analysis pipeline execution failed');
  }
  return res.json();
}

export async function simulateCycloneFeed(cycloneId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cyclones/${cycloneId}/simulate-feed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Feed simulation failed: ${res.statusText}`);
  return res.json();
}

export async function fetchCycloneBulletin(cycloneId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cyclones/${cycloneId}/bulletin`);
  if (!res.ok) throw new Error(`Failed to load bulletin: ${res.statusText}`);
  return res.json();
}


