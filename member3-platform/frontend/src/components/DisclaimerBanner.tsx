import React from 'react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <footer className="bg-[#0e1012] border-t border-[#1c1f24] py-2 px-6 text-center text-[11px] text-[#8b96aa] flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <span className="w-2 h-2 rounded-full bg-amber-500/80 inline-block" />
        <span className="font-semibold text-[#d5dae2]">OPERATIONAL BOUNDARY NOTICE:</span>
        <span>
          CycloneAI is an AI/ML research and decision-support prototype. It does not replace official meteorological bulletins, advisories, or warnings issued by the India Meteorological Department (IMD) / Ministry of Earth Sciences (MoES).
        </span>
      </div>
      <div className="text-[10px] text-[#566171] font-mono whitespace-nowrap">
        WGS84 · EPSG:4326 · UTC
      </div>
    </footer>
  );
};
