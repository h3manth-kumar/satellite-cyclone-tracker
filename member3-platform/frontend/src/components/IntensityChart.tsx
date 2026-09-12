import React, { useState } from 'react';
import { Observation, ForecastPoint } from '../types/cyclone';

interface IntensityChartProps {
  observations: Observation[];
  forecastPoints: ForecastPoint[];
}

export const IntensityChart: React.FC<IntensityChartProps> = ({
  observations,
  forecastPoints,
}) => {
  const [selectedLead, setSelectedLead] = useState<number | null>(null);
  const [hoverPoint, setHoverPoint] = useState<{
    label: string;
    wind: number;
    pressure: number;
    isPredicted: boolean;
    conf?: number;
    x: number;
    y: number;
  } | null>(null);

  // 1. Sort historical observations chronologically
  const sortedObs = [...observations].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  const pastPoints = sortedObs.slice(-6).map((o) => ({
    label: o.timestamp.substring(11, 16) + 'z',
    wind: o.wind_speed ?? 65,
    pressure: o.pressure ?? 980,
    isPredicted: false,
    lead: 0,
  }));

  // 2. Sort future forecast points
  const sortedForecasts = [...forecastPoints].sort((a, b) => a.lead_hours - b.lead_hours);
  const futurePoints = sortedForecasts.map((f) => ({
    label: `+${f.lead_hours}h`,
    wind: f.predicted_wind_speed ?? 85,
    pressure: f.predicted_pressure ?? 965,
    isPredicted: true,
    lead: f.lead_hours,
    confidence: f.confidence,
    uncertaintyKm: f.uncertainty_radius_km,
  }));

  const data = [...pastPoints, ...futurePoints];

  if (data.length === 0) {
    return (
      <div className="bg-[#10141b] border border-[#222936] rounded-2xl p-6 flex items-center justify-center text-xs text-[#8b96aa] h-72 shadow-2xl">
        No intensity telemetry available for this system.
      </div>
    );
  }

  const peakForecastWind = futurePoints.length > 0 ? Math.max(...futurePoints.map((f) => f.wind)) : (pastPoints.length > 0 ? pastPoints[pastPoints.length - 1].wind : 0);
  const minForecastPres = futurePoints.length > 0 ? Math.min(...futurePoints.map((f) => f.pressure)) : (pastPoints.length > 0 ? pastPoints[pastPoints.length - 1].pressure : 1000);

  // Responsive SVG Canvas dimensions
  const svgWidth = 660;
  const svgHeight = 230;
  const paddingLeft = 50;
  const paddingRight = 50;
  const paddingTop = 28;
  const paddingBottom = 38;

  const chartWidth = svgWidth - paddingLeft - paddingRight;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  const maxWind = 150;
  const minWind = 20;

  const maxPres = 1010;
  const minPres = 910;

  const getX = (index: number) => {
    if (data.length <= 1) return paddingLeft + chartWidth / 2;
    return paddingLeft + (index / (data.length - 1)) * chartWidth;
  };

  const getYWind = (val: number) => {
    const ratio = (val - minWind) / (maxWind - minWind);
    return paddingTop + (1 - Math.max(0, Math.min(1, ratio))) * chartHeight;
  };

  const getYPres = (val: number) => {
    const ratio = (val - minPres) / (maxPres - minPres);
    return paddingTop + (1 - Math.max(0, Math.min(1, ratio))) * chartHeight;
  };

  const observedData = data.filter((d) => !d.isPredicted);
  const predictedData = data.filter((d) => d.isPredicted);

  // Build Wind Paths
  let observedWindPath = '';
  observedData.forEach((d, i) => {
    const x = getX(i);
    const y = getYWind(d.wind);
    observedWindPath += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });

  let forecastWindPath = '';
  if (predictedData.length > 0 && observedData.length > 0) {
    const lastObsIdx = observedData.length - 1;
    forecastWindPath += `M ${getX(lastObsIdx)} ${getYWind(observedData[lastObsIdx].wind)}`;
    predictedData.forEach((d, i) => {
      const idx = observedData.length + i;
      forecastWindPath += ` L ${getX(idx)} ${getYWind(d.wind)}`;
    });
  }

  // Build Pressure Path
  let fullPressurePath = '';
  data.forEach((d, i) => {
    const x = getX(i);
    const y = getYPres(d.pressure);
    fullPressurePath += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
  });

  return (
    <div className="bg-[#10141b] border border-[#222936] rounded-2xl p-5 shadow-2xl space-y-4">
      {/* Header with High-Impact Telemetry HUD */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <h3 className="text-white font-black text-sm tracking-tight">
              AI Multi-Lead Forecast & Intensity Trajectory
            </h3>
          </div>
          <p className="text-[11px] text-[#8899b5] mt-0.5">
            Max sustained surface wind (kts / km/h) & barometric pressure curve across synoptic horizons
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="bg-[#141822] border border-cyan-500/40 px-3 py-1 rounded-xl text-xs font-mono shadow-md">
            <span className="text-[#8899b5] text-[9px] block">PEAK WIND (V-MAX)</span>
            <span className="text-cyan-400 font-black text-sm">
              {peakForecastWind.toFixed(1)} kts <span className="text-[10px] text-[#8899b5] font-normal">({Math.round(peakForecastWind * 1.852)} km/h)</span>
            </span>
          </div>
          <div className="bg-[#141822] border border-emerald-500/40 px-3 py-1 rounded-xl text-xs font-mono shadow-md">
            <span className="text-[#8899b5] text-[9px] block">MIN PRESSURE (P-MIN)</span>
            <span className="text-emerald-400 font-black text-sm">{minForecastPres.toFixed(1)} hPa</span>
          </div>
        </div>
      </div>

      {/* Interactive Milestone Cards or On-Demand Callout */}
      {futurePoints.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {futurePoints.map((f, fIdx) => (
            <button
              key={f.lead}
              onClick={() => setSelectedLead(selectedLead === f.lead ? null : f.lead)}
              onMouseEnter={() => {
                const totalIdx = observedData.length + fIdx;
                setHoverPoint({
                  label: f.label,
                  wind: f.wind,
                  pressure: f.pressure,
                  isPredicted: true,
                  conf: f.confidence,
                  x: getX(totalIdx),
                  y: getYWind(f.wind),
                });
              }}
              onMouseLeave={() => setHoverPoint(null)}
              className={`p-3 rounded-xl text-left transition-all border shadow-sm ${
                selectedLead === f.lead
                  ? 'bg-cyan-950/60 border-cyan-400 shadow-[0_0_15px_rgba(0,240,255,0.3)] scale-[1.02]'
                  : 'bg-[#141822] border-[#222936] hover:border-cyan-500/50 hover:bg-[#181d2a]'
              }`}
            >
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-cyan-400 font-bold">+{f.lead}h Horizon</span>
                <span className="text-emerald-400 font-mono font-bold">{(f.confidence * 100).toFixed(0)}% Conf</span>
              </div>
              <div className="mt-1 flex items-baseline justify-between">
                <div>
                  <span className="text-white font-black text-base">{f.wind.toFixed(1)}</span>
                  <span className="text-[#8899b5] text-[10px] ml-1">kts</span>
                </div>
                <span className="text-emerald-400 text-[10px] font-mono font-bold">{f.pressure.toFixed(1)} hPa</span>
              </div>
              <div className="text-[9px] text-[#8899b5] mt-1 flex justify-between">
                <span>Cone: ±{f.uncertaintyKm} km</span>
                <span className="text-cyan-300 font-mono font-bold">{Math.round(f.wind * 1.852)} km/h</span>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div className="bg-[#141822]/80 border border-cyan-500/30 rounded-xl p-3 text-center flex items-center justify-center space-x-2 text-xs shadow-inner">
          <span className="text-cyan-400 font-bold animate-pulse">⚡</span>
          <span className="text-[#8899b5]">
            Forecast models initialized. Click <strong className="text-cyan-400">"⚡ Run AI Pipeline"</strong> above to compute deep learning multi-lead trajectory (+6h to +72h).
          </span>
        </div>
      )}

      {/* Large Dynamic & Responsive SVG Chart */}
      <div className="relative w-full bg-[#080a0f] border border-[#222936] rounded-xl p-2.5 overflow-hidden shadow-inner">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto">
          {/* Gradients */}
          <defs>
            <linearGradient id="forecastAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#00f0ff" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="pressureLineGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#34d399" stopOpacity="1.0" />
            </linearGradient>
          </defs>

          {/* Reference Category Lines */}
          {[
            { wind: 120, label: 'Super Cyclone (120 kts)', color: '#ec4899' },
            { wind: 90, label: 'Extremely Severe (90 kts)', color: '#ef4444' },
            { wind: 64, label: 'Very Severe (64 kts)', color: '#f97316' },
            { wind: 34, label: 'Gale Threshold (34 kts)', color: '#eab308' },
          ].map((cat, idx) => {
            const y = getYWind(cat.wind);
            return (
              <g key={idx}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={svgWidth - paddingRight}
                  y2={y}
                  stroke={cat.color}
                  strokeWidth="0.8"
                  strokeDasharray="3, 4"
                  opacity="0.35"
                />
                <text
                  x={svgWidth - paddingRight + 4}
                  y={y + 3}
                  fill={cat.color}
                  fontSize="8"
                  fontWeight="bold"
                  opacity="0.8"
                >
                  {cat.wind}k
                </text>
              </g>
            );
          })}

          {/* Left Y-Axis (Wind Speed) */}
          <line x1={paddingLeft} y1={paddingTop} x2={paddingLeft} y2={svgHeight - paddingBottom} stroke="#232832" strokeWidth="1" />
          <text x={paddingLeft - 8} y={paddingTop - 10} fill="#00f0ff" fontSize="9" fontWeight="bold" textAnchor="end">
            Wind (kts)
          </text>
          {[30, 60, 90, 120, 150].map((w) => (
            <text key={w} x={paddingLeft - 6} y={getYWind(w) + 3} fill="#8899b5" fontSize="8" textAnchor="end">
              {w}
            </text>
          ))}

          {/* Right Y-Axis (Pressure) */}
          <line x1={svgWidth - paddingRight} y1={paddingTop} x2={svgWidth - paddingRight} y2={svgHeight - paddingBottom} stroke="#232832" strokeWidth="1" />
          <text x={svgWidth - paddingRight + 8} y={paddingTop - 10} fill="#10b981" fontSize="9" fontWeight="bold">
            hPa
          </text>

          {/* X-Axis Horizontal Line */}
          <line
            x1={paddingLeft}
            y1={svgHeight - paddingBottom}
            x2={svgWidth - paddingRight}
            y2={svgHeight - paddingBottom}
            stroke="#232832"
            strokeWidth="1"
          />

          {/* Pressure Line Curve (Dotted Green) */}
          {fullPressurePath && (
            <path
              d={fullPressurePath}
              fill="none"
              stroke="url(#pressureLineGrad)"
              strokeWidth="2"
              strokeDasharray="4, 4"
              opacity="0.85"
            />
          )}

          {/* Observed Wind Path (Solid White-Cyan) */}
          {observedWindPath && (
            <path
              d={observedWindPath}
              fill="none"
              stroke="#ffffff"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
          )}

          {/* Forecast Wind Path (Glowing Dashed Cyan) */}
          {forecastWindPath && (
            <g>
              <path
                d={forecastWindPath}
                fill="none"
                stroke="#00f0ff"
                strokeWidth="7"
                opacity="0.35"
                strokeLinecap="round"
              />
              <path
                d={forecastWindPath}
                fill="none"
                stroke="#00f0ff"
                strokeWidth="3"
                strokeDasharray="6, 6"
                strokeLinecap="round"
              />
            </g>
          )}

          {/* Data Points */}
          {data.map((d, i) => {
            const x = getX(i);
            const y = getYWind(d.wind);
            const isHovered = hoverPoint?.label === d.label;
            const isLeadSelected = selectedLead === d.lead;

            return (
              <g
                key={i}
                className="cursor-pointer transition-all"
                onMouseEnter={() =>
                  setHoverPoint({
                    label: d.label,
                    wind: d.wind,
                    pressure: d.pressure,
                    isPredicted: d.isPredicted,
                    conf: (d as any).confidence,
                    x,
                    y,
                  })
                }
                onMouseLeave={() => setHoverPoint(null)}
              >
                {/* Vertical Guideline */}
                <line
                  x1={x}
                  y1={paddingTop}
                  x2={x}
                  y2={svgHeight - paddingBottom}
                  stroke={isHovered || isLeadSelected ? '#00f0ff' : '#1e2430'}
                  strokeWidth={isHovered || isLeadSelected ? 1.5 : 0.8}
                  strokeDasharray={isHovered ? 'none' : '2, 3'}
                  opacity={isHovered ? 0.8 : 0.4}
                />

                {/* Outer Glow Halo on Hover / Selected */}
                {(isHovered || isLeadSelected) && (
                  <circle cx={x} cy={y} r="12" fill="#00f0ff" opacity="0.3" className="animate-ping" />
                )}

                {/* Point Marker */}
                <circle
                  cx={x}
                  cy={y}
                  r={d.isPredicted ? (isHovered || isLeadSelected ? 7 : 5.5) : (isHovered ? 6 : 4.5)}
                  fill={d.isPredicted ? '#00f0ff' : '#ffffff'}
                  stroke={d.isPredicted ? '#080a0f' : '#007afc'}
                  strokeWidth="2"
                />

                {/* X-Axis Label */}
                <text
                  x={x}
                  y={svgHeight - paddingBottom + 16}
                  fill={d.isPredicted ? '#00f0ff' : '#8899b5'}
                  fontSize="8.5"
                  fontWeight={d.isPredicted || isHovered ? 'bold' : 'normal'}
                  textAnchor="middle"
                >
                  {d.label}
                </text>

                {/* Wind Value Tag Above Node */}
                <text
                  x={x}
                  y={y - 8}
                  fill={d.isPredicted ? '#00f0ff' : '#ffffff'}
                  fontSize="8"
                  fontWeight="bold"
                  textAnchor="middle"
                >
                  {d.wind.toFixed(0)}k
                </text>
              </g>
            );
          })}

          {/* Floating Tooltip Card */}
          {hoverPoint && (
            <g transform={`translate(${Math.min(svgWidth - 140, Math.max(paddingLeft, hoverPoint.x - 60))}, ${Math.max(10, hoverPoint.y - 55)})`}>
              <rect
                width="120"
                height="45"
                rx="6"
                fill="#0c1017"
                stroke="#00f0ff"
                strokeWidth="1.2"
                filter="drop-shadow(0 4px 8px rgba(0,0,0,0.8))"
              />
              <text x="8" y="14" fill="#ffffff" fontSize="9" fontWeight="bold">
                {hoverPoint.label} {hoverPoint.isPredicted ? '· AI Forecast' : '· Observed'}
              </text>
              <text x="8" y="27" fill="#00f0ff" fontSize="8.5" fontWeight="bold">
                💨 Wind: {hoverPoint.wind.toFixed(1)} kts ({Math.round(hoverPoint.wind * 1.852)} km/h)
              </text>
              <text x="8" y="39" fill="#10b981" fontSize="8" fontWeight="bold">
                ⏲ Pressure: {hoverPoint.pressure.toFixed(1)} hPa
              </text>
            </g>
          )}
        </svg>
      </div>
    </div>
  );
};
