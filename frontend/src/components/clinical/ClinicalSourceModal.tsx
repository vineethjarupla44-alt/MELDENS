import React from 'react';
import { X, FileText, Quote, ShieldCheck, AlertCircle } from 'lucide-react';
import { documentService } from '../../services/documentService';

import { ProvenanceBadge } from '../common/ProvenanceBadge';
import type { ProvenanceSource } from '../../types';

interface ClinicalSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId?: string | null;
  documentName?: string | null;
  pageNumber?: number | null;
  sourceSnippet?: string | null;
  provenanceSource?: ProvenanceSource | string;
  confidence?: number | null;
  verificationStatus?: string | null;
  testOrEntityName?: string | null;
}

export const ClinicalSourceModal: React.FC<ClinicalSourceModalProps> = ({
  isOpen,
  onClose,
  documentId,
  documentName,
  pageNumber,
  sourceSnippet,
  provenanceSource = 'DOCUMENT_EXTRACTION',
  confidence,
  verificationStatus,
  testOrEntityName,
}) => {
  if (!isOpen) return null;

  const fileUrl = documentId ? documentService.getDocumentFileUrl(documentId) : null;
  const isPdf = documentName?.toLowerCase().endsWith('.pdf');

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl h-[88vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-white">
                  Source Provenance: {testOrEntityName || documentName || 'Document Citation'}
                </h3>
                {verificationStatus === 'VERIFIED' ? (
                  <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-500/30">
                    <ShieldCheck className="w-3 h-3" /> Human Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-500/30">
                    <AlertCircle className="w-3 h-3" /> Requires Verification
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 mt-0.5 flex items-center gap-2">
                <span>Document: <strong className="text-slate-300">{documentName || 'Medical Report'}</strong></span>
                {pageNumber && (
                  <span className="bg-slate-800 px-1.5 py-0.2 rounded font-mono text-cyan-300">
                    Page {pageNumber}
                  </span>
                )}
                {confidence !== undefined && confidence !== null && (
                  <span>Confidence: <strong className="text-white">{(confidence * 100).toFixed(0)}%</strong></span>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <ProvenanceBadge 
              source={provenanceSource as any} 
              documentName={documentName} 
              pageNumber={pageNumber} 
            />
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors ml-2"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Verbatim Supporting Snippet Banner */}
        {sourceSnippet && (
          <div className="px-5 py-3 bg-cyan-950/20 border-b border-cyan-500/20 flex items-start gap-3">
            <Quote className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">
                Verbatim Report Excerpt:
              </span>
              <p className="text-xs text-slate-200 font-mono mt-0.5 bg-slate-950/80 p-2 rounded border border-slate-800/80">
                "{sourceSnippet}"
              </p>
            </div>
          </div>
        )}

        {/* Document Streaming Body */}
        <div className="flex-1 bg-slate-950 p-2 overflow-hidden flex items-center justify-center relative">
          {fileUrl ? (
            isPdf ? (
              <iframe
                src={`${fileUrl}#page=${pageNumber || 1}`}
                title={documentName || 'Document View'}
                className="w-full h-full rounded-xl border border-slate-800 shadow-inner"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center p-4">
                <img
                  src={fileUrl}
                  alt={documentName || 'Document Preview'}
                  className="max-h-full max-w-full object-contain rounded-xl border border-slate-800"
                />
              </div>
            )
          ) : (
            <div className="text-center p-8 text-slate-500">
              <FileText className="w-12 h-12 text-slate-700 mx-auto mb-3" />
              <p className="text-sm font-medium text-slate-400">Direct file stream unavailable for this record</p>
              <p className="text-xs text-slate-600 mt-1 max-w-sm mx-auto">
                Source: {documentName || 'Clinical Record'} {pageNumber ? `(Page ${pageNumber})` : ''}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
