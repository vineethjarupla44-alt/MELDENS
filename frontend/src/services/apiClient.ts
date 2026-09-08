import axios from 'axios';
import type { AxiosError, AxiosResponse } from 'axios';

// In development, the Vite server proxies /api to http://127.0.0.1:8000
const baseURL = import.meta.env.VITE_API_BASE_URL || '';

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Response interceptor for consistent error handling and static-host fallback detection
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // If the static hosting returns index.html for unknown /api/ routes, treat as route failure
    const contentType = String(response.headers?.['content-type'] || '');
    if (
      contentType.includes('text/html') ||
      (typeof response.data === 'string' && response.data.trim().startsWith('<!doctype'))
    ) {
      const err: any = new Error('Static host SPA rewrite detected for API route');
      err.isStaticFallback = true;
      err.response = response;
      return Promise.reject(err);
    }
    return response;
  },
  (error: AxiosError) => {
    const message = (error.response?.data as any)?.detail || error.message || 'An unexpected error occurred';
    console.warn(`[API Notice] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`, message);
    return Promise.reject(error);
  }
);
