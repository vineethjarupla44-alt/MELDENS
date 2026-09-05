import { apiClient } from './apiClient';
import type { ConflictRecord } from '../types';

export const conflictService = {
  async getConflicts(patientId?: string, status?: string): Promise<ConflictRecord[]> {
    const params: Record<string, string> = {};
    if (patientId) params.patient_id = patientId;
    if (status && status !== 'ALL') params.status = status;
    const response = await apiClient.get<ConflictRecord[]>('/api/v1/conflicts', { params });
    return response.data;
  },

  async getUnresolvedConflicts(patientId?: string): Promise<ConflictRecord[]> {
    return this.getConflicts(patientId, 'UNRESOLVED');
  },

  async resolveConflict(
    conflictId: string, 
    resolutionNotes: string, 
    resolvedBy: string,
    status: 'RESOLVED' | 'DISMISSED' = 'RESOLVED'
  ): Promise<ConflictRecord> {
    const response = await apiClient.post<ConflictRecord>(`/api/v1/conflicts/${conflictId}/resolve`, {
      resolution_notes: resolutionNotes,
      resolved_by: resolvedBy,
      status: status,
    });
    return response.data;
  },
};
