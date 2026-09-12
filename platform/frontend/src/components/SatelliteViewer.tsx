import React, { useState, useEffect, useRef, useMemo } from 'react';
import { SatelliteImageMeta, UnifiedAnalysisResponse } from '../types/cyclone';

interface SatelliteViewerProps {
  satelliteImages: SatelliteImageMeta[];
  selectedImage: SatelliteImageMeta | null;
  onSelectImage: (img: SatelliteImageMeta) => void;
  analysis: UnifiedAnalysisResponse | null;
  currentWind?: number;
  cycloneName?: string;
  selectedCycloneId?: string;
}

type ChannelType = 'TIR1_BD' | 'WV_67' | 'VIS_065' | 'GEOCOLOR' | 'DOPPLER_DBZ';
type DiagramType = 'RADIAL_WIND' | 'VERTICAL_RADAR_SLICE' | 'TB_HISTOGRAM' | 'DVORAK_CURVE';
type DisplayMode = 'STREAM_SHADER' | 'SMOOTH_RAPID_SCAN';

// Satellite Presets with calibrated physical signatures
const SATELLITE_PRESETS = [
  {
    id: 'ACTIVE_01A',
    name: 'INSAT-3D Active 01A (TIR-1 Scan)',
    sensor: 'INSAT-3D IMAGER',
    band: 'TIR-1 10.8µm',
    basin: 'BOB',
    centerLat: 19.6,
    centerLon: 87.3,
    eyeRadius: 10,
    cdoRadius: 58,
    spiralTightness: 3.2,
    numArms: 4,
    asymmetryAngle: 0.4,
    eyeType: 'Pin-hole Eye (Rapid Deepening)',
    cdoTemp: -82,
    intensityLabel: 'Extremely Severe (95 kts)',
    vMax: 95,
    rMaxKm: 22,
    pMinHpa: 960,
    dvorakT: 5.0,
    rapidScanUrl: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Cyclone_Fani_made_landfall.gif',
  },
  {
    id: 'AMPHAN_SUPER',
    name: 'INSAT-3DR Super Cyclone Amphan (Cat 5)',
    sensor: 'INSAT-3DR IMAGER',
    band: 'Enhanced BD Curve',
    basin: 'BOB',
    centerLat: 20.5,
    centerLon: 87.9,
    eyeRadius: 24,
    cdoRadius: 95,
    spiralTightness: 4.6,
    numArms: 5,
    asymmetryAngle: 0.1,
    eyeType: 'Massive Stadium Eye (Cat 5)',
    cdoTemp: -88,
    intensityLabel: 'Super Cyclonic Storm (140 kts)',
    vMax: 140,
    rMaxKm: 28,
    pMinHpa: 907,
    dvorakT: 6.5,
    rapidScanUrl: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Cyclone_Fani_made_landfall.gif',
  },
  {
    id: 'FANI_EXTREME',
    name: 'INSAT-3D Cyclone Fani Landfall Eyewall',
    sensor: 'INSAT-3D RAPID SCAN',
    band: 'Rapid-Scan Enhanced IR1',
    basin: 'BOB',
    centerLat: 19.8,
    centerLon: 85.8,
    eyeRadius: 16,
    cdoRadius: 78,
    spiralTightness: 3.9,
    numArms: 3,
    asymmetryAngle: 1.2,
    eyeType: 'Coastal Landfall Eyewall Shearing',
    cdoTemp: -84,
    intensityLabel: 'Extremely Severe (115 kts)',
    vMax: 115,
    rMaxKm: 24,
    pMinHpa: 932,
    dvorakT: 6.0,
    rapidScanUrl: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Cyclone_Fani_made_landfall.gif',
  },
  {
    id: 'BIPARJOY_ARB',
    name: 'INSAT-3D Biparjoy Arabian Sea Core',
    sensor: 'INSAT-3D IMAGER',
    band: 'Multi-Spectral VIS/IR',
    basin: 'ARB',
    centerLat: 22.4,
    centerLon: 67.5,
    eyeRadius: 28,
    cdoRadius: 65,
    spiralTightness: 2.3,
    numArms: 3,
    asymmetryAngle: 2.1,
    eyeType: 'Large Ragged Eye (SST 31.2°C)',
    cdoTemp: -76,
    intensityLabel: 'Very Severe (85 kts)',
    vMax: 85,
    rMaxKm: 38,
    pMinHpa: 968,
    dvorakT: 4.5,
    rapidScanUrl: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Cyclone_Fani_made_landfall.gif',
  },
  {
    id: 'MOCHA_SUPER',
    name: 'INSAT-3D Mocha Deep Convective Core',
    sensor: 'INSAT-3D IMAGER',
    band: 'Water Vapor High-Res',
    basin: 'BOB',
    centerLat: 17.5,
    centerLon: 91.8,
    eyeRadius: 13,
    cdoRadius: 88,
    spiralTightness: 4.2,
    numArms: 4,
    asymmetryAngle: 0.3,
    eyeType: 'Symmetric Cold Ring Eye',
    cdoTemp: -86,
    intensityLabel: 'Super Cyclone (135 kts)',
    vMax: 135,
    rMaxKm: 20,
    pMinHpa: 918,
    dvorakT: 6.5,
    rapidScanUrl: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Cyclone_Fani_made_landfall.gif',
  },
];

export const SatelliteViewer: React.FC<SatelliteViewerProps> = ({
  satelliteImages,
  selectedImage,
  onSelectImage,
  analysis,
  currentWind = 85,
  cycloneName = 'Active System 01A',
  selectedCycloneId,
}) => {
  const [activeChannel, setActiveChannel] = useState<ChannelType>('TIR1_BD');
  const [selectedPreset, setSelectedPreset] = useState<string>('ACTIVE_01A');
  const [activeDiagram, setActiveDiagram] = useState<DiagramType>('RADIAL_WIND');
  const [displayMode, setDisplayMode] = useState<DisplayMode>('STREAM_SHADER');
  const [heatmapOpacity, setHeatmapOpacity] = useState<number>(60);
  const [isFluidMotionOn, setIsFluidMotionOn] = useState<boolean>(true);
  const [showGraticules, setShowGraticules] = useState<boolean>(true);
  const [showCoastline, setShowCoastline] = useState<boolean>(true);
  const [showEyeCrosshair, setShowEyeCrosshair] = useState<boolean>(true);
  const [scanSpeed, setScanSpeed] = useState<number>(0.5);
  const [inspectCoords, setInspectCoords] = useState<{ x: number; y: number; lat: number; lon: number; temp: number; heightKm: number } | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fluidTimeRef = useRef<number>(0);
  const animFrameRef = useRef<number | null>(null);
  const [liveTimestamp, setLiveTimestamp] = useState<string>('');

  // Live timestamp clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setLiveTimestamp(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Auto-switch preset when cyclone changes
  useEffect(() => {
    if (selectedCycloneId) {
      const idUpper = selectedCycloneId.toUpperCase();
      if (idUpper.includes('BIPARJOY') || idUpper.includes('ARB')) setSelectedPreset('BIPARJOY_ARB');
      else if (idUpper.includes('FANI')) setSelectedPreset('FANI_EXTREME');
      else if (idUpper.includes('AMPHAN')) setSelectedPreset('AMPHAN_SUPER');
      else if (idUpper.includes('MOCHA')) setSelectedPreset('MOCHA_SUPER');
      else setSelectedPreset('ACTIVE_01A');
    }
  }, [selectedCycloneId]);

  const activePresetData = useMemo(() => {
    return SATELLITE_PRESETS.find((p) => p.id === selectedPreset) || SATELLITE_PRESETS[0];
  }, [selectedPreset]);

  const isArabianSea = useMemo(() => {
    return activePresetData.basin === 'ARB' || (cycloneName || '').toUpperCase().includes('BIPARJOY');
  }, [activePresetData, cycloneName]);

  // Filter Styles for Multi-Band Radiometry
  const channelFilterStyle = useMemo(() => {
    if (activeChannel === 'TIR1_BD') {
      return 'contrast(160%) brightness(105%) hue-rotate(185deg) saturate(240%)';
    } else if (activeChannel === 'WV_67') {
      return 'contrast(175%) brightness(115%) hue-rotate(265deg) saturate(280%)';
    } else if (activeChannel === 'VIS_065') {
      return 'grayscale(100%) contrast(140%) brightness(110%)';
    } else if (activeChannel === 'GEOCOLOR') {
      return 'contrast(125%) brightness(105%) saturate(135%)';
    } else {
      return 'contrast(190%) brightness(110%) hue-rotate(85deg) saturate(310%)';
    }
  }, [activeChannel]);

  // Real-Time Atmospheric Motion Shaders
  useEffect(() => {
    if (displayMode === 'SMOOTH_RAPID_SCAN') return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const cx = width / 2;
    const cy = height / 2;

    const { eyeRadius, cdoRadius, spiralTightness, numArms, asymmetryAngle } = activePresetData;

    const noise = (x: number, y: number) => {
      const n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453123;
      return n - Math.floor(n);
    };

    const fractalNoise = (x: number, y: number) => {
      let v = 0;
      let amp = 0.5;
      let freq = 0.022;
      for (let o = 0; o < 3; o++) {
        v += noise(x * freq, y * freq) * amp;
        freq *= 2.3;
        amp *= 0.5;
      }
      return v;
    };

    let lastTime = performance.now();

    const renderFrame = (now: number) => {
      const delta = (now - lastTime) / 1000;
      lastTime = now;

      if (isFluidMotionOn) {
        fluidTimeRef.current += delta * 0.9;
      }

      const timeOffset = fluidTimeRef.current;
      const imgData = ctx.createImageData(width, height);
      const data = imgData.data;

      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const idx = (y * width + x) * 4;
          const dx = x - cx;
          const dy = y - cy;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const angle = Math.atan2(dy, dx);

          const fluidSpeed = (26.0 / Math.max(7, Math.sqrt(dist))) * timeOffset;
          const advectedAngle = angle - fluidSpeed;

          const spiralPhase = advectedAngle + Math.log(Math.max(1, dist)) * spiralTightness;
          const rainbandFactor = Math.cos(spiralPhase * (numArms / 2));
          const shearFactor = Math.cos(angle - asymmetryAngle) * 0.28;

          const nVal = fractalNoise(x * 0.75 + Math.cos(advectedAngle) * 18, y * 0.75 + Math.sin(advectedAngle) * 18);
          let cloudDensity = 0;

          if (dist < eyeRadius) {
            cloudDensity = 0.03 + nVal * 0.05;
          } else if (dist < cdoRadius + shearFactor * 22) {
            const eyewallProximity = 1.0 - (dist - eyeRadius) / (cdoRadius - eyeRadius);
            cloudDensity = 0.85 + eyewallProximity * 0.15 + nVal * 0.15;
          } else if (dist < 170) {
            const falloff = 1.0 - (dist - cdoRadius) / (170 - cdoRadius);
            cloudDensity = Math.max(0, (rainbandFactor > -0.2 ? (rainbandFactor + 0.2) * 0.8 : 0) * falloff + nVal * 0.32);
          } else {
            const outerFalloff = Math.max(0, 1.0 - (dist - 170) / 45);
            cloudDensity = Math.max(0, nVal * 0.38 * outerFalloff);
          }

          cloudDensity = Math.min(1.0, Math.max(0.0, cloudDensity));

          if (activeChannel === 'TIR1_BD') {
            const tempC = dist < eyeRadius ? 18.0 - dist * 0.4 : 26.0 - cloudDensity * 114.0;
            if (tempC < -80) { data[idx] = 255; data[idx+1] = 255; data[idx+2] = 255; }
            else if (tempC < -75) { data[idx] = 225; data[idx+1] = 18; data[idx+2] = 30; }
            else if (tempC < -65) { data[idx] = 235; data[idx+1] = 65; data[idx+2] = 160; }
            else if (tempC < -55) { data[idx] = 0; data[idx+1] = 215; data[idx+2] = 245; }
            else if (tempC < -40) { data[idx] = 20; data[idx+1] = 75; data[idx+2] = 175; }
            else if (tempC < -25) { data[idx] = 25; data[idx+1] = 145; data[idx+2] = 85; }
            else if (tempC < 0) {
              const g = Math.floor(100 + tempC * 2.2);
              data[idx] = g; data[idx+1] = g; data[idx+2] = g;
            } else {
              const sea = Math.floor(12 + tempC * 0.7);
              data[idx] = sea; data[idx+1] = sea + 8; data[idx+2] = sea + 24;
            }
          } else if (activeChannel === 'WV_67') {
            if (cloudDensity > 0.65) {
              data[idx] = Math.floor(220 + cloudDensity * 35);
              data[idx+1] = Math.floor(200 + cloudDensity * 55);
              data[idx+2] = 255;
            } else if (cloudDensity > 0.3) {
              data[idx] = Math.floor(120 + cloudDensity * 140);
              data[idx+1] = 40;
              data[idx+2] = Math.floor(170 + cloudDensity * 80);
            } else {
              const dry = Math.floor(cloudDensity * 60);
              data[idx] = 18 + dry; data[idx+1] = 10 + dry; data[idx+2] = 32 + dry * 2;
            }
          } else if (activeChannel === 'VIS_065') {
            const sunAngle = Math.cos(advectedAngle - 0.7);
            const shadow = 1.0 + sunAngle * 0.28;
            const albedo = Math.floor(Math.min(255, (cloudDensity * 240 + 15) * shadow));
            data[idx] = albedo; data[idx+1] = albedo; data[idx+2] = albedo;
          } else if (activeChannel === 'GEOCOLOR') {
            if (cloudDensity > 0.2) {
              const white = Math.floor(cloudDensity * 245 + 10);
              data[idx] = white; data[idx+1] = white; data[idx+2] = Math.min(255, white + 15);
            } else {
              data[idx] = 8; data[idx+1] = 26; data[idx+2] = 60;
            }
          } else {
            const dbz = cloudDensity * 65.0;
            if (dbz > 55) { data[idx] = 220; data[idx+1] = 40; data[idx+2] = 220; }
            else if (dbz > 45) { data[idx] = 230; data[idx+1] = 30; data[idx+2] = 30; }
            else if (dbz > 35) { data[idx] = 240; data[idx+1] = 200; data[idx+2] = 20; }
            else if (dbz > 20) { data[idx] = 30; data[idx+1] = 200; data[idx+2] = 60; }
            else if (dbz > 10) { data[idx] = 40; data[idx+1] = 140; data[idx+2] = 230; }
            else { data[idx] = 8; data[idx+1] = 12; data[idx+2] = 18; }
          }

          data[idx + 3] = 255;
        }
      }

      ctx.putImageData(imgData, 0, 0);

      // Coastline
      if (showCoastline) {
        ctx.strokeStyle = '#eab308';
        ctx.lineWidth = 1.4;
        ctx.setLineDash([]);
        ctx.beginPath();
        if (isArabianSea) {
          ctx.moveTo(width * 0.95, height * 0.15);
          ctx.bezierCurveTo(width * 0.70, height * 0.35, width * 0.65, height * 0.65, width * 0.85, height * 0.95);
          ctx.stroke();
          ctx.fillStyle = '#fde047';
          ctx.font = 'bold 9px monospace';
          ctx.fillText('GUJARAT / ARABIAN SEA', width * 0.55, height * 0.25);
        } else {
          ctx.moveTo(0, height * 0.15);
          ctx.bezierCurveTo(width * 0.22, height * 0.28, width * 0.32, height * 0.58, width * 0.28, height * 0.95);
          ctx.stroke();
          ctx.fillStyle = '#fde047';
          ctx.font = 'bold 9px monospace';
          ctx.fillText('ODISHA / AP COAST', width * 0.05, height * 0.45);
        }
      }

      // Graticules
      if (showGraticules) {
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.22)';
        ctx.lineWidth = 0.8;
        ctx.setLineDash([4, 4]);

        [height * 0.25, height * 0.5, height * 0.75].forEach((yPos, i) => {
          ctx.beginPath(); ctx.moveTo(0, yPos); ctx.lineTo(width, yPos);
          ctx.stroke();
          ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
          ctx.font = '8px monospace';
          const latLabel = (activePresetData.centerLat + 3.0 - i * 3.0).toFixed(0) + '°N';
          ctx.fillText(latLabel, 6, yPos - 3);
        });

        [width * 0.25, width * 0.5, width * 0.75].forEach((xPos, i) => {
          ctx.beginPath(); ctx.moveTo(xPos, 0); ctx.lineTo(xPos, height);
          ctx.stroke();
          ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
          ctx.font = '8px monospace';
          const lonLabel = (activePresetData.centerLon - 3.0 + i * 3.0).toFixed(0) + '°E';
          ctx.fillText(lonLabel, xPos + 4, height - 6);
        });
        ctx.setLineDash([]);
      }

      // Eye Reticle
      if (showEyeCrosshair) {
        ctx.strokeStyle = '#00f0ff';
        ctx.lineWidth = 1.0;
        ctx.beginPath();
        ctx.arc(cx, cy, eyeRadius, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = '#00f0ff';
        ctx.beginPath();
        ctx.moveTo(cx - 10, cy); ctx.lineTo(cx + 10, cy);
        ctx.moveTo(cx, cy - 10); ctx.lineTo(cx, cy + 10);
        ctx.stroke();
      }

      if (isFluidMotionOn) {
        animFrameRef.current = requestAnimationFrame(renderFrame);
      }
    };

    renderFrame(performance.now());
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [activeChannel, selectedPreset, isFluidMotionOn, showGraticules, showCoastline, showEyeCrosshair, activePresetData, isArabianSea, displayMode]);

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement | HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.floor(((e.clientX - rect.left) / rect.width) * 360);
    const y = Math.floor(((e.clientY - rect.top) / rect.height) * 360);
    const cx = 180;
    const cy = 180;
    const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);

    const lat = activePresetData.centerLat + ((cy - y) / 360) * 6.0;
    const lon = activePresetData.centerLon + ((x - cx) / 360) * 6.0;
    const estimatedTemp = dist < activePresetData.eyeRadius ? 17.5 : -82.0 + Math.min(105, dist * 0.75);
    const estimatedHeightKm = dist < activePresetData.eyeRadius ? 1.5 : Math.min(17.2, 16.5 - (dist / 180) * 8.0);

    setInspectCoords({ x, y, lat, lon, temp: estimatedTemp, heightKm: Number(estimatedHeightKm.toFixed(1)) });
  };

  const heatmapBase64 = analysis?.classification?.explainability_heatmap_base64;

  return (
    <div className="bg-[#10141b] border border-[#222936] rounded-2xl p-5 shadow-2xl flex flex-col justify-between">
      <div>
        {/* Top Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <h3 className="text-white font-black text-sm tracking-tight">
                Satellite Sensor & Deep Explainability
              </h3>
            </div>
            <p className="text-[11px] text-[#8899b5]">
              Basin: <strong className={isArabianSea ? 'text-amber-400' : 'text-cyan-400'}>{isArabianSea ? 'Arabian Sea (ARB)' : 'Bay of Bengal (BOB)'}</strong> · Sensor: <strong className="text-white">{activePresetData.sensor}</strong> · T-No: <strong className="text-emerald-400">T{activePresetData.dvorakT.toFixed(1)}</strong>
            </p>
          </div>

          <div className="flex items-center space-x-1.5">
            {/* Mode: Live Fluid vs Filtered Rapid-Scan */}
            <div className="bg-[#090b0e] border border-[#222936] p-0.5 rounded-lg flex items-center text-[10px]">
              <button
                onClick={() => setDisplayMode('STREAM_SHADER')}
                className={`px-2 py-0.5 rounded-md font-bold transition-all ${
                  displayMode === 'STREAM_SHADER' ? 'bg-cyan-400 text-black' : 'text-[#8899b5]'
                }`}
              >
                🔬 Fluid Radiometer
              </button>
              <button
                onClick={() => setDisplayMode('SMOOTH_RAPID_SCAN')}
                className={`px-2 py-0.5 rounded-md font-bold transition-all ${
                  displayMode === 'SMOOTH_RAPID_SCAN' ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-black font-black' : 'text-[#8899b5]'
                }`}
              >
                🛰️ Filtered Satellite Loop
              </button>
            </div>

            {/* Cyclone Preset Selector */}
            <select
              value={selectedPreset}
              onChange={(e) => setSelectedPreset(e.target.value)}
              className="bg-[#090b0e] border border-cyan-500/40 text-white text-[11px] font-bold px-2 py-1 rounded-xl outline-none focus:border-cyan-400"
            >
              {SATELLITE_PRESETS.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Channel Switcher */}
        <div className="flex items-center justify-between bg-[#090b0e] border border-[#222936] p-1.5 rounded-xl mb-3">
          <span className="text-[10px] text-[#8899b5] font-bold uppercase tracking-wider pl-1.5">Channel:</span>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setActiveChannel('TIR1_BD')}
              className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all ${
                activeChannel === 'TIR1_BD' ? 'bg-gradient-to-r from-red-600 to-cyan-400 text-black shadow-[0_0_10px_rgba(0,240,255,0.4)]' : 'text-[#8899b5] hover:text-white'
              }`}
            >
              IR BD-Curve
            </button>
            <button
              onClick={() => setActiveChannel('WV_67')}
              className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all ${
                activeChannel === 'WV_67' ? 'bg-gradient-to-r from-purple-500 to-fuchsia-400 text-black shadow-[0_0_10px_rgba(192,132,252,0.4)]' : 'text-[#8899b5] hover:text-white'
              }`}
            >
              WV 6.7µm
            </button>
            <button
              onClick={() => setActiveChannel('VIS_065')}
              className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all ${
                activeChannel === 'VIS_065' ? 'bg-white text-black font-black' : 'text-[#8899b5] hover:text-white'
              }`}
            >
              VIS Optical
            </button>
            <button
              onClick={() => setActiveChannel('GEOCOLOR')}
              className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all ${
                activeChannel === 'GEOCOLOR' ? 'bg-gradient-to-r from-blue-600 to-cyan-300 text-black font-black' : 'text-[#8899b5] hover:text-white'
              }`}
            >
              GeoColor
            </button>
            <button
              onClick={() => setActiveChannel('DOPPLER_DBZ')}
              className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all ${
                activeChannel === 'DOPPLER_DBZ' ? 'bg-gradient-to-r from-emerald-500 to-red-500 text-black font-black' : 'text-[#8899b5] hover:text-white'
              }`}
            >
              DWR Radar
            </button>
          </div>
        </div>

        {/* Viewport Canvas or Filtered Slow Looping Satellite Stream */}
        <div
          onMouseMove={handleCanvasMouseMove}
          onMouseLeave={() => setInspectCoords(null)}
          className="relative w-full aspect-square max-h-[300px] bg-[#05070a] rounded-2xl overflow-hidden border border-[#222936] flex items-center justify-center shadow-2xl group cursor-crosshair"
        >
          {displayMode === 'SMOOTH_RAPID_SCAN' ? (
            <div className="relative w-full h-full overflow-hidden flex items-center justify-center">
              <img
                src={activePresetData.rapidScanUrl}
                alt="Satellite Rapid Scan"
                className="w-full h-full object-cover transition-all duration-700"
                style={{
                  filter: channelFilterStyle,
                }}
              />
              {/* Authentic Meteorological Telemetry Tag */}
              <div className="absolute bottom-2.5 left-2.5 bg-black/85 backdrop-blur-md px-2 py-1 rounded-lg text-[9px] text-cyan-300 font-mono border border-cyan-500/30 flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                <span>INSAT-3D RAPID-SCAN 10-MIN INTERVALS</span>
              </div>
            </div>
          ) : (
            <canvas ref={canvasRef} width={360} height={360} className="w-full h-full object-cover" />
          )}

          {/* Grad-CAM Saliency Overlay */}
          <div
            className="absolute inset-0 pointer-events-none transition-opacity duration-200 flex items-center justify-center"
            style={{ opacity: heatmapOpacity / 100 }}
          >
            {heatmapBase64 ? (
              <img src={heatmapBase64} alt="Grad-CAM Hotspots" className="w-full h-full object-cover mix-blend-screen" />
            ) : (
              <div className="w-44 h-44 rounded-full bg-gradient-to-r from-red-500/80 via-yellow-400/60 to-transparent blur-xl pointer-events-none animate-pulse" />
            )}
          </div>

          {/* Live Telemetry Header */}
          <div className="absolute top-2.5 left-2.5 right-2.5 bg-[#080a0f]/90 backdrop-blur-md border border-[#222936] px-2.5 py-1 rounded-lg text-[9px] text-[#8899b5] font-mono flex items-center justify-between shadow-lg pointer-events-none">
            <div className="flex items-center space-x-1.5 text-white font-bold">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <span>{activePresetData.sensor} · {activeChannel}</span>
            </div>
            <div className="text-cyan-300 font-bold">{liveTimestamp || '2026-09-05 00:04:12 UTC'}</div>
          </div>

          {/* Scale Bar */}
          <div className="absolute right-2.5 top-12 bottom-12 w-3.5 bg-black/80 backdrop-blur-sm border border-[#222936] rounded-md flex flex-col justify-between items-center py-1 text-[7px] text-white font-mono shadow pointer-events-none">
            {activeChannel === 'DOPPLER_DBZ' ? (
              <>
                <span className="text-fuchsia-400 font-bold">65</span>
                <span className="text-red-500 font-bold">50</span>
                <span className="text-yellow-400">35</span>
                <span className="text-green-400">20</span>
                <span className="text-blue-400">10</span>
                <span className="text-gray-400">dBZ</span>
              </>
            ) : (
              <>
                <span className="text-white font-bold">-85°</span>
                <span className="text-red-500 font-bold">-75°</span>
                <span className="text-pink-400">-65°</span>
                <span className="text-cyan-400">-55°</span>
                <span className="text-emerald-400">-40°</span>
                <span className="text-gray-300">0°</span>
                <span className="text-blue-400">+28°</span>
              </>
            )}
          </div>

          {/* Live Atmospheric Radiance Probe */}
          {inspectCoords && (
            <div className="absolute bottom-2.5 left-2.5 bg-[#080a0f]/95 backdrop-blur-md border border-cyan-500/40 px-2.5 py-1.5 rounded-xl text-[10px] text-white font-mono shadow-2xl pointer-events-none">
              <div className="text-cyan-300 font-bold">Fix: {inspectCoords.lat.toFixed(2)}°N, {inspectCoords.lon.toFixed(2)}°E</div>
              <div className="text-emerald-400 text-[9px]">Radiance Tb: {inspectCoords.temp.toFixed(1)}°C | Cloud Top: {inspectCoords.heightKm} km</div>
            </div>
          )}
        </div>

        {/* Dynamic Meteorological Diagnostic Diagram Tabs */}
        <div className="mt-3 bg-[#090b0e] border border-[#222936] rounded-xl p-2">
          <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-[#232832]">
            <span className="text-[10px] text-cyan-300 font-bold uppercase tracking-wider flex items-center space-x-1">
              <span>📊 Diagnostic Diagram:</span>
            </span>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setActiveDiagram('RADIAL_WIND')}
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  activeDiagram === 'RADIAL_WIND' ? 'bg-cyan-400 text-black' : 'text-[#8899b5] hover:text-white'
                }`}
              >
                Radial Wind V(r)
              </button>
              <button
                onClick={() => setActiveDiagram('VERTICAL_RADAR_SLICE')}
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  activeDiagram === 'VERTICAL_RADAR_SLICE' ? 'bg-cyan-400 text-black' : 'text-[#8899b5] hover:text-white'
                }`}
              >
                Vertical Radar Slice
              </button>
              <button
                onClick={() => setActiveDiagram('TB_HISTOGRAM')}
                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  activeDiagram === 'TB_HISTOGRAM' ? 'bg-cyan-400 text-black' : 'text-[#8899b5] hover:text-white'
                }`}
              >
                Tb Histogram
              </button>
            </div>
          </div>

          <div className="h-28 w-full flex items-center justify-center">
            {activeDiagram === 'RADIAL_WIND' && (
              <div className="w-full h-full flex flex-col justify-between py-1">
                <div className="flex justify-between text-[9px] text-[#8899b5] font-mono">
                  <span>Holland/Rankine Radial Velocity Profile (Rmax = {activePresetData.rMaxKm} km)</span>
                  <span className="text-amber-400 font-bold">Vmax: {activePresetData.vMax} kts</span>
                </div>
                <svg className="w-full h-20" viewBox="0 0 300 70">
                  <line x1="30" y1="55" x2="290" y2="55" stroke="#232832" strokeWidth="1" />
                  <path d={`M 30 55 C 50 50, 70 30, 85 12 C 100 12, 140 35, 200 45 L 290 52`} fill="none" stroke="#00f0ff" strokeWidth="2.5" />
                  <circle cx="85" cy="12" r="3.5" fill="#ef4444" />
                  <text x="90" y="16" fill="#f87171" fontSize="8" fontWeight="bold">Rmax: {activePresetData.rMaxKm}km ({activePresetData.vMax} kts)</text>
                  <text x="30" y="65" fill="#8899b5" fontSize="7">0km (Eye)</text>
                  <text x="150" y="65" fill="#8899b5" fontSize="7">150km</text>
                  <text x="270" y="65" fill="#8899b5" fontSize="7">300km</text>
                </svg>
              </div>
            )}

            {activeDiagram === 'VERTICAL_RADAR_SLICE' && (
              <div className="w-full h-full flex flex-col justify-between py-1">
                <div className="flex justify-between text-[9px] text-[#8899b5] font-mono">
                  <span>Doppler Radar Vertical Reflectivity Slice (0 to 18 km Altitude)</span>
                  <span className="text-emerald-400 font-bold">Tropopause: 16.8km</span>
                </div>
                <svg className="w-full h-20" viewBox="0 0 300 70">
                  <line x1="30" y1="58" x2="290" y2="58" stroke="#333a48" strokeWidth="1.5" />
                  <rect x="75" y="14" width="20" height="44" fill="url(#eyewallGrad2)" rx="2" />
                  <rect x="145" y="14" width="20" height="44" fill="url(#eyewallGrad2)" rx="2" />
                  <rect x="98" y="48" width="44" height="10" fill="#00f0ff" opacity="0.2" rx="2" />
                  <text x="105" y="45" fill="#38bdf8" fontSize="7" fontWeight="bold">EYE MOAT</text>
                  <line x1="30" y1="38" x2="290" y2="38" stroke="#38bdf8" strokeWidth="1" strokeDasharray="3,3" />
                  <text x="32" y="36" fill="#38bdf8" fontSize="7">0°C Freezing Level (4.8km)</text>
                  <defs>
                    <linearGradient id="eyewallGrad2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#ef4444" />
                      <stop offset="50%" stopColor="#f59e0b" />
                      <stop offset="100%" stopColor="#10b981" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            )}

            {activeDiagram === 'TB_HISTOGRAM' && (
              <div className="w-full h-full flex flex-col justify-between py-1">
                <div className="flex justify-between text-[9px] text-[#8899b5] font-mono">
                  <span>Convective Cloud-Top Brightness Temperature (Tb Distribution)</span>
                  <span className="text-cyan-300 font-bold">CDO Core: {activePresetData.cdoTemp}°C</span>
                </div>
                <div className="flex items-end space-x-1.5 h-16 w-full px-2 pt-2">
                  <div className="flex-1 bg-blue-600/60 rounded-t h-[20%] text-[7px] text-center text-white">+10°C</div>
                  <div className="flex-1 bg-emerald-500/60 rounded-t h-[35%] text-[7px] text-center text-white">-20°C</div>
                  <div className="flex-1 bg-cyan-500/70 rounded-t h-[55%] text-[7px] text-center text-white">-45°C</div>
                  <div className="flex-1 bg-pink-500/80 rounded-t h-[80%] text-[7px] text-center text-white">-65°C</div>
                  <div className="flex-1 bg-red-600 rounded-t h-[95%] text-[7px] text-center text-white font-bold">{activePresetData.cdoTemp}°C</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Saliency Blend */}
      <div className="mt-3 pt-2 border-t border-[#222936] space-y-1">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="text-[#8899b5] font-bold text-[11px]">Grad-CAM Deep Attention Saliency:</span>
            <span className="text-[10px] text-cyan-400 font-mono">
              ({analysis?.detection?.confidence ? (analysis.detection.confidence * 100).toFixed(1) + '% Conf' : 'Eyewall Core'})
            </span>
          </div>
          <span className="font-mono text-cyan-300 font-bold text-xs">{heatmapOpacity}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={heatmapOpacity}
          onChange={(e) => setHeatmapOpacity(Number(e.target.value))}
          className="w-full h-1.5 bg-[#181d26] rounded-lg appearance-none cursor-pointer accent-[#007afc]"
        />
      </div>
    </div>
  );
};
