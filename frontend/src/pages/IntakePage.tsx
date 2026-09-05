import React, { useEffect, useState } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { Button } from '../components/common/Button';
import { PatientIntakeForm } from '../components/intake/PatientIntakeForm';
import { PatientDetailCard } from '../components/intake/PatientDetailCard';
import { patientService, type PatientDetailResponse } from '../services/patientService';
import type { 
  Patient, 
  AuditLog, 
  PatientIntakeSubmission 
} from '../types';
import { 
  UserPlus, 
  Users, 
  CheckCircle2, 
  FileCheck,
  AlertCircle
} from 'lucide-react';

const STORAGE_KEY = 'medlens_active_patient_id';

export const IntakePage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(() => {
    return localStorage.getItem(STORAGE_KEY);
  });
  const [activePatient, setActivePatient] = useState<PatientDetailResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreatingNew, setIsCreatingNew] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Load all patients
  const loadPatients = async (selectIdAfterLoad?: string) => {
    try {
      setLoading(true);
      const list = await patientService.getPatients();
      setPatients(list);

      // Determine which patient to select
      let targetId = selectIdAfterLoad || selectedPatientId;
      if (!targetId && list.length > 0) {
        targetId = list[0].id;
      }

      if (targetId && list.some(p => p.id === targetId)) {
        setSelectedPatientId(targetId);
        localStorage.setItem(STORAGE_KEY, targetId);
        await loadPatientDetail(targetId);
      } else if (list.length > 0) {
        const first = list[0].id;
        setSelectedPatientId(first);
        localStorage.setItem(STORAGE_KEY, first);
        await loadPatientDetail(first);
      } else {
        setIsCreatingNew(true);
      }
    } catch (err: any) {
      console.error('Failed to load patients', err);
      setNotification({ type: 'error', message: 'Failed to load patients from server.' });
    } finally {
      setLoading(false);
    }
  };

  const loadPatientDetail = async (id: string) => {
    try {
      const [detail, logs] = await Promise.all([
        patientService.getPatientById(id),
        patientService.getPatientAuditLogs(id),
      ]);
      setActivePatient(detail);
      setAuditLogs(logs);
      setIsEditing(false);
      setIsCreatingNew(false);
    } catch (err: any) {
      console.error('Failed to load patient detail', err);
    }
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleSelectPatient = (id: string) => {
    setSelectedPatientId(id);
    localStorage.setItem(STORAGE_KEY, id);
    loadPatientDetail(id);
  };

  const handleNewIntake = () => {
    setIsCreatingNew(true);
    setIsEditing(false);
    setActivePatient(null);
  };

  const handleSubmitNew = async (data: PatientIntakeSubmission) => {
    try {
      setSubmitting(true);
      const res = await patientService.submitIntake(data);
      setNotification({
        type: 'success',
        message: `Patient intake recorded successfully for ${res.first_name} ${res.last_name} (MRN: ${res.mrn})! Provenance tagged as PATIENT_INPUT.`,
      });
      await loadPatients(res.patient_id);
    } catch (err: any) {
      console.error('Intake submission error', err);
      setNotification({ type: 'error', message: err.response?.data?.detail || 'Submission failed' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdate = async (data: PatientIntakeSubmission) => {
    if (!activePatient) return;
    try {
      setSubmitting(true);
      const res = await patientService.updateIntake(activePatient.id, data);
      setNotification({
        type: 'success',
        message: `Intake updated successfully for ${res.first_name} ${res.last_name}. Audit log recorded.`,
      });
      await loadPatientDetail(activePatient.id);
    } catch (err: any) {
      console.error('Intake update error', err);
      setNotification({ type: 'error', message: err.response?.data?.detail || 'Update failed' });
    } finally {
      setSubmitting(false);
    }
  };

  // Convert activePatient to initial form values for editing
  const getInitialFormData = (): PatientIntakeSubmission | undefined => {
    if (!activePatient) return undefined;
    return {
      first_name: activePatient.first_name,
      last_name: activePatient.last_name,
      date_of_birth: activePatient.date_of_birth || '',
      gender: activePatient.gender || 'Female',
      blood_type: activePatient.blood_type || undefined,
      mrn: activePatient.mrn || undefined,
      symptoms: activePatient.profile?.symptoms || undefined,
      existing_conditions: activePatient.conditions?.map(c => ({
        condition_name: c.condition_name,
        onset_date: c.onset_date || undefined,
        clinical_status: c.clinical_status,
      })) || [],
      allergies: activePatient.allergies?.map(a => ({
        allergen: a.allergen,
        reaction: a.reaction || undefined,
        severity: (a.severity as any) || 'MODERATE',
      })) || [],
      current_medications: activePatient.medications?.map(m => ({
        medication_name: m.medication_name,
        dosage: m.dosage || undefined,
        frequency: m.frequency || undefined,
        route: m.route || 'Oral',
      })) || [],
      additional_notes: activePatient.profile?.baseline_notes || undefined,
      emergency_contact_name: activePatient.profile?.emergency_contact_name || undefined,
      emergency_contact_phone: activePatient.profile?.emergency_contact_phone || undefined,
      preferred_language: activePatient.profile?.preferred_language || 'English',
    };
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileCheck className="h-6 w-6 text-cyan-400" />
            Patient Information Intake
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Structured capture of patient-reported symptoms, medications, allergies, and history with immutable audit tracking.
          </p>
        </div>

        {/* Patient Selection & New Action */}
        <div className="flex flex-wrap items-center gap-3">
          {patients.length > 0 && (
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-lg">
              <Users className="w-4 h-4 text-slate-400" />
              <select
                value={selectedPatientId || ''}
                onChange={(e) => handleSelectPatient(e.target.value)}
                className="bg-transparent text-sm text-white focus:outline-none cursor-pointer"
              >
                {patients.map((p) => (
                  <option key={p.id} value={p.id} className="bg-slate-900 text-white">
                    {p.first_name} {p.last_name} ({p.mrn})
                  </option>
                ))}
              </select>
            </div>
          )}

          <Button 
            variant={isCreatingNew ? 'secondary' : 'primary'} 
            size="sm" 
            onClick={handleNewIntake}
          >
            <UserPlus className="w-4 h-4 mr-1.5" />
            New Patient Intake
          </Button>
        </div>
      </div>

      {/* Feedback Notification Banner */}
      {notification && (
        <GlassCard 
          variant={notification.type === 'success' ? 'accent' : 'danger'}
          className="flex items-center justify-between py-3 px-4"
        >
          <div className="flex items-center gap-2.5 text-xs">
            {notification.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            )}
            <span className={notification.type === 'success' ? 'text-emerald-300' : 'text-rose-300'}>
              {notification.message}
            </span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-white text-xs ml-4"
          >
            Dismiss
          </button>
        </GlassCard>
      )}

      {/* Main View Area */}
      {isCreatingNew ? (
        <PatientIntakeForm
          onSubmit={handleSubmitNew}
          onCancel={patients.length > 0 ? () => {
            setIsCreatingNew(false);
            if (selectedPatientId) loadPatientDetail(selectedPatientId);
          } : undefined}
          isLoading={submitting}
        />
      ) : isEditing ? (
        <PatientIntakeForm
          initialData={getInitialFormData()}
          isEditing={true}
          onSubmit={handleUpdate}
          onCancel={() => setIsEditing(false)}
          isLoading={submitting}
        />
      ) : activePatient ? (
        <PatientDetailCard
          patient={activePatient}
          auditLogs={auditLogs}
          onEdit={() => setIsEditing(true)}
        />
      ) : loading ? (
        <GlassCard className="text-center p-12">
          <p className="text-sm text-slate-400">Loading patient intake records...</p>
        </GlassCard>
      ) : (
        <GlassCard className="text-center p-12 space-y-3">
          <p className="text-sm text-slate-400">No patient records found.</p>
          <Button variant="primary" onClick={handleNewIntake}>
            Create First Patient Intake
          </Button>
        </GlassCard>
      )}
    </div>
  );
};
