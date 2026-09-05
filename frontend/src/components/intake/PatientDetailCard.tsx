import React, { useState } from 'react';
import { GlassCard } from '../common/GlassCard';
import { Button } from '../common/Button';
import { ProvenanceBadge } from '../common/ProvenanceBadge';
import { 
  User, 
  HeartPulse, 
  Pill, 
  AlertCircle, 
  Edit3, 
  History
} from 'lucide-react';
import type { 
  PatientDetailResponse, 
  AuditLog, 
  Medication, 
  Allergy, 
  Condition 
} from '../../types';

interface PatientDetailCardProps {
  patient: PatientDetailResponse;
  auditLogs: AuditLog[];
  onEdit: () => void;
}

export const PatientDetailCard: React.FC<PatientDetailCardProps> = ({
  patient,
  auditLogs,
  onEdit,
}) => {
  const [showAudit, setShowAudit] = useState(false);

  // Calculate age from DOB (safe from timezone offset)
  let age: number | null = null;
  let formattedDOB = patient.date_of_birth || 'N/A';
  if (patient.date_of_birth) {
    const parts = patient.date_of_birth.trim().split(/[-/]/);
    if (parts.length === 3) {
      let y = 0, m = 0, d = 0;
      if (parts[0].length === 4) {
        [y, m, d] = parts.map(Number);
        formattedDOB = `${String(d).padStart(2, '0')}-${String(m).padStart(2, '0')}-${y}`;
      } else {
        [d, m, y] = parts.map(Number);
        formattedDOB = `${String(d).padStart(2, '0')}-${String(m).padStart(2, '0')}-${y}`;
      }
      const birth = new Date(y, m - 1, d);
      const now = new Date();
      age = now.getFullYear() - birth.getFullYear();
      const monthDiff = now.getMonth() - birth.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && now.getDate() < birth.getDate())) {
        age--;
      }
    }
  }

  return (
    <div className="space-y-6">
      {/* Patient Header Card */}
      <GlassCard variant="glow" className="relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-950/50 flex-shrink-0">
              <User className="w-7 h-7" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h2 className="text-2xl font-extrabold text-white tracking-tight">
                  {patient.first_name} {patient.last_name}
                </h2>
                <span className="text-xs font-mono bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 px-2 py-0.5 rounded">
                  MRN: {patient.mrn || 'N/A'}
                </span>
                <ProvenanceBadge source="PATIENT_INPUT" />
              </div>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                <span>{patient.gender}</span>
                <span>•</span>
                <span>DOB: {formattedDOB} {age !== null ? `(${age} yrs)` : ''}</span>
                {patient.blood_type && (
                  <>
                    <span>•</span>
                    <span className="font-mono text-cyan-400">Blood Type: {patient.blood_type}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 self-stretch sm:self-auto justify-end">
            <Button variant="secondary" size="sm" onClick={() => setShowAudit(!showAudit)}>
              <History className="w-4 h-4 mr-1.5" />
              {showAudit ? 'Hide Audit Trail' : `Audit History (${auditLogs.length})`}
            </Button>
            <Button variant="primary" size="sm" onClick={onEdit}>
              <Edit3 className="w-4 h-4 mr-1.5" />
              Edit Record
            </Button>
          </div>
        </div>

        {/* Symptoms Banner */}
        {patient.profile?.symptoms && (
          <div className="mt-4 pt-4 border-t border-slate-800/80">
            <div className="flex items-start gap-2 bg-amber-950/20 border border-amber-500/20 p-3 rounded-lg text-amber-200">
              <HeartPulse className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-xs font-bold text-amber-400 uppercase tracking-wide block mb-0.5">
                  Present Symptoms & Chief Complaints (Patient-Reported)
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {patient.profile.symptoms}
                </p>
              </div>
            </div>
          </div>
        )}
      </GlassCard>

      {/* Audit History Drawer / Section */}
      {showAudit && (
        <GlassCard variant="default" className="border-indigo-500/30 bg-slate-950/80 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
              <History className="w-4 h-4" />
              <h3>Immutable Audit Log History</h3>
            </div>
            <span className="text-[11px] text-slate-500 font-mono">Preserved for Compliance</span>
          </div>

          {auditLogs.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No audit logs recorded.</p>
          ) : (
            <div className="space-y-2">
              {auditLogs.map((log) => (
                <div key={log.id} className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-cyan-400 font-mono">
                      Action: {log.action} • {log.actor_name}
                    </span>
                    <span className="text-slate-400 font-mono">
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                  </div>
                  {log.change_reason && (
                    <p className="text-slate-300 italic">{log.change_reason}</p>
                  )}
                  {log.new_state && (
                    <details className="mt-1">
                      <summary className="text-[10px] text-slate-400 cursor-pointer hover:text-slate-200">
                        View Logged State Snapshot
                      </summary>
                      <pre className="mt-1 p-2 bg-slate-950 rounded text-[10px] text-cyan-300 font-mono overflow-x-auto">
                        {(() => {
                          try {
                            return JSON.stringify(JSON.parse(log.new_state), null, 2);
                          } catch {
                            return log.new_state;
                          }
                        })()}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      )}

      {/* Clinical Facts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Medications Card */}
        <GlassCard className="space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center gap-2 text-purple-400 font-semibold text-sm">
              <Pill className="w-4 h-4" />
              <h3>Current Medications</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {patient.medications?.length || 0}
            </span>
          </div>

          {(!patient.medications || patient.medications.length === 0) ? (
            <p className="text-xs text-slate-500 italic">No medications recorded.</p>
          ) : (
            <div className="space-y-2">
              {patient.medications.map((med: Medication) => (
                <div key={med.id} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{med.medication_name}</span>
                    <ProvenanceBadge source={med.provenance_source} />
                  </div>
                  <div className="text-[11px] text-slate-400">
                    <span>{med.dosage || 'Dose not specified'}</span> • <span>{med.frequency || 'Frequency not specified'}</span>
                  </div>
                  {med.route && (
                    <span className="inline-block text-[10px] text-slate-500 font-mono">
                      Route: {med.route}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Allergies Card */}
        <GlassCard className="space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
              <AlertCircle className="w-4 h-4" />
              <h3>Known Allergies</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {patient.allergies?.length || 0}
            </span>
          </div>

          {(!patient.allergies || patient.allergies.length === 0) ? (
            <p className="text-xs text-slate-500 italic">No allergies recorded.</p>
          ) : (
            <div className="space-y-2">
              {patient.allergies.map((al: Allergy) => (
                <div key={al.id} className="p-2.5 rounded-lg bg-rose-950/10 border border-rose-500/20 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-rose-300">{al.allergen}</span>
                    <ProvenanceBadge source={al.provenance_source} />
                  </div>
                  <div className="text-[11px] text-slate-300">
                    Reaction: {al.reaction || 'Unspecified'}
                  </div>
                  {al.severity && (
                    <span className="inline-block text-[10px] font-mono text-rose-400 uppercase">
                      Severity: {al.severity}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Conditions Card */}
        <GlassCard className="space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
              <HeartPulse className="w-4 h-4" />
              <h3>Medical Conditions</h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {patient.conditions?.length || 0}
            </span>
          </div>

          {(!patient.conditions || patient.conditions.length === 0) ? (
            <p className="text-xs text-slate-500 italic">No conditions recorded.</p>
          ) : (
            <div className="space-y-2">
              {patient.conditions.map((cond: Condition) => (
                <div key={cond.id} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{cond.condition_name}</span>
                    <ProvenanceBadge source={cond.provenance_source} />
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-slate-400">
                    {cond.onset_date && <span>Onset: {cond.onset_date}</span>}
                    <span className="font-mono text-cyan-400/80">{cond.clinical_status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>

      {/* Additional Notes & Emergency Contacts Footer */}
      {(patient.profile?.baseline_notes || patient.profile?.emergency_contact_name) && (
        <GlassCard className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Additional Patient-Reported Notes & Contact
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-400 pt-1">
            {patient.profile.emergency_contact_name && (
              <div>
                <span className="text-slate-500 block">Emergency Contact:</span>
                <span className="text-slate-200 font-medium">
                  {patient.profile.emergency_contact_name} ({patient.profile.emergency_contact_phone || 'No phone provided'})
                </span>
              </div>
            )}
            {patient.profile.baseline_notes && (
              <div>
                <span className="text-slate-500 block">Notes / History:</span>
                <span className="text-slate-200">{patient.profile.baseline_notes}</span>
              </div>
            )}
          </div>
        </GlassCard>
      )}
    </div>
  );
};
