import React, { useEffect, useState } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { StatusIndicator } from '../components/common/StatusIndicator';
import { Button } from '../components/common/Button';
import { healthService } from '../services';
import type { HealthResponse } from '../types';
import { Activity, RefreshCw, Database, Server, Cpu, CheckCircle2, XCircle } from 'lucide-react';

export const HealthPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await healthService.getHealth();
      setHealth(data);
      setLastChecked(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to reach API endpoint');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Activity className="h-6 w-6 text-cyan-400" />
            Backend System Health & Diagnostics
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time verification of the FastAPI service layer, database connectivity, and MedLens architecture.
          </p>
        </div>
        <Button 
          variant="secondary" 
          size="sm" 
          onClick={fetchHealth} 
          isLoading={loading}
        >
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
          Refresh Diagnostics
        </Button>
      </div>

      {/* Health Overview Banner */}
      <GlassCard variant={health?.status === 'healthy' ? 'accent' : error ? 'danger' : 'default'}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {health?.status === 'healthy' ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            ) : (
              <XCircle className="w-8 h-8 text-rose-400" />
            )}
            <div>
              <h2 className="text-lg font-bold text-white">
                {loading ? 'Querying API /api/health...' : health?.status === 'healthy' ? 'System Operational' : 'Connection Failed'}
              </h2>
              <p className="text-xs text-slate-400">
                Endpoint: <code className="text-cyan-400">GET /api/health</code> • Last checked: {lastChecked.toLocaleTimeString()}
              </p>
            </div>
          </div>
          <StatusIndicator 
            status={loading ? 'busy' : health?.status === 'healthy' ? 'online' : 'offline'} 
            label={loading ? 'Checking' : health?.status === 'healthy' ? 'HEALTHY' : 'UNREACHABLE'} 
          />
        </div>
      </GlassCard>

      {/* Diagnostics Grid */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <GlassCard className="space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 text-sm font-semibold">
              <Server className="w-4 h-4" />
              <h3>Service Metadata</h3>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Name</span>
                <span className="text-slate-200 font-medium">{health.service}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Version</span>
                <span className="text-cyan-400 font-mono">{health.version}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Environment</span>
                <span className="text-slate-200 font-mono capitalize">{health.environment}</span>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold">
              <Database className="w-4 h-4" />
              <h3>Database Layer</h3>
            </div>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Status</span>
                <span className="text-emerald-400 font-semibold uppercase">{health.database}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Driver</span>
                <span className="text-slate-200 font-mono">SQLAlchemy / SQLite (Dev)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">PostgreSQL Ready</span>
                <span className="text-emerald-400">Yes (Abstract Repository)</span>
              </div>
            </div>
          </GlassCard>

          <GlassCard className="space-y-2">
            <div className="flex items-center gap-2 text-purple-400 text-sm font-semibold">
              <Cpu className="w-4 h-4" />
              <h3>System Capabilities</h3>
            </div>
            <div className="space-y-1 text-xs">
              {health.system_capabilities && Object.entries(health.system_capabilities).map(([key, value]) => (
                <div key={key} className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="text-purple-300 font-mono">{String(value)}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      )}

      {/* Raw Payload View */}
      <GlassCard>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-300 font-mono">Raw API Response JSON</h3>
          <span className="text-[11px] text-slate-500 font-mono">200 OK</span>
        </div>
        <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-300 overflow-x-auto">
          {health ? JSON.stringify(health, null, 2) : error ? JSON.stringify({ error }, null, 2) : 'Loading...'}
        </pre>
      </GlassCard>
    </div>
  );
};
