import React, { useEffect, useState } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { RangeBadge } from '../components/common/RangeBadge';
import { StatusIndicator } from '../components/common/StatusIndicator';
import { Button } from '../components/common/Button';
import { healthService } from '../services';
import type { HealthResponse } from '../types';
import { 
  FileCheck2, 
  GitCompare, 
  ShieldAlert, 
  Database, 
  Terminal,
  Activity,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const navigate = useNavigate();

  useEffect(() => {
    healthService.getHealth()
      .then(setHealth)
      .catch(() => setHealth(null))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      {/* Top Banner / Hero */}
      <div className="relative overflow-hidden rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 p-8 shadow-2xl shadow-cyan-950/30">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-400">
            <Activity className="h-3.5 w-3.5" />
            <span>Phase 1 Foundation Operational</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-white">
            MedLens Clinical Intelligence
          </h1>
          <p className="text-base text-slate-300 leading-relaxed">
            Transforming fragmented medical records into structured, verifiable, and traceable clinical intelligence.
            Built with strict non-diagnostic clinical guardrails and report-derived reference validation.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button variant="primary" onClick={() => navigate('/records')}>
              Medical Record & AI Summary <ArrowRight className="w-4 h-4 ml-1" />
            </Button>
            <Button variant="secondary" onClick={() => navigate('/intake')}>
              Patient Intake
            </Button>
            <Button variant="secondary" onClick={() => navigate('/health')}>
              Backend Health
            </Button>
          </div>
        </div>
      </div>

      {/* Live System Health Card */}
      <GlassCard variant="glow">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-cyan-400" />
              Core API & Database Status
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live communication with FastAPI backend at <code className="text-cyan-400">/api/health</code>
            </p>
          </div>
          <div className="flex items-center gap-3">
            {loading ? (
              <StatusIndicator status="busy" label="Checking..." />
            ) : health && health.status === 'healthy' ? (
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 px-2.5 py-1 rounded-md">
                  Database: {health.database}
                </span>
                <span className="text-xs font-mono bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 px-2.5 py-1 rounded-md">
                  v{health.version}
                </span>
                <StatusIndicator status="online" label="Online" />
              </div>
            ) : (
              <StatusIndicator status="offline" label="Offline / Disconnected" />
            )}
          </div>
        </div>
      </GlassCard>

      {/* Component Showcase & Clinical Guardrails */}
      <div>
        <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-cyan-400" />
          Foundation Architecture & Clinical Primitives
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Provenance Primitives */}
          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
              <FileCheck2 className="w-4 h-4" />
              <h3>Provenance Tracking</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every data point tracks its exact origin, document reference, and verification status:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <ProvenanceBadge source="PATIENT_INPUT" />
              <ProvenanceBadge source="DOCUMENT_EXTRACTION" documentName="discharge_summary.pdf" pageNumber={2} />
              <ProvenanceBadge source="AI_GENERATED" />
              <ProvenanceBadge source="HUMAN_VERIFIED" />
            </div>
          </GlassCard>

          {/* Reference Range Engine Rules */}
          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <ShieldAlert className="w-4 h-4" />
              <h3>Report-Derived Range Bounds</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Reference ranges originate <strong>strictly</strong> from the uploaded report. Never assumes textbook ranges:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <RangeBadge status="NORMAL" referenceRangeRaw="12.0 - 16.0 g/dL" />
              <RangeBadge status="LOW" referenceRangeRaw="12.0 - 16.0 g/dL" />
              <RangeBadge status="HIGH" referenceRangeRaw="70 - 99 mg/dL" />
              <RangeBadge status="UNKNOWN" />
            </div>
          </GlassCard>

          {/* Cross-Source Conflict Detection */}
          <GlassCard className="space-y-3">
            <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
              <GitCompare className="w-4 h-4" />
              <h3>Cross-Source Conflict Detection</h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Automated reconciliation cross-references discrepancies between patient inputs and clinical documents for clinician review.
            </p>
            <div className="rounded-lg bg-rose-950/20 border border-rose-500/30 p-2.5 text-xs text-rose-300">
              <span className="font-semibold">Allergy Mismatch Detected:</span> Patient reports Penicillin allergy; Note states NKDA.
            </div>
          </GlassCard>

          {/* AI Clinical Summary Module */}
          <GlassCard className="space-y-3 md:col-span-2 lg:col-span-3 border-cyan-500/30 bg-gradient-to-r from-slate-900 via-cyan-950/20 to-slate-900">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-cyan-300 font-semibold text-sm">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <h3>AI Clinical Summary Module (7 Structured Sections)</h3>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-500/30">
                Non-Diagnostic & Grounded
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Synthesizes validated clinical data into 7 patient-friendly sections: Record Overview, Recently Documented, Laboratory Values & Report Status, Historical Changes, Potential Conflicts, Missing Information, and Verification-Required Information.
            </p>
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
              <span className="text-[11px] text-slate-400">
                Mandatory Safety Disclaimer · Report-Derived Reference Ranges · Exact Provenance Tracking
              </span>
              <Button size="sm" variant="secondary" onClick={() => navigate('/records')}>
                View Active Patient Summary →
              </Button>
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Architectural Safety Guarantees */}
      <GlassCard variant="warning" className="border-amber-500/40">
        <h3 className="text-sm font-bold text-amber-300 uppercase tracking-wide flex items-center gap-2 mb-2">
          <ShieldAlert className="w-4 h-4" />
          MedLens Core Clinical Guardrails
        </h3>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-slate-300 list-disc list-inside">
          <li><strong>Never Diagnoses:</strong> MedLens categorizes documented findings without inferring diagnoses.</li>
          <li><strong>Never Prescribes:</strong> Medication reconciliation organizes orders without recommending changes.</li>
          <li><strong>Never Invents Facts:</strong> Omitted data remains explicit as unknown or unverified.</li>
          <li><strong>Zero Generic Ranges:</strong> Lab ranges are derived only from the source lab document itself.</li>
        </ul>
      </GlassCard>
    </div>
  );
};
