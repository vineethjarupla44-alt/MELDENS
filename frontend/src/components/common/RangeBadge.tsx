import React from 'react';
import type { LabStatus } from '../../types';
import { ArrowDown, ArrowUp, Check, HelpCircle } from 'lucide-react';
import { clsx } from 'clsx';

interface RangeBadgeProps {
  status: LabStatus;
  referenceRangeRaw?: string | null;
  className?: string;
}

export const RangeBadge: React.FC<RangeBadgeProps> = ({
  status,
  referenceRangeRaw,
  className,
}) => {
  const statusConfig = {
    NORMAL: {
      label: 'Normal',
      icon: Check,
      classes: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    },
    LOW: {
      label: 'Low',
      icon: ArrowDown,
      classes: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
    },
    HIGH: {
      label: 'High',
      icon: ArrowUp,
      classes: 'bg-rose-500/10 text-rose-400 border-rose-500/30 font-semibold',
    },
    UNKNOWN: {
      label: 'Unknown Ref',
      icon: HelpCircle,
      classes: 'bg-slate-500/10 text-slate-400 border-slate-700/50',
    },
  };

  const config = statusConfig[status] || statusConfig.UNKNOWN;
  const Icon = config.icon;

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono border',
        config.classes,
        className
      )}
      title={
        referenceRangeRaw
          ? `Report Range: ${referenceRangeRaw}`
          : 'No reference range provided in source document'
      }
    >
      <Icon className="w-3 h-3" />
      <span>{config.label}</span>
    </span>
  );
};
