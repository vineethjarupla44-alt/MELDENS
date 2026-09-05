import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileCheck2,
  ShieldCheck,
  UserPlus,
  FileText, 
  AlertTriangle, 
  Clock, 
  Activity,
  Layers
} from 'lucide-react';
import { clsx } from 'clsx';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/record', label: 'Medical Record', icon: FileCheck2 },
    { to: '/verification', label: 'Verification Queue', icon: ShieldCheck, badge: 'Review' },
    { to: '/intake', label: 'Patient Intake', icon: UserPlus },
    { to: '/documents', label: 'Documents', icon: FileText, badge: 'Phase 2' },
    { to: '/conflicts', label: 'Conflict Detection', icon: AlertTriangle, badge: 'Phase 3' },
    { to: '/timeline', label: 'Timeline', icon: Clock, badge: 'Phase 4' },
    { to: '/health', label: 'System Health', icon: Activity },
  ];



  return (
    <aside className="w-64 flex-shrink-0 border-r border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between">
      <div className="space-y-6">
        <div>
          <h2 className="px-3 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
            Clinical Navigation
          </h2>
          <nav className="mt-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                      isActive
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.15)]'
                        : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
                    )
                  }
                >
                  <div className="flex items-center gap-3">
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="rounded bg-slate-800/80 px-1.5 py-0.5 text-[9px] font-mono text-slate-400 border border-slate-700/50">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* 3D Dashboard Preview Notice */}
        <div className="rounded-xl border border-slate-800/80 bg-gradient-to-b from-slate-900/60 to-slate-950/80 p-4">
          <div className="flex items-center gap-2 text-cyan-400 mb-1.5">
            <Layers className="h-4 w-4" />
            <span className="text-xs font-semibold">3D Clinical Graph</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Orbital relationship graph connecting Patient Core to Labs, Meds, Conditions, Allergies & Timeline ready for Phase 5.
          </p>
        </div>
      </div>

      <div className="border-t border-slate-800/60 pt-4">
        <div className="text-[11px] text-slate-500 flex flex-col gap-0.5">
          <span>MedLens Architecture v1.0</span>
          <span className="text-slate-600">Strict Non-Diagnostic Mode</span>
        </div>
      </div>
    </aside>
  );
};
