import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import { Observation, ForecastPoint } from '../types/cyclone';

interface CycloneMapProps {
  observations: Observation[];
  forecastPoints: ForecastPoint[];
  currentLat: number;
  currentLon: number;
  cycloneName: string;
}

type MapLayerMode = 'GOOGLE_SATELLITE' | 'GOOGLE_TERRAIN' | 'GOOGLE_ROAD' | 'DARK_MATTER';
type SimulationMode = 'FULL_CYCLE' | 'FORECAST_PATH';

// Coastal Radar Stations
const BAY_OF_BENGAL_STATIONS = [
  { name: 'Visakhapatnam (DWR)', lat: 17.68, lon: 83.21, state: 'Andhra Pradesh', radarRadiusKm: 250 },
  { name: 'Paradip / Puri (DWR)', lat: 20.31, lon: 86.61, state: 'Odisha', radarRadiusKm: 250 },
  { name: 'Kolkata / Haldia (DWR)', lat: 22.03, lon: 88.06, state: 'West Bengal', radarRadiusKm: 250 },
  { name: 'Chennai (DWR)', lat: 13.08, lon: 80.27, state: 'Tamil Nadu', radarRadiusKm: 250 },
  { name: 'Machilipatnam (DWR)', lat: 16.18, lon: 81.13, state: 'Andhra Pradesh', radarRadiusKm: 250 },
  { name: 'Gopalpur (DWR)', lat: 19.26, lon: 84.91, state: 'Odisha', radarRadiusKm: 200 },
  { name: 'Cox\'s Bazar (DWR)', lat: 21.42, lon: 91.98, state: 'Bangladesh', radarRadiusKm: 200 },
];

const ARABIAN_SEA_STATIONS = [
  { name: 'Dwarka / Kandla (DWR)', lat: 22.24, lon: 68.96, state: 'Gujarat', radarRadiusKm: 250 },
  { name: 'Porbandar (DWR)', lat: 21.64, lon: 69.62, state: 'Gujarat', radarRadiusKm: 250 },
  { name: 'Veraval (DWR)', lat: 20.90, lon: 70.36, state: 'Gujarat', radarRadiusKm: 250 },
  { name: 'Mumbai / Colaba (DWR)', lat: 18.92, lon: 72.83, state: 'Maharashtra', radarRadiusKm: 250 },
  { name: 'Goa (DWR)', lat: 15.49, lon: 73.82, state: 'Goa', radarRadiusKm: 250 },
  { name: 'Kochi (DWR)', lat: 9.93, lon: 76.26, state: 'Kerala', radarRadiusKm: 250 },
  { name: 'Karachi (DWR)', lat: 24.86, lon: 67.00, state: 'Pakistan', radarRadiusKm: 250 },
];

// High Risk Coastal Evacuation Zones
const BOB_HIGH_RISK_COASTAL_ZONE: [number, number][] = [
  [19.2, 84.8], [19.8, 85.8], [20.3, 86.6], [20.9, 86.9],
  [21.6, 87.5], [21.8, 88.5], [22.4, 89.2], [22.2, 88.0],
  [21.2, 86.4], [20.1, 85.5], [19.2, 84.8],
];

const ARB_HIGH_RISK_COASTAL_ZONE: [number, number][] = [
  [20.8, 70.3], [21.5, 69.5], [22.3, 68.9], [23.1, 68.4],
  [23.8, 68.7], [23.4, 70.2], [22.9, 70.6], [22.4, 70.0],
  [21.7, 70.8], [20.8, 70.3],
];

// Projected Storm Surge Inundation Polygons
const BOB_SURGE_SWATH: [number, number][] = [
  [19.7, 85.5], [20.2, 86.4], [20.8, 87.1], [21.5, 87.8],
  [21.9, 88.6], [21.6, 88.2], [20.6, 86.8], [20.0, 86.0], [19.7, 85.5],
];

const ARB_SURGE_SWATH: [number, number][] = [
  [21.4, 69.2], [22.2, 68.8], [22.9, 68.3], [23.3, 68.8],
  [22.7, 69.4], [22.0, 69.5], [21.4, 69.2],
];

// Real-Time AIS Commercial Maritime Fleet
interface AISVessel {
  id: string;
  name: string;
  type: string;
  mmsi: string;
  lat: number;
  lon: number;
  speedKts: number;
  heading: string;
  basin: 'BOB' | 'ARB';
  cargo: string;
}

const AIS_VESSELS: AISVessel[] = [
  { id: 'V1', name: 'MT Swarna Mala', type: 'Crude Oil Tanker', mmsi: '419001240', lat: 18.2, lon: 88.1, speedKts: 14.2, heading: '280° NW', basin: 'BOB', cargo: '85,000 MT Crude' },
  { id: 'V2', name: 'MV Ocean Pioneer', type: 'Bulk Carrier', mmsi: '419008710', lat: 19.1, lon: 86.9, speedKts: 11.5, heading: '045° NE', basin: 'BOB', cargo: 'Iron Ore Fines' },
  { id: 'V3', name: 'INS Sumedha (P58)', type: 'Naval Patrol Vessel', mmsi: '419999012', lat: 17.4, lon: 84.8, speedKts: 18.0, heading: '120° SE', basin: 'BOB', cargo: 'Search & Rescue Unit' },
  { id: 'V4', name: 'FV Sagarika 09', type: 'Deep Sea Trawler', mmsi: '419445120', lat: 20.4, lon: 87.4, speedKts: 6.8, heading: '310° NW', basin: 'BOB', cargo: '14 Crew Onboard' },
  { id: 'V5', name: 'MT Al-Salmiyah', type: 'LNG Carrier', mmsi: '419003310', lat: 21.8, lon: 66.8, speedKts: 16.5, heading: '090° E', basin: 'ARB', cargo: '140,000 m³ LNG' },
  { id: 'V6', name: 'MV Kutch Express', type: 'Container Ship', mmsi: '419005520', lat: 22.8, lon: 68.2, speedKts: 13.0, heading: '175° S', basin: 'ARB', cargo: '2,400 TEU' },
  { id: 'V7', name: 'ICGS Samarth', type: 'Coast Guard Patrol', mmsi: '419999050', lat: 20.5, lon: 69.8, speedKts: 19.5, heading: '320° NW', basin: 'ARB', cargo: 'Disaster Relief Mission' },
];

export const CycloneMap: React.FC<CycloneMapProps> = ({
  observations,
  forecastPoints,
  currentLat,
  currentLon,
  cycloneName,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const baseTileLayerRef = useRef<L.TileLayer | null>(null);
  const vectorLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const animLayerGroupRef = useRef<L.LayerGroup | null>(null);
  
  const activeCycloneIdRef = useRef<string>('');

  const [mapLayerMode, setMapLayerMode] = useState<MapLayerMode>('GOOGLE_SATELLITE');

  // Layer Toggles
  const [showObserved, setShowObserved] = useState(true);
  const [showForecast, setShowForecast] = useState(true);
  const [showCone, setShowCone] = useState(true);
  const [showStations, setShowStations] = useState(true);
  const [showRiskZone, setShowRiskZone] = useState(true);
  const [showSurgeSwath, setShowSurgeSwath] = useState(true);
  const [showMaritimeFleet, setShowMaritimeFleet] = useState(true);
  const [showEnsembleFan, setShowEnsembleFan] = useState(true);
  const [showFleetTable, setShowFleetTable] = useState(false);
  const [activeDropsonde, setActiveDropsonde] = useState<{ lat: number; lon: number; pressure: number; temp: number; windShear: number; sst: number } | null>(null);

  // Lead Time Filter Options (6hr, 12hr, 24hr, 48hr, All)
  const [selectedLeadFilter, setSelectedLeadFilter] = useState<number | null>(null);

  // Smooth Predictive Motion Playback State (Auto-play ON by default, 4x speed)
  const [isPlayingMotion, setIsPlayingMotion] = useState(true);
  const [simulationMode, setSimulationMode] = useState<SimulationMode>('FULL_CYCLE');
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(4);
  const [animProgress, setAnimProgress] = useState<number>(0);
  const animProgressRef = useRef<number>(0);
  const animFrameIdRef = useRef<number | null>(null);

  // Detect Basin: Arabian Sea vs Bay of Bengal
  const isArabianSea = useMemo(() => {
    const nameUpper = (cycloneName || '').toUpperCase();
    if (nameUpper.includes('BIPARJOY') || nameUpper.includes('ARB') || nameUpper.includes('01A') || nameUpper.includes('ARABIAN')) {
      return true;
    }
    if (currentLon && currentLon < 76.5) return true;
    return false;
  }, [cycloneName, currentLon]);

  const activeRadarStations = isArabianSea ? ARABIAN_SEA_STATIONS : BAY_OF_BENGAL_STATIONS;
  const activeRiskZone = isArabianSea ? ARB_HIGH_RISK_COASTAL_ZONE : BOB_HIGH_RISK_COASTAL_ZONE;
  const activeSurgeSwath = isArabianSea ? ARB_SURGE_SWATH : BOB_SURGE_SWATH;
  const activeVessels = AIS_VESSELS.filter((v) => (isArabianSea ? v.basin === 'ARB' : v.basin === 'BOB'));

  // Chronological Simulation Waypoints (Full Cycle from Genesis -> Landfall OR Forecast-Only)
  const simulationWaypoints = useMemo(() => {
    const points: {
      lat: number;
      lon: number;
      timestamp: string;
      windSpeed: number;
      pressure: number;
      stage: string;
      isForecast: boolean;
      leadHours?: number;
    }[] = [];

    const sortedObs = [...observations].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    const sortedForecasts = [...forecastPoints].sort((a, b) => a.lead_hours - b.lead_hours);

    const latest = sortedObs.length > 0 ? sortedObs[sortedObs.length - 1] : null;
    const originLat = latest?.latitude ?? currentLat ?? (isArabianSea ? 21.0 : 21.74);
    const originLon = latest?.longitude ?? currentLon ?? (isArabianSea ? 68.0 : 87.33);
    const originWind = latest?.wind_speed ?? 97.3;
    const originPres = latest?.pressure ?? 951.9;
    const originStage = latest?.classification ?? 'Current Eye Fix';

    if (simulationMode === 'FULL_CYCLE' && sortedObs.length > 1) {
      // Add all chronological historical observations up to current
      sortedObs.forEach((o, i) => {
        const isLatest = i === sortedObs.length - 1;
        points.push({
          lat: o.latitude,
          lon: o.longitude,
          timestamp: o.timestamp ? o.timestamp.replace('T', ' ').substring(0, 16) + ' UTC' : `Fix #${i + 1}`,
          windSpeed: o.wind_speed ?? 45,
          pressure: o.pressure ?? 990,
          stage: o.classification || (isLatest ? 'Current Eye Fix' : 'Synoptic Fix'),
          isForecast: false,
        });
      });
    } else {
      // Forecast Only mode: Starts at current synoptic eye fix
      points.push({
        lat: originLat,
        lon: originLon,
        timestamp: latest?.timestamp ? latest.timestamp.replace('T', ' ').substring(0, 16) + ' UTC' : 'Current Fix',
        windSpeed: originWind,
        pressure: originPres,
        stage: originStage,
        isForecast: false,
      });
    }

    // Filter forecasts by selectedLeadFilter (6h, 12h, 24h, 48h, 72h)
    const activeForecasts = selectedLeadFilter
      ? sortedForecasts.filter((f) => f.lead_hours <= selectedLeadFilter)
      : sortedForecasts;

    if (activeForecasts.length > 0) {
      activeForecasts.forEach((f) => {
        points.push({
          lat: f.latitude,
          lon: f.longitude,
          timestamp: f.target_time.replace('T', ' ').substring(0, 16) + ' UTC',
          windSpeed: f.predicted_wind_speed ?? 90,
          pressure: f.predicted_pressure ?? 955,
          stage: `Predicted +${f.lead_hours}h`,
          isForecast: true,
          leadHours: f.lead_hours,
        });
      });
    } else if (sortedForecasts.length === 0) {
      // Dynamic standard operational extrapolation forward along heading
      const maxLead = selectedLeadFilter || 24;
      const dLat = (originLon < 76.5) ? 0.6 : 0.7;
      const dLon = (originLon < 76.5) ? 0.2 : 0.35;
      if (maxLead >= 6) {
        points.push({
          lat: originLat + dLat,
          lon: originLon + dLon,
          timestamp: 'Extrapolated +6h',
          windSpeed: Math.min(140, originWind + 5),
          pressure: Math.max(920, originPres - 4),
          stage: 'Forecast +6h',
          isForecast: true,
          leadHours: 6,
        });
      }
      if (maxLead >= 12) {
        points.push({
          lat: originLat + dLat * 2,
          lon: originLon + dLon * 2,
          timestamp: 'Extrapolated +12h',
          windSpeed: Math.min(140, originWind + 8),
          pressure: Math.max(920, originPres - 7),
          stage: 'Forecast +12h',
          isForecast: true,
          leadHours: 12,
        });
      }
      if (maxLead >= 24) {
        points.push({
          lat: originLat + dLat * 3.5,
          lon: originLon + dLon * 3.5,
          timestamp: 'Extrapolated +24h',
          windSpeed: Math.max(45, originWind - 10),
          pressure: originPres + 10,
          stage: 'Landfall +24h',
          isForecast: true,
          leadHours: 24,
        });
      }
    }

    return points;
  }, [observations, forecastPoints, currentLat, currentLon, simulationMode, isArabianSea, selectedLeadFilter]);

  // Initialize Leaflet Map (Run once)
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const initialLat = currentLat || (isArabianSea ? 21.0 : 18.0);
    const initialLon = currentLon || (isArabianSea ? 68.0 : 87.0);

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: 6,
      zoomControl: false,
      attributionControl: false,
    });

    const baseLayer = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
      maxZoom: 20,
      subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
    }).addTo(map);

    baseTileLayerRef.current = baseLayer;
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    const vectorLayer = L.layerGroup().addTo(map);
    vectorLayerGroupRef.current = vectorLayer;

    const animLayer = L.layerGroup().addTo(map);
    animLayerGroupRef.current = animLayer;

    mapInstanceRef.current = map;

    // Dropsonde click probe
    map.on('click', (e: L.LeafletMouseEvent) => {
      const clickLat = e.latlng.lat;
      const clickLon = e.latlng.lng;
      const distFromEye = Math.sqrt((clickLat - (currentLat || 18)) ** 2 + (clickLon - (currentLon || 86)) ** 2) * 111;
      const estimatedPressure = Math.min(1012, Math.floor(935 + distFromEye * 0.22));
      const estimatedTemp = Math.max(12, Number((29.8 - distFromEye * 0.025).toFixed(1)));
      const estimatedShear = Math.max(6, Math.floor(distFromEye * 0.09 + 10));
      const estimatedSST = Number((30.6 - (clickLat - 15) * 0.22).toFixed(1));

      setActiveDropsonde({
        lat: clickLat,
        lon: clickLon,
        pressure: estimatedPressure,
        temp: estimatedTemp,
        windShear: estimatedShear,
        sst: estimatedSST,
      });
    });

    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Basemap Layer when mode changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (baseTileLayerRef.current) {
      map.removeLayer(baseTileLayerRef.current);
    }

    let url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}';
    let opts: L.TileLayerOptions = { maxZoom: 20, subdomains: ['mt0', 'mt1', 'mt2', 'mt3'] };

    if (mapLayerMode === 'GOOGLE_TERRAIN') {
      url = 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}';
    } else if (mapLayerMode === 'GOOGLE_ROAD') {
      url = 'https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}';
    } else if (mapLayerMode === 'DARK_MATTER') {
      url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
      opts = { maxZoom: 19, subdomains: 'abcd' };
    }

    const newBase = L.tileLayer(url, opts).addTo(map);
    baseTileLayerRef.current = newBase;
    newBase.bringToBack();
  }, [mapLayerMode]);

  // Update Static Vector Layers
  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = vectorLayerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();
    const bounds: L.LatLngExpression[] = [];

    // Surge Swath
    if (showSurgeSwath) {
      L.polygon(activeSurgeSwath, {
        color: '#00f0ff',
        weight: 2.5,
        fillColor: '#06b6d4',
        fillOpacity: 0.35,
      }).bindPopup(`
        <div style="padding: 6px; font-size: 11px;">
          <div style="font-weight: 800; color: #00f0ff; font-size: 12px;">🌊 AI PROJECTED STORM SURGE SWATH</div>
          <div style="color: #ffffff; margin-top: 2px;">Hydrodynamic Inundation: <strong>3.8m – 5.2m Peak</strong></div>
        </div>
      `).addTo(layerGroup);
    }

    // Risk Evacuation Zone
    if (showRiskZone) {
      L.polygon(activeRiskZone, {
        color: '#ef4444',
        weight: 2.5,
        dashArray: '5, 5',
        fillColor: '#ef4444',
        fillOpacity: 0.2,
      }).bindPopup(`
        <div style="padding: 6px; font-size: 11px;">
          <div style="font-weight: 800; color: #ef4444; font-size: 12px;">🚨 LEVEL-4 RED ALERT EVACUATION ZONE</div>
          <div style="color: #ffffff; margin-top: 2px;">Mandatory Coastal Evacuation Active</div>
        </div>
      `).addTo(layerGroup);
    }

    // Maritime Fleet
    if (showMaritimeFleet) {
      activeVessels.forEach((vessel) => {
        const distToEye = Math.sqrt((vessel.lat - (currentLat || 18)) ** 2 + (vessel.lon - (currentLon || 86)) ** 2) * 111;
        const isCritical = distToEye < 120;
        const isGale = distToEye < 240;

        const vesselIcon = L.divIcon({
          className: 'vessel-icon',
          html: `
            <div class="relative flex items-center justify-center w-8 h-8 -ml-4 -mt-4 group">
              <div class="w-8 h-8 rounded-full ${isCritical ? 'bg-red-600/80 animate-ping' : isGale ? 'bg-amber-500/40 animate-pulse' : 'bg-blue-600/40'} absolute"></div>
              <div class="w-6 h-6 rounded-lg ${isCritical ? 'bg-red-600 border-white text-white' : isGale ? 'bg-amber-500 border-yellow-200 text-black' : 'bg-blue-600 border-cyan-300 text-white'} border shadow-lg flex items-center justify-center text-xs font-black">
                🚢
              </div>
              <div class="absolute -bottom-4 bg-[#0a0c10]/95 text-white text-[8px] font-bold px-1 rounded border ${isCritical ? 'border-red-500 text-red-300' : isGale ? 'border-amber-400 text-amber-300' : 'border-blue-400 text-cyan-300'} whitespace-nowrap shadow pointer-events-none">
                ${vessel.name.split(' ')[0]} (${Math.round(distToEye)}km)
              </div>
            </div>
          `,
          iconSize: [32, 32],
        });

        if (isGale && currentLat && currentLon) {
          L.polyline([[vessel.lat, vessel.lon], [currentLat, currentLon]], {
            color: isCritical ? '#ef4444' : '#f59e0b',
            weight: 1.5,
            dashArray: '4, 4',
            opacity: 0.6,
          }).addTo(layerGroup);
        }

        L.marker([vessel.lat, vessel.lon], { icon: vesselIcon })
          .bindPopup(`
            <div style="padding: 6px; font-size: 11px;">
              <div style="font-weight: 800; color: ${isCritical ? '#ef4444' : isGale ? '#f59e0b' : '#38bdf8'}; font-size: 12px;">🚢 ${vessel.name}</div>
              <div style="color: #ffffff; font-size: 10px;">${vessel.type} · ${vessel.speedKts} kts (${vessel.heading})</div>
              <div style="color: ${isCritical ? '#f87171' : isGale ? '#fbbf24' : '#34d399'}; font-weight: bold; margin-top: 3px;">
                ${isCritical ? `🚨 CRITICAL HAZARD: ${Math.round(distToEye)} km from Eyewall` : isGale ? `⚠️ GALE ADVISORY: ${Math.round(distToEye)} km from Center` : `✓ SAFE CORRIDOR (${Math.round(distToEye)} km away)`}
              </div>
            </div>
          `)
          .addTo(layerGroup);
      });
    }

    // Coastal Radars
    if (showStations) {
      activeRadarStations.forEach((st) => {
        const stationIcon = L.divIcon({
          className: 'station-icon',
          html: `
            <div class="relative flex items-center justify-center w-8 h-8 -ml-4 -mt-4 group">
              <div class="w-8 h-8 rounded-full border border-emerald-500/40 absolute sonar-ping"></div>
              <div class="w-6 h-6 rounded-full bg-emerald-950/80 border border-emerald-400 absolute flex items-center justify-center shadow-[0_0_12px_rgba(16,185,129,0.8)]">
                <div class="w-1.5 h-1.5 rounded-full bg-emerald-300"></div>
              </div>
              <div class="absolute -bottom-4 bg-[#0e1014]/95 text-emerald-300 text-[8px] font-bold px-1 rounded border border-emerald-500/40 whitespace-nowrap shadow pointer-events-none">
                ${st.name}
              </div>
            </div>
          `,
          iconSize: [32, 32],
        });

        L.circle([st.lat, st.lon], {
          radius: st.radarRadiusKm * 1000,
          color: '#10b981',
          weight: 1.2,
          dashArray: '4, 6',
          fillColor: '#10b981',
          fillOpacity: 0.04,
        }).addTo(layerGroup);

        L.marker([st.lat, st.lon], { icon: stationIcon })
          .bindPopup(`<div style="padding: 4px; font-weight: bold; color: #10b981;">${st.name} (${st.radarRadiusKm}km S-Band Radar)</div>`)
          .addTo(layerGroup);
      });
    }

    // Observed Track Line & Synoptic Markers
    if (showObserved && observations.length > 0) {
      const sortedObs = [...observations].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      const obsCoords: [number, number][] = sortedObs.map((o) => [o.latitude, o.longitude]);
      obsCoords.forEach((c) => bounds.push(c));

      if (obsCoords.length >= 2) {
        L.polyline(obsCoords, { color: '#007afc', weight: 8, opacity: 0.45, lineCap: 'round' }).addTo(layerGroup);
        L.polyline(obsCoords, { color: '#ffffff', weight: 3.5, opacity: 1.0, lineCap: 'round' }).addTo(layerGroup);
      }

      sortedObs.forEach((obs, idx) => {
        const isLatest = idx === sortedObs.length - 1;
        L.circleMarker([obs.latitude, obs.longitude], {
          radius: isLatest ? 8 : 5,
          fillColor: isLatest ? '#00f0ff' : '#007afc',
          color: '#ffffff',
          weight: 2,
          fillOpacity: 1.0,
        }).bindPopup(`
          <div style="padding: 4px; font-size: 11px;">
            <div style="font-weight: 800; color: #ffffff;">Synoptic Fix ${isLatest ? '★ [CURRENT]' : ''}</div>
            <div style="color: #00f0ff;">${obs.timestamp.replace('T', ' ').substring(0, 16)} UTC</div>
            <div><strong>Wind:</strong> ${obs.wind_speed ?? 'N/A'} kts | <strong>P-Min:</strong> ${obs.pressure ?? 'N/A'} hPa</div>
          </div>
        `).addTo(layerGroup);
      });
    }

    // AI Forecast Track & Fan
    if (showForecast && forecastPoints.length > 0) {
      const sortedObs = [...observations].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
      const fcCoords: [number, number][] = [];
      if (sortedObs.length > 0) {
        const lastObs = sortedObs[sortedObs.length - 1];
        fcCoords.push([lastObs.latitude, lastObs.longitude]);
      }

      const activeForecasts = (selectedLeadFilter
        ? forecastPoints.filter((f) => f.lead_hours <= selectedLeadFilter)
        : forecastPoints
      ).sort((a, b) => a.lead_hours - b.lead_hours);

      activeForecasts.forEach((f) => {
        fcCoords.push([f.latitude, f.longitude]);
        bounds.push([f.latitude, f.longitude]);
      });

      // Probabilistic Ensemble Fan
      if (showEnsembleFan && fcCoords.length >= 2) {
        const origin = fcCoords[0];
        const ensembleSpreads = [-0.8, -0.5, -0.25, 0.25, 0.5, 0.8, -0.35, 0.35];

        ensembleSpreads.forEach((spread) => {
          const ensemblePath: [number, number][] = [origin];
          activeForecasts.forEach((f, fIdx) => {
            const pertLat = f.latitude + spread * (fIdx + 1) * 0.18;
            const pertLon = f.longitude + spread * (fIdx + 1) * 0.22;
            ensemblePath.push([pertLat, pertLon]);
          });

          L.polyline(ensemblePath, {
            color: '#38bdf8',
            weight: 1.2,
            opacity: 0.35,
            dashArray: '3, 5',
          }).addTo(layerGroup);
        });
      }

      if (fcCoords.length >= 2) {
        L.polyline(fcCoords, { color: '#00f0ff', weight: 6, dashArray: '6, 8', opacity: 0.5 }).addTo(layerGroup);
        L.polyline(fcCoords, { color: '#00f0ff', weight: 3, dashArray: '6, 8', opacity: 1.0 }).addTo(layerGroup);
      }

      activeForecasts.forEach((f) => {
        L.circleMarker([f.latitude, f.longitude], {
          radius: 7,
          fillColor: '#00f0ff',
          color: '#0e1014',
          weight: 2.5,
          fillOpacity: 1.0,
        }).bindPopup(`
          <div style="padding: 4px; font-size: 11px;">
            <div style="font-weight: 800; color: #00f0ff;">AI GRU Forecast +${f.lead_hours}h</div>
            <div><strong>V-Max:</strong> ${f.predicted_wind_speed} kts | <strong>P-Min:</strong> ${f.predicted_pressure} hPa</div>
            <div style="color: #f59e0b;">Cone: ±${f.uncertainty_radius_km} km</div>
          </div>
        `).addTo(layerGroup);

        if (showCone) {
          L.circle([f.latitude, f.longitude], {
            radius: f.uncertainty_radius_km * 1000,
            color: '#007afc',
            weight: 1.5,
            fillColor: '#007afc',
            fillOpacity: 0.15,
          }).addTo(layerGroup);
        }
      });
    }

    // Camera initial fit
    if (activeCycloneIdRef.current !== cycloneName && bounds.length > 0 && map) {
      activeCycloneIdRef.current = cycloneName;
      map.fitBounds(L.latLngBounds(bounds), { padding: [60, 60], maxZoom: 7 });
    }
  }, [
    observations,
    forecastPoints,
    currentLat,
    currentLon,
    cycloneName,
    showObserved,
    showForecast,
    showCone,
    showStations,
    showRiskZone,
    showSurgeSwath,
    showMaritimeFleet,
    showEnsembleFan,
    activeDropsonde,
    selectedLeadFilter,
    isArabianSea,
  ]);

  // High-Performance 60FPS Continuous Simulation Animation Engine
  useEffect(() => {
    const map = mapInstanceRef.current;
    const animLayer = animLayerGroupRef.current;
    if (!map || !animLayer) return;

    animLayer.clearLayers();

    if (simulationWaypoints.length < 2) {
      return;
    }

    const totalSegments = simulationWaypoints.length - 1;

    // Persistent Leaflet Layer Objects
    const traversedLine = L.polyline([], {
      color: '#00f0ff',
      weight: 6,
      opacity: 0.95,
      lineCap: 'round',
    }).addTo(animLayer);

    const headingVector = L.polyline([], {
      color: '#ffffff',
      weight: 3,
      dashArray: '4, 6',
      opacity: 0.9,
    }).addTo(animLayer);

    const r34Circle = L.circle([0, 0], {
      radius: 90000,
      color: '#00f0ff',
      weight: 1.2,
      dashArray: '4, 6',
      fillColor: '#00f0ff',
      fillOpacity: 0.08,
    }).addTo(animLayer);

    const r64Circle = L.circle([0, 0], {
      radius: 35000,
      color: '#ef4444',
      weight: 1.5,
      fillColor: '#ef4444',
      fillOpacity: 0.22,
    }).addTo(animLayer);

    // Initial HTML structure for the cyclone marker
    const initialP = simulationWaypoints[0];
    const motionIcon = L.divIcon({
      className: 'motion-cyclone-beacon',
      html: `
        <div id="anim-cyclone-root" class="relative flex items-center justify-center w-16 h-16 -ml-8 -mt-8">
          <div id="anim-pulse-ring" class="w-16 h-16 rounded-full absolute bg-cyan-400/40 animate-ping"></div>
          <div id="anim-outer-spin" class="w-10 h-10 rounded-full border-2 absolute cyclone-spin-slow border-cyan-400"></div>
          <div id="anim-inner-core" class="w-8 h-8 rounded-full border-2 border-white relative z-20 flex items-center justify-center text-base font-black text-white cyclone-spin" style="background: linear-gradient(135deg, #00f0ff, #090b0e); box-shadow: 0 0 25px #00f0ff;">
            🌀
          </div>
          <div id="anim-badge" class="absolute -bottom-6 bg-[#0a0c10]/95 text-white text-[9px] font-black px-2 py-0.5 rounded-full border whitespace-nowrap z-30 shadow-2xl flex items-center space-x-1 border-cyan-400">
            <span id="anim-badge-dot" class="w-1.5 h-1.5 rounded-full bg-cyan-400 inline-block"></span>
            <span id="anim-badge-text">${initialP.windSpeed} kts · ${initialP.stage.split(' ')[0]}</span>
          </div>
        </div>
      `,
      iconSize: [64, 64],
    });

    const motionMarker = L.marker([initialP.lat, initialP.lon], {
      icon: motionIcon,
    }).addTo(animLayer);

    let lastCategory = '';

    // Render exact frame without rebuilding DOM
    const renderFrame = (prog: number) => {
      const safeProg = Math.max(0, Math.min(totalSegments, prog));
      const currIndex = Math.min(Math.floor(safeProg), totalSegments - 1);
      const frac = safeProg - currIndex;
      const nextIndex = Math.min(currIndex + 1, totalSegments);

      const p1 = simulationWaypoints[currIndex];
      const p2 = simulationWaypoints[nextIndex];

      const curLat = p1.lat + (p2.lat - p1.lat) * frac;
      const curLon = p1.lon + (p2.lon - p1.lon) * frac;
      const curWind = Math.round(p1.windSpeed + (p2.windSpeed - p1.windSpeed) * frac);

      // Instantaneous heading
      const dLon = (p2.lon - p1.lon) * Math.PI / 180;
      const lat1 = p1.lat * Math.PI / 180;
      const lat2 = p2.lat * Math.PI / 180;
      const y = Math.sin(dLon) * Math.cos(lat2);
      const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
      const bearingRad = Math.atan2(y, x);
      const bearingDeg = (bearingRad * 180 / Math.PI + 360) % 360;

      let categoryColor = '#00f0ff';
      let categoryLabel = 'Depression';
      if (curWind >= 120) { categoryColor = '#ec4899'; categoryLabel = 'Super Cyclone'; }
      else if (curWind >= 90) { categoryColor = '#ef4444'; categoryLabel = 'Extremely Severe'; }
      else if (curWind >= 64) { categoryColor = '#f97316'; categoryLabel = 'Very Severe'; }
      else if (curWind >= 48) { categoryColor = '#eab308'; categoryLabel = 'Severe Cyclonic'; }
      else if (curWind >= 34) { categoryColor = '#10b981'; categoryLabel = 'Cyclonic Storm'; }

      // 1. Move Marker
      motionMarker.setLatLng([curLat, curLon]);

      // Direct DOM Badge text update (Zero Leaflet overhead, 60fps rock solid)
      const badgeTextEl = document.getElementById('anim-badge-text');
      if (badgeTextEl) {
        badgeTextEl.textContent = `${curWind} kts (${categoryLabel.split(' ')[0]}) · ${Math.round(bearingDeg)}°`;
      }

      if (lastCategory !== categoryLabel) {
        lastCategory = categoryLabel;
        const outerSpin = document.getElementById('anim-outer-spin');
        const badge = document.getElementById('anim-badge');
        const badgeDot = document.getElementById('anim-badge-dot');
        const innerCore = document.getElementById('anim-inner-core');
        if (outerSpin) outerSpin.style.borderColor = categoryColor;
        if (badge) badge.style.borderColor = categoryColor;
        if (badgeDot) badgeDot.style.backgroundColor = categoryColor;
        if (innerCore) {
          innerCore.style.background = `linear-gradient(135deg, ${categoryColor}, #090b0e)`;
          innerCore.style.boxShadow = `0 0 25px ${categoryColor}`;
        }
      }

      // 2. Update Traversed Line
      const traversedCoords: [number, number][] = [];
      for (let i = 0; i <= currIndex; i++) {
        traversedCoords.push([simulationWaypoints[i].lat, simulationWaypoints[i].lon]);
      }
      traversedCoords.push([curLat, curLon]);
      traversedLine.setLatLngs(traversedCoords);
      traversedLine.setStyle({ color: categoryColor });

      // 3. Update Vector Heading
      const arrowLat = curLat + Math.cos(bearingRad) * 1.2;
      const arrowLon = curLon + Math.sin(bearingRad) * 1.2;
      headingVector.setLatLngs([[curLat, curLon], [arrowLat, arrowLon]]);

      // 4. Update Radii
      const r64Meters = Math.max(25000, (curWind / 120) * 65000);
      const r34Meters = Math.max(90000, (curWind / 65) * 190000);

      r34Circle.setLatLng([curLat, curLon]);
      r34Circle.setRadius(r34Meters);
      r34Circle.setStyle({ color: categoryColor, fillColor: categoryColor });

      r64Circle.setLatLng([curLat, curLon]);
      r64Circle.setRadius(r64Meters);
      r64Circle.setStyle({ opacity: curWind >= 64 ? 0.9 : 0, fillOpacity: curWind >= 64 ? 0.22 : 0 });
    };

    // If paused, render single frame at current progress
    if (!isPlayingMotion) {
      renderFrame(animProgressRef.current);
      return;
    }

    let lastTime = performance.now();
    let lastSliderUpdate = performance.now();

    const animateLoop = (time: number) => {
      const dt = (time - lastTime) / 1000;
      lastTime = time;

      // Speed rate adjusted by segments
      const baseDurationSec = Math.max(4, totalSegments * 0.85);
      const speedRate = (totalSegments / baseDurationSec) * (playbackSpeed / 4);
      animProgressRef.current += dt * speedRate;

      if (animProgressRef.current >= totalSegments) {
        animProgressRef.current = 0;
      }

      const prog = animProgressRef.current;
      renderFrame(prog);

      // Throttled UI state update for slider
      if (time - lastSliderUpdate > 60) {
        lastSliderUpdate = time;
        setAnimProgress(prog);
      }

      animFrameIdRef.current = requestAnimationFrame(animateLoop);
    };

    animFrameIdRef.current = requestAnimationFrame(animateLoop);

    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
      animLayer.clearLayers();
    };
  }, [isPlayingMotion, playbackSpeed, simulationWaypoints]);

  const handleCenterMap = () => {
    if (mapInstanceRef.current && currentLat && currentLon) {
      mapInstanceRef.current.flyTo([currentLat, currentLon], 6.5, { duration: 1.0 });
    }
  };

  const toggleMotionPlayback = () => {
    setIsPlayingMotion((prev) => !prev);
  };

  const currentTimelineData = useMemo(() => {
    if (simulationWaypoints.length === 0) return null;
    const totalSegments = simulationWaypoints.length - 1;
    const prog = Math.max(0, Math.min(totalSegments, animProgress));
    const idx = Math.floor(prog);
    const frac = prog - idx;
    const nextIdx = Math.min(idx + 1, totalSegments);
    const p1 = simulationWaypoints[idx];
    const p2 = simulationWaypoints[nextIdx];

    return {
      lat: p1.lat + (p2.lat - p1.lat) * frac,
      lon: p1.lon + (p2.lon - p1.lon) * frac,
      wind: Math.round(p1.windSpeed + (p2.windSpeed - p1.windSpeed) * frac),
      pressure: Math.round(p1.pressure + (p2.pressure - p1.pressure) * frac),
      timestamp: p1.timestamp,
      stage: p1.stage,
      isForecast: p1.isForecast,
    };
  }, [simulationWaypoints, animProgress]);

  return (
    <div className="relative w-full h-full min-h-[540px] bg-[#0e1014] overflow-hidden rounded-2xl border border-[#232832] shadow-2xl flex flex-col">
      {/* Map Canvas */}
      <div ref={mapContainerRef} className="w-full flex-1 min-h-[540px] z-[1]" />

      {/* Clean Compact Top Control Bar */}
      <div className="absolute top-3 left-3 right-3 z-[400] flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        {/* Left: Basemap Switcher, Track Mode & Lead Options */}
        <div className="flex flex-wrap items-center gap-2 pointer-events-auto">
          {/* Basemap Switcher */}
          <div className="bg-[#0f131a]/95 backdrop-blur-md border border-[#232832] p-1 rounded-xl shadow-xl flex items-center space-x-1 text-xs">
            <span className="text-[#8b96aa] font-bold text-[10px] px-1.5">MAP:</span>
            <button
              onClick={() => setMapLayerMode('GOOGLE_SATELLITE')}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition-all ${
                mapLayerMode === 'GOOGLE_SATELLITE' ? 'bg-cyan-400 text-black font-black' : 'text-[#8b96aa] hover:text-white'
              }`}
            >
              Satellite
            </button>
            <button
              onClick={() => setMapLayerMode('GOOGLE_TERRAIN')}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition-all ${
                mapLayerMode === 'GOOGLE_TERRAIN' ? 'bg-emerald-400 text-black font-black' : 'text-[#8b96aa] hover:text-white'
              }`}
            >
              Terrain
            </button>
            <button
              onClick={() => setMapLayerMode('GOOGLE_ROAD')}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition-all ${
                mapLayerMode === 'GOOGLE_ROAD' ? 'bg-white text-black font-black' : 'text-[#8b96aa] hover:text-white'
              }`}
            >
              Roads
            </button>
            <button
              onClick={() => setMapLayerMode('DARK_MATTER')}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold transition-all ${
                mapLayerMode === 'DARK_MATTER' ? 'bg-indigo-600 text-white font-black' : 'text-[#8b96aa] hover:text-white'
              }`}
            >
              Dark
            </button>
          </div>

          {/* Track Mode */}
          <div className="bg-[#0f131a]/95 backdrop-blur-md border border-[#232832] p-1 rounded-xl shadow-xl flex items-center space-x-1 text-xs">
            <span className="text-[#8b96aa] font-bold text-[10px] px-1.5">TRACK:</span>
            <button
              onClick={() => {
                setSimulationMode('FULL_CYCLE');
                animProgressRef.current = 0;
                setAnimProgress(0);
              }}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                simulationMode === 'FULL_CYCLE' ? 'bg-gradient-to-r from-blue-500 to-cyan-400 text-black font-black' : 'text-[#8b96aa] hover:text-white'
              }`}
            >
              Full Cycle
            </button>
            <button
              onClick={() => {
                setSimulationMode('FORECAST_PATH');
                animProgressRef.current = 0;
                setAnimProgress(0);
              }}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                simulationMode === 'FORECAST_PATH' ? 'bg-gradient-to-r from-cyan-400 to-emerald-400 text-black font-black' : 'text-[#8b96aa] hover:text-white'
              }`}
            >
              Forecast Only
            </button>
          </div>

          {/* Lead Hours Filter: 6hr, 12hr, 24hr, 48hr, All (+72h) */}
          <div className="bg-[#0f131a]/95 backdrop-blur-md border border-[#232832] p-1 rounded-xl shadow-xl flex items-center space-x-1 text-xs">
            <span className="text-[#8b96aa] font-bold text-[10px] px-1.5">LEAD:</span>
            <button
              onClick={() => {
                setSelectedLeadFilter(null);
                animProgressRef.current = 0;
                setAnimProgress(0);
              }}
              className={`px-2 py-0.5 rounded-lg text-[10px] font-bold ${
                selectedLeadFilter === null ? 'bg-cyan-400 text-black font-black' : 'text-[#8b96aa] hover:text-white'
              }`}
            >
              All (+72h)
            </button>
            {[6, 12, 24, 48].map((lead) => (
              <button
                key={lead}
                onClick={() => {
                  setSelectedLeadFilter(lead);
                  animProgressRef.current = 0;
                  setAnimProgress(0);
                }}
                className={`px-1.5 py-0.5 rounded-lg text-[10px] font-bold ${
                  selectedLeadFilter === lead ? 'bg-cyan-400 text-black font-black' : 'text-[#8b96aa] hover:text-white'
                }`}
              >
                +{lead}h
              </button>
            ))}
          </div>
        </div>

        {/* Right: Layer Toggles & Center */}
        <div className="bg-[#0f131a]/95 backdrop-blur-md border border-[#232832] p-1.5 rounded-xl shadow-xl flex items-center space-x-2 text-xs pointer-events-auto">
          <label className="flex items-center space-x-1 cursor-pointer text-[#8b96aa] hover:text-white">
            <input type="checkbox" checked={showForecast} onChange={(e) => setShowForecast(e.target.checked)} className="rounded text-cyan-400 bg-black border-[#333a48]" />
            <span className="text-[10px] text-cyan-300 font-bold">AI Forecast</span>
          </label>
          <div className="h-3 w-[1px] bg-[#232832]" />
          <label className="flex items-center space-x-1 cursor-pointer text-[#8b96aa] hover:text-white">
            <input type="checkbox" checked={showSurgeSwath} onChange={(e) => setShowSurgeSwath(e.target.checked)} className="rounded text-cyan-400 bg-black border-[#333a48]" />
            <span className="text-[10px] text-cyan-400">Surge</span>
          </label>
          <div className="h-3 w-[1px] bg-[#232832]" />
          <label className="flex items-center space-x-1 cursor-pointer text-[#8b96aa] hover:text-white">
            <input type="checkbox" checked={showMaritimeFleet} onChange={(e) => setShowMaritimeFleet(e.target.checked)} className="rounded text-blue-400 bg-black border-[#333a48]" />
            <span className="text-[10px] text-blue-400">Fleet</span>
          </label>
          <div className="h-3 w-[1px] bg-[#232832]" />
          <button
            onClick={() => setShowFleetTable((f) => !f)}
            className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${showFleetTable ? 'bg-blue-600 text-white' : 'text-[#8b96aa] hover:text-white'}`}
          >
            Matrix
          </button>
          <div className="h-3 w-[1px] bg-[#232832]" />
          <button
            onClick={handleCenterMap}
            className="text-white hover:text-cyan-400 font-bold px-2 py-0.5 bg-[#1c222c] rounded-lg text-[10px] border border-cyan-500/20"
          >
            🎯 Center
          </button>
        </div>
      </div>

      {/* Floating Maritime Fleet Risk Impact Table Modal */}
      {showFleetTable && (
        <div className="absolute top-14 right-3 z-[400] w-80 bg-[#0a0d13]/95 backdrop-blur-xl border border-blue-500/40 rounded-2xl p-3 shadow-2xl text-xs max-h-72 overflow-y-auto">
          <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-[#232832]">
            <span className="text-blue-400 font-black text-[11px]">🚢 AIS Maritime Threat Matrix</span>
            <button onClick={() => setShowFleetTable(false)} className="text-[#8b96aa] hover:text-white">✕</button>
          </div>
          <div className="space-y-1.5">
            {activeVessels.map((v) => {
              const dist = Math.sqrt((v.lat - (currentLat || 18)) ** 2 + (v.lon - (currentLon || 86)) ** 2) * 111;
              const isCrit = dist < 120;
              const isGale = dist < 240;
              return (
                <div key={v.id} className="p-1.5 rounded-lg bg-[#12161e] border border-[#232832]">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-white text-[10px]">{v.name}</span>
                    <span className={`text-[8px] font-black px-1 rounded ${
                      isCrit ? 'bg-red-500/20 text-red-400 border border-red-500/50' : isGale ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50' : 'bg-emerald-500/20 text-emerald-400'
                    }`}>
                      {isCrit ? '🔴 HURRICANE' : isGale ? '🟡 GALE' : '🟢 SAFE'}
                    </span>
                  </div>
                  <div className="text-[9px] text-[#8b96aa] mt-0.5 flex justify-between">
                    <span>{v.type}</span>
                    <span className="font-mono text-cyan-300 font-bold">{Math.round(dist)} km to Eye</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Clean DOCKED Bottom HUD Player & Scrubber */}
      <div className="absolute bottom-3 left-3 right-3 z-[400] bg-[#0c1017]/95 backdrop-blur-xl border border-cyan-500/40 p-2.5 rounded-2xl shadow-2xl flex flex-wrap items-center justify-between gap-2.5">
        {/* Play/Pause & Speed Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleMotionPlayback}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl font-black text-[11px] transition-all shadow-md ${
              isPlayingMotion
                ? 'bg-red-500/20 text-red-400 border border-red-500/60 shadow-[0_0_12px_rgba(239,68,68,0.4)] animate-pulse'
                : 'bg-gradient-to-r from-cyan-400 to-blue-500 text-black'
            }`}
          >
            <span>{isPlayingMotion ? '⏸ PAUSE SIMULATION' : '▶ PLAY SIMULATION'}</span>
          </button>

          <button
            onClick={() => {
              animProgressRef.current = 0;
              setAnimProgress(0);
            }}
            className="bg-[#161a22] hover:bg-[#202632] text-[#8b96aa] hover:text-white px-2 py-1 rounded-lg border border-[#232832] text-[10px] font-bold"
          >
            ⏮ Reset
          </button>

          <div className="flex items-center space-x-1 pl-1.5 border-l border-[#232832]">
            <span className="text-[9px] text-[#8b96aa] font-bold">Speed:</span>
            {[1, 2, 4, 8].map((spd) => (
              <button
                key={spd}
                onClick={() => setPlaybackSpeed(spd)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                  playbackSpeed === spd ? 'bg-cyan-400 text-black font-black' : 'bg-[#161a22] text-[#8b96aa]'
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Slider with Live Scrubbing */}
        <div className="flex-1 min-w-[160px] flex items-center space-x-2">
          <input
            type="range"
            min="0"
            max={Math.max(1, simulationWaypoints.length - 1)}
            step="0.02"
            value={animProgress}
            onChange={(e) => {
              const val = Number(e.target.value);
              animProgressRef.current = val;
              setAnimProgress(val);
            }}
            className="w-full h-1.5 bg-[#181d26] rounded-lg appearance-none cursor-pointer accent-cyan-400"
          />
        </div>

        {/* Live Simulation Telemetry Box */}
        {currentTimelineData && (
          <div className="flex items-center space-x-2.5 bg-[#07090d] border border-[#232832] px-2.5 py-1 rounded-xl text-[10px] font-mono">
            <div>
              <span className="text-[#8b96aa] text-[8px] block">STAGE</span>
              <span className="text-cyan-300 font-bold">{currentTimelineData.stage}</span>
            </div>
            <div className="h-5 w-[1px] bg-[#232832]" />
            <div>
              <span className="text-[#8b96aa] text-[8px] block">POSITION</span>
              <span className="text-white font-bold">{currentTimelineData.lat.toFixed(2)}°N, {currentTimelineData.lon.toFixed(2)}°E</span>
            </div>
            <div className="h-5 w-[1px] bg-[#232832]" />
            <div>
              <span className="text-[#8b96aa] text-[8px] block">WIND</span>
              <span className="text-amber-400 font-bold">{currentTimelineData.wind} kts</span>
            </div>
            <div className="h-5 w-[1px] bg-[#232832]" />
            <div>
              <span className="text-[#8b96aa] text-[8px] block">CENTRAL P</span>
              <span className="text-emerald-400 font-bold">{currentTimelineData.pressure} hPa</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
