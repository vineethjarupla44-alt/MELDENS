import { apiClient } from './apiClient';
import type { 
  MedicalDocument, 
  DocumentPage,
  DocumentTextExtractionResponse,
  ExtractedDocumentData,
} from '../types';

import { mockDataStore } from './mockDataStore';

export const documentService = {
  async uploadDocument(
    patientId: string, 
    file: File, 
    onUploadProgress?: (progress: number) => void
  ): Promise<MedicalDocument> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post<MedicalDocument>(
        `/api/v1/patients/${patientId}/documents/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total && onUploadProgress) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              onUploadProgress(percentCompleted);
            }
          },
        }
      );
      if (response.data && response.data.id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.uploadDocument(patientId, file, onUploadProgress);
  },

  async getPatientDocuments(patientId: string): Promise<MedicalDocument[]> {
    try {
      const response = await apiClient.get<MedicalDocument[]>(`/api/v1/patients/${patientId}/documents`);
      if (Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getPatientDocuments(patientId);
  },

  async getDocument(documentId: string): Promise<MedicalDocument> {
    try {
      const response = await apiClient.get<MedicalDocument>(`/api/v1/documents/${documentId}`);
      if (response.data && response.data.id) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getDocument(documentId);
  },

  async deleteDocument(documentId: string): Promise<{ status: string; id: string; message: string }> {
    try {
      const response = await apiClient.delete<{ status: string; id: string; message: string }>(
        `/api/v1/documents/${documentId}`
      );
      if (response.data && response.data.status) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.deleteDocument(documentId);
  },

  getDocumentFileUrl(documentId: string): string {
    const localFile = mockDataStore.getDocumentFileUrl(documentId);
    if (localFile) return localFile;
    const baseURL = import.meta.env.VITE_API_BASE_URL || '';
    return `${baseURL}/api/v1/documents/${documentId}/file`;
  },

  async processDocument(documentId: string): Promise<DocumentTextExtractionResponse> {
    try {
      const response = await apiClient.post<DocumentTextExtractionResponse>(
        `/api/v1/documents/${documentId}/process`
      );
      if (response.data && Array.isArray(response.data.pages)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.processDocument(documentId);
  },

  async getDocumentPages(documentId: string): Promise<DocumentPage[]> {
    try {
      const response = await apiClient.get<DocumentPage[]>(
        `/api/v1/documents/${documentId}/pages`
      );
      if (Array.isArray(response.data)) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.getDocumentPages(documentId);
  },

  async extractMedicalData(documentId: string): Promise<ExtractedDocumentData> {
    try {
      const response = await apiClient.post<ExtractedDocumentData>(
        `/api/v1/documents/${documentId}/extract-medical-data`
      );
      if (response.data && response.data.laboratories) {
        return response.data;
      }
    } catch {
      // Fallback
    }
    return mockDataStore.extractMedicalData(documentId);
  },
};
