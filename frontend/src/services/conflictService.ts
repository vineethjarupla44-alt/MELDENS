import { apiClient } from './apiClient';
import type { ConflictRecord } from '../types';

import { mockDataStore } from './mockDataStore';

export const conflictService = {
  async getConflicts(patientId?: string, status?: string): Promise<ConflictRecord[]> {
    try {
      const params: Record<string, string> = {};
      if (patientId) params.patient_id = patientId;
      if (status && status !== 'ALL') params.status = status;
      const response = await apiClient.get<ConflictRecord[]>('/api/v1/conflicts', { params });
      if (Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getConflicts(patientId, status);
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
    try {
      const response = await apiClient.post<ConflictRecord>(`/api/v1/conflicts/${conflictId}/resolve`, {
        resolution_notes: resolutionNotes,
        resolved_by: resolvedBy,
        status: status,
      });
      if (response.data && response.data.id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.resolveConflict(conflictId, resolutionNotes, resolvedBy, status);
  },
};
