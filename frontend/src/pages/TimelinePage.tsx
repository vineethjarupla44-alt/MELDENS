import React, { useEffect, useState } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { Button } from '../components/common/Button';
import { patientService } from '../services/patientService';
import type { TimelineEvent, Patient } from '../types';
import { 
  Clock, 
  Calendar, 
  FileText, 
  User, 
  Activity, 
  Pill, 
  AlertCircle, 
  FileCheck2,
  ArrowUpDown,
  RefreshCw,
  Info
} from 'lucide-react';

export const TimelinePage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  // Load patients list on mount
  useEffect(() => {
    patientService.getPatients()
      .then((data) => {
        setPatients(data);
        if (data.length > 0) {
          setSelectedPatientId(data[0].id);
        }
      })
      .catch((err) => console.error('Failed to load patients:', err));
  }, []);

  // Fetch timeline for selected patient
  const loadTimeline = async (patientId: string) => {
    if (!patientId) {
      setEvents([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await patientService.getPatientTimeline(patientId);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load timeline events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPatientId) {
      loadTimeline(selectedPatientId);
    }
  }, [selectedPatientId]);

  // Filter and sort events
  const filteredEvents = events
    .filter((ev) => (typeFilter === 'ALL' ? true : ev.event_type.toLowerCase() === typeFilter.toLowerCase()))
    .sort((a, b) => {
      const dateA = new Date(a.event_date).getTime();
      const dateB = new Date(b.event_date).getTime();
      return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });

  // Unique event types for filter
  const eventTypes = ['ALL', ...Array.from(new Set(events.map((e) => e.event_type)))];

  const getEventIcon = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('lab') || t.includes('test')) return Activity;
    if (t.includes('med')) return Pill;
    if (t.includes('allergy') || t.includes('conflict')) return AlertCircle;
    if (t.includes('intake')) return User;
    return FileText;
  };

  const getImportanceBadge = (importance: string) => {
    switch (importance) {
      case 'CRITICAL':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      case 'SIGNIFICANT':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Clock className="h-6 w-6 text-cyan-400" />
            Clinical Longitudinal Timeline
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Chronological aggregation of laboratory panels, medications, diagnoses, and clinician encounters.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={() => selectedPatientId && loadTimeline(selectedPatientId)} 
            disabled={loading || !selectedPatientId}
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Patient Selector and Controls */}
      <GlassCard className="p-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <label className="text-xs font-semibold text-slate-300 whitespace-nowrap flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-cyan-400" />
              Patient:
            </label>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 max-w-sm w-full"
            >
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} ({p.mrn})
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Type Filter */}
            <div className="flex items-center gap-1 bg-slate-950/60 p-1 rounded-lg border border-slate-800">
              {eventTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => setTypeFilter(type)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    typeFilter === type
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {type === 'ALL' ? 'All Types' : type.replace(/_/g, ' ')}
                </button>
              ))}
            </div>

            {/* Sort Toggle */}
            <button
              onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium text-slate-300 hover:text-white"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-cyan-400" />
              <span>{sortOrder === 'desc' ? 'Newest First' : 'Oldest First'}</span>
            </button>
          </div>
        </div>
      </GlassCard>

      {/* Events Count Banner */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <span>
          Showing <strong className="text-cyan-400">{filteredEvents.length}</strong> temporal events for this record
        </span>
        <span className="font-mono text-[11px] text-slate-500">
          Temporal resolution: strictly chronological
        </span>
      </div>

      {/* Timeline Stream */}
      <div className="relative pl-6 sm:pl-8 border-l-2 border-cyan-500/20 space-y-6 ml-2 sm:ml-4">
        {loading ? (
          <GlassCard className="p-8 text-center text-slate-400 text-sm">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyan-400 mb-2" />
            Compiling patient temporal chronicle...
          </GlassCard>
        ) : filteredEvents.length === 0 ? (
          <GlassCard className="p-8 text-center text-slate-400">
            <Calendar className="w-8 h-8 mx-auto text-slate-500 mb-2" />
            <p className="text-base font-semibold text-slate-200">No Timeline Events</p>
            <p className="text-xs text-slate-400 mt-1">
              No historical events recorded matching the selected filter.
            </p>
          </GlassCard>
        ) : (
          filteredEvents.map((event) => {
            const Icon = getEventIcon(event.event_type);
            const importanceStyle = getImportanceBadge(event.importance);
            const formattedDate = new Date(event.event_date).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            });

            return (
              <div key={event.id} className="relative group">
                {/* Visual Timeline Node Dot on the vertical line */}
                <div className="absolute -left-[31px] sm:-left-[39px] top-4 w-4 h-4 rounded-full bg-slate-950 border-2 border-cyan-400 group-hover:scale-125 transition-transform flex items-center justify-center shadow-[0_0_8px_rgba(6,182,212,0.6)]">
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                </div>

                <GlassCard className="p-5 border-slate-800/80 hover:border-cyan-500/40 transition-all bg-slate-900/70">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2.5 border-b border-slate-800/80">
                    <div className="flex items-center gap-2 flex-wrap">
                      <div className="p-1 rounded bg-cyan-950/60 border border-cyan-500/30 text-cyan-400">
                        <Icon className="w-4 h-4" />
                      </div>
                      <h3 className="text-sm font-bold text-white tracking-wide">
                        {event.title}
                      </h3>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${importanceStyle}`}>
                        {event.importance}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-cyan-300 font-mono">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{formattedDate}</span>
                    </div>
                  </div>

                  {event.description && (
                    <p className="text-xs text-slate-300 mt-2.5 leading-relaxed">
                      {event.description}
                    </p>
                  )}

                  {/* Provenance Document Footer */}
                  <div className="mt-3 pt-2.5 border-t border-slate-800/50 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <FileCheck2 className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Source: <strong className="text-slate-200">{event.source_document || 'Clinical Intake'}</strong></span>
                      {event.source_page && (
                        <span className="font-mono text-slate-500">(Page {event.source_page})</span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 font-mono text-[10px] text-slate-500">
                      <span>Type: {event.event_type}</span>
                    </div>
                  </div>
                </GlassCard>
              </div>
            );
          })
        )}
      </div>

      {/* Non-Diagnostic Clinical Notice */}
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/20 p-4 text-xs text-slate-300 flex items-start gap-3">
        <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <p>
          <strong className="text-cyan-300">Longitudinal Timeline Notice:</strong> MedLens organizes historical records chronologically from source documentation dates. It does not predict future disease progression, evaluate treatment efficacy, or provide clinical prognoses.
        </p>
      </div>
    </div>
  );
};
