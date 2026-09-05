import React from 'react';
import { clsx } from 'clsx';

interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'warning' | 'busy';
  label?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, label }) => {
  const statusColors = {
    online: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]',
    offline: 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.6)]',
    warning: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)]',
    busy: 'bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.6)]',
  };

  return (
    <div className="inline-flex items-center gap-2">
      <span className={clsx('w-2 h-2 rounded-full inline-block', statusColors[status])} />
      {label && <span className="text-xs text-slate-300 font-medium">{label}</span>}
    </div>
  );
};
