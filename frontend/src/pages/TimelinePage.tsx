import React from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { Clock, Calendar } from 'lucide-react';

export const TimelinePage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Clock className="h-6 w-6 text-cyan-400" />
          Clinical Event Timeline
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Chronological progression of laboratory tests, medication changes, and clinical encounters across documents.
        </p>
      </div>

      <GlassCard className="p-8">
        <div className="flex items-center gap-3 text-cyan-400 mb-4">
          <Calendar className="w-5 h-5" />
          <h3 className="text-base font-semibold">Chronological Event Aggregation (Phase 4)</h3>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed max-w-xl mb-4">
          Timeline records weave together dates extracted from disparate laboratory panels, physician consultations, and patient history cards into an interactive longitudinal health story.
        </p>
        <span className="text-xs text-cyan-400 font-mono bg-cyan-950/60 border border-cyan-500/30 px-3 py-1 rounded-full">
          Temporal Model Structure Ready
        </span>
      </GlassCard>
    </div>
  );
};
