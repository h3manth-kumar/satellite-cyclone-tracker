import React, { useState, useEffect } from 'react';
import { CycloneSummary, HealthResponse } from '../types/cyclone';

interface HeaderProps {
  onOpenAlertModal?: () => void;
  cyclones: CycloneSummary[];
  selectedCycloneId: string;
  onSelectCyclone: (id: string) => void;
  health: HealthResponse | null;
  onOpenAnalysisModal: () => void;
  isAnalyzing: boolean;
  onQuickSimulate?: () => void;
  isSimulating?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  cyclones,
  selectedCycloneId,
  onSelectCyclone,
  health,
  onOpenAnalysisModal,
  isAnalyzing,
  onQuickSimulate,
  isSimulating,
  onOpenAlertModal,
}) => {
  const [utcTime, setUtcTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const currentCyclone = cyclones.find((c) => c.id === selectedCycloneId);

  return (
    <header className="h-[68px] bg-[#12151a] border-b border-[#232832] px-6 flex items-center justify-between sticky top-0 z-[5000] shadow-lg">
      {/* Left: Branding & National Weather Insignia */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#007afc]/20 to-[#00f0ff]/10 border border-[#007afc]/40 flex items-center justify-center text-xl shadow-[0_0_15px_rgba(0,122,252,0.25)]">
            🌀
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-black text-white text-lg tracking-tight">CycloneAI</span>
              <span className="text-[10px] uppercase font-black tracking-widest text-[#00f0ff] bg-[#00f0ff]/15 border border-[#00f0ff]/40 px-2 py-0.5 rounded-md">
                MoES · RSMC NIO
              </span>
            </div>
            <p className="text-[11px] text-[#8b96aa] leading-tight">Operational Multi-Scale Decision Support System</p>
          </div>
        </div>

        <div className="h-7 w-[1px] bg-[#232832] mx-2 hidden sm:block" />

        {/* Cyclone Selector Dropdown */}
        <div className="flex items-center space-x-2">
          <label htmlFor="cyclone-select" className="text-xs text-[#8b96aa] uppercase tracking-wider font-bold hidden md:inline">
            Storm:
          </label>
          <select
            id="cyclone-select"
            value={selectedCycloneId}
            onChange={(e) => onSelectCyclone(e.target.value)}
            className="bg-[#161a22] border border-[#333a48] text-white text-xs font-bold rounded-xl px-3 py-2 focus:outline-none focus:border-[#007afc] hover:border-[#444d5a] transition-all shadow-inner"
          >
            {cyclones.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name ? `${c.name} (${c.basin})` : c.id} {c.is_active ? '● [ACTIVE]' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Center: Live UTC Clock & Telemetry Heartbeat */}
      <div className="hidden lg:flex items-center space-x-3 bg-[#161a22] border border-[#232832] px-4 py-2 rounded-xl shadow-inner">
        <div className="w-2.5 h-2.5 rounded-full bg-[#10b981] animate-pulse" />
        <span className="text-xs font-mono font-bold text-white tracking-wider">{utcTime}</span>
        <span className="text-[10px] text-[#8b96aa] border-l border-[#232832] pl-2">SYNOPTIC 06Z</span>
      </div>

      {/* Right: Health Status & Trigger Action Buttons */}
      <div className="flex items-center space-x-3">
        {/* Service Health Badges */}
        <div className="hidden xl:flex items-center space-x-3 text-xs bg-[#161a22] border border-[#232832] px-3 py-1.5 rounded-xl">
          <div className="flex items-center space-x-1.5" title={`PostgreSQL PostGIS: ${health?.database?.status || 'connected'}`}>
            <span className={`w-2 h-2 rounded-full ${health?.database?.status === 'connected' ? 'bg-[#10b981]' : 'bg-red-500'}`} />
            <span className="text-[#8b96aa] text-[11px] font-mono">PostGIS</span>
          </div>
          <div className="flex items-center space-x-1.5" title={`ML Detection: ${health?.services?.ml_detection?.status || 'online'}`}>
            <span className={`w-2 h-2 rounded-full ${health?.services?.ml_detection?.status === 'online' ? 'bg-[#10b981]' : 'bg-amber-500'}`} />
            <span className="text-[#8b96aa] text-[11px] font-mono">CNN-M1</span>
          </div>
          <div className="flex items-center space-x-1.5" title={`ML Forecasting: ${health?.services?.ml_prediction?.status || 'online'}`}>
            <span className={`w-2 h-2 rounded-full ${health?.services?.ml_prediction?.status === 'online' ? 'bg-[#10b981]' : 'bg-amber-500'}`} />
            <span className="text-[#8b96aa] text-[11px] font-mono">GRU-M2</span>
          </div>
        </div>

        {/* Quick Ingest Stream Button */}
        {onQuickSimulate && (
          <button
            onClick={onQuickSimulate}
            disabled={isSimulating}
            className="hidden sm:flex items-center space-x-1.5 bg-[#161a22] hover:bg-[#1f242e] border border-[#333a48] text-[#00f0ff] hover:text-white text-xs font-bold px-3.5 py-2 rounded-xl transition-all shadow"
            title="Stream next observation fix from buoy / satellite network"
          >
            <span>📡 Ingest Fix</span>
          </button>
        )}

        {/* Primary CTA Button (High-Contrast Gradient Pill) */}
        <button
          onClick={onOpenAnalysisModal}
          disabled={isAnalyzing}
          className="bg-gradient-to-r from-[#007afc] to-[#00f0ff] hover:brightness-110 active:scale-95 disabled:opacity-50 text-[#0e1014] text-xs font-black px-5 py-2.5 rounded-xl shadow-[0_0_20px_rgba(0,122,252,0.4)] transition-all flex items-center space-x-2"
        >
          {isAnalyzing ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-black/40 border-t-black rounded-full animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <span>⚡ Run AI Pipeline</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
};
