import React, { useEffect, useState } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { Button } from '../components/common/Button';
import { conflictService } from '../services/conflictService';
import { patientService } from '../services/patientService';
import type { ConflictRecord, Patient } from '../types';
import { 
  AlertTriangle, 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  User, 
  FileText, 
  FileCheck2, 
  RefreshCw, 
  Info 
} from 'lucide-react';

export const ConflictsPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [conflicts, setConflicts] = useState<ConflictRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'UNRESOLVED' | 'RESOLVED' | 'DISMISSED'>('ALL');

  // Resolution modal state
  const [activeConflict, setActiveConflict] = useState<ConflictRecord | null>(null);
  const [resolutionAction, setResolutionAction] = useState<'RESOLVED' | 'DISMISSED'>('RESOLVED');
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [clinicianName, setClinicianName] = useState<string>('Dr. Sarah Lin, MD');
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Load patients on mount
  useEffect(() => {
    patientService.getPatients()
      .then((data) => {
        setPatients(data);
      })
      .catch((err) => console.error('Failed to load patients:', err));
  }, []);

  // Fetch conflicts whenever selected patient or status changes
  const loadConflicts = async () => {
    setLoading(true);
    try {
      const data = await conflictService.getConflicts(
        selectedPatientId || undefined,
        statusFilter === 'ALL' ? undefined : statusFilter
      );
      setConflicts(data);
    } catch (err) {
      console.error('Failed to load conflicts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConflicts();
  }, [selectedPatientId, statusFilter]);

  const handleOpenResolveModal = (conflict: ConflictRecord) => {
    setActiveConflict(conflict);
    setResolutionNotes('');
    setResolutionAction('RESOLVED');
  };

  const handleSubmitResolution = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeConflict) return;
    setSubmitting(true);
    try {
      await conflictService.resolveConflict(
        activeConflict.id,
        resolutionNotes || 'Clinical discrepancy reviewed and verified against source records.',
        clinicianName,
        resolutionAction
      );
      setActiveConflict(null);
      await loadConflicts();
    } catch (err) {
      console.error('Failed to resolve conflict:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Metrics calculation
  const totalCount = conflicts.length;
  const unresolvedCount = conflicts.filter((c) => c.status === 'UNRESOLVED').length;
  const resolvedCount = conflicts.filter((c) => c.status === 'RESOLVED').length;
  const criticalCount = conflicts.filter((c) => c.severity === 'CRITICAL' || c.severity === 'HIGH').length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-amber-400" />
            Cross-Source Conflict Detection & Reconciliation
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Detects discrepancies between patient-reported inputs and uploaded clinical reports without deciding medical correctness.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={loadConflicts} 
            disabled={loading}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Patient Selector & Filters Bar */}
      <GlassCard className="p-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <label className="text-xs font-semibold text-slate-300 whitespace-nowrap flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-cyan-400" />
              Patient:
            </label>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 max-w-xs w-full"
            >
              <option value="">All Patients</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} ({p.mrn})
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter Tabs */}
          <div className="flex items-center gap-1.5 bg-slate-950/60 p-1 rounded-lg border border-slate-800">
            {(['ALL', 'UNRESOLVED', 'RESOLVED', 'DISMISSED'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  statusFilter === st
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st === 'ALL' ? 'All Records' : st.charAt(0) + st.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>
      </GlassCard>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard className="p-4">
          <span className="text-xs text-slate-400 font-medium">Total Flagged</span>
          <p className="text-2xl font-bold text-white mt-1">{totalCount}</p>
        </GlassCard>
        <GlassCard className="p-4 border-amber-500/20 bg-amber-950/10">
          <span className="text-xs text-amber-400 font-medium">Unresolved Discrepancies</span>
          <p className="text-2xl font-bold text-amber-300 mt-1">{unresolvedCount}</p>
        </GlassCard>
        <GlassCard className="p-4 border-rose-500/20 bg-rose-950/10">
          <span className="text-xs text-rose-400 font-medium">High / Critical Severity</span>
          <p className="text-2xl font-bold text-rose-300 mt-1">{criticalCount}</p>
        </GlassCard>
        <GlassCard className="p-4 border-emerald-500/20 bg-emerald-950/10">
          <span className="text-xs text-emerald-400 font-medium">Resolved by Clinician</span>
          <p className="text-2xl font-bold text-emerald-300 mt-1">{resolvedCount}</p>
        </GlassCard>
      </div>

      {/* Conflict Cards List */}
      <div className="space-y-4">
        {loading ? (
          <GlassCard className="p-8 text-center text-slate-400 text-sm">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyan-400 mb-2" />
            Loading conflict records...
          </GlassCard>
        ) : conflicts.length === 0 ? (
          <GlassCard className="p-8 text-center text-slate-400">
            <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-400/80 mb-2" />
            <p className="text-base font-semibold text-slate-200">No Discrepancies Found</p>
            <p className="text-xs text-slate-400 mt-1">
              No conflicting records match the current filter criteria.
            </p>
          </GlassCard>
        ) : (
          conflicts.map((conflict) => {
            const isResolved = conflict.status === 'RESOLVED';
            const isDismissed = conflict.status === 'DISMISSED';

            const severityColor = 
              conflict.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' :
              conflict.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' :
              conflict.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
              'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';

            return (
              <GlassCard 
                key={conflict.id} 
                className={`p-5 transition-all ${
                  isResolved 
                    ? 'border-emerald-500/20 bg-slate-900/40' 
                    : isDismissed 
                    ? 'border-slate-700/40 bg-slate-900/30' 
                    : 'border-amber-500/30 bg-slate-900/80 shadow-[0_0_15px_rgba(245,158,11,0.05)]'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono font-bold bg-slate-800 text-cyan-300 px-2.5 py-0.5 rounded border border-slate-700">
                      {conflict.category.replace(/_/g, ' ')}
                    </span>
                    <span className={`text-[11px] font-mono px-2 py-0.5 rounded border font-semibold ${severityColor}`}>
                      {conflict.severity} SEVERITY
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      Field: <strong className="text-slate-200">{conflict.field_name}</strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {isResolved ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2.5 py-0.5 rounded-full">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Resolved
                      </span>
                    ) : isDismissed ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 bg-slate-800/60 border border-slate-700 px-2.5 py-0.5 rounded-full">
                        <XCircle className="w-3.5 h-3.5" />
                        Dismissed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-amber-400 bg-amber-950/60 border border-amber-500/40 px-2.5 py-0.5 rounded-full animate-pulse">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Unresolved
                      </span>
                    )}
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs text-slate-300 mt-3 mb-4 leading-relaxed">
                  {conflict.description}
                </p>

                {/* Side-by-Side Comparison Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                  {/* Source A */}
                  <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
                      <span className="font-semibold text-cyan-400 flex items-center gap-1">
                        <FileText className="w-3 h-3" />
                        Source A: {conflict.source_a_type.replace(/_/g, ' ')}
                      </span>
                      {conflict.source_a_page && (
                        <span className="font-mono text-[10px] text-slate-500">Page {conflict.source_a_page}</span>
                      )}
                    </div>
                    {conflict.source_a_document && (
                      <p className="text-[11px] text-slate-400 truncate mb-1">
                        Doc: {conflict.source_a_document}
                      </p>
                    )}
                    <div className="mt-2 bg-slate-900/90 border border-slate-800/80 rounded p-2 text-xs font-mono text-cyan-200">
                      "{conflict.source_a_value}"
                    </div>
                  </div>

                  {/* Source B */}
                  <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3">
                    <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1.5">
                      <span className="font-semibold text-amber-400 flex items-center gap-1">
                        <FileCheck2 className="w-3 h-3" />
                        Source B: {conflict.source_b_type.replace(/_/g, ' ')}
                      </span>
                      {conflict.source_b_page && (
                        <span className="font-mono text-[10px] text-slate-500">Page {conflict.source_b_page}</span>
                      )}
                    </div>
                    {conflict.source_b_document && (
                      <p className="text-[11px] text-slate-400 truncate mb-1">
                        Doc: {conflict.source_b_document}
                      </p>
                    )}
                    <div className="mt-2 bg-slate-900/90 border border-slate-800/80 rounded p-2 text-xs font-mono text-amber-200">
                      "{conflict.source_b_value}"
                    </div>
                  </div>
                </div>

                {/* Resolution Stamp or Action Button */}
                {isResolved || isDismissed ? (
                  <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-slate-400">
                    <div>
                      <span className="text-slate-300 font-medium">Resolution Notes: </span>
                      <span>{conflict.resolution_notes || 'Reviewed and reconciled by clinician.'}</span>
                    </div>
                    <div className="text-[11px] font-mono text-slate-500 whitespace-nowrap">
                      Resolved by {conflict.resolved_by || 'Clinician'} on {conflict.resolved_at ? new Date(conflict.resolved_at).toLocaleDateString() : 'N/A'}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-end gap-3 pt-2">
                    <Button 
                      variant="primary" 
                      size="sm"
                      onClick={() => handleOpenResolveModal(conflict)}
                    >
                      <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
                      Resolve Discrepancy
                    </Button>
                  </div>
                )}
              </GlassCard>
            );
          })
        )}
      </div>

      {/* Resolution Modal */}
      {activeConflict && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <GlassCard className="max-w-lg w-full p-6 space-y-4 border-cyan-500/40 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                Clinician Reconciliation Audit
              </h3>
              <button 
                onClick={() => setActiveConflict(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Recording an immutable reconciliation log for conflict on <strong className="text-cyan-300">{activeConflict.field_name}</strong>.
            </p>

            <form onSubmit={handleSubmitResolution} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Reconciliation Action
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setResolutionAction('RESOLVED')}
                    className={`p-2.5 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                      resolutionAction === 'RESOLVED'
                        ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300'
                        : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    Confirm / Resolve
                  </button>
                  <button
                    type="button"
                    onClick={() => setResolutionAction('DISMISSED')}
                    className={`p-2.5 rounded-lg border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                      resolutionAction === 'DISMISSED'
                        ? 'border-slate-500 bg-slate-800/40 text-slate-200'
                        : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <XCircle className="w-4 h-4 text-slate-400" />
                    Dismiss Discrepancy
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Clinician Reviewer Name
                </label>
                <input
                  type="text"
                  value={clinicianName}
                  onChange={(e) => setClinicianName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Clinical Reconciliation Notes
                </label>
                <textarea
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Enter clinical rationale, confirmed medication dose, or verified allergy status based on authoritative report..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 h-24 resize-none"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <Button 
                  variant="secondary" 
                  type="button" 
                  onClick={() => setActiveConflict(null)}
                  disabled={submitting}
                >
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  type="submit" 
                  disabled={submitting}
                >
                  {submitting ? 'Recording Audit...' : 'Commit Reconciliation'}
                </Button>
              </div>
            </form>
          </GlassCard>
        </div>
      )}

      {/* Non-Diagnostic Disclaimer */}
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-4 text-xs text-slate-300 flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <p>
          <strong className="text-cyan-300">Deterministic Conflict Engine Notice:</strong> MedLens highlights information discrepancies across documents and patient forms. It does not decide medical accuracy, recommend drug discontinuation, or substitute for physician chart review.
        </p>
      </div>
    </div>
  );
};
