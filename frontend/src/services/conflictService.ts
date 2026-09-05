import { apiClient } from './apiClient';
import type { ConflictRecord } from '../types';

export const conflictService = {
  async getUnresolvedConflicts(patientId?: string): Promise<ConflictRecord[]> {
    const params = patientId ? { patient_id: patientId } : {};
    const response = await apiClient.get<ConflictRecord[]>('/api/v1/conflicts', { params });
    return response.data;
  },

  async resolveConflict(
    conflictId: string, 
    resolutionNotes: string, 
    resolvedBy: string
  ): Promise<ConflictRecord> {
    const response = await apiClient.post<ConflictRecord>(`/api/v1/conflicts/${conflictId}/resolve`, {
      resolution_notes: resolutionNotes,
      resolved_by: resolvedBy,
    });
    return response.data;
  },
};
