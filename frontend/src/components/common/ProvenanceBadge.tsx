import React from 'react';
import type { ProvenanceSource } from '../../types';
import { UserCheck, FileText, Bot, ShieldCheck, AlertCircle, ExternalLink } from 'lucide-react';
import { clsx } from 'clsx';

export type ProvenanceBadgeType = 
  | ProvenanceSource 
  | 'PATIENT_PROVIDED'
  | 'DOCUMENT_EXTRACTED'
  | 'REQUIRES_VERIFICATION'
  | 'Patient Provided'
  | 'Document Extracted'
  | 'AI Generated'
  | 'Human Verified'
  | 'Requires Verification';

interface ProvenanceBadgeProps {
  source: ProvenanceBadgeType;
  documentName?: string | null;
  pageNumber?: number | null;
  confidence?: number | null;
  showDetails?: boolean;
  showConfidence?: boolean;
  requiresVerification?: boolean;
  onSourceClick?: () => void;
  onClick?: () => void;
  className?: string;
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({
  source,
  documentName,
  pageNumber,
  confidence,
  showDetails = false,
  showConfidence = false,
  requiresVerification = false,
  onSourceClick,
  onClick,
  className,
}) => {
  const handleClick = onSourceClick || onClick;
  // Map various casing and sources to the 5 official MedLens badges
  let normalizedKey = String(source).toUpperCase().replace(/\s+/g, '_');

  if (requiresVerification) {
    normalizedKey = 'REQUIRES_VERIFICATION';
  } else if (normalizedKey === 'PATIENT_INPUT') {
    normalizedKey = 'PATIENT_PROVIDED';
  }

  const badgeConfig: Record<string, { label: string; icon: React.ElementType; classes: string }> = {
    PATIENT_PROVIDED: {
      label: 'Patient Provided',
      icon: UserCheck,
      classes: 'bg-indigo-950/80 text-indigo-300 border-indigo-500/40 shadow-[0_0_10px_rgba(99,102,241,0.15)]',
    },
    DOCUMENT_EXTRACTION: {
      label: 'Document Extracted',
      icon: FileText,
      classes: 'bg-cyan-950/80 text-cyan-300 border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.15)]',
    },
    DOCUMENT_EXTRACTED: {
      label: 'Document Extracted',
      icon: FileText,
      classes: 'bg-cyan-950/80 text-cyan-300 border-cyan-500/40 shadow-[0_0_10px_rgba(6,182,212,0.15)]',
    },
    AI_GENERATED: {
      label: 'AI Generated',
      icon: Bot,
      classes: 'bg-purple-950/80 text-purple-300 border-purple-500/40 shadow-[0_0_10px_rgba(168,85,247,0.15)]',
    },
    HUMAN_VERIFIED: {
      label: 'Human Verified',
      icon: ShieldCheck,
      classes: 'bg-emerald-950/80 text-emerald-300 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.15)]',
    },
    REQUIRES_VERIFICATION: {
      label: 'Requires Verification',
      icon: AlertCircle,
      classes: 'bg-amber-950/80 text-amber-300 border-amber-500/40 shadow-[0_0_10px_rgba(245,158,11,0.15)]',
    },
  };

  const config = badgeConfig[normalizedKey] || badgeConfig.DOCUMENT_EXTRACTED;
  const Icon = config.icon;

  const content = (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border tracking-wide transition-all select-none',
        config.classes,
        handleClick && 'hover:scale-[1.03] cursor-pointer hover:border-cyan-400 hover:shadow-lg',
        className
      )}
      onClick={handleClick}
      title={
        documentName
          ? `Source: ${documentName}${pageNumber ? ` (Page ${pageNumber})` : ''}${confidence !== undefined && confidence !== null ? ` | Confidence: ${(confidence * 100).toFixed(0)}%` : ''} — Click to inspect provenance`
          : `Origin: ${config.label} — Click to inspect provenance`
      }
    >
      <Icon className="w-3.5 h-3.5 flex-shrink-0" />
      <span>{config.label}</span>
      {showConfidence && confidence !== undefined && confidence !== null && (
        <span className="font-mono text-[10px] bg-slate-900/60 px-1 rounded text-cyan-300 border border-slate-700/50">
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
      {showDetails && documentName && (
        <span className="text-[10px] opacity-80 border-l border-current/30 pl-1.5 ml-0.5 max-w-[130px] truncate flex items-center gap-1">
          {documentName}{pageNumber ? ` :p.${pageNumber}` : ''}
          {handleClick && <ExternalLink className="w-2.5 h-2.5" />}
        </span>
      )}
    </span>
  );

  return content;
};

