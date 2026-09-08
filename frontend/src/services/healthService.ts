import { apiClient } from './apiClient';
import type { HealthResponse } from '../types';

import { mockDataStore } from './mockDataStore';

export const healthService = {
  /**
   * Fetches backend health status, database connectivity, and MedLens capabilities.
   */
  async getHealth(): Promise<HealthResponse> {
    try {
      const response = await apiClient.get<HealthResponse>('/api/health');
      if (response.data && response.data.status) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getHealth();
  },
};
