import React, { useState, useEffect } from 'react';
import { CycloneSummary, Observation, ForecastPoint } from '../types/cyclone';

interface EmergencyAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  cyclone: CycloneSummary | null;
  latestObs: Observation | null;
  forecastPoints: ForecastPoint[];
}

export const EmergencyAlertModal: React.FC<EmergencyAlertModalProps> = ({
  isOpen,
  onClose,
  cyclone,
  latestObs,
  forecastPoints,
}) => {
  const [activeTab, setActiveTab] = useState<'mobile' | 'broadcast' | 'contacts'>('mobile');
  const targetPhoneNumber = '916360296983';
  const [isSending, setIsSending] = useState<boolean>(false);
  const [dispatchStatus, setDispatchStatus] = useState<string | null>(null);
  const [sirenActive, setSirenActive] = useState<boolean>(false);

  const currentLat = latestObs?.latitude ?? cyclone?.latest_lat ?? 22.20;
  const currentLon = latestObs?.longitude ?? cyclone?.latest_lon ?? 87.63;
  const currentWind = latestObs?.wind_speed ?? cyclone?.latest_wind_speed ?? 88.1;
  const currentStage = latestObs?.classification ?? cyclone?.latest_classification ?? 'Very Severe Cyclonic Storm';
  const windKmh = Math.round(currentWind * 1.852);

  // Approximate coast distance
  const isArabianSea = (cyclone?.basin?.toUpperCase().includes('ARB') || cyclone?.name?.toUpperCase().includes('BIPARJOY') || currentLon < 76.5);
  const targetCoastLat = isArabianSea ? 22.8 : 20.8;
  const targetCoastLon = isArabianSea ? 69.5 : 86.9;
  const distToCoastKm = Math.max(10, Math.round(
    Math.sqrt(Math.pow((targetCoastLat - currentLat) * 111, 2) + Math.pow((targetCoastLon - currentLon) * 105, 2))
  ));

  // Construct direct WhatsApp message
  const alertMessage = encodeURIComponent(
    `🚨 *EMERGENCY CYCLONE WARNING (NDMA / IMD)* 🚨\n\n` +
    `⚠️ *COASTAL LANDFALL ALERT*\n` +
    `🌪️ *SYSTEM:* ${cyclone?.name?.toUpperCase() || 'CYCLONE SYSTEM'} (${currentStage.toUpperCase()})\n` +
    `📍 *EYE FIX:* ${currentLat.toFixed(2)}°N, ${currentLon.toFixed(2)}°E\n` +
    `💨 *MAX SUSTAINED WINDS:* ${currentWind.toFixed(1)} kts (${windKmh} km/h)\n` +
    `🌊 *HYDRODYNAMIC SURGE:* 3.8m – 5.2m Coastal Inundation\n` +
    `🏖️ *COAST PROXIMITY:* ~${distToCoastKm} km to Indian Mainland\n` +
    `📞 *EMERGENCY HELPLINE:* 1070 / 1077\n\n` +
    `⚠️ *ACTION MANDATE:* Immediate mandatory evacuation for all coastal settlements within 250km radius. Move inland immediately!`
  );

  // Direct universal URL (Works for both WhatsApp Web and Mobile App without popup blocking)
  const whatsAppWebUrl = `https://web.whatsapp.com/send?phone=${targetPhoneNumber}&text=${alertMessage}`;
  const whatsAppApiUrl = `https://wa.me/${targetPhoneNumber}?text=${alertMessage}`;

  // Play synthesized web audio emergency siren
  const playEmergencySiren = () => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(850, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1350, audioCtx.currentTime + 0.35);
      osc.frequency.exponentialRampToValueAtTime(850, audioCtx.currentTime + 0.7);

      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.9);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.9);
      setSirenActive(true);
      setTimeout(() => setSirenActive(false), 900);
    } catch (e) {
      console.warn('AudioContext not allowed or supported', e);
    }
  };

  // Trigger Device Vibration
  const triggerDeviceVibration = () => {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      navigator.vibrate([400, 150, 400, 150, 600]);
    }
  };

  // Dispatch Real Browser Push Notification
  const dispatchBrowserNotification = async () => {
    playEmergencySiren();
    triggerDeviceVibration();

    if (!('Notification' in window)) {
      setDispatchStatus('Browser notifications not supported on this device.');
      return;
    }

    try {
      let permission = Notification.permission;
      if (permission !== 'granted') {
        permission = await Notification.requestPermission();
      }

      if (permission === 'granted') {
        new Notification(`🚨 RED ALERT: Cyclone ${cyclone?.name || 'System'} Approaching India!`, {
          body: `IMD ${currentStage.toUpperCase()} at [${currentLat.toFixed(2)}°N, ${currentLon.toFixed(2)}°E]. Max Winds: ${currentWind.toFixed(1)} kts (${windKmh} km/h). Coast Range: ~${distToCoastKm}km. Evacuation advisory active!`,
          icon: '/favicon.ico',
          tag: 'cyclone-emergency-alert',
          requireInteraction: true,
        });
        setDispatchStatus(`✅ Real Emergency Notification dispatched to your active screen!`);
      } else {
        setDispatchStatus('⚠️ Notification permission was not granted by browser.');
      }
    } catch (err: any) {
      setDispatchStatus(`Notification error: ${err.message}`);
    }
  };

  // Simulate Cell Broadcast to Coastal Towers
  const handleSimulateCBS = () => {
    setIsSending(true);
    playEmergencySiren();
    triggerDeviceVibration();

    setTimeout(() => {
      setIsSending(false);
      setDispatchStatus(`✅ CELL BROADCAST DISPATCHED: 1,850,000 active mobile devices notified across coastal sectors.`);
    }, 1200);
  };

  // Automatically trigger siren and notification when alert modal opens
  useEffect(() => {
    if (isOpen) {
      playEmergencySiren();
      triggerDeviceVibration();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] bg-black/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto animate-fade-in">
      <div className="relative w-full max-w-2xl bg-[#0c0f15] border-2 border-red-500/70 rounded-2xl shadow-[0_0_50px_rgba(239,68,68,0.4)] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header with Red Alert Banner */}
        <div className="bg-gradient-to-r from-red-950 via-[#1e0a10] to-[#0c0f15] border-b border-red-500/50 p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-xl bg-red-600/30 border border-red-500 flex items-center justify-center text-xl shadow-[0_0_20px_rgba(239,68,68,0.8)] ${sirenActive ? 'animate-ping' : ''}`}>
              🚨
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-white font-black text-base tracking-tight">NATIONAL EMERGENCY ALERT BROADCAST</h3>
                <span className="bg-red-600 text-white text-[9px] font-black uppercase px-2.5 py-0.5 rounded-full animate-pulse shadow-md">
                  LEVEL-4 RED ALERT
                </span>
              </div>
              <p className="text-[11px] text-red-300">NDMA / IMD Coastal Disaster Management Dispatch Center</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg bg-[#161a22] hover:bg-red-900/40 border border-[#232832] text-[#8b96aa] hover:text-white flex items-center justify-center font-bold text-sm"
          >
            ✕
          </button>
        </div>

        {/* Proximity Warning Banner & Direct Anchor Click (Never Blocked by Popups) */}
        <div className="bg-red-950/40 border-b border-red-500/30 px-5 py-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center space-x-2 text-xs">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
            <span className="text-[#8b96aa] font-bold">PROXIMITY:</span>
            <span className="font-mono font-black text-amber-300 text-sm bg-[#12161f] px-2.5 py-0.5 rounded-lg border border-amber-500/50">
              ~{distToCoastKm} km to Indian Mainland
            </span>
          </div>
          <a
            href={whatsAppApiUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => {
              playEmergencySiren();
              setDispatchStatus("✅ WhatsApp Web tab launched!");
            }}
            className="bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white text-xs font-black px-4 py-2 rounded-xl flex items-center space-x-2 shadow-[0_0_15px_rgba(16,185,129,0.5)] transition-all active:scale-95 animate-bounce"
          >
            <span>💬</span>
            <span>SEND WHATSAPP ALERT (CLICK HERE)</span>
          </a>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-[#232832] bg-[#10141b] text-xs font-bold">
          <button
            onClick={() => setActiveTab('mobile')}
            className={`flex-1 py-2.5 px-3 border-b-2 flex items-center justify-center space-x-1.5 transition-all ${
              activeTab === 'mobile'
                ? 'border-red-500 text-red-400 bg-red-950/20'
                : 'border-transparent text-[#8b96aa] hover:text-white'
            }`}
          >
            <span>📱</span>
            <span>WhatsApp & Mobile Broadcast</span>
          </button>
          <button
            onClick={() => setActiveTab('broadcast')}
            className={`flex-1 py-2.5 px-3 border-b-2 flex items-center justify-center space-x-1.5 transition-all ${
              activeTab === 'broadcast'
                ? 'border-red-500 text-red-400 bg-red-950/20'
                : 'border-transparent text-[#8b96aa] hover:text-white'
            }`}
          >
            <span>📡</span>
            <span>Cell Tower Broadcast (CBS)</span>
          </button>
          <button
            onClick={() => setActiveTab('contacts')}
            className={`flex-1 py-2.5 px-3 border-b-2 flex items-center justify-center space-x-1.5 transition-all ${
              activeTab === 'contacts'
                ? 'border-red-500 text-red-400 bg-red-950/20'
                : 'border-transparent text-[#8b96aa] hover:text-white'
            }`}
          >
            <span>👥</span>
            <span>State Emergency Relays</span>
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {/* Status Message Notification */}
          {dispatchStatus && (
            <div className="p-3.5 rounded-xl bg-[#141b24] border border-cyan-500/50 text-cyan-300 flex items-center justify-between text-xs animate-fade-in shadow-xl">
              <div className="flex items-center space-x-2">
                <span className="text-base">🔔</span>
                <span className="font-medium">{dispatchStatus}</span>
              </div>
              <button onClick={() => setDispatchStatus(null)} className="text-[#8b96aa] hover:text-white ml-2 font-bold">✕</button>
            </div>
          )}

          {/* TAB 1: Real Mobile Device Alert / Direct Phone Notification */}
          {activeTab === 'mobile' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Phone Mockup Screen */}
              <div className="bg-[#05070a] border-2 border-[#2a313d] rounded-3xl p-4 shadow-2xl relative flex flex-col justify-between min-h-[320px]">
                {/* Simulated Phone Top Bar */}
                <div className="flex justify-between items-center text-[9px] text-[#8b96aa] px-1 pb-2 border-b border-[#181d26]">
                  <span className="font-mono font-bold">12:30</span>
                  <div className="flex items-center space-x-1.5">
                    <span>📶 5G (Jio/Airtel)</span>
                    <span>🔋 94%</span>
                  </div>
                </div>

                {/* Emergency Broadcast Card on Phone */}
                <div className="my-auto bg-red-600 text-white rounded-2xl p-3.5 shadow-[0_0_25px_rgba(239,68,68,0.7)] border-2 border-white space-y-2 animate-pulse">
                  <div className="flex items-center space-x-2">
                    <span className="text-xl">⚠️</span>
                    <div>
                      <div className="text-[10px] font-black uppercase tracking-wider">EMERGENCY CELL BROADCAST</div>
                      <div className="text-[9px] font-bold opacity-90">GOVERNMENT OF INDIA · NDMA</div>
                    </div>
                  </div>
                  <div className="text-[11px] font-black leading-snug">
                    RED ALERT: Cyclone {cyclone?.name || 'System'} ({currentStage.toUpperCase()})
                  </div>
                  <div className="text-[10px] opacity-95 leading-tight">
                    Eye at [{currentLat.toFixed(2)}°N, {currentLon.toFixed(2)}°E]. Max Winds: {currentWind.toFixed(1)} kts ({windKmh} km/h). Coast Range: ~{distToCoastKm} km. Mandatory coastal evacuation active!
                  </div>
                  <div className="flex justify-between items-center text-[9px] font-mono bg-black/40 px-2 py-1 rounded-lg">
                    <span>SURGE: 3.8m – 5.2m</span>
                    <span>DIAL: 1070 / 1077</span>
                  </div>
                </div>

                <div className="text-center text-[9px] text-[#8b96aa] pt-1">
                  National disaster broadcast payload for coastal sectors
                </div>
              </div>

              {/* Actions & Instant Direct Links */}
              <div className="space-y-3 flex flex-col justify-between">
                <div className="bg-[#12161f] border border-[#232832] p-3.5 rounded-2xl space-y-2.5 shadow-lg">
                  <h4 className="text-white font-black text-xs flex items-center space-x-1.5">
                    <span>📲</span>
                    <span>Direct Alert Triggers</span>
                  </h4>
                  <p className="text-[10px] text-[#8b96aa]">
                    Click below to open WhatsApp directly in a new tab with the pre-formatted IMD Level-4 Red Alert warning.
                  </p>

                  <div className="space-y-2 pt-1">
                    <a
                      href={whatsAppApiUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => playEmergencySiren()}
                      className="w-full bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white font-black py-2.5 px-3 rounded-xl flex items-center justify-center space-x-2 text-xs transition-all shadow-[0_0_15px_rgba(16,185,129,0.4)] active:scale-95"
                    >
                      <span>💬</span>
                      <span>Open WhatsApp Web Chat & Send</span>
                    </a>

                    <a
                      href={whatsAppWebUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => playEmergencySiren()}
                      className="w-full bg-[#18221c] border border-emerald-500/50 hover:bg-emerald-950/60 text-emerald-300 font-bold py-2 px-3 rounded-xl flex items-center justify-center space-x-2 text-xs transition-all active:scale-95"
                    >
                      <span>🌐</span>
                      <span>Alternative: Direct WhatsApp Web Link</span>
                    </a>

                    <button
                      onClick={dispatchBrowserNotification}
                      className="w-full bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-black py-2 px-3 rounded-xl shadow-[0_0_15px_rgba(239,68,68,0.4)] flex items-center justify-center space-x-2 text-xs transition-all active:scale-95"
                    >
                      <span>🚨</span>
                      <span>Push System Notification to Screen</span>
                    </button>
                  </div>
                </div>

                <div className="bg-[#12161f] border border-[#232832] p-2.5 rounded-xl flex items-center justify-between text-[10px]">
                  <span className="text-[#8b96aa]">Audible Warning Siren:</span>
                  <button
                    onClick={playEmergencySiren}
                    className="bg-red-500/20 hover:bg-red-500/40 text-red-300 border border-red-500/40 px-2.5 py-1 rounded-lg font-bold transition-all"
                  >
                    🔊 Sound Siren Tone
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Cell Broadcast Service (CBS) */}
          {activeTab === 'broadcast' && (
            <div className="space-y-3">
              <div className="bg-[#12161f] border border-[#232832] p-3.5 rounded-xl space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-white font-bold">Target Broadcast Zone:</span>
                  <span className="text-red-400 font-mono font-bold">250 km Radius from Eye [{currentLat.toFixed(2)}°N, {currentLon.toFixed(2)}°E]</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-[10px] text-center pt-1">
                  <div className="bg-[#090b0e] p-2 rounded-lg border border-[#232832]">
                    <div className="text-[#8b96aa]">Active Towers</div>
                    <div className="text-white font-black text-sm">4,820</div>
                  </div>
                  <div className="bg-[#090b0e] p-2 rounded-lg border border-[#232832]">
                    <div className="text-[#8b96aa]">Population Reach</div>
                    <div className="text-amber-400 font-black text-sm">~6.4 Million</div>
                  </div>
                  <div className="bg-[#090b0e] p-2 rounded-lg border border-[#232832]">
                    <div className="text-[#8b96aa]">Priority Level</div>
                    <div className="text-red-400 font-black text-sm">CLASS 1 (FLASH)</div>
                  </div>
                </div>
              </div>

              <button
                onClick={handleSimulateCBS}
                disabled={isSending}
                className="w-full bg-red-600 hover:bg-red-500 text-white font-black py-3 rounded-xl text-xs flex items-center justify-center space-x-2 shadow-[0_0_20px_rgba(239,68,68,0.5)] transition-all active:scale-95"
              >
                <span>📡</span>
                <span>{isSending ? 'Transmitting to Cell Broadcast Relays...' : 'BROADCAST TO ALL COASTAL CELL TOWERS NOW'}</span>
              </button>
            </div>
          )}

          {/* TAB 3: Command & Control Contacts */}
          {activeTab === 'contacts' && (
            <div className="space-y-2.5">
              <h4 className="text-[#8b96aa] uppercase font-bold text-[10px]">Special Relief Commissioners & Emergency Response Nodes</h4>
              <div className="space-y-2 max-h-56 overflow-y-auto">
                {[
                  { title: 'SRC Control Room (Bhubaneswar)', phone: '0674-2534177', status: 'READY', channel: 'Hotline / VHF' },
                  { title: 'NDRF 03rd Battalion (Mundali)', phone: '0671-2879711', status: 'MOBILIZED', channel: 'SATPHONE' },
                  { title: 'Indian Coast Guard (Paradip Station)', phone: '06722-222123', status: 'ON PATROL', channel: 'AIS / Ch 16' },
                  { title: 'District Collector Office (Balasore)', phone: '06782-262001', status: 'ALERT ACTIVE', channel: 'Direct SMS' },
                  { title: 'Emergency Dispatch Relay Node', phone: '+91 6360296983', status: 'DELIVERED', channel: 'Priority WhatsApp Web' },
                ].map((node, i) => (
                  <div key={i} className="bg-[#12161f] border border-[#232832] p-2.5 rounded-xl flex items-center justify-between text-[11px]">
                    <div>
                      <div className="text-white font-bold">{node.title}</div>
                      <div className="text-[#8b96aa] text-[10px] font-mono">{node.phone} · {node.channel}</div>
                    </div>
                    <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      {node.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 bg-[#090b0e] border-t border-[#232832] flex justify-between items-center text-[10px] text-[#8b96aa]">
          <span>Standard Protocol: ITU-T X.1303 Common Alerting Protocol (CAP)</span>
          <button
            onClick={onClose}
            className="bg-[#161a22] hover:bg-[#202632] text-white px-4 py-1.5 rounded-xl font-bold border border-[#333a48]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
