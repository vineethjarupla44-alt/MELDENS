import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { GlassCard } from '../components/common/GlassCard';

import { ProvenanceBadge } from '../components/common/ProvenanceBadge';
import { LabGauge2D } from '../components/clinical/LabGauge2D';
import { ProvenanceDetails } from '../components/clinical/ProvenanceDetails';
import { ClinicalSourceModal } from '../components/clinical/ClinicalSourceModal';
import { patientService } from '../services/patientService';
import { documentService } from '../services/documentService';
import type { 
  Patient, 
  LabResult, 
  Medication, 
  Condition, 
  Allergy, 
  Observation, 
  TimelineEvent,
  MedicalDocument,
  ClinicalProvenanceDetail,
} from '../types';
import { PatientSummaryCard } from '../components/clinical/PatientSummaryCard';
import { 
  User, 
  Activity, 
  ShieldAlert, 
  AlertTriangle, 
  Pill, 
  FlaskConical, 
  FileText, 
  Clock, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle,
  ExternalLink,
  Info,
  Sparkles,
  Layers
} from 'lucide-react';
import { ClinicalGraph3D } from '../components/clinical/ClinicalGraph3D';


export const MedicalRecordPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [patientData, setPatientData] = useState<any>(null);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [documents, setDocuments] = useState<MedicalDocument[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeSection, setActiveSection] = useState<string>('labs');

  // Provenance Details Panel state
  const [inspectingProvenance, setInspectingProvenance] = useState<ClinicalProvenanceDetail | null>(null);
  const [isProvenancePanelOpen, setIsProvenancePanelOpen] = useState<boolean>(false);

  // Document Citation Modal state
  const [citationModal, setCitationModal] = useState<{
    isOpen: boolean;
    documentId?: string | null;
    documentName?: string | null;
    pageNumber?: number | null;
    sourceSnippet?: string | null;
    provenanceSource?: any;
    confidence?: number | null;
    verificationStatus?: string | null;
    testOrEntityName?: string | null;
  }>({ isOpen: false });

  // 1. Initial Load of Patients
  useEffect(() => {
    async function loadPatients() {
      try {
        setLoading(true);
        const list = await patientService.getPatients();
        setPatients(list);
        const storedId = localStorage.getItem('medlens_selected_patient');
        if (storedId && list.some(p => p.id === storedId)) {
          setSelectedPatientId(storedId);
        } else if (list.length > 0) {
          setSelectedPatientId(list[0].id);
        }
      } catch (err) {
        console.error('Failed to load patients', err);
      } finally {
        setLoading(false);
      }
    }
    loadPatients();
  }, []);

  // 2. Load Patient Clinical Record on Patient Change
  useEffect(() => {
    if (!selectedPatientId) return;
    localStorage.setItem('medlens_selected_patient', selectedPatientId);

    async function loadClinicalRecord() {
      try {
        setLoading(true);
        const [detail, docs, timeline] = await Promise.all([
          patientService.getPatientById(selectedPatientId),
          documentService.getPatientDocuments(selectedPatientId),
          patientService.getPatientTimeline(selectedPatientId).catch(() => []),
        ]);
        setPatientData(detail);
        setDocuments(docs);
        setTimelineEvents(timeline);
      } catch (err) {
        console.error('Failed to load clinical record', err);
      } finally {
        setLoading(false);
      }
    }
    loadClinicalRecord();
  }, [selectedPatientId]);

  // Handler: Inspect item provenance
  const handleInspectProvenance = async (entityType: string, entityId: string, fallbackItem?: any) => {
    try {
      const detail = await patientService.getProvenanceDetails(entityType, entityId);
      setInspectingProvenance(detail);
      setIsProvenancePanelOpen(true);
    } catch (err) {
      // Fallback if provenance endpoint cannot find record
      if (fallbackItem) {
        const fallbackDetail: ClinicalProvenanceDetail = {
          entity_type: entityType,
          entity_id: entityId,
          item_name: fallbackItem.test_name || fallbackItem.medication_name || fallbackItem.condition_name || fallbackItem.allergen || fallbackItem.observation_name || 'Item',
          item_value: fallbackItem.value !== undefined ? `${fallbackItem.value} ${fallbackItem.unit || ''}` : fallbackItem.dosage || fallbackItem.clinical_status,
          raw_value: fallbackItem.raw_value || fallbackItem.raw_text,
          source_type: fallbackItem.provenance_source || 'DOCUMENT_EXTRACTION',
          method: fallbackItem.provenance_source === 'PATIENT_INPUT' ? 'Patient Input' : 'AI Extraction',
          document_id: fallbackItem.document_id,
          filename: fallbackItem.source_document,
          page_number: fallbackItem.source_page || 1,
          extraction_timestamp: fallbackItem.created_at,
          confidence: fallbackItem.confidence,
          verification_status: fallbackItem.verification_status || 'UNVERIFIED',
          verified_by: fallbackItem.verified_by,
          source_snippet: fallbackItem.source_snippet,
          document_stream_url: fallbackItem.document_id ? documentService.getDocumentFileUrl(fallbackItem.document_id) : undefined,
        };
        setInspectingProvenance(fallbackDetail);
        setIsProvenancePanelOpen(true);
      }
    }
  };

  // Handler: Open source citation in document viewer
  const handleOpenSourceDocument = (docId: string, pageNum?: number, itemContext?: any) => {
    const doc = documents.find(d => d.id === docId);
    setCitationModal({
      isOpen: true,
      documentId: docId,
      documentName: doc?.original_name || doc?.filename || itemContext?.filename || 'Clinical Report',
      pageNumber: pageNum || itemContext?.page_number || 1,
      sourceSnippet: itemContext?.source_snippet,
      provenanceSource: itemContext?.source_type || itemContext?.provenance_source || 'DOCUMENT_EXTRACTION',
      confidence: itemContext?.confidence,
      verificationStatus: itemContext?.verification_status,
      testOrEntityName: itemContext?.item_name || itemContext?.test_name || 'Document Citation',
    });
  };

  // Handler: Human clinician verification
  const handleVerifyClinicalItem = async (entityType: string, entityId: string, newStatus: string) => {
    try {
      await patientService.verifyClinicalItem({
        entity_type: entityType,
        entity_id: entityId,
        verification_status: newStatus,
        verified_by: 'Dr. Sarah Lin, MD',
        verification_notes: 'Verified against source document in MedLens Record Review',
      });

      // Reload patient details to update UI state
      const updated = await patientService.getPatientById(selectedPatientId);
      setPatientData(updated);

      if (inspectingProvenance && inspectingProvenance.entity_id === entityId) {
        setInspectingProvenance({
          ...inspectingProvenance,
          verification_status: newStatus as any,
          verified_by: 'Dr. Sarah Lin, MD',
          verified_at: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.error('Failed to verify item', err);
    }
  };

  const labs: LabResult[] = patientData?.lab_results || [];
  const meds: Medication[] = patientData?.medications || [];
  const conditions: Condition[] = patientData?.conditions || [];
  const allergies: Allergy[] = patientData?.allergies || [];
  const observations: Observation[] = patientData?.observations || [];

  // Metrics for Verification Status section
  const allClinicalItems = [...labs, ...meds, ...conditions, ...allergies, ...observations];
  const verifiedCount = allClinicalItems.filter(i => i.verification_status === 'VERIFIED').length;
  const unverifiedCount = allClinicalItems.length - verifiedCount;

  const sections = [
    { id: 'ai-summary', label: 'AI Summary', icon: Sparkles, count: 'AI' },
    { id: '3d-graph', label: '3D Clinical Graph', icon: Layers, count: '3D' },
    { id: 'patient-info', label: '1. Patient Info', icon: User, count: null },
    { id: 'symptoms', label: '2. Symptoms', icon: Activity, count: patientData?.profile?.symptoms ? 1 : 0 },
    { id: 'conditions', label: '3. Conditions', icon: ShieldAlert, count: conditions.length },
    { id: 'allergies', label: '4. Allergies', icon: AlertTriangle, count: allergies.length },
    { id: 'medications', label: '5. Medications', icon: Pill, count: meds.length },
    { id: 'labs', label: '6. Laboratory Results', icon: FlaskConical, count: labs.length },
    { id: 'observations', label: '7. Observations', icon: Activity, count: observations.length },
    { id: 'documents', label: '8. Documents', icon: FileText, count: documents.length },
    { id: 'timeline', label: '9. Timeline', icon: Clock, count: timelineEvents.length },
    { id: 'verification', label: '10. Verification Status', icon: ShieldCheck, count: unverifiedCount > 0 ? `${unverifiedCount} Pending` : 'All Verified' },
  ];

  if (loading && !patientData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-3">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-slate-400 font-medium">Loading clinical intelligence...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-20">

      
      {/* Page Header & Patient Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Structured Medical Record</h1>
            <span className="rounded-full bg-cyan-950 px-2.5 py-0.5 text-[11px] font-mono font-medium text-cyan-300 border border-cyan-500/30">
              Deterministic & Audited
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Standardized clinical intelligence organized across 10 structured sections with immutable source provenance.
          </p>
        </div>

        {/* Patient Selection Dropdown */}
        <div className="flex items-center gap-3 bg-slate-900/80 p-2 rounded-xl border border-slate-800">
          <User className="w-4 h-4 text-cyan-400 ml-1" />
          <span className="text-xs text-slate-400 font-medium">Active Patient:</span>
          <select
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
            className="bg-slate-950 text-white text-xs rounded-lg px-3 py-1.5 border border-slate-700 focus:outline-none focus:border-cyan-500"
          >
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.last_name}, {p.first_name} {p.mrn ? `(${p.mrn})` : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 10-Section Navigation Bar (Jump Tabs) */}
      <div className="flex items-center gap-1 overflow-x-auto pb-2 border-b border-slate-800/80 scrollbar-thin">
        {sections.map((sec) => {
          const Icon = sec.icon;
          const isActive = activeSection === sec.id;
          return (
            <button
              key={sec.id}
              onClick={() => {
                setActiveSection(sec.id);
                const el = document.getElementById(sec.id);
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-[0_0_10px_rgba(6,182,212,0.15)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{sec.label}</span>
              {sec.count !== null && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                  typeof sec.count === 'string' && sec.count.includes('Pending')
                    ? 'bg-amber-950/80 text-amber-400 border border-amber-500/30'
                    : 'bg-slate-800 text-slate-400'
                }`}>
                  {sec.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Clinical Warning / Non-Diagnostic Notice */}
      <div className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-cyan-400 flex-shrink-0" />
          <span>
            <strong>Clinical Safety Mandate:</strong> MedLens strictly reflects report-derived facts. Missing reference ranges are designated as <code className="text-slate-300">Reference range not provided</code> and are never automatically generated.
          </span>
        </div>
        <span className="text-[11px] text-slate-500 hidden md:inline">
          Click any badge or source to inspect origin
        </span>
      </div>

      {/* AI Clinical Summary Module */}
      <section id="ai-summary" className="scroll-mt-24">
        {selectedPatientId && (
          <PatientSummaryCard
            patientId={selectedPatientId}
            patientName={patientData ? `${patientData.first_name} ${patientData.last_name}` : undefined}
            onOpenSourceDocument={(docId) => handleOpenSourceDocument(docId)}
          />
        )}
      </section>

      {/* 3D Clinical Information Graph Module */}
      <section id="3d-graph" className="scroll-mt-24">
        {patientData && (
          <ClinicalGraph3D
            patientName={`${patientData.first_name} ${patientData.last_name}`}
            patientMrn={patientData.mrn}
            counts={{
              documents: documents.length,
              labs: labs.length,
              medications: meds.length,
              conditions: conditions.length,
              allergies: allergies.length,
              timeline: timelineEvents.length,
              conflicts: 2,
              summary: 'AI'
            }}
            onSelectNode={(nodeId) => {
              const el = document.getElementById(nodeId);
              if (el) {
                el.scrollIntoView({ behavior: 'smooth' });
              }
            }}
            height="500px"
          />
        )}
      </section>

      {/* SECTION 1: Patient Information */}
      <section id="patient-info" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <User className="w-4 h-4 text-cyan-400" />
            1. Patient Information
          </h2>
          <ProvenanceBadge source="PATIENT_INPUT" />
        </div>

        <GlassCard className="p-5">
          {patientData ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Full Name</span>
                <span className="text-sm font-semibold text-white">
                  {patientData.first_name} {patientData.last_name}
                </span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">MRN</span>
                <span className="text-sm font-mono text-cyan-400">{patientData.mrn || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Date of Birth</span>
                <span className="text-sm text-slate-200">{patientData.date_of_birth || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Gender</span>
                <span className="text-sm text-slate-200">{patientData.gender || 'N/A'}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Blood Type</span>
                <span className="text-sm font-mono text-rose-400 font-semibold">{patientData.blood_type || 'Unknown'}</span>
              </div>
              <div>
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Language</span>
                <span className="text-sm text-slate-200">{patientData.profile?.preferred_language || 'English'}</span>
              </div>

              {patientData.profile?.emergency_contact_name && (
                <div className="col-span-2 sm:col-span-3 pt-3 border-t border-slate-800/80">
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Emergency Contact</span>
                  <span className="text-xs text-slate-300">
                    {patientData.profile.emergency_contact_name} ({patientData.profile.emergency_contact_phone || 'No phone'})
                  </span>
                </div>
              )}
              {patientData.profile?.insurance_provider && (
                <div className="col-span-2 sm:col-span-3 pt-3 border-t border-slate-800/80">
                  <span className="text-[11px] text-slate-500 uppercase tracking-wider block">Insurance</span>
                  <span className="text-xs text-slate-300">{patientData.profile.insurance_provider}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="text-xs text-slate-500">Loading patient profile...</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 2: Symptoms */}
      <section id="symptoms" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            2. Symptoms
          </h2>
          <span className="text-xs text-slate-500">Patient-Reported & Clinical Ingestion</span>
        </div>

        <GlassCard className="p-5">
          {patientData?.profile?.symptoms ? (
            <div className="flex flex-wrap gap-2 items-center">
              {patientData.profile.symptoms.split(',').map((s: string, idx: number) => (
                <div 
                  key={idx}
                  className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                  <span className="font-medium">{s.trim()}</span>
                  <ProvenanceBadge source="PATIENT_INPUT" className="text-[10px]" />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">No acute symptoms reported during intake.</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 3: Existing Conditions */}
      <section id="conditions" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            3. Existing Conditions
          </h2>
          <span className="text-xs text-slate-500">{conditions.length} Documented</span>
        </div>

        <GlassCard className="overflow-hidden">
          {conditions.length > 0 ? (
            <div className="divide-y divide-slate-800">
              {conditions.map((cond) => (
                <div 
                  key={cond.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/40 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-white">{cond.condition_name}</span>
                      {cond.icd10_code && (
                        <span className="font-mono text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                          ICD-10: {cond.icd10_code}
                        </span>
                      )}
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-cyan-300 border border-slate-700">
                        {cond.clinical_status}
                      </span>
                    </div>
                    {cond.onset_date && (
                      <span className="text-xs text-slate-400 block mt-0.5">Onset: {cond.onset_date}</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <ProvenanceBadge 
                      source={cond.provenance_source}
                      documentName={cond.source_document}
                      pageNumber={cond.source_page}
                      confidence={cond.confidence}
                      showDetails={true}
                      onClick={() => handleInspectProvenance('condition', cond.id, cond)}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-5 text-xs text-slate-500 italic">No existing conditions recorded.</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 4: Allergies */}
      <section id="allergies" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            4. Allergies
          </h2>
          <span className="text-xs text-slate-500">{allergies.length} Recorded</span>
        </div>

        <GlassCard className="overflow-hidden">
          {allergies.length > 0 ? (
            <div className="divide-y divide-slate-800">
              {allergies.map((alg) => (
                <div 
                  key={alg.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/40 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-rose-300">{alg.allergen}</span>
                      {alg.severity && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-950/80 text-rose-300 border border-rose-500/40">
                          {alg.severity}
                        </span>
                      )}
                    </div>
                    {alg.reaction && (
                      <span className="text-xs text-slate-300 block mt-0.5">Reaction: {alg.reaction}</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <ProvenanceBadge 
                      source={alg.provenance_source}
                      documentName={alg.source_document}
                      pageNumber={alg.source_page}
                      confidence={alg.confidence}
                      showDetails={true}
                      onClick={() => handleInspectProvenance('allergy', alg.id, alg)}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-5 text-xs text-slate-500 italic">No documented drug or environmental allergies.</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 5: Medications */}
      <section id="medications" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Pill className="w-4 h-4 text-cyan-400" />
            5. Medications
          </h2>
          <span className="text-xs text-slate-500">{meds.length} Documented</span>
        </div>

        <GlassCard className="overflow-hidden">
          {meds.length > 0 ? (
            <div className="divide-y divide-slate-800">
              {meds.map((m) => (
                <div 
                  key={m.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/40 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-white">{m.medication_name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                        {m.clinical_status}
                      </span>
                    </div>
                    <div className="text-xs text-cyan-400 font-mono mt-0.5">
                      {[m.dosage, m.frequency, m.route ? `(${m.route})` : ''].filter(Boolean).join(' · ')}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <ProvenanceBadge 
                      source={m.provenance_source}
                      documentName={m.source_document}
                      pageNumber={m.source_page}
                      confidence={m.confidence}
                      showDetails={true}
                      onClick={() => handleInspectProvenance('medication', m.id, m)}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-5 text-xs text-slate-500 italic">No medications documented.</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 6: Laboratory Results (Core requirement with 2D Gauge and required columns) */}
      <section id="labs" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-cyan-400" />
              6. Laboratory Results
            </h2>
            <p className="text-xs text-slate-400">
              Deterministic validation of numeric tests against report-printed bounds.
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">{labs.length} Test Records</span>
        </div>

        <GlassCard className="overflow-hidden">
          {labs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400">
                    <th className="py-3 px-4 font-semibold">Test</th>
                    <th className="py-3 px-3 font-semibold">Value</th>
                    <th className="py-3 px-2 font-semibold">Unit</th>
                    <th className="py-3 px-4 font-semibold min-w-[220px]">Reference Range (2D Precision)</th>
                    <th className="py-3 px-3 font-semibold">Status</th>
                    <th className="py-3 px-3 font-semibold">Date</th>
                    <th className="py-3 px-4 font-semibold">Source</th>
                    <th className="py-3 px-3 font-semibold">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {labs.map((lab) => {
                    const statusColor = 
                      lab.status === 'LOW' ? 'bg-sky-950 text-sky-300 border-sky-500/40' :
                      lab.status === 'HIGH' ? 'bg-rose-950 text-rose-300 border-rose-500/40' :
                      lab.status === 'NORMAL' ? 'bg-emerald-950 text-emerald-300 border-emerald-500/40' :
                      'bg-slate-800 text-slate-400 border-slate-700';

                    return (
                      <tr 
                        key={lab.id} 
                        className="hover:bg-slate-800/30 transition-colors group cursor-pointer"
                        onClick={() => handleInspectProvenance('lab', lab.id, lab)}
                      >
                        {/* 1. Test Name */}
                        <td className="py-3 px-4 font-medium text-white group-hover:text-cyan-300 transition-colors">
                          {lab.test_name}
                        </td>

                        {/* 2. Value */}
                        <td className="py-3 px-3 font-mono font-bold text-slate-100">
                          {lab.value !== null && lab.value !== undefined ? lab.value : (lab.raw_value || 'N/A')}
                        </td>

                        {/* 3. Unit */}
                        <td className="py-3 px-2 text-slate-400 font-mono">
                          {lab.unit || '—'}
                        </td>

                        {/* 4. Reference Range with 2D Gauge */}
                        <td className="py-2.5 px-4" onClick={(e) => e.stopPropagation()}>
                          <LabGauge2D
                            value={lab.value}
                            low={lab.reference_range_low}
                            high={lab.reference_range_high}
                            unit={lab.unit}
                            status={lab.status}
                          />
                        </td>

                        {/* 5. Status */}
                        <td className="py-3 px-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${statusColor}`}>
                            {lab.status}
                          </span>
                        </td>

                        {/* 6. Date */}
                        <td className="py-3 px-3 text-slate-400 text-[11px] whitespace-nowrap">
                          {lab.report_date || '—'}
                        </td>

                        {/* 7. Source Citation Badge (Click opens ProvenanceDetails) */}
                        <td className="py-3 px-4" onClick={(e) => e.stopPropagation()}>
                          <ProvenanceBadge
                            source={lab.provenance_source}
                            documentName={lab.source_document}
                            pageNumber={lab.source_page}
                            confidence={lab.confidence}
                            showDetails={true}
                            onClick={() => handleInspectProvenance('lab', lab.id, lab)}
                          />
                        </td>

                        {/* 8. Confidence */}
                        <td className="py-3 px-3 font-mono text-slate-300">
                          {lab.confidence !== null && lab.confidence !== undefined ? (
                            <span className={`text-[11px] ${lab.confidence >= 0.9 ? 'text-emerald-400' : 'text-cyan-400'}`}>
                              {(lab.confidence * 100).toFixed(0)}%
                            </span>
                          ) : (
                            <span className="text-slate-500">—</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-500">
              No laboratory records found for this patient.
            </div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 7: Observations (Vitals / Findings) */}
      <section id="observations" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            7. Observations & Vitals
          </h2>
          <span className="text-xs text-slate-500">{observations.length} Findings</span>
        </div>

        <GlassCard className="p-5">
          {observations.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {observations.map((obs) => (
                <div 
                  key={obs.id}
                  className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col justify-between cursor-pointer hover:border-cyan-500/40 transition-all"
                  onClick={() => handleInspectProvenance('observation', obs.id, obs)}
                >
                  <div>
                    <div className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
                      {obs.observation_name || obs.observation_type}
                    </div>
                    <div className="text-lg font-mono font-bold text-white mt-0.5">
                      {obs.numeric_value !== null ? obs.numeric_value : obs.string_value} {obs.unit || ''}
                    </div>
                  </div>
                  <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between">
                    <ProvenanceBadge source={obs.provenance_source} className="text-[10px]" />
                    <span className="text-[10px] text-slate-500 font-mono">{obs.observation_date || 'Discharge'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">No vital observations recorded.</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 8: Documents */}
      <section id="documents" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            8. Ingested Documents
          </h2>
          <span className="text-xs text-slate-500">{documents.length} Files</span>
        </div>

        <GlassCard className="overflow-hidden">
          {documents.length > 0 ? (
            <div className="divide-y divide-slate-800">
              {documents.map((doc) => (
                <div 
                  key={doc.id}
                  className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-900/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="text-sm font-semibold text-white block">{doc.original_name || doc.filename}</span>
                      <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                        <span className="font-mono">{doc.page_count} {doc.page_count === 1 ? 'Page' : 'Pages'}</span>
                        <span>·</span>
                        <span>{(doc.file_size / 1024).toFixed(0)} KB</span>
                        <span>·</span>
                        <span className="text-cyan-400 font-mono">{doc.processing_status}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleOpenSourceDocument(doc.id, 1, { filename: doc.original_name })}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-medium transition-all"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      View Document Stream
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-5 text-xs text-slate-500 italic">No medical documents uploaded yet.</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 9: Timeline */}
      <section id="timeline" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            9. Historical Clinical Timeline
          </h2>
          <span className="text-xs text-slate-500">{timelineEvents.length} Events</span>
        </div>

        <GlassCard className="p-5">
          {timelineEvents.length > 0 ? (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
              {timelineEvents.map((evt) => (
                <div key={evt.id} className="relative group">
                  <div className="absolute -left-[23px] top-1 w-3 h-3 rounded-full bg-cyan-400 border-2 border-slate-950 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-cyan-400">{evt.event_date}</span>
                      <span className="text-xs font-semibold text-white">{evt.title}</span>
                      <span className="text-[10px] px-2 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">
                        {evt.event_type}
                      </span>
                    </div>
                    {evt.description && (
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{evt.description}</p>
                    )}
                    {evt.source_document && (
                      <div className="mt-1 text-[11px] text-slate-500 flex items-center gap-1.5">
                        <FileText className="w-3 h-3" />
                        <span>Source: {evt.source_document} {evt.source_page ? `(Page ${evt.source_page})` : ''}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic">No timeline events synthesized.</div>
          )}
        </GlassCard>
      </section>

      {/* SECTION 10: Verification Status */}
      <section id="verification" className="scroll-mt-24 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            10. Verification Status
          </h2>
          <span className="text-xs text-slate-500">Human Clinician Audit Oversight</span>
        </div>

        <GlassCard className="p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold block">
                Total Extracted Entities
              </span>
              <span className="text-2xl font-mono font-bold text-white mt-1 block">
                {allClinicalItems.length}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-500/20">
              <span className="text-[11px] uppercase tracking-wider text-emerald-400 font-semibold block flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Human Verified
              </span>
              <span className="text-2xl font-mono font-bold text-emerald-400 mt-1 block">
                {verifiedCount}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-amber-500/20">
              <span className="text-[11px] uppercase tracking-wider text-amber-400 font-semibold block flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" /> Pending Clinician Review
              </span>
              <span className="text-2xl font-mono font-bold text-amber-400 mt-1 block">
                {unverifiedCount}
              </span>
            </div>
          </div>

          <div className="p-3 bg-slate-900/40 rounded-xl border border-slate-800 text-xs text-slate-400 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-cyan-400 text-[11px]">
                Audit Trail Active:
              </span>
              <span>All manual reviews and confirmations are recorded in the MedLens immutable audit log.</span>
            </div>
            {unverifiedCount > 0 && (
              <Link
                to="/verification"
                className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-semibold transition-all whitespace-nowrap"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                Open Verification Queue ({unverifiedCount} Items) &rarr;
              </Link>
            )}
          </div>
        </GlassCard>
      </section>


      {/* Slide-Over / Modal: ProvenanceDetails Inspector Panel */}
      <ProvenanceDetails
        isOpen={isProvenancePanelOpen}
        onClose={() => setIsProvenancePanelOpen(false)}
        provenance={inspectingProvenance}
        onOpenDocument={(docId, pageNum) => {
          setIsProvenancePanelOpen(false);
          handleOpenSourceDocument(docId, pageNum, inspectingProvenance);
        }}
        onVerify={handleVerifyClinicalItem}
      />

      {/* Modal: Document Stream Citation Preview */}
      <ClinicalSourceModal
        isOpen={citationModal.isOpen}
        onClose={() => setCitationModal({ ...citationModal, isOpen: false })}
        documentId={citationModal.documentId}
        documentName={citationModal.documentName}
        pageNumber={citationModal.pageNumber}
        sourceSnippet={citationModal.sourceSnippet}
        provenanceSource={citationModal.provenanceSource}
        confidence={citationModal.confidence}
        verificationStatus={citationModal.verificationStatus}
        testOrEntityName={citationModal.testOrEntityName}
      />

    </div>
  );
};
