import React, { useState, useEffect } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { ClinicalSourceModal } from '../components/clinical/ClinicalSourceModal';

import { patientService } from '../services/patientService';
import type { 
  Patient, 
  VerificationQueueItem,
} from '../types';
import { 
  ShieldCheck, 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  Edit3, 
  FileText, 
  ExternalLink, 
  Clock, 
  User, 
  Sparkles, 
  Lock, 
  Quote, 
  Search
} from 'lucide-react';

export const VerificationPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [queueItems, setQueueItems] = useState<VerificationQueueItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterReason, setFilterReason] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Editable values state mapped by item ID
  const [editableValues, setEditableValues] = useState<Record<string, string>>({});
  const [reviewerNotes, setReviewerNotes] = useState<Record<string, string>>({});
  const [processingId, setProcessingId] = useState<string | null>(null);

  // Document Stream Preview Modal state
  const [citationModal, setCitationModal] = useState<{
    isOpen: boolean;
    documentId?: string | null;
    documentName?: string | null;
    pageNumber?: number | null;
    sourceSnippet?: string | null;
    confidence?: number | null;
    testOrEntityName?: string | null;
  }>({ isOpen: false });

  // 1. Fetch Patients
  useEffect(() => {
    async function loadPatients() {
      try {
        const list = await patientService.getPatients();
        setPatients(list);
        const stored = localStorage.getItem('medlens_selected_patient');
        if (stored && list.some(p => p.id === stored)) {
          setSelectedPatientId(stored);
        }
      } catch (err) {
        console.error('Failed to load patients', err);
      }
    }
    loadPatients();
  }, []);

  // 2. Fetch Verification Queue
  const loadQueue = async () => {
    try {
      setLoading(true);
      const items = await patientService.getVerificationQueue(selectedPatientId || undefined);
      setQueueItems(items);
      
      // Initialize editable inputs
      const initialVals: Record<string, string> = {};
      const initialNotes: Record<string, string> = {};
      items.forEach(item => {
        initialVals[item.id] = item.corrected_value || item.editable_value || item.original_value || '';
        initialNotes[item.id] = '';
      });
      setEditableValues(initialVals);
      setReviewerNotes(initialNotes);
    } catch (err) {
      console.error('Failed to load verification queue', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, [selectedPatientId]);

  // Handler: Execute Action (ACCEPT / EDIT / REJECT)
  const handleAction = async (item: VerificationQueueItem, action: 'ACCEPT' | 'EDIT' | 'REJECT') => {
    try {
      setProcessingId(item.id);
      const correctedVal = editableValues[item.id] || item.editable_value;
      const note = reviewerNotes[item.id];

      await patientService.executeVerificationAction({
        entity_type: item.entity_type,
        entity_id: item.id,
        action,
        corrected_value: action === 'EDIT' ? correctedVal : (item.corrected_value || undefined),
        reviewer_name: 'Dr. Sarah Lin, MD',
        reviewer_role: 'Lead Clinician Reviewer',
        notes: note || undefined,
      });

      // Reload queue to reflect updated state
      await loadQueue();
    } catch (err) {
      console.error(`Failed to execute ${action}`, err);
    } finally {
      setProcessingId(null);
    }
  };

  // Filter queue items
  const filteredItems = queueItems.filter(item => {
    // Status filter
    if (filterStatus === 'PENDING' && item.verification_status !== 'UNVERIFIED') return false;
    if (filterStatus === 'VERIFIED' && item.verification_status !== 'VERIFIED') return false;
    if (filterStatus === 'REJECTED' && item.verification_status !== 'REJECTED') return false;

    // Reason filter
    if (filterReason === 'LOW_CONFIDENCE' && !item.reasons.some(r => r.includes('Low Confidence'))) return false;
    if (filterReason === 'AMBIGUITY' && !item.reasons.some(r => r.includes('Ambiguity') || r.includes('Range'))) return false;
    if (filterReason === 'CONFLICT' && !item.reasons.some(r => r.includes('Conflict'))) return false;

    // Search query
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchName = item.item_name.toLowerCase().includes(q);
      const matchDoc = item.source_document?.toLowerCase().includes(q);
      const matchVal = item.extracted_value.toLowerCase().includes(q);
      if (!matchName && !matchDoc && !matchVal) return false;
    }

    return true;
  });

  // Metrics
  const totalItems = queueItems.length;
  const pendingItems = queueItems.filter(i => i.verification_status === 'UNVERIFIED').length;
  const lowConfItems = queueItems.filter(i => i.reasons.some(r => r.includes('Low Confidence'))).length;
  const conflictItems = queueItems.filter(i => i.reasons.some(r => r.includes('Conflict'))).length;
  const verifiedItems = queueItems.filter(i => i.verification_status === 'VERIFIED').length;

  return (
    <div className="space-y-6 pb-20">
      
      {/* Header & Metrics */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Human Verification Queue
                <span className="rounded-full bg-amber-950 px-2.5 py-0.5 text-[11px] font-mono font-medium text-amber-300 border border-amber-500/30">
                  Clinician Oversight Active
                </span>
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Review, accept, edit, or reject clinical extractions. Original AI ground truth is never deleted.
              </p>
            </div>
          </div>
        </div>

        {/* Patient Switcher */}
        <div className="flex items-center gap-3 bg-slate-900/80 p-2 rounded-xl border border-slate-800">
          <User className="w-4 h-4 text-cyan-400 ml-1" />
          <span className="text-xs text-slate-400 font-medium">Patient:</span>
          <select
            value={selectedPatientId}
            onChange={(e) => {
              setSelectedPatientId(e.target.value);
              if (e.target.value) localStorage.setItem('medlens_selected_patient', e.target.value);
            }}
            className="bg-slate-950 text-white text-xs rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Ingested Patients</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.last_name}, {p.first_name} {p.mrn ? `(${p.mrn})` : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Metrics Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] uppercase font-semibold text-slate-500 tracking-wider block">Total Items</span>
          <span className="text-2xl font-mono font-bold text-white mt-0.5 block">{totalItems}</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-amber-500/20">
          <span className="text-[10px] uppercase font-semibold text-amber-400 tracking-wider block flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> Pending Review
          </span>
          <span className="text-2xl font-mono font-bold text-amber-400 mt-0.5 block">{pendingItems}</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-sky-500/20">
          <span className="text-[10px] uppercase font-semibold text-sky-400 tracking-wider block flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> Low Confidence
          </span>
          <span className="text-2xl font-mono font-bold text-sky-400 mt-0.5 block">{lowConfItems}</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-rose-500/20">
          <span className="text-[10px] uppercase font-semibold text-rose-400 tracking-wider block flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> Cross-Doc Conflicts
          </span>
          <span className="text-2xl font-mono font-bold text-rose-400 mt-0.5 block">{conflictItems}</span>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-emerald-500/20">
          <span className="text-[10px] uppercase font-semibold text-emerald-400 tracking-wider block flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Verified
          </span>
          <span className="text-2xl font-mono font-bold text-emerald-400 mt-0.5 block">{verifiedItems}</span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <GlassCard className="p-3.5 flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Filter Buttons */}
        <div className="flex flex-wrap items-center gap-2 text-xs w-full md:w-auto">
          <span className="text-slate-500 font-medium text-[11px] uppercase mr-1">Filter Reason:</span>
          {[
            { id: 'ALL', label: 'All' },
            { id: 'LOW_CONFIDENCE', label: 'Low Confidence' },
            { id: 'AMBIGUITY', label: 'Ambiguity / Range' },
            { id: 'CONFLICT', label: 'Conflicts' },
          ].map(btn => (
            <button
              key={btn.id}
              onClick={() => setFilterReason(btn.id)}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                filterReason === btn.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {btn.label}
            </button>
          ))}

          <span className="text-slate-600 mx-1">|</span>
          <span className="text-slate-500 font-medium text-[11px] uppercase mr-1">Status:</span>
          {[
            { id: 'ALL', label: 'All' },
            { id: 'PENDING', label: 'Pending Only' },
            { id: 'VERIFIED', label: 'Verified' },
          ].map(btn => (
            <button
              key={btn.id}
              onClick={() => setFilterStatus(btn.id)}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all ${
                filterStatus === btn.id
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search test, med, doc..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 text-white text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-700 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </GlassCard>

      {/* Queue Items List */}
      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[300px] gap-3">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-slate-400">Loading verification queue...</span>
        </div>
      ) : filteredItems.length === 0 ? (
        <GlassCard className="p-8 text-center text-slate-400">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-white">Verification Queue is Empty</h3>
          <p className="text-xs text-slate-500 mt-1">
            No clinical items currently match your filter criteria. All pending items have been resolved.
          </p>
        </GlassCard>
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item) => {
            const isVerified = item.verification_status === 'VERIFIED';
            const isRejected = item.verification_status === 'REJECTED';
            const isPending = item.verification_status === 'UNVERIFIED';
            const confidencePct = item.confidence !== null && item.confidence !== undefined
              ? Math.round(item.confidence * 100)
              : null;

            return (
              <GlassCard 
                key={item.id} 
                className={`p-5 transition-all ${
                  isPending 
                    ? 'border-amber-500/30 bg-slate-900/90' 
                    : isVerified 
                    ? 'border-emerald-500/20 bg-slate-900/50' 
                    : 'border-rose-500/20 bg-slate-900/40 opacity-80'
                }`}
              >
                {/* Item Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                      {item.entity_type}
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-white tracking-tight">
                        {item.item_name}
                      </h3>
                      <span className="text-xs text-slate-400">
                        Patient: <strong className="text-slate-300">{item.patient_name}</strong>
                      </span>
                    </div>
                  </div>

                  {/* Reasons Badges */}
                  <div className="flex flex-wrap items-center gap-1.5">
                    {item.reasons.map((r, idx) => (
                      <span 
                        key={idx}
                        className={`text-[10px] px-2 py-0.5 rounded-full font-medium border ${
                          r.includes('Conflict') 
                            ? 'bg-rose-950 text-rose-300 border-rose-500/40' 
                            : r.includes('Low') 
                            ? 'bg-sky-950 text-sky-300 border-sky-500/40' 
                            : 'bg-amber-950 text-amber-300 border-amber-500/40'
                        }`}
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                </div>

                {/* DUAL COMPARISON GRID: AI Extracted vs Human Verified */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
                  
                  {/* LEFT: AI Extracted Column */}
                  <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/10 p-4 flex flex-col justify-between">
                    <div>
                      {/* Badge: AI Extracted */}
                      <div className="flex items-center justify-between mb-2">
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-950 text-cyan-300 border border-cyan-500/40 shadow-sm">
                          <Sparkles className="w-3.5 h-3.5" />
                          AI Extracted
                        </span>

                        {confidencePct !== null && (
                          <span className="text-xs font-mono text-cyan-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                            Confidence: {confidencePct}%
                          </span>
                        )}
                      </div>

                      {/* Original AI Value (Read-Only & Immutable) */}
                      <div className="mt-2">
                        <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                          Extracted Value:
                        </span>
                        <div className="text-lg font-mono font-bold text-white mt-0.5">
                          {item.extracted_value}
                        </div>
                      </div>

                      {/* Preserved Raw Value Indicator */}
                      {item.original_value && (
                        <div className="mt-2 flex items-center gap-1.5 text-xs text-slate-400 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
                          <Lock className="w-3 h-3 text-cyan-400 flex-shrink-0" />
                          <span>Original raw text:</span>
                          <span className="font-mono text-slate-200">"{item.original_value}"</span>
                        </div>
                      )}

                      {/* Verbatim Source Snippet */}
                      {item.source_snippet && (
                        <div className="mt-2 text-xs text-slate-400 bg-slate-950/40 p-2 rounded border border-slate-800/80 flex items-start gap-1.5">
                          <Quote className="w-3 h-3 text-cyan-400 flex-shrink-0 mt-0.5" />
                          <p className="font-mono text-[11px] text-slate-300 truncate">
                            "{item.source_snippet}"
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Source Citation & Preview Action */}
                    <div className="mt-3 pt-2 border-t border-cyan-500/20 flex items-center justify-between text-xs">
                      <div className="truncate max-w-[240px] text-slate-400" title={item.source_document || 'Source'}>
                        <FileText className="w-3.5 h-3.5 inline mr-1 text-cyan-400" />
                        <span>{item.source_document || 'Report'} {item.page_number ? `(p.${item.page_number})` : ''}</span>
                      </div>

                      {item.document_id && (
                        <button
                          onClick={() => setCitationModal({
                            isOpen: true,
                            documentId: item.document_id,
                            documentName: item.source_document,
                            pageNumber: item.page_number,
                            sourceSnippet: item.source_snippet,
                            confidence: item.confidence,
                            testOrEntityName: item.item_name,
                          })}
                          className="inline-flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300 font-medium underline-offset-2 hover:underline"
                        >
                          <ExternalLink className="w-3 h-3" />
                          Preview Document
                        </button>
                      )}
                    </div>
                  </div>

                  {/* RIGHT: Human Verified Column */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 flex flex-col justify-between">
                    <div>
                      {/* Badge: Human Verified / Status */}
                      <div className="flex items-center justify-between mb-2">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                          isVerified 
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40 shadow-sm'
                            : isRejected 
                            ? 'bg-rose-950 text-rose-300 border-rose-500/40'
                            : 'bg-amber-950 text-amber-300 border-amber-500/40'
                        }`}>
                          <ShieldCheck className="w-3.5 h-3.5" />
                          {isVerified ? 'Human Verified' : isRejected ? 'Rejected by Clinician' : 'Pending Verification'}
                        </span>

                        {isVerified && item.verified_by && (
                          <span className="text-[11px] text-slate-400">
                            By {item.verified_by}
                          </span>
                        )}
                      </div>

                      {/* Display Human Corrected Value if already saved */}
                      {item.corrected_value && (
                        <div className="mb-3 p-2 rounded-lg bg-emerald-950/30 border border-emerald-500/30">
                          <span className="text-[10px] uppercase font-semibold text-emerald-400 block">
                            Human Corrected Value:
                          </span>
                          <span className="text-base font-mono font-bold text-emerald-300">
                            {item.corrected_value}
                          </span>
                        </div>
                      )}

                      {/* Editable Value Input Field */}
                      <div className="space-y-2">
                        <label className="text-[11px] text-slate-300 font-semibold flex items-center gap-1.5">
                          <Edit3 className="w-3.5 h-3.5 text-cyan-400" />
                          Editable Clinical Value:
                        </label>
                        <input
                          type="text"
                          value={editableValues[item.id] !== undefined ? editableValues[item.id] : item.editable_value}
                          onChange={(e) => setEditableValues({ ...editableValues, [item.id]: e.target.value })}
                          placeholder="Enter verified or corrected value..."
                          className="w-full bg-slate-900 text-white font-mono text-xs px-3 py-2 rounded-lg border border-slate-700 focus:outline-none focus:border-cyan-500"
                        />

                        {/* Optional Clinician Note Field */}
                        <input
                          type="text"
                          value={reviewerNotes[item.id] || ''}
                          onChange={(e) => setReviewerNotes({ ...reviewerNotes, [item.id]: e.target.value })}
                          placeholder="Optional audit rationale (e.g., corrected from report table line 3)..."
                          className="w-full bg-slate-900/60 text-slate-300 text-xs px-3 py-1.5 rounded-lg border border-slate-800 focus:outline-none focus:border-slate-600"
                        />
                      </div>
                    </div>

                    {/* Verifier Signing Info */}
                    {isVerified && item.verified_at && (
                      <div className="mt-3 pt-2 border-t border-slate-800 flex items-center gap-1 text-[11px] text-slate-500">
                        <Clock className="w-3 h-3 text-emerald-500" />
                        <span>Signed at: {new Date(item.verified_at).toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                </div>

                {/* ACTION BAR: ACCEPT, EDIT, REJECT */}
                <div className="border-t border-slate-800 pt-3 flex flex-wrap items-center justify-between gap-3">
                  <div className="text-xs text-slate-500 flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5 text-cyan-500" />
                    <span>Never overwrites original extraction. All edits generate immutable audit entries.</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* REJECT Button */}
                    <button
                      onClick={() => handleAction(item, 'REJECT')}
                      disabled={processingId === item.id || isRejected}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900 text-rose-300 border border-rose-500/40 text-xs font-semibold transition-all disabled:opacity-50"
                      title="Reject this extraction as inaccurate"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      Reject
                    </button>

                    {/* EDIT & SAVE Button */}
                    <button
                      onClick={() => handleAction(item, 'EDIT')}
                      disabled={processingId === item.id}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                      title="Save edited value alongside original AI extraction"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      Save & Verify
                    </button>

                    {/* ACCEPT Button */}
                    <button
                      onClick={() => handleAction(item, 'ACCEPT')}
                      disabled={processingId === item.id || isVerified}
                      className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                      title="Confirm AI extracted value as accurate without edits"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Accept As Valid
                    </button>
                  </div>
                </div>

              </GlassCard>
            );
          })}
        </div>
      )}

      {/* Document Stream Citation Preview Modal */}
      <ClinicalSourceModal
        isOpen={citationModal.isOpen}
        onClose={() => setCitationModal({ ...citationModal, isOpen: false })}
        documentId={citationModal.documentId}
        documentName={citationModal.documentName}
        pageNumber={citationModal.pageNumber}
        sourceSnippet={citationModal.sourceSnippet}
        confidence={citationModal.confidence}
        testOrEntityName={citationModal.testOrEntityName}
      />

    </div>
  );
};
