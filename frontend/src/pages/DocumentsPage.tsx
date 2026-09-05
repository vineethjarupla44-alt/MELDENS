import React, { useState, useEffect, useRef } from 'react';
import { GlassCard } from '../components/common/GlassCard';
import { Button } from '../components/common/Button';
import { documentService } from '../services/documentService';
import { patientService } from '../services/patientService';
import type { 
  Patient, 
  MedicalDocument, 
  DocumentPage,
  ExtractedDocumentData,
  DocumentStatus,
} from '../types';
import { 
  FileText, 
  UploadCloud, 
  Trash2, 
  Eye, 
  Cpu, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  X, 
  FileCode,
  ShieldCheck,
  User,
  FlaskConical,
  Pill,
  HeartPulse,
} from 'lucide-react';

export const DocumentsPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [documents, setDocuments] = useState<MedicalDocument[]>([]);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);


  // Modals / Drawers state
  const [previewDoc, setPreviewDoc] = useState<MedicalDocument | null>(null);
  const [activeTextDoc, setActiveTextDoc] = useState<MedicalDocument | null>(null);
  const [docPages, setDocPages] = useState<DocumentPage[]>([]);
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [isProcessingText, setIsProcessingText] = useState<boolean>(false);

  // AI Extraction state
  const [aiExtractedData, setAiExtractedData] = useState<ExtractedDocumentData | null>(null);
  const [isExtractingAI, setIsExtractingAI] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);

  // 1. Fetch Patients on Mount
  useEffect(() => {
    async function loadPatients() {
      try {
        const data = await patientService.getPatients();
        setPatients(data);
        const stored = localStorage.getItem('medlens_selected_patient');
        if (stored && data.some(p => p.id === stored)) {
          setSelectedPatientId(stored);
        } else if (data.length > 0) {
          setSelectedPatientId(data[0].id);
        }
      } catch (err: any) {
        setErrorMsg('Failed to fetch patients list.');
      }
    }
    loadPatients();
  }, []);

  // 2. Fetch Documents whenever selected patient changes
  useEffect(() => {
    if (!selectedPatientId) return;
    localStorage.setItem('medlens_selected_patient', selectedPatientId);
    fetchDocuments(selectedPatientId);
  }, [selectedPatientId]);

  async function fetchDocuments(patientId: string) {
    try {
      const docs = await documentService.getPatientDocuments(patientId);
      setDocuments(docs);
    } catch (err: any) {
      setErrorMsg('Failed to load documents for the selected patient.');
    }
  }

  // 3. File Upload Handler
  async function handleFileUpload(file: File) {
    if (!selectedPatientId) {
      setErrorMsg('Please select a patient before uploading documents.');
      return;
    }

    const validExtensions = ['.pdf', '.png', '.jpg', '.jpeg'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!validExtensions.includes(ext)) {
      setErrorMsg(`Invalid file type "${ext}". Allowed: PDF, PNG, JPG, JPEG.`);
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setErrorMsg('File size exceeds the maximum limit of 25 MB.');
      return;
    }

    setErrorMsg(null);
    setSuccessMsg(null);
    setUploadProgress(0);

    try {
      await documentService.uploadDocument(selectedPatientId, file, (progress) => {
        setUploadProgress(progress);
      });
      setSuccessMsg(`Document "${file.name}" uploaded successfully.`);
      await fetchDocuments(selectedPatientId);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setTimeout(() => setUploadProgress(null), 1000);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  // 4. Delete Document Handler
  async function handleDeleteDocument(docId: string, filename: string) {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;

    try {
      await documentService.deleteDocument(docId);
      setSuccessMsg(`Document "${filename}" deleted.`);
      setDocuments(prev => prev.filter(d => d.id !== docId));
      if (previewDoc?.id === docId) setPreviewDoc(null);
      if (activeTextDoc?.id === docId) setActiveTextDoc(null);
      if (aiExtractedData?.document_id === docId) setAiExtractedData(null);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to delete document.');
    }
  }

  // 5. Run Text Extraction Pipeline
  async function handleExtractText(doc: MedicalDocument) {
    setIsProcessingText(true);
    setErrorMsg(null);
    try {
      await documentService.processDocument(doc.id);
      const pages = await documentService.getDocumentPages(doc.id);
      setActiveTextDoc(doc);
      setDocPages(pages);
      setSelectedPageNum(1);
      await fetchDocuments(selectedPatientId);
      setSuccessMsg(`Text extraction complete for "${doc.original_name}".`);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to extract text from document.');
    } finally {
      setIsProcessingText(false);
    }
  }

  // 6. View Stored Text
  async function handleViewText(doc: MedicalDocument) {
    try {
      const pages = await documentService.getDocumentPages(doc.id);
      setActiveTextDoc(doc);
      setDocPages(pages);
      setSelectedPageNum(1);
    } catch (err: any) {
      setErrorMsg('Failed to load document pages.');
    }
  }

  // 7. Run AI Clinical Information Extraction
  async function handleExtractAIData(doc: MedicalDocument) {
    setIsExtractingAI(true);
    setErrorMsg(null);
    try {
      // If document hasn't been processed for text yet, run text extraction first
      if (doc.processing_status === 'UPLOADED') {
        await documentService.processDocument(doc.id);
      }
      const data = await documentService.extractMedicalData(doc.id);
      setAiExtractedData(data);
      await fetchDocuments(selectedPatientId);
      setSuccessMsg(`AI Medical Information extracted from "${doc.original_name}".`);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'AI Clinical Extraction failed.');
    } finally {
      setIsExtractingAI(false);
    }
  }

  // Render Status Badge
  const renderStatusBadge = (status: DocumentStatus) => {
    switch (status) {
      case 'PROCESSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" /> PROCESSED
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-cyan-950/80 text-cyan-300 border border-cyan-500/30 animate-pulse">
            <Cpu className="w-3 h-3 animate-spin" /> PROCESSING
          </span>
        );
      case 'NEEDS_REVIEW':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-950/80 text-amber-300 border border-amber-500/40">
            <AlertTriangle className="w-3 h-3" /> NEEDS REVIEW
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/80 text-rose-300 border border-rose-500/40">
            <X className="w-3 h-3" /> FAILED
          </span>
        );
      case 'UPLOADED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
            UPLOADED
          </span>
        );
    }
  };

  const selectedPatient = patients.find(p => p.id === selectedPatientId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FileText className="h-6 w-6 text-cyan-400" />
            Medical Document Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Secure multi-page ingestion, text extraction pipeline, and verified AI clinical information intelligence.
          </p>
        </div>

        {/* Patient Switcher */}
        <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-800 rounded-lg p-2">
          <User className="w-4 h-4 text-cyan-400" />
          <span className="text-xs text-slate-400 font-medium">Patient:</span>
          <select
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
            className="bg-slate-950 text-white text-xs border border-slate-700 rounded px-2.5 py-1.5 focus:outline-none focus:border-cyan-500"
          >
            {patients.map(p => (
              <option key={p.id} value={p.id}>
                {p.first_name} {p.last_name} ({p.mrn || 'No MRN'})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Feedback Alerts */}
      {errorMsg && (
        <div className="bg-rose-950/40 border border-rose-500/50 rounded-lg p-3 text-sm text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-rose-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-lg p-3 text-sm text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-emerald-400 hover:text-emerald-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Dropzone */}
      <GlassCard className="p-6">
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
              handleFileUpload(e.dataTransfer.files[0]);
            }
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
            isDragging 
              ? 'border-cyan-400 bg-cyan-950/30' 
              : 'border-slate-700 hover:border-cyan-500/50 hover:bg-slate-900/50'
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
              }
            }}
            accept=".pdf,.png,.jpg,.jpeg"
            className="hidden"
          />

          <div className="w-14 h-14 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-3">
            <UploadCloud className="w-7 h-7" />
          </div>

          <h3 className="text-base font-semibold text-white">
            Upload Medical Report or Clinical PDF
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm">
            Drag and drop clinical documents, discharge summaries, or laboratory tests. Supports PDF, PNG, JPG (up to 25 MB).
          </p>

          <span className="mt-4 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-md border border-slate-700">
            Browse Local File
          </span>

          {uploadProgress !== null && (
            <div className="w-full max-w-xs mt-4">
              <div className="flex justify-between text-xs text-cyan-300 mb-1">
                <span>Uploading to isolated vault...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-cyan-500 transition-all duration-200" 
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </GlassCard>

      {/* Document Records List */}
      <GlassCard className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <FileCode className="w-5 h-5 text-cyan-400" />
            Patient Documents ({documents.length})
          </h2>
          {selectedPatient && (
            <span className="text-xs text-slate-400">
              Assigned to: <strong className="text-white">{selectedPatient.first_name} {selectedPatient.last_name}</strong>
            </span>
          )}
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-sm">
            No medical documents uploaded for this patient yet. Use the upload box above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 border-b border-slate-800 pb-2">
                <tr>
                  <th className="py-2.5 font-medium">Document Name</th>
                  <th className="py-2.5 font-medium">Pages</th>
                  <th className="py-2.5 font-medium">Size</th>
                  <th className="py-2.5 font-medium">Upload Date</th>
                  <th className="py-2.5 font-medium">Status</th>
                  <th className="py-2.5 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 font-medium text-slate-200 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-cyan-400 flex-shrink-0" />
                      <span className="truncate max-w-xs" title={doc.original_name}>
                        {doc.original_name}
                      </span>
                    </td>
                    <td className="py-3 text-slate-300">{doc.page_count} pg</td>
                    <td className="py-3 text-slate-400">{(doc.file_size / 1024).toFixed(1)} KB</td>
                    <td className="py-3 text-slate-400">{new Date(doc.upload_date).toLocaleDateString()}</td>
                    <td className="py-3">{renderStatusBadge(doc.processing_status)}</td>
                    <td className="py-3 text-right space-x-1.5">
                      {/* Extract / View Text Button */}
                      {doc.raw_text ? (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleViewText(doc)}
                          title="View extracted page-level text"
                        >
                          <FileCode className="w-3.5 h-3.5" />
                          View Text
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleExtractText(doc)}
                          isLoading={isProcessingText && activeTextDoc?.id === doc.id}
                          title="Run layout-aware text extraction pipeline"
                        >
                          <Cpu className="w-3.5 h-3.5" />
                          Extract Text
                        </Button>
                      )}

                      {/* AI Extract Clinical Data Button */}
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleExtractAIData(doc)}
                        isLoading={isExtractingAI}
                        title="Extract structured clinical entities and laboratory bounds"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        AI Extraction
                      </Button>

                      {/* Preview PDF/Image */}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setPreviewDoc(doc)}
                        title="Preview document stream"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </Button>

                      {/* Delete */}
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={() => handleDeleteDocument(doc.id, doc.original_name)}
                        title="Delete document and remove file"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>

      {/* Extracted Text Viewer Modal / Drawer */}
      {activeTextDoc && (
        <GlassCard className="p-6 border-cyan-500/30">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <FileCode className="w-5 h-5 text-cyan-400" />
                Extracted Page-Level Text: {activeTextDoc.original_name}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Layout-preserved digital extraction. All text is enclosed in untrusted boundaries.
              </p>
            </div>
            <button
              onClick={() => setActiveTextDoc(null)}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Page Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4 overflow-x-auto">
            {docPages.map(page => (
              <button
                key={page.id}
                onClick={() => setSelectedPageNum(page.page_number)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                  selectedPageNum === page.page_number
                    ? 'bg-cyan-600 text-white shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <span>Page {page.page_number}</span>
                {page.extraction_status === 'OCR_REQUIRED' && (
                  <span className="w-2 h-2 rounded-full bg-amber-400" title="OCR Required (Scanned)" />
                )}
                {page.extraction_status === 'SUCCESS' && (
                  <span className="w-2 h-2 rounded-full bg-emerald-400" title="Digital text extracted" />
                )}
              </button>
            ))}
          </div>

          {/* Selected Page Text View */}
          {(() => {
            const currentPage = docPages.find(p => p.page_number === selectedPageNum);
            if (!currentPage) return <div className="text-slate-500 text-xs">No page selected.</div>;

            return (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Extraction Status: <strong className="text-cyan-400">{currentPage.extraction_status || 'SUCCESS'}</strong></span>
                  <span>Confidence: <strong className="text-white">{((currentPage.confidence_score ?? 1.0) * 100).toFixed(0)}%</strong></span>
                </div>

                {currentPage.extraction_status === 'OCR_REQUIRED' ? (
                  <div className="p-6 bg-amber-950/20 border border-amber-500/30 rounded-lg text-center">
                    <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
                    <h4 className="text-sm font-semibold text-amber-300">Scanned Document Detected (OCR Required)</h4>
                    <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                      This page contains raster images of text without embedded digital font streams. Marked for OCR processing.
                    </p>
                  </div>
                ) : (
                  <pre className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto max-h-96 whitespace-pre-wrap leading-relaxed">
                    {currentPage.extracted_text || '(Empty page)'}
                  </pre>
                )}
              </div>
            );
          })()}
        </GlassCard>
      )}

      {/* Structured AI Clinical Intelligence Viewer */}
      {aiExtractedData && (
        <GlassCard className="p-6 border-emerald-500/40 bg-slate-900/90 shadow-[0_0_25px_rgba(16,185,129,0.1)]">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-5">
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-6 h-6 text-emerald-400" />
                Validated AI Clinical Intelligence
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Deterministic post-validation passed. Report reference intervals strictly enforced. Non-diagnostic.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs px-3 py-1 rounded-full bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-mono">
                Overall Confidence: {(aiExtractedData.overall_confidence * 100).toFixed(1)}%
              </span>
              <button
                onClick={() => setAiExtractedData(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Demographics & Clinical Context */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-cyan-400" /> Patient Demographics
              </h4>
              <p className="text-sm text-slate-200">
                Age: <strong className="text-white">{aiExtractedData.patient_info.age ?? 'Not specified'}</strong>
              </p>
              <p className="text-sm text-slate-200 mt-1">
                Sex: <strong className="text-white">{aiExtractedData.patient_info.sex ?? 'Not specified'}</strong>
              </p>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <HeartPulse className="w-3.5 h-3.5 text-rose-400" /> Documented Symptoms
              </h4>
              {aiExtractedData.patient_info.symptoms.length > 0 ? (
                <ul className="text-xs text-slate-300 list-disc list-inside space-y-1">
                  {aiExtractedData.patient_info.symptoms.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-xs text-slate-500">None explicitly documented</span>
              )}
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Pill className="w-3.5 h-3.5 text-amber-400" /> Documented Medications & Allergies
              </h4>
              <div className="text-xs space-y-1.5">
                <div>
                  <span className="text-slate-400 font-medium">Meds: </span>
                  <span className="text-slate-200">
                    {aiExtractedData.patient_info.medications.map(m => m.medication_name).join(', ') || 'None'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Allergies: </span>
                  <span className="text-slate-200">
                    {aiExtractedData.patient_info.allergies.map(a => a.allergen).join(', ') || 'None'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Laboratory Intelligence Panel */}
          <div>
            <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-cyan-400" />
              Extracted Laboratory Results ({aiExtractedData.laboratories.length})
            </h4>

            {aiExtractedData.laboratories.length === 0 ? (
              <div className="text-xs text-slate-500 py-4 text-center">
                No laboratory tests identified in this document.
              </div>
            ) : (
              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="p-3 font-medium">Test Name</th>
                      <th className="p-3 font-medium">Result Value</th>
                      <th className="p-3 font-medium">Report Reference Interval</th>
                      <th className="p-3 font-medium">Status</th>
                      <th className="p-3 font-medium">Source Page</th>
                      <th className="p-3 font-medium">Confidence</th>
                      <th className="p-3 font-medium">Human Verification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-900/50">
                    {aiExtractedData.laboratories.map((lab, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        <td className="p-3 font-medium text-slate-200">
                          {lab.test_name}
                        </td>
                        <td className="p-3 font-mono text-cyan-300">
                          {lab.value !== null ? lab.value : lab.raw_value} {lab.unit || ''}
                        </td>
                        <td className="p-3 text-slate-300 font-mono">
                          {lab.reference_range_low !== null && lab.reference_range_high !== null ? (
                            <span className="text-slate-200 font-medium">
                              {lab.reference_range_low} – {lab.reference_range_high} {lab.unit || ''}
                            </span>
                          ) : (
                            <span className="text-slate-500 italic">Not in report (NULL)</span>
                          )}
                        </td>
                        <td className="p-3">
                          {typeof lab.reference_range_low === 'number' && 
                           typeof lab.reference_range_high === 'number' && 
                           typeof lab.value === 'number' ? (
                            lab.value < lab.reference_range_low ? (
                              <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-950 text-amber-300 border border-amber-500/40">LOW</span>
                            ) : lab.value > lab.reference_range_high ? (
                              <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-950 text-rose-300 border border-rose-500/40">HIGH</span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40">NORMAL</span>
                            )
                          ) : (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-400">UNKNOWN</span>
                          )}
                        </td>
                        <td className="p-3 text-slate-400 font-mono">Page {lab.source_page}</td>
                        <td className="p-3 font-mono text-slate-300">{(lab.confidence * 100).toFixed(0)}%</td>
                        <td className="p-3">
                          {lab.requires_human_verification ? (
                            <span className="px-2 py-0.5 rounded-full text-[11px] bg-amber-950 text-amber-300 border border-amber-500/40 font-medium">
                              Needs Human Review
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[11px] bg-emerald-950 text-emerald-400 border border-emerald-500/30">
                              High Confidence
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </GlassCard>
      )}

      {/* PDF / File Streaming Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-4xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-950/80">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-semibold text-white truncate max-w-md">
                  {previewDoc.original_name}
                </h3>
              </div>
              <button
                onClick={() => setPreviewDoc(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 bg-slate-950 p-2 overflow-hidden flex items-center justify-center">
              {previewDoc.file_type === 'application/pdf' ? (
                <iframe
                  src={documentService.getDocumentFileUrl(previewDoc.id)}
                  title={previewDoc.original_name}
                  className="w-full h-full rounded border border-slate-800"
                />
              ) : (
                <img
                  src={documentService.getDocumentFileUrl(previewDoc.id)}
                  alt={previewDoc.original_name}
                  className="max-h-full max-w-full object-contain rounded border border-slate-800"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
