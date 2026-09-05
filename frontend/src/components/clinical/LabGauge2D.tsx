import React from 'react';
import type { LabStatus } from '../../types';
import { HelpCircle } from 'lucide-react';

interface LabGauge2DProps {
  value?: number | null;
  low?: number | null;
  high?: number | null;
  unit?: string | null;
  status: LabStatus | string;
  className?: string;
}

export const LabGauge2D: React.FC<LabGauge2DProps> = ({
  value,
  low,
  high,
  unit,
  status,
  className = '',
}) => {
  // Case 1: Missing reference range (Strict requirement: Never invent a range!)
  const hasRange = typeof low === 'number' && typeof high === 'number';

  if (!hasRange || value === null || value === undefined) {
    return (
      <div className={`flex flex-col gap-1 min-w-[180px] ${className}`}>
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="font-mono text-slate-300">
            {value !== null && value !== undefined ? `${value} ${unit || ''}` : 'No numeric value'}
          </span>
          <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 font-sans italic">
            <HelpCircle className="w-2.5 h-2.5" />
            Reference range not provided
          </span>
        </div>
        <div className="w-full h-2 bg-slate-800/80 rounded-full border border-slate-700/50 overflow-hidden relative">
          <div className="w-full h-full bg-slate-700/30 dashed-bar" />
        </div>
      </div>
    );
  }

  // Case 2: Valid report bounds available
  const rangeSpan = high - low;
  // Dynamic display scale: extend 30% beyond low and high for visual context
  const padding = rangeSpan > 0 ? rangeSpan * 0.35 : (low * 0.3 || 1.0);
  const minScale = Math.max(0, low - padding);
  const maxScale = high + padding;
  const totalScale = maxScale - minScale;

  // Normal zone left and width in percentages
  const normalLeftPct = Math.max(0, Math.min(100, ((low - minScale) / totalScale) * 100));
  const normalWidthPct = Math.max(5, Math.min(100 - normalLeftPct, (rangeSpan / totalScale) * 100));

  // Value marker position
  const rawValuePct = ((value - minScale) / totalScale) * 100;
  const valueMarkerPct = Math.max(2, Math.min(98, rawValuePct));

  // Marker color according to clinical status
  const getMarkerColor = () => {
    switch (status) {
      case 'LOW':
        return 'bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.8)] border-white';
      case 'HIGH':
        return 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)] border-white';
      case 'NORMAL':
        return 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] border-white';
      default:
        return 'bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)] border-white';
    }
  };

  return (
    <div className={`flex flex-col gap-1.5 min-w-[200px] ${className}`}>
      {/* 2D Track Bar */}
      <div className="relative w-full h-2.5 bg-slate-950 rounded-full border border-slate-800 overflow-visible flex items-center">
        {/* Low Zone (Left of Normal) */}
        <div 
          className="h-full bg-sky-950/60 rounded-l-full" 
          style={{ width: `${normalLeftPct}%` }}
          title={`Low Zone (< ${low} ${unit || ''})`}
        />

        {/* Normal Zone (Between Low and High) */}
        <div 
          className="h-full bg-emerald-500/25 border-x border-emerald-500/50" 
          style={{ width: `${normalWidthPct}%` }}
          title={`Normal Zone (${low} – ${high} ${unit || ''})`}
        />

        {/* High Zone (Right of Normal) */}
        <div 
          className="h-full bg-rose-950/60 rounded-r-full flex-1" 
          title={`High Zone (> ${high} ${unit || ''})`}
        />

        {/* Value Precision Indicator Pin */}
        <div
          className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 flex flex-col items-center pointer-events-none transition-all duration-300"
          style={{ left: `${valueMarkerPct}%` }}
        >
          <div className={`w-3.5 h-3.5 rounded-full border-2 ${getMarkerColor()}`} />
        </div>
      </div>

      {/* Axis Labels Below */}
      <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 px-0.5">
        <span className="text-slate-500">{low}</span>
        <span className="text-emerald-400 font-medium">
          {low} – {high} {unit || ''}
        </span>
        <span className="text-slate-500">{high}</span>
      </div>
    </div>
  );
};
