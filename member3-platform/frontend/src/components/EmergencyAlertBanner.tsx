import React, { useState, useEffect, useRef } from 'react';
import { CycloneSummary, Observation, ForecastPoint } from '../types/cyclone';

interface EmergencyAlertBannerProps {
  cyclone: CycloneSummary | null;
  latestObs: Observation | null;
  forecastPoints: ForecastPoint[];
}

export const EmergencyAlertBanner: React.FC<EmergencyAlertBannerProps> = ({
  cyclone,
  latestObs,
  forecastPoints,
}) => {
  const [isAlarmActive, setIsAlarmActive] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(true);
  const [landfallCountdown, setLandfallCountdown] = useState<string>('14h 25m');
  const audioCtxRef = useRef<AudioContext | null>(null);
  const oscillatorRef = useRef<OscillatorNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const sirenIntervalRef = useRef<any>(null);

  const windSpeed = latestObs?.wind_speed ?? 95;
  const isHighThreat = windSpeed >= 64; // Cyclone or above

  // Calculate dynamic landfall countdown
  useEffect(() => {
    if (forecastPoints.length > 0) {
      const landfallPoint = forecastPoints.find((f) => f.lead_hours >= 12) || forecastPoints[0];
      const hours = landfallPoint.lead_hours;
      setLandfallCountdown(`${hours}h 00m`);
    }
  }, [forecastPoints]);

  // Web Audio API Synthesized Disaster Warning Siren
  const startSiren = () => {
    try {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === 'suspended') {
        ctx.resume();
      }

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sawtooth';
      gain.gain.setValueAtTime(0.08, ctx.currentTime);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();

      oscillatorRef.current = osc;
      gainNodeRef.current = gain;

      let freqToggle = false;
      sirenIntervalRef.current = setInterval(() => {
        if (oscillatorRef.current && audioCtxRef.current) {
          const targetFreq = freqToggle ? 720 : 440;
          oscillatorRef.current.frequency.setTargetAtTime(targetFreq, audioCtxRef.current.currentTime, 0.15);
          freqToggle = !freqToggle;
        }
      }, 600);

      setIsMuted(false);
      setIsAlarmActive(true);
    } catch (e) {
      console.warn('Audio Siren playback blocked or unsupported:', e);
    }
  };

  const stopSiren = () => {
    if (sirenIntervalRef.current) {
      clearInterval(sirenIntervalRef.current);
      sirenIntervalRef.current = null;
    }
    if (oscillatorRef.current) {
      try {
        oscillatorRef.current.stop();
        oscillatorRef.current.disconnect();
      } catch (e) {}
      oscillatorRef.current = null;
    }
    setIsMuted(true);
    setIsAlarmActive(false);
  };

  const toggleAlarm = () => {
    if (isAlarmActive && !isMuted) {
      stopSiren();
    } else {
      startSiren();
    }
  };

  useEffect(() => {
    return () => {
      stopSiren();
      if (audioCtxRef.current) {
        audioCtxRef.current.close().catch(() => {});
      }
    };
  }, []);

  return (
    <div className={`mx-6 mt-4 rounded-2xl border transition-all duration-500 overflow-hidden ${
      isHighThreat
        ? 'bg-gradient-to-r from-red-950/90 via-[#181116]/95 to-[#12151a] border-red-500/80 shadow-[0_0_30px_rgba(239,68,68,0.25)] emergency-strobe'
        : 'bg-[#12151a] border-[#232832]'
    }`}>
      <div className="p-3.5 px-6 flex flex-wrap items-center justify-between gap-4">
        {/* Left Threat Indicator */}
        <div className="flex items-center space-x-4">
          <div className="relative flex items-center justify-center">
            <div className="w-10 h-10 rounded-2xl bg-red-500/20 border border-red-500/50 flex items-center justify-center text-xl animate-bounce">
              🚨
            </div>
            <div className="w-3 h-3 rounded-full bg-red-500 absolute -top-1 -right-1 animate-ping" />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-black tracking-wider uppercase px-2 py-0.5 rounded-md bg-red-600 text-white shadow-[0_0_10px_rgba(239,68,68,0.8)]">
                CRITICAL WARNING: LEVEL 4 RED ALERT
              </span>
              <span className="text-xs font-bold text-red-300 hidden md:inline">
                • Mandatory Evacuation within 15km Coastal Buffer
              </span>
            </div>
            <p className="text-xs text-[#d5dae2] font-medium mt-0.5">
              <strong className="text-white">{cyclone?.name || 'Active Storm'}</strong> approaching coast. Expected Landfall Intensity: <strong className="text-red-400">{latestObs?.classification || 'Extremely Severe Storm'}</strong> ({windSpeed} kts / {Math.round(windSpeed * 1.852)} km/h).
            </p>
          </div>
        </div>

        {/* Center: Landfall Countdown & Storm Surge Meter */}
        <div className="flex items-center space-x-6 text-xs bg-[#090b0e]/80 border border-[#232832] px-4 py-2 rounded-xl">
          <div>
            <span className="text-[10px] text-[#8b96aa] block uppercase font-bold">Est. Landfall In:</span>
            <span className="font-mono text-sm font-black text-amber-400 tracking-wider">
              ⏱ {landfallCountdown}
            </span>
          </div>

          <div className="h-6 w-[1px] bg-[#232832]" />

          <div>
            <span className="text-[10px] text-[#8b96aa] block uppercase font-bold">Storm Surge:</span>
            <span className="font-mono text-sm font-black text-cyan-400">
              🌊 4.2 - 5.8 m
            </span>
          </div>

          <div className="h-6 w-[1px] bg-[#232832]" />

          <div>
            <span className="text-[10px] text-[#8b96aa] block uppercase font-bold">NDRF Alert:</span>
            <span className="font-mono text-xs font-bold text-emerald-400">
              ● 24 BATTALIONS DEPLOYED
            </span>
          </div>
        </div>

        {/* Right: Audio Siren Alarm Trigger */}
        <div className="flex items-center space-x-3">
          <button
            onClick={toggleAlarm}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-black transition-all shadow-lg ${
              isAlarmActive && !isMuted
                ? 'bg-red-600 hover:bg-red-700 text-white shadow-[0_0_20px_rgba(239,68,68,0.9)] animate-pulse'
                : 'bg-[#1c222c] hover:bg-red-900/40 text-red-300 border border-red-500/40 hover:border-red-400'
            }`}
          >
            <span>{isAlarmActive && !isMuted ? '🔊 SIREN ACTIVE (CLICK TO MUTE)' : '🚨 TEST EVACUATION SIREN'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
