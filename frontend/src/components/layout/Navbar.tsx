import React, { useEffect, useState } from 'react';
import { Shield, Activity } from 'lucide-react';
import { healthService } from '../../services';
import type { HealthResponse } from '../../types';
import { StatusIndicator } from '../common/StatusIndicator';

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await healthService.getHealth();
        setHealth(data);
      } catch (err) {
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-emerald-400 p-0.5 shadow-[0_0_15px_rgba(6,182,212,0.4)]">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-slate-950">
              <Activity className="h-5 w-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tight text-white">MEDLENS</span>
              <span className="rounded bg-cyan-500/10 px-1.5 py-0.2 text-[10px] font-semibold text-cyan-400 border border-cyan-500/30">
                PHASE 1 FOUNDATION
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Clinical Information Intelligence</p>
          </div>
        </div>

        {/* Safety Disclaimer Banner */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-amber-500/30 text-[11px] text-amber-300/90 shadow-inner">
          <Shield className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
          <span>Non-Diagnostic System • Reference Ranges Derived Exclusively From Source Documents</span>
        </div>

        {/* System Health & Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800">
            {loading ? (
              <StatusIndicator status="busy" label="Checking backend..." />
            ) : health && health.status === 'healthy' ? (
              <StatusIndicator status="online" label={`API Online (${health.database})`} />
            ) : (
              <StatusIndicator status="offline" label="Backend Offline" />
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
