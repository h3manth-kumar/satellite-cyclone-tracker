import React, { useState, useEffect, useMemo } from 'react';
import { Header } from './components/Header';
import { TelemetryBar } from './components/TelemetryBar';
import { CycloneMap } from './components/CycloneMap';
import { OfficialVsAICard } from './components/OfficialVsAICard';
import { IntensityChart } from './components/IntensityChart';
import { SatelliteViewer } from './components/SatelliteViewer';
import { AnalysisModal } from './components/AnalysisModal';
import { EmergencyAlertModal } from './components/EmergencyAlertModal';
import { DisclaimerBanner } from './components/DisclaimerBanner';

import {
  fetchHealth,
  fetchCyclones,
  fetchCycloneObservations,
  fetchSatelliteImages,
  runFullAnalysis,
  simulateCycloneFeed,
  fetchTrackGeoJSON,
} from './services/api';

import {
  CycloneSummary,
  Observation,
  ForecastPoint,
  SatelliteImageMeta,
  HealthResponse,
  UnifiedAnalysisResponse,
} from './types/cyclone';

export const App: React.FC = () => {
  const [cyclones, setCyclones] = useState<CycloneSummary[]>([]);
  const [selectedCycloneId, setSelectedCycloneId] = useState<string>('');
  const [observations, setObservations] = useState<Observation[]>([]);
  const [forecastPoints, setForecastPoints] = useState<ForecastPoint[]>([]);
  const [satelliteImages, setSatelliteImages] = useState<SatelliteImageMeta[]>([]);
  const [selectedImage, setSelectedImage] = useState<SatelliteImageMeta | null>(null);

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [latestAnalysis, setLatestAnalysis] = useState<UnifiedAnalysisResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [isAutoStreaming, setIsAutoStreaming] = useState<boolean>(true);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isAlertModalOpen, setIsAlertModalOpen] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // Initial Data Load
  const reloadData = async () => {
    try {
      try {
        const h = await fetchHealth();
        setHealth(h);
      } catch (e) {
        console.warn('Backend /health unreachable during init:', e);
      }

      const list = await fetchCyclones();
      setCyclones(list);

      if (list.length > 0 && !selectedCycloneId) {
        const active = list.find((c) => c.is_active) || list[0];
        setSelectedCycloneId(active.id);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to initialize meteorological console.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    reloadData();
  }, []);

  // When selected cyclone changes, reload observations and satellite images (AI Prediction is ONLY generated on-demand when user clicks 'Run AI Pipeline')
  useEffect(() => {
    if (!selectedCycloneId) return;

    const loadCycloneData = async () => {
      try {
        // Reset forecast & analysis until user explicitly executes the AI pipeline
        setForecastPoints([]);
        setLatestAnalysis(null);

        const obs = await fetchCycloneObservations(selectedCycloneId);
        setObservations(obs);

        const imgs = await fetchSatelliteImages(selectedCycloneId);
        setSatelliteImages(imgs);
        setSelectedImage(imgs.length > 0 ? imgs[0] : null);
      } catch (err: any) {
        console.error('Error loading cyclone data:', err);
      }
    };

    loadCycloneData();
  }, [selectedCycloneId]);

  // Execute Analysis Pipeline manually
  const handleExecuteAnalysis = async (cycloneId: string, imageId?: string) => {
    try {
      setIsAnalyzing(true);
      setErrorMessage(null);
      const res = await runFullAnalysis(cycloneId, imageId);
      setLatestAnalysis(res);
      setForecastPoints(res.forecast);
      setSuccessToast(`AI Multi-Scale Forecast Pipeline executed! Stage: ${res.classification?.classification}`);
      setTimeout(() => setSuccessToast(null), 4000);
    } catch (err: any) {
      setErrorMessage(`AI Pipeline Error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Quick Ingest Live Feed Fix (+6h) - Dynamically advances synoptic fix and updates telemetry
  const handleQuickSimulate = async () => {
    if (!selectedCycloneId) return;
    try {
      setIsSimulating(true);
      const res = await simulateCycloneFeed(selectedCycloneId);
      
      // Fetch fresh observations and cyclone summaries
      const obs = await fetchCycloneObservations(selectedCycloneId);
      setObservations([...obs]);

      const cycList = await fetchCyclones();
      setCyclones([...cycList]);

      setSuccessToast(`📡 Ingested +6h Fix: ${res.observation?.classification} (${res.observation?.wind_speed} kts) at [${res.observation?.latitude}°N, ${res.observation?.longitude}°E]`);
      setTimeout(() => setSuccessToast(null), 4500);

      // Trigger automatic background AI trajectory update
      try {
        const aiRes = await runFullAnalysis(selectedCycloneId);
        setLatestAnalysis(aiRes);
        setForecastPoints([...aiRes.forecast]);
      } catch (e) {
        console.warn('Auto AI update skipped:', e);
      }
    } catch (err: any) {
      setErrorMessage(`Live Feed Error: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleExportGeoJSON = async () => {
    if (!selectedCycloneId) return;
    try {
      const data = await fetchTrackGeoJSON(selectedCycloneId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedCycloneId}_track.geojson`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setErrorMessage(`Export Failed: ${err.message}`);
    }
  };

  const currentCyclone = cyclones.find((c) => c.id === selectedCycloneId) || null;
  const sortedObs = useMemo(() => [...observations].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()), [observations]);
  const latestObs = sortedObs.length > 0 ? sortedObs[sortedObs.length - 1] : null;
  const currentLat = latestObs?.latitude ?? latestAnalysis?.detection?.latitude ?? currentCyclone?.latest_lat ?? 20.37;
  const currentLon = latestObs?.longitude ?? latestAnalysis?.detection?.longitude ?? currentCyclone?.latest_lon ?? 87.46;

  return (
    <div className="flex flex-col min-h-screen bg-[#080a0f] text-[#a0aaba] font-sans selection:bg-[#007afc] selection:text-white">
      {/* Top Header */}
      <Header
        onOpenAlertModal={() => setIsAlertModalOpen(true)}
        cyclones={cyclones}
        selectedCycloneId={selectedCycloneId}
        onSelectCyclone={(id) => setSelectedCycloneId(id)}
        health={health}
        onOpenAnalysisModal={() => setIsModalOpen(true)}
        isAnalyzing={isAnalyzing}
        onQuickSimulate={handleQuickSimulate}
        isSimulating={isSimulating}
      />

      {/* Quick Telemetry HUD Bar */}
      <TelemetryBar
        onOpenAlertModal={() => setIsAlertModalOpen(true)}
        isAutoStreaming={isAutoStreaming}
        onToggleAutoStream={() => setIsAutoStreaming((prev) => !prev)}
        cyclone={currentCyclone}
        latestObs={latestObs}
        latestAnalysis={latestAnalysis}
        onQuickSimulate={handleQuickSimulate}
        isSimulating={isSimulating}
      />

      {/* Dynamic Success Notification */}
      {successToast && (
        <div className="bg-emerald-500/90 backdrop-blur-md border-b border-emerald-400 text-black font-bold px-6 py-2 text-xs flex items-center justify-between shadow-lg animate-in slide-in-from-top duration-300">
          <div className="flex items-center space-x-2">
            <span>✓</span>
            <span>{successToast}</span>
          </div>
          <button onClick={() => setSuccessToast(null)} className="text-black/70 hover:text-black">
            ✕
          </button>
        </div>
      )}

      {/* Error Alert if any */}
      {errorMessage && (
        <div className="bg-red-950/90 border-b border-red-700 text-red-200 px-6 py-2.5 text-xs flex items-center justify-between shadow-lg">
          <div className="flex items-center space-x-2">
            <span>⚠️</span>
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-red-400 hover:text-white">
            ✕
          </button>
        </div>
      )}

      {/* Main Console Grid */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1800px] w-full mx-auto">
        {/* Left GIS & Telemetry Column (7 of 12 columns) */}
        <div className="lg:col-span-7 flex flex-col space-y-6">
          {/* Interactive GIS Cyclone Map */}
          <div className="flex-1 min-h-[540px]">
            <CycloneMap
              observations={observations}
              forecastPoints={forecastPoints}
              currentLat={currentLat}
              currentLon={currentLon}
              cycloneName={currentCyclone?.name || selectedCycloneId}
            />
          </div>

          {/* Side-by-Side Official vs AI Telemetry Validation */}
          <OfficialVsAICard
            latestObs={latestObs}
            latestAnalysis={latestAnalysis}
          />
        </div>

        {/* Right Remote Sensing & Forecasting Column (5 of 12 columns) */}
        <div className="lg:col-span-5 flex flex-col space-y-6">
          {/* Satellite Viewer with Explainability Overlay */}
          <SatelliteViewer
            satelliteImages={satelliteImages}
            selectedImage={selectedImage}
            onSelectImage={(img) => setSelectedImage(img)}
            analysis={latestAnalysis}
            currentWind={latestObs?.wind_speed ?? 85}
            cycloneName={currentCyclone?.name || selectedCycloneId}
            selectedCycloneId={selectedCycloneId}
          />

          {/* Intensity & Wind Speed Forecast Curve */}
          <IntensityChart
            observations={observations}
            forecastPoints={forecastPoints}
          />

          {/* Quick Action Buttons */}
          <div className="bg-[#10141b] border border-[#222936] rounded-2xl p-4 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2">
              <span className="text-cyan-400 font-bold">Quick Actions:</span>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleExportGeoJSON}
                className="bg-[#141822] hover:bg-[#1f2636] border border-[#2b3342] text-white px-3.5 py-1.5 rounded-xl font-semibold transition-all flex items-center space-x-1.5"
              >
                <span>📥 Export GeoJSON</span>
              </button>
              <button
                onClick={() => setIsModalOpen(true)}
                className="bg-gradient-to-r from-cyan-400 to-blue-500 hover:brightness-110 text-black px-4.5 py-1.5 rounded-xl font-black transition-all flex items-center space-x-1.5 shadow-[0_0_15px_rgba(0,240,255,0.3)]"
              >
                <span>⚡ AI Pipeline Console</span>
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Mandatory Disaster Management Disclaimer */}
      <DisclaimerBanner />

      {/* Analysis Execution Dialog (Z-Index 99999) */}
      <AnalysisModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        cyclones={cyclones}
        selectedCycloneId={selectedCycloneId}
        satelliteImages={satelliteImages}
        onExecuteAnalysis={handleExecuteAnalysis}
        isAnalyzing={isAnalyzing}
        latestResult={latestAnalysis}
        onRefreshData={() => {
          fetchCycloneObservations(selectedCycloneId).then(setObservations);
        }}
      />
    </div>
  );
};
