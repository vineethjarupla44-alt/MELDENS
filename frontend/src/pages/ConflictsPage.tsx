import React from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export const ConflictsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-amber-400" />
          Cross-Source Conflict Detection & Reconciliation
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Detects potential discrepancies between patient-reported inputs and uploaded clinical reports without deciding medical correctness.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <GlassCard variant="warning">
          <h3 className="text-sm font-semibold text-amber-400 flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4" />
            Deterministic Conflict Engine Rules
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed mb-3">
            The conflict engine compares clinical facts across multiple sources. Discrepancies are flagged for human clinician verification:
          </p>
          <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
            <li>Allergy mismatches (e.g. Patient claims Allergy vs Physician note reports NKDA)</li>
            <li>Medication dose/frequency discrepancies</li>
            <li>Conflicting laboratory values across dates or unit mismatches</li>
            <li>Demographic discrepancies (DOB, names)</li>
          </ul>
        </GlassCard>

        <GlassCard variant="accent">
          <h3 className="text-sm font-semibold text-emerald-400 flex items-center gap-2 mb-2">
            <ShieldCheck className="w-4 h-4" />
            Human Verification Workflow (Phase 3)
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed mb-3">
            In Phase 3, clinicians can review flagged conflicts, view side-by-side excerpts of the original documents, and record an immutable audit stamp.
          </p>
          <span className="text-xs text-emerald-400 font-mono bg-emerald-950/60 border border-emerald-500/30 px-3 py-1 rounded-full">
            Conflict Database Schema Ready
          </span>
        </GlassCard>
      </div>
    </div>
  );
};
