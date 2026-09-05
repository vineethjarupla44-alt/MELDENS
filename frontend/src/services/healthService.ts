import { apiClient } from './apiClient';
import type { HealthResponse } from '../types';

export const healthService = {
  /**
   * Fetches backend health status, database connectivity, and MedLens capabilities.
   */
  async getHealth(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>('/api/health');
    return response.data;
  },
};
