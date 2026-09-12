import React, { useState, useEffect } from 'react';
import { CycloneSummary, SatelliteImageMeta, UnifiedAnalysisResponse } from '../types/cyclone';
import { simulateCycloneFeed, fetchCycloneBulletin } from '../services/api';

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  cyclones: CycloneSummary[];
  selectedCycloneId: string;
  satelliteImages: SatelliteImageMeta[];
  onExecuteAnalysis: (cycloneId: string, imageId?: string) => Promise<void>;
  isAnalyzing: boolean;
  latestResult: UnifiedAnalysisResponse | null;
  onRefreshData?: () => void;
}

export const AnalysisModal: React.FC<AnalysisModalProps> = ({
  isOpen,
  onClose,
  cyclones,
  selectedCycloneId,
  satelliteImages,
  onExecuteAnalysis,
  isAnalyzing,
  latestResult,
  onRefreshData,
}) => {
  const [activeTab, setActiveTab] = useState<'pipeline' | 'sensors' | 'simulation' | 'bulletin'>('pipeline');
  const [selectedImageId, setSelectedImageId] = useState<string>('');
  const [spectralChannel, setSpectralChannel] = useState<string>('TIR1');
  const [simulationStatus, setSimulationStatus] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [bulletinData, setBulletinData] = useState<string | null>(null);
  const [copiedBulletin, setCopiedBulletin] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen && activeTab === 'bulletin' && selectedCycloneId) {
      fetchCycloneBulletin(selectedCycloneId)
        .then((data) => setBulletinData(data.bulletin_text))
        .catch(() => setBulletinData('Error generating bulletin.'));
    }
  }, [isOpen, activeTab, selectedCycloneId]);

  if (!isOpen) return null;

  const currentCyclone = cyclones.find((c) => c.id === selectedCycloneId);

  const handleRun = async () => {
    await onExecuteAnalysis(selectedCycloneId, selectedImageId || undefined);
  };

  const handleStepSimulation = async () => {
    try {
      setIsSimulating(true);
      setSimulationStatus('Ingesting live MOSDAC / Ocean Buoy synoptic fix...');
      const res = await simulateCycloneFeed(selectedCycloneId);
      setSimulationStatus(`✓ ${res.message} (Wind: ${res.observation?.wind_speed} kts, Lat: ${res.observation?.latitude}°N, Lon: ${res.observation?.longitude}°E)`);
      if (onRefreshData) onRefreshData();
    } catch (err: any) {
      setSimulationStatus(`Simulation Error: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleCopyBulletin = () => {
    if (bulletinData) {
      navigator.clipboard.writeText(bulletinData);
      setCopiedBulletin(true);
      setTimeout(() => setCopiedBulletin(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-[#10141b] border border-[#222936] w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-[#141822] border-b border-[#222936] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/15 border border-cyan-500/40 flex items-center justify-center text-lg shadow-[0_0_15px_rgba(0,240,255,0.2)]">
              ⚡
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-white font-black text-base tracking-wide">AI Multi-Scale Forecast Pipeline</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                  OPERATIONAL
                </span>
              </div>
              <p className="text-xs text-[#8b96aa]">
                Target: <span className="text-white font-semibold">{currentCyclone?.name || selectedCycloneId}</span> ({currentCyclone?.basin})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[#8b96aa] hover:text-white p-1.5 rounded-xl hover:bg-[#1f242e] transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Modal Tabs Bar */}
        <div className="px-6 bg-[#0c0f15] border-b border-[#222936] flex space-x-2 text-xs font-semibold overflow-x-auto">
          <button
            onClick={() => setActiveTab('pipeline')}
            className={`py-3 px-3 border-b-2 transition-all flex items-center space-x-1.5 ${
              activeTab === 'pipeline'
                ? 'border-cyan-400 text-white font-bold bg-[#141822]/60'
                : 'border-transparent text-[#8b96aa] hover:text-[#d5dae2]'
            }`}
          >
            <span>⚡</span>
            <span>Execute Forecast Pipeline</span>
          </button>
          <button
            onClick={() => setActiveTab('simulation')}
            className={`py-3 px-3 border-b-2 transition-all flex items-center space-x-1.5 ${
              activeTab === 'simulation'
                ? 'border-cyan-400 text-cyan-300 font-bold bg-[#141822]/60'
                : 'border-transparent text-[#8b96aa] hover:text-[#d5dae2]'
            }`}
          >
            <span>📡</span>
            <span>Live Synoptic Ingest</span>
          </button>
          <button
            onClick={() => setActiveTab('sensors')}
            className={`py-3 px-3 border-b-2 transition-all flex items-center space-x-1.5 ${
              activeTab === 'sensors'
                ? 'border-amber-400 text-amber-300 font-bold bg-[#141822]/60'
                : 'border-transparent text-[#8b96aa] hover:text-[#d5dae2]'
            }`}
          >
            <span>🛰️</span>
            <span>Sensor Channels</span>
          </button>
          <button
            onClick={() => setActiveTab('bulletin')}
            className={`py-3 px-3 border-b-2 transition-all flex items-center space-x-1.5 ${
              activeTab === 'bulletin'
                ? 'border-emerald-400 text-emerald-400 font-bold bg-[#141822]/60'
                : 'border-transparent text-[#8b96aa] hover:text-[#d5dae2]'
            }`}
          >
            <span>📋</span>
            <span>IMD Advisory Bulletin</span>
          </button>
        </div>

        {/* Modal Body Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs flex-1">
          {/* TAB 1: PIPELINE EXECUTION */}
          {activeTab === 'pipeline' && (
            <div className="space-y-4">
              {/* Target Summary Card */}
              <div className="bg-[#141822] border border-[#222936] p-4 rounded-xl space-y-2.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[#8b96aa]">Active Storm System:</span>
                  <span className="text-white font-black text-sm">{currentCyclone?.name} [{currentCyclone?.id}]</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[#8b96aa]">Oceanic Basin:</span>
                  <span className="text-cyan-300 font-medium">{currentCyclone?.basin}</span>
                </div>
                <div className="flex justify-between items-center pt-2 border-t border-[#222936]">
                  <span className="text-[#8b96aa]">Satellite Image Scene:</span>
                  <select
                    value={selectedImageId}
                    onChange={(e) => setSelectedImageId(e.target.value)}
                    className="bg-[#090b0e] border border-[#333a48] text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyan-400"
                  >
                    <option value="">Latest Synoptic Scene (Auto-Resolve)</option>
                    {satelliteImages.map((img) => (
                      <option key={img.id} value={img.id}>
                        {img.id} — {img.satellite} ({img.channel})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Execution Steps */}
              <div className="space-y-2.5">
                <h4 className="text-[#8b96aa] font-bold uppercase tracking-wider text-[11px]">
                  Autonomous AI Pipeline Architecture
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-[11px]">
                  <div className="bg-[#141822] border border-[#222936] p-3 rounded-xl flex items-start space-x-2.5">
                    <span className="text-cyan-400 font-bold">1</span>
                    <div>
                      <div className="text-white font-bold">Deep Eye Center Localization</div>
                      <div className="text-[#8b96aa] text-[10px]">PyTorch CNN bounding regression</div>
                    </div>
                  </div>
                  <div className="bg-[#141822] border border-[#222936] p-3 rounded-xl flex items-start space-x-2.5">
                    <span className="text-cyan-400 font-bold">2</span>
                    <div>
                      <div className="text-white font-bold">IMD Intensity Classification</div>
                      <div className="text-[#8b96aa] text-[10px]">8-Stage categorization + Grad-CAM</div>
                    </div>
                  </div>
                  <div className="bg-[#141822] border border-[#222936] p-3 rounded-xl flex items-start space-x-2.5">
                    <span className="text-cyan-400 font-bold">3</span>
                    <div>
                      <div className="text-white font-bold">Recurrent Trajectory Forecaster</div>
                      <div className="text-[#8b96aa] text-[10px]">GRU +6h to +72h with Monte-Carlo uncertainty</div>
                    </div>
                  </div>
                  <div className="bg-[#141822] border border-[#222936] p-3 rounded-xl flex items-start space-x-2.5">
                    <span className="text-cyan-400 font-bold">4</span>
                    <div>
                      <div className="text-white font-bold">Spatial GIS Persistence</div>
                      <div className="text-[#8b96aa] text-[10px]">PostGIS commit & GeoJSON vector stream</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Latest Result Banner */}
              {latestResult && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-xl text-xs space-y-2">
                  <div className="text-emerald-400 font-bold flex items-center space-x-2">
                    <span>✓</span>
                    <span>AI Analysis Pipeline Completed Successfully</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] text-[#d5dae2]">
                    <div>
                      <span className="text-[#8b96aa]">Stage: </span>
                      <strong>{latestResult.classification?.classification}</strong>
                    </div>
                    <div>
                      <span className="text-[#8b96aa]">Wind Speed: </span>
                      <strong>{latestResult.classification?.estimated_wind_speed} kts</strong>
                    </div>
                    <div>
                      <span className="text-[#8b96aa]">Forecast Points: </span>
                      <strong>{latestResult.forecast?.length} milestones</strong>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: LIVE SIMULATION STREAM */}
          {activeTab === 'simulation' && (
            <div className="space-y-4">
              <div className="bg-[#141822] border border-[#222936] p-4 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[#8b96aa] font-semibold">Real-Time Ingestion Mode:</span>
                  <span className="text-emerald-400 font-bold">● ACTIVE SATELLITE LINK</span>
                </div>
                <p className="text-[11px] text-[#8b96aa] leading-relaxed">
                  Ingests the next synoptic 6-hour observation package from INSAT-3D/3DR and coastal ocean buoys into the database, instantly triggering downstream neural forecasting.
                </p>
                <button
                  onClick={handleStepSimulation}
                  disabled={isSimulating}
                  className="w-full bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/50 text-cyan-300 font-bold py-2.5 rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg disabled:opacity-50"
                >
                  <span>{isSimulating ? 'Ingesting Satellite Telemetry...' : '📡 Ingest Next Synoptic Fix (+6h)'}</span>
                </button>
                {simulationStatus && (
                  <div className="p-2.5 rounded-lg bg-[#090b0e] border border-[#222936] text-[11px] font-mono text-cyan-300">
                    {simulationStatus}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: SENSORS */}
          {activeTab === 'sensors' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { id: 'TIR1', name: 'Thermal IR 10.8µm', desc: 'Core Cloud-top Temperature' },
                  { id: 'TIR2', name: 'Split-Window 12.0µm', desc: 'Moisture Gradient & Low-level Cirrus' },
                  { id: 'WV', name: 'Water Vapor 6.7µm', desc: 'Upper Tropospheric Vorticity' },
                  { id: 'VIS', name: 'Visible Optical 0.65µm', desc: 'High-Res Day Albedo & Eyewall Texture' },
                ].map((ch) => (
                  <button
                    key={ch.id}
                    onClick={() => setSpectralChannel(ch.id)}
                    className={`p-3 rounded-xl text-left border transition-all ${
                      spectralChannel === ch.id
                        ? 'bg-cyan-950/40 border-cyan-400 text-white'
                        : 'bg-[#141822] border-[#222936] text-[#8b96aa] hover:text-white'
                    }`}
                  >
                    <div className="font-bold text-xs">{ch.name}</div>
                    <div className="text-[10px] text-[#8b96aa] mt-1">{ch.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: BULLETIN */}
          {activeTab === 'bulletin' && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[#8b96aa] font-semibold text-xs">Official IMD Standard Advisory Bulletin:</span>
                <button
                  onClick={handleCopyBulletin}
                  className="px-2.5 py-1 bg-[#141822] border border-[#222936] rounded-lg text-[10px] text-cyan-300 font-bold hover:bg-[#1a202c]"
                >
                  {copiedBulletin ? '✓ Copied' : '📋 Copy Bulletin Text'}
                </button>
              </div>
              <pre className="bg-[#090b0e] border border-[#222936] p-3.5 rounded-xl font-mono text-[10px] text-emerald-300 leading-relaxed overflow-x-auto whitespace-pre-wrap max-h-60">
                {bulletinData || 'Generating standard IMD tropical cyclone warning bulletin...'}
              </pre>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-[#141822] border-t border-[#222936] flex items-center justify-between">
          <div className="text-[11px] text-[#8b96aa]">
            Status: <span className="text-cyan-400 font-bold">{isAnalyzing ? 'Running AI inference...' : 'Ready for analysis'}</span>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[#1b202c] hover:bg-[#232a3a] text-[#8b96aa] hover:text-white rounded-xl text-xs font-semibold transition-colors"
            >
              Close
            </button>
            <button
              onClick={handleRun}
              disabled={isAnalyzing}
              className="px-5 py-2 bg-gradient-to-r from-cyan-400 to-blue-500 hover:brightness-110 text-black font-black rounded-xl text-xs transition-all shadow-[0_0_15px_rgba(0,240,255,0.3)] disabled:opacity-50"
            >
              {isAnalyzing ? 'Executing Pipeline...' : '⚡ Run AI Pipeline'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
