import { apiClient } from './apiClient';
import type { 
  MedicalDocument, 
  DocumentPage,
  DocumentTextExtractionResponse,
  ExtractedDocumentData,
} from '../types';

export const documentService = {
  async uploadDocument(
    patientId: string, 
    file: File, 
    onUploadProgress?: (progress: number) => void
  ): Promise<MedicalDocument> {
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
    return response.data;
  },

  async getPatientDocuments(patientId: string): Promise<MedicalDocument[]> {
    const response = await apiClient.get<MedicalDocument[]>(`/api/v1/patients/${patientId}/documents`);
    return response.data;
  },

  async getDocument(documentId: string): Promise<MedicalDocument> {
    const response = await apiClient.get<MedicalDocument>(`/api/v1/documents/${documentId}`);
    return response.data;
  },

  async deleteDocument(documentId: string): Promise<{ status: string; id: string; message: string }> {
    const response = await apiClient.delete<{ status: string; id: string; message: string }>(
      `/api/v1/documents/${documentId}`
    );
    return response.data;
  },

  getDocumentFileUrl(documentId: string): string {
    const baseURL = import.meta.env.VITE_API_BASE_URL || '';
    return `${baseURL}/api/v1/documents/${documentId}/file`;
  },

  async processDocument(documentId: string): Promise<DocumentTextExtractionResponse> {
    const response = await apiClient.post<DocumentTextExtractionResponse>(
      `/api/v1/documents/${documentId}/process`
    );
    return response.data;
  },

  async getDocumentPages(documentId: string): Promise<DocumentPage[]> {
    const response = await apiClient.get<DocumentPage[]>(
      `/api/v1/documents/${documentId}/pages`
    );
    return response.data;
  },

  async extractMedicalData(documentId: string): Promise<ExtractedDocumentData> {
    const response = await apiClient.post<ExtractedDocumentData>(
      `/api/v1/documents/${documentId}/extract-medical-data`
    );
    return response.data;
  },
};
