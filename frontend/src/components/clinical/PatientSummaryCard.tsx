import React, { useState, useEffect } from 'react';
import { GlassCard } from '../common/GlassCard';
import { Button } from '../common/Button';
import { patientService } from '../../services/patientService';
import type { ClinicalSummary } from '../../types';
import {
  Sparkles,
  RefreshCw,
  Info,
  CheckCircle2,
  AlertTriangle,
  FlaskConical,
  Clock,
  Layers,
  ChevronDown,
  ChevronUp,
  FileText,
  AlertCircle,
  User,
  ShieldCheck,
  HelpCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface PatientSummaryCardProps {
  patientId: string;
  patientName?: string;
  onOpenSourceDocument?: (documentId: string) => void;
}

export const PatientSummaryCard: React.FC<PatientSummaryCardProps> = ({
  patientId,
  patientName,
  onOpenSourceDocument,
}) => {
  const [summary, setSummary] = useState<ClinicalSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [regenerating, setRegenerating] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [showProvenance, setShowProvenance] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async (force: boolean = false) => {
    try {
      if (force) {
        setRegenerating(true);
      } else {
        setLoading(true);
      }
      setError(null);

      let data: ClinicalSummary | null = null;
      if (force) {
        data = await patientService.generatePatientSummary(patientId, true);
      } else {
        data = await patientService.getPatientSummary(patientId);
        if (!data) {
          // Generate on first view if none exists
          data = await patientService.generatePatientSummary(patientId, false);
        }
      }
      setSummary(data);
    } catch (err: any) {
      console.error('Failed to load patient clinical summary:', err);
      setError('Unable to synthesize clinical summary. Please check backend connection.');
    } finally {
      setLoading(false);
      setRegenerating(false);
    }
  };

  useEffect(() => {
    if (patientId) {
      fetchSummary(false);
    }
  }, [patientId]);

  if (loading) {
    return (
      <GlassCard className="p-6 border-cyan-500/20 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-cyan-950/20">
        <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
          <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          <div>
            <h3 className="text-sm font-semibold text-white">Synthesizing Clinical Intelligence Summary</h3>
            <p className="text-xs text-slate-400 mt-1">
              Evaluating validated structured records across documents, laboratory results, and medications...
            </p>
          </div>
        </div>
      </GlassCard>
    );
  }

  if (error || !summary) {
    return (
      <GlassCard className="p-6 border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-slate-300">
            <AlertCircle className="w-5 h-5 text-amber-400" />
            <span className="text-sm">{error || 'No summary currently available for this patient.'}</span>
          </div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchSummary(true)}
            disabled={regenerating}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
            <span>Generate Summary</span>
          </Button>
        </div>
      </GlassCard>
    );
  }

  const sections = summary.sections;
  const prov = summary.structured_provenance_sources;

  const sectionTabs = [
    { id: 'overview', label: '1. Record Overview', icon: User },
    { id: 'recent', label: '2. Recently Documented', icon: Clock },
    { id: 'labs', label: '3. Laboratory Values', icon: FlaskConical },
    { id: 'history', label: '4. Historical Changes', icon: Layers },
    { id: 'conflicts', label: '5. Potential Conflicts', icon: AlertTriangle },
    { id: 'missing', label: '6. Missing Information', icon: HelpCircle },
    { id: 'verification', label: '7. Verification Required', icon: ShieldCheck },
  ];

  return (
    <div className="space-y-4">
      {/* Main Glass Card */}
      <GlassCard className="p-6 border-cyan-500/25 bg-gradient-to-br from-slate-900/95 via-slate-900/80 to-cyan-950/25 shadow-xl shadow-cyan-950/20">
        
        {/* Top Header: Badge, Model Version, Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-teal-400 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Sparkles className="w-5 h-5 text-slate-950" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-tight">
                  {patientName ? `${patientName} — AI Clinical Summary` : 'MedLens AI Clinical Summary'}
                </h2>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  <Sparkles className="w-3 h-3 text-cyan-400" />
                  AI-Generated
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Generated from validated database records · Model: <code className="text-cyan-300">{summary.model_version}</code> · {new Date(summary.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={() => setShowProvenance(!showProvenance)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showProvenance
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-800/80 text-slate-400 hover:text-white border border-slate-700'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Provenance ({prov ? (prov.document_ids.length + prov.lab_ids.length + prov.medication_ids.length) : 0} Records)</span>
              {showProvenance ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            <Button
              variant="secondary"
              size="sm"
              onClick={() => fetchSummary(true)}
              disabled={regenerating}
              className="flex items-center gap-1.5 text-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin text-cyan-400' : ''}`} />
              <span>{regenerating ? 'Updating...' : 'Regenerate'}</span>
            </Button>
          </div>
        </div>

        {/* Mandatory Safety Disclaimer Banner */}
        <div className="mt-4 p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/30 text-amber-200 text-xs flex items-start gap-3 shadow-inner">
          <Info className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold text-amber-300 uppercase text-[10px] tracking-wider block">
              Mandatory Clinical Disclaimer
            </span>
            <p className="leading-relaxed">
              {summary.disclaimer}
            </p>
          </div>
        </div>

        {/* Executive Overview Narrative */}
        <div className="mt-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/70 text-slate-200 text-sm leading-relaxed">
          <p className="font-medium text-slate-100">
            {summary.summary_text}
          </p>

          {/* Key Findings Bullet Tags */}
          {summary.key_findings && summary.key_findings.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-800/60 flex flex-wrap gap-2">
              {summary.key_findings.map((finding, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs bg-slate-900 border border-slate-700/80 text-slate-300"
                >
                  <CheckCircle2 className="w-3 h-3 text-cyan-400 flex-shrink-0" />
                  <span>{finding}</span>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 7 Structured Sections Navigation Tabs */}
        {sections && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-slate-800/80 scrollbar-thin">
              {sectionTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                      isActive
                        ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-950'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Active Section Card Content */}
            <div className="rounded-xl p-5 bg-slate-950/40 border border-slate-800/80">
              {activeTab === 'overview' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                    <User className="w-4 h-4" />
                    <span>Section 1: Record Overview</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {sections.record_overview}
                  </p>
                </div>
              )}

              {activeTab === 'recent' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                    <Clock className="w-4 h-4" />
                    <span>Section 2: Recently Documented Information</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {sections.recently_documented}
                  </p>
                </div>
              )}

              {activeTab === 'labs' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                      <FlaskConical className="w-4 h-4" />
                      <span>Section 3: Laboratory Values & Source-Report Status</span>
                    </div>
                    <span className="text-[11px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      Report-Derived Status Only
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {sections.laboratory_values}
                  </p>
                  <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-center gap-2">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    <span>
                      Tests marked without ranges state <strong className="text-slate-300">Reference range not provided</strong>. MedLens never fabricates outside standards.
                    </span>
                  </div>
                </div>
              )}

              {activeTab === 'history' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                    <Layers className="w-4 h-4" />
                    <span>Section 4: Historical Changes</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {sections.historical_changes}
                  </p>
                </div>
              )}

              {activeTab === 'conflicts' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-amber-400 text-xs font-semibold uppercase tracking-wider">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Section 5: Potential Conflicts & Cross-Record Discrepancies</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {sections.potential_conflicts}
                  </p>
                  <div className="pt-1">
                    <Link
                      to="/conflicts"
                      className="inline-flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 font-medium"
                    >
                      <span>Open Conflict Resolution Center</span>
                      <span>→</span>
                    </Link>
                  </div>
                </div>
              )}

              {activeTab === 'missing' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    <HelpCircle className="w-4 h-4 text-cyan-400" />
                    <span>Section 6: Missing Information & Documentation Gaps</span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {sections.missing_information}
                  </p>
                </div>
              )}

              {activeTab === 'verification' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                      <ShieldCheck className="w-4 h-4" />
                      <span>Section 7: Verification-Required Information</span>
                    </div>
                    <Link
                      to="/verification"
                      className="text-xs text-cyan-400 hover:text-cyan-300 font-medium"
                    >
                      View Verification Queue →
                    </Link>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {sections.verification_required}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Structured Provenance Record Drawer */}
        {showProvenance && prov && (
          <div className="mt-6 pt-5 border-t border-slate-800/80 space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Summary Provenance Sources (Entity Grounding)
                </h3>
              </div>
              <span className="text-[11px] text-slate-400">
                100% Grounded on Internal Database Records
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Documents</span>
                <span className="text-base font-bold text-white">{prov.document_ids.length}</span>
                <span className="text-[10px] text-cyan-400 block mt-0.5">Indexed PDFs</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Lab Tests</span>
                <span className="text-base font-bold text-white">{prov.lab_ids.length}</span>
                <span className="text-[10px] text-emerald-400 block mt-0.5">Evaluated</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Medications</span>
                <span className="text-base font-bold text-white">{prov.medication_ids.length}</span>
                <span className="text-[10px] text-purple-400 block mt-0.5">Reconciled</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Conditions</span>
                <span className="text-base font-bold text-white">{prov.condition_ids.length}</span>
                <span className="text-[10px] text-blue-400 block mt-0.5">Active</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Allergies</span>
                <span className="text-base font-bold text-white">{prov.allergy_ids.length}</span>
                <span className="text-[10px] text-amber-400 block mt-0.5">Documented</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Conflicts</span>
                <span className="text-base font-bold text-white">{prov.conflict_ids.length}</span>
                <span className="text-[10px] text-rose-400 block mt-0.5">Flagged</span>
              </div>
            </div>

            {/* Document citations list */}
            {prov.document_ids.length > 0 && onOpenSourceDocument && (
              <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-400 font-medium">Source Documents:</span>
                {prov.document_ids.slice(0, 5).map((docId, idx) => (
                  <button
                    key={docId}
                    onClick={() => onOpenSourceDocument(docId)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-xs text-cyan-300 hover:border-cyan-500 transition-colors"
                  >
                    <FileText className="w-3 h-3 text-cyan-400" />
                    <span>Document #{idx + 1}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

      </GlassCard>
    </div>
  );
};
