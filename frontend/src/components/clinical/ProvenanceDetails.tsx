import React, { useState } from 'react';
import type { ClinicalProvenanceDetail } from '../../types';
import { 
  X, 
  FileText, 
  Sparkles, 
  ShieldCheck, 
  AlertCircle, 
  ExternalLink, 
  Clock, 
  Quote, 
  Lock,
  CheckCircle2,
  Maximize2
} from 'lucide-react';
import { ProvenanceBadge } from '../common/ProvenanceBadge';
import { documentService } from '../../services/documentService';

interface ProvenanceDetailsProps {
  isOpen: boolean;
  onClose: () => void;
  provenance: ClinicalProvenanceDetail | null;
  onOpenDocument?: (documentId: string, pageNumber?: number) => void;
  onVerify?: (entityType: string, entityId: string, newStatus: string) => Promise<void>;
}

export const ProvenanceDetails: React.FC<ProvenanceDetailsProps> = ({
  isOpen,
  onClose,
  provenance,
  onOpenDocument,
  onVerify,
}) => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [inlinePreview, setInlinePreview] = useState(false);

  if (!isOpen || !provenance) return null;

  const handleVerify = async () => {
    if (!onVerify) return;
    try {
      setIsVerifying(true);
      await onVerify(provenance.entity_type, provenance.entity_id, 'VERIFIED');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleOpenSource = () => {
    if (provenance.document_id && onOpenDocument) {
      onOpenDocument(provenance.document_id, provenance.page_number || 1);
    }
  };

  const confidencePct = provenance.confidence !== null && provenance.confidence !== undefined
    ? Math.round(provenance.confidence * 100)
    : null;

  const isVerified = provenance.verification_status === 'VERIFIED';
  const fileUrl = provenance.document_id ? documentService.getDocumentFileUrl(provenance.document_id) : null;
  const isPdf = provenance.filename?.toLowerCase().endsWith('.pdf');

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div 
        className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Panel Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/90 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                Provenance & Traceability
                {isVerified ? (
                  <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/30 font-normal">
                    <ShieldCheck className="w-3 h-3" /> Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-500/30 font-normal">
                    <AlertCircle className="w-3 h-3" /> Pending Review
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-400">
                Immutable origin record for clinical audit and validation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ProvenanceBadge 
              source={provenance.source_type} 
              requiresVerification={!isVerified && provenance.source_type !== 'PATIENT_INPUT'}
            />
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors ml-1"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-slate-900/60">
          
          {/* Main Item & Value Showcase (Exact format requested) */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-5 shadow-inner">
            <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-1">
              {provenance.entity_type.toUpperCase()} IDENTIFIER
            </div>
            <div className="text-2xl font-bold text-white tracking-tight">
              {provenance.item_name}
            </div>
            <div className="text-lg font-mono text-cyan-400 font-semibold mt-1">
              {provenance.item_value || 'Value recorded'}
            </div>

            {/* Original raw data preservation guarantee */}
            {provenance.raw_value && (
              <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                <span className="text-slate-500 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-slate-400" />
                  Original Extracted Raw Value:
                </span>
                <span className="font-mono text-slate-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  "{provenance.raw_value}"
                </span>
              </div>
            )}
          </div>

          {/* Structured Provenance Fields Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs">
            
            {/* Field: Source */}
            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/50 flex flex-col justify-between">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Source
              </span>
              <div>
                <div className="font-semibold text-slate-200 text-sm truncate" title={provenance.filename || 'Not provided'}>
                  {provenance.filename || 'Document not specified'}
                </div>
                <div className="text-cyan-400 font-mono mt-0.5">
                  {provenance.page_number ? `Page ${provenance.page_number}` : 'Page N/A'}
                </div>
              </div>

              {provenance.document_id && (
                <div className="mt-3 pt-2 border-t border-slate-800 flex items-center gap-2">
                  <button
                    onClick={handleOpenSource}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-medium transition-all"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Open Source Page
                  </button>
                  {fileUrl && (
                    <button
                      onClick={() => setInlinePreview(!inlinePreview)}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium transition-all"
                      title={inlinePreview ? 'Hide preview' : 'Peek document'}
                    >
                      <Maximize2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Field: Method */}
            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/50 flex flex-col justify-between">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Method
              </span>
              <div>
                <div className="font-semibold text-slate-200 text-sm flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-400" />
                  {provenance.method || 'AI extraction'}
                </div>
                <div className="text-slate-400 text-[11px] mt-1">
                  Validated deterministically via Clinical Gate
                </div>
              </div>
              <div className="mt-3 pt-2 border-t border-slate-800 text-[11px] text-slate-500">
                Source Type: <span className="font-mono text-slate-400">{provenance.source_type}</span>
              </div>
            </div>

            {/* Field: Confidence */}
            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/50 flex flex-col justify-between">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Confidence
              </span>
              <div>
                <div className="font-mono font-bold text-2xl text-emerald-400">
                  {confidencePct !== null ? `${confidencePct}%` : 'N/A'}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  {confidencePct !== null && confidencePct >= 90
                    ? 'High Extraction Confidence'
                    : 'Standard Confidence'}
                </div>
              </div>
              {confidencePct !== null && (
                <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div 
                    className="bg-emerald-400 h-full rounded-full transition-all duration-500" 
                    style={{ width: `${confidencePct}%` }}
                  />
                </div>
              )}
            </div>

            {/* Field: Verification */}
            <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/50 flex flex-col justify-between">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                Verification
              </span>
              <div>
                <div className="font-semibold text-sm flex items-center gap-2">
                  {isVerified ? (
                    <span className="text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" /> Verified
                    </span>
                  ) : (
                    <span className="text-amber-400 flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4" /> Pending
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">
                  {isVerified && provenance.verified_by
                    ? `By ${provenance.verified_by}`
                    : 'Requires human clinician confirmation'}
                </div>
              </div>

              {!isVerified && onVerify && (
                <div className="mt-3 pt-2 border-t border-slate-800">
                  <button
                    onClick={handleVerify}
                    disabled={isVerifying}
                    className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    {isVerifying ? 'Signing...' : 'Verify Item Now'}
                  </button>
                </div>
              )}
            </div>

          </div>

          {/* Extraction Timestamp */}
          {provenance.extraction_timestamp && (
            <div className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80 text-xs text-slate-400">
              <Clock className="w-4 h-4 text-cyan-400 flex-shrink-0" />
              <span>Extraction Timestamp:</span>
              <span className="font-mono text-slate-300">
                {new Date(provenance.extraction_timestamp).toUTCString()}
              </span>
            </div>
          )}

          {/* Verbatim Supporting Quoted Snippet */}
          {provenance.source_snippet && (
            <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-4">
              <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-2">
                <Quote className="w-4 h-4" />
                Verbatim Report Excerpt
              </div>
              <blockquote className="font-mono text-xs text-slate-200 bg-slate-950/80 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                "{provenance.source_snippet}"
              </blockquote>
              <div className="text-[11px] text-slate-400 mt-2 flex items-center justify-between">
                <span>Citation: {provenance.filename} (p. {provenance.page_number || 1})</span>
                <span className="text-slate-500 italic">Preserved verbatim from source</span>
              </div>
            </div>
          )}

          {/* Inline Document Peek (if toggled) */}
          {inlinePreview && fileUrl && (
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-2 h-72 overflow-hidden shadow-inner">
              {isPdf ? (
                <iframe
                  src={`${fileUrl}#page=${provenance.page_number || 1}`}
                  title="Source document view"
                  className="w-full h-full rounded-lg border border-slate-800"
                />
              ) : (
                <img
                  src={fileUrl}
                  alt="Source document preview"
                  className="max-h-full max-w-full object-contain mx-auto rounded-lg"
                />
              )}
            </div>
          )}

        </div>

        {/* Panel Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/90 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-cyan-500" />
            <span>MedLens Strict Non-Diagnostic Guardrail: Data is never altered or diagnosed.</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
