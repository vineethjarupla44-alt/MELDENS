import { apiClient } from './apiClient';
import type { 
  Patient, 
  LabResult, 
  Medication, 
  Condition, 
  Allergy,
  Observation,
  AuditLog,
  TimelineEvent,
  ClinicalProvenanceDetail,
  VerificationQueueItem,
  VerificationActionPayload,
  VerificationActionResponse,
  PatientIntakeSubmission,
  PatientIntakeResponse,
  ClinicalSummary,
} from '../types';


export interface PatientDetailResponse extends Patient {
  documents?: any[];
  lab_results?: LabResult[];
  medications?: Medication[];
  conditions?: Condition[];
  allergies?: Allergy[];
  observations?: Observation[];
}

export const patientService = {
  async getPatients(): Promise<Patient[]> {
    const response = await apiClient.get<Patient[]>('/api/v1/patients');
    return response.data;
  },

  async getPatientById(id: string): Promise<PatientDetailResponse> {
    const response = await apiClient.get<PatientDetailResponse>(`/api/v1/patients/${id}`);
    return response.data;
  },

  async submitIntake(data: PatientIntakeSubmission): Promise<PatientIntakeResponse> {
    const response = await apiClient.post<PatientIntakeResponse>('/api/v1/patients/intake', data);
    return response.data;
  },

  async updateIntake(patientId: string, data: PatientIntakeSubmission): Promise<PatientIntakeResponse> {
    const response = await apiClient.put<PatientIntakeResponse>(`/api/v1/patients/${patientId}/intake`, data);
    return response.data;
  },

  async getPatientAuditLogs(patientId: string): Promise<AuditLog[]> {
    const response = await apiClient.get<AuditLog[]>(`/api/v1/patients/${patientId}/audit`);
    return response.data;
  },

  async getPatientTimeline(patientId: string): Promise<TimelineEvent[]> {
    const response = await apiClient.get<TimelineEvent[]>(`/api/v1/patients/${patientId}/timeline`);
    return response.data;
  },

  async getProvenanceDetails(entityType: string, entityId: string): Promise<ClinicalProvenanceDetail> {
    const response = await apiClient.get<ClinicalProvenanceDetail>(`/api/v1/clinical/${entityType}/${entityId}/provenance`);
    return response.data;
  },

  async verifyClinicalItem(payload: {
    entity_type: string;
    entity_id: string;
    verification_status?: string;
    verified_by?: string;
    verification_notes?: string;
  }): Promise<any> {
    const response = await apiClient.post('/api/v1/clinical/verify-item', {
      entity_type: payload.entity_type,
      entity_id: payload.entity_id,
      verification_status: payload.verification_status || 'VERIFIED',
      verified_by: payload.verified_by || 'Dr. Sarah Lin, MD',
      verification_notes: payload.verification_notes,
    });
    return response.data;
  },

  async getVerificationQueue(patientId?: string): Promise<VerificationQueueItem[]> {
    const url = patientId 
      ? `/api/v1/clinical/verification-queue?patient_id=${patientId}`
      : '/api/v1/clinical/verification-queue';
    const response = await apiClient.get<VerificationQueueItem[]>(url);
    return response.data;
  },

  async executeVerificationAction(payload: VerificationActionPayload): Promise<VerificationActionResponse> {
    const response = await apiClient.post<VerificationActionResponse>('/api/v1/clinical/verify-action', payload);
    return response.data;
  },

  async getPatientSummary(patientId: string): Promise<ClinicalSummary | null> {
    const response = await apiClient.get<ClinicalSummary | null>(`/api/v1/patients/${patientId}/summary`);
    return response.data;
  },

  async generatePatientSummary(patientId: string, forceRegenerate: boolean = false): Promise<ClinicalSummary> {
    const response = await apiClient.post<ClinicalSummary>(`/api/v1/patients/${patientId}/summary/generate`, {
      force_regenerate: forceRegenerate,
    });
    return response.data;
  },
};


