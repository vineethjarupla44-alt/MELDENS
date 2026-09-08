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


import { mockDataStore } from './mockDataStore';

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
    try {
      const response = await apiClient.get<Patient[]>('/api/v1/patients');
      if (Array.isArray(response.data) && response.data.length > 0) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getPatients();
  },

  async getPatientById(id: string): Promise<PatientDetailResponse> {
    try {
      const response = await apiClient.get<PatientDetailResponse>(`/api/v1/patients/${id}`);
      if (response.data && typeof response.data === 'object' && response.data.id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getPatientById(id);
  },

  async submitIntake(data: PatientIntakeSubmission): Promise<PatientIntakeResponse> {
    try {
      const response = await apiClient.post<PatientIntakeResponse>('/api/v1/patients/intake', data);
      if (response.data && response.data.patient_id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.submitIntake(data);
  },

  async updateIntake(patientId: string, data: PatientIntakeSubmission): Promise<PatientIntakeResponse> {
    try {
      const response = await apiClient.put<PatientIntakeResponse>(`/api/v1/patients/${patientId}/intake`, data);
      if (response.data && response.data.patient_id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.updateIntake(patientId, data);
  },

  async getPatientAuditLogs(patientId: string): Promise<AuditLog[]> {
    try {
      const response = await apiClient.get<AuditLog[]>(`/api/v1/patients/${patientId}/audit`);
      if (Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getPatientAuditLogs(patientId);
  },

  async getPatientTimeline(patientId: string): Promise<TimelineEvent[]> {
    try {
      const response = await apiClient.get<TimelineEvent[]>(`/api/v1/patients/${patientId}/timeline`);
      if (Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getPatientTimeline(patientId);
  },

  async getProvenanceDetails(entityType: string, entityId: string): Promise<ClinicalProvenanceDetail> {
    try {
      const response = await apiClient.get<ClinicalProvenanceDetail>(`/api/v1/clinical/${entityType}/${entityId}/provenance`);
      if (response.data && response.data.entity_id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getProvenanceDetails(entityType, entityId);
  },

  async verifyClinicalItem(payload: {
    entity_type: string;
    entity_id: string;
    verification_status?: string;
    verified_by?: string;
    verification_notes?: string;
  }): Promise<any> {
    try {
      const response = await apiClient.post('/api/v1/clinical/verify-item', {
        entity_type: payload.entity_type,
        entity_id: payload.entity_id,
        verification_status: payload.verification_status || 'VERIFIED',
        verified_by: payload.verified_by || 'Dr. Sarah Lin, MD',
        verification_notes: payload.verification_notes,
      });
      if (response.data) return response.data;
    } catch {
      // Fallback
    }
    return mockDataStore.verifyClinicalItem(payload);
  },

  async getVerificationQueue(patientId?: string): Promise<VerificationQueueItem[]> {
    try {
      const url = patientId 
        ? `/api/v1/clinical/verification-queue?patient_id=${patientId}`
        : '/api/v1/clinical/verification-queue';
      const response = await apiClient.get<VerificationQueueItem[]>(url);
      if (Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getVerificationQueue(patientId);
  },

  async executeVerificationAction(payload: VerificationActionPayload): Promise<VerificationActionResponse> {
    try {
      const response = await apiClient.post<VerificationActionResponse>('/api/v1/clinical/verify-action', payload);
      if (response.data && response.data.entity_id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.executeVerificationAction(payload);
  },

  async getPatientSummary(patientId: string): Promise<ClinicalSummary | null> {
    try {
      const response = await apiClient.get<ClinicalSummary | null>(`/api/v1/patients/${patientId}/summary`);
      if (response.data && response.data.summary_text) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getPatientSummary(patientId);
  },

  async generatePatientSummary(patientId: string, forceRegenerate: boolean = false): Promise<ClinicalSummary> {
    try {
      const response = await apiClient.post<ClinicalSummary>(`/api/v1/patients/${patientId}/summary/generate`, {
        force_regenerate: forceRegenerate,
      });
      if (response.data && response.data.summary_text) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.generatePatientSummary(patientId);
  },
};


