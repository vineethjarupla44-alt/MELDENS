// MedLens Core Type Definitions (Phase 2 Expanded)

export type ProvenanceSource = 
  | 'PATIENT_INPUT' 
  | 'DOCUMENT_EXTRACTION' 
  | 'AI_GENERATED' 
  | 'HUMAN_VERIFIED';

export type VerificationStatus = 
  | 'UNVERIFIED' 
  | 'VERIFIED' 
  | 'DISPUTED' 
  | 'REJECTED';

export type LabStatus = 
  | 'NORMAL' 
  | 'LOW' 
  | 'HIGH' 
  | 'UNKNOWN';

export type ConflictCategory = 
  | 'ALLERGY' 
  | 'MEDICATION' 
  | 'LAB_RESULT' 
  | 'DEMOGRAPHIC' 
  | 'OTHER';

export type ConflictStatus = 
  | 'UNRESOLVED' 
  | 'RESOLVED' 
  | 'DISMISSED';

export interface PatientProfile {
  id: string;
  patient_id: string;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  preferred_language: string;
  insurance_provider?: string | null;
  baseline_notes?: string | null;
  symptoms?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Patient {
  id: string;
  mrn?: string | null;
  first_name: string;
  last_name: string;
  date_of_birth?: string | null;
  gender?: string | null;
  blood_type?: string | null;
  profile?: PatientProfile | null;
  created_at: string;
  updated_at: string;
}

export interface PatientDetailResponse extends Patient {
  documents?: MedicalDocument[];
  lab_results?: LabResult[];
  medications?: Medication[];
  conditions?: Condition[];
  allergies?: Allergy[];
  observations?: Observation[];
}

export type DocumentStatus = 
  | 'UPLOADED' 
  | 'PROCESSING' 
  | 'PROCESSED' 
  | 'FAILED' 
  | 'NEEDS_REVIEW';

export type PageExtractionStatus = 
  | 'PENDING' 
  | 'SUCCESS' 
  | 'OCR_REQUIRED' 
  | 'EMPTY' 
  | 'FAILED';

export interface DocumentPage {
  id: string;
  document_id: string;
  page_number: number;
  extracted_text?: string | null;
  ocr_applied: boolean;
  confidence_score?: number | null;
  width?: number | null;
  height?: number | null;
  image_path?: string | null;
  extraction_status?: PageExtractionStatus | string;
  created_at: string;
}

export interface MedicalDocument {
  id: string;
  patient_id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  processing_status: DocumentStatus;
  raw_text?: string | null;
  page_count: number;
  checksum?: string | null;
  pages?: DocumentPage[];
}

export interface ExtractedPageResult {
  page_number: number;
  extracted_text?: string | null;
  extraction_status: PageExtractionStatus | string;
}

export interface DocumentTextExtractionResponse {
  document_id: string;
  pages: ExtractedPageResult[];
}

export interface ExtractedLabItem {
  test_name: string;
  raw_value?: string | null;
  value?: number | null;
  unit?: string | null;
  reference_range_low?: number | null;
  reference_range_high?: number | null;
  reference_range_text?: string | null;
  observation?: string | null;
  report_date?: string | null;
  source_page: number;
  confidence: number;
  source_snippet?: string | null;
  requires_human_verification: boolean;
}

export interface ExtractedMedicationItem {
  medication_name: string;
  dosage?: string | null;
  frequency?: string | null;
  route?: string | null;
  source_page: number;
  confidence: number;
  source_snippet?: string | null;
  requires_human_verification: boolean;
}

export interface ExtractedConditionItem {
  condition_name: string;
  onset_date?: string | null;
  source_page: number;
  confidence: number;
  source_snippet?: string | null;
  requires_human_verification: boolean;
}

export interface ExtractedAllergyItem {
  allergen: string;
  reaction?: string | null;
  severity?: string | null;
  source_page: number;
  confidence: number;
  source_snippet?: string | null;
  requires_human_verification: boolean;
}

export interface ExtractedPatientInfo {
  age?: number | null;
  sex?: string | null;
  symptoms: string[];
  conditions: ExtractedConditionItem[];
  allergies: ExtractedAllergyItem[];
  medications: ExtractedMedicationItem[];
  confidence: number;
}

export interface ExtractedDocumentData {
  document_id: string;
  patient_info: ExtractedPatientInfo;
  laboratories: ExtractedLabItem[];
  extraction_notes?: string | null;
  overall_confidence: number;
  has_unverified_items: boolean;
  processed_pages: number[];
}


export interface LabResult {
  id: string;
  patient_id: string;
  document_id?: string | null;
  page_id?: string | null;
  test_name: string;
  raw_value?: string | null;
  value?: number | null;
  unit?: string | null;
  
  // Strictly report-derived bounds (NULL allowed, NEVER auto-populated)
  reference_range_low?: number | null;
  reference_range_high?: number | null;
  reference_range_text?: string | null;
  status: LabStatus;
  report_date?: string | null;

  // Provenance
  provenance_source: ProvenanceSource;
  source_document?: string | null;
  source_page?: number | null;
  confidence?: number | null;
  source_snippet?: string | null;
  verification_status: VerificationStatus;
  verified_by?: string | null;
  verified_at?: string | null;
  created_at: string;
}

export interface Medication {
  id: string;
  patient_id: string;
  document_id?: string | null;
  page_id?: string | null;
  medication_name: string;
  dosage?: string | null;
  frequency?: string | null;
  route?: string | null;
  clinical_status: string;
  prescribed_date?: string | null;
  raw_text?: string | null;

  // Provenance
  provenance_source: ProvenanceSource;
  source_document?: string | null;
  source_page?: number | null;
  confidence?: number | null;
  source_snippet?: string | null;
  verification_status: VerificationStatus;
  verified_by?: string | null;
  verified_at?: string | null;
  created_at: string;
}

export interface Condition {
  id: string;
  patient_id: string;
  document_id?: string | null;
  page_id?: string | null;
  condition_name: string;
  icd10_code?: string | null;
  onset_date?: string | null;
  clinical_status: string;
  raw_text?: string | null;

  // Provenance
  provenance_source: ProvenanceSource;
  source_document?: string | null;
  source_page?: number | null;
  confidence?: number | null;
  source_snippet?: string | null;
  verification_status: VerificationStatus;
  verified_by?: string | null;
  verified_at?: string | null;
  created_at: string;
}

export interface Allergy {
  id: string;
  patient_id: string;
  document_id?: string | null;
  page_id?: string | null;
  allergen: string;
  reaction?: string | null;
  severity?: string | null;
  raw_text?: string | null;

  // Provenance
  provenance_source: ProvenanceSource;
  source_document?: string | null;
  source_page?: number | null;
  confidence?: number | null;
  source_snippet?: string | null;
  verification_status: VerificationStatus;
  verified_by?: string | null;
  verified_at?: string | null;
  created_at: string;
}

export interface Observation {
  id: string;
  patient_id: string;
  document_id?: string | null;
  page_id?: string | null;
  observation_type: string;
  observation_name: string;
  numeric_value?: number | null;
  string_value?: string | null;
  unit?: string | null;
  observation_date?: string | null;

  // Provenance
  provenance_source: ProvenanceSource;
  source_document?: string | null;
  source_page?: number | null;
  confidence?: number | null;
  source_snippet?: string | null;
  verification_status: VerificationStatus;
  verified_by?: string | null;
  verified_at?: string | null;
  created_at: string;
}

export interface ConflictRecord {
  id: string;
  patient_id: string;
  category: ConflictCategory;
  field_name: string;
  
  source_a_type: string;
  source_a_document?: string | null;
  source_a_page?: number | null;
  source_a_value: string;
  
  source_b_type: string;
  source_b_document?: string | null;
  source_b_page?: number | null;
  source_b_value: string;
  
  description: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: ConflictStatus;
  resolution_notes?: string | null;
  resolved_by?: string | null;
  created_at: string;
  resolved_at?: string | null;
}

export interface VerificationRecord {
  id: string;
  entity_type: string;
  entity_id: string;
  reviewer_id: string;
  reviewer_name: string;
  reviewer_role: string;
  status: VerificationStatus;
  notes?: string | null;
  signed_at: string;
}


export interface TimelineEvent {
  id: string;
  patient_id: string;
  event_date: string;
  event_type: string;
  title: string;
  description?: string | null;
  entity_type?: string | null;
  entity_id?: string | null;
  source_document?: string | null;
  source_page?: number | null;
  importance: 'ROUTINE' | 'SIGNIFICANT' | 'CRITICAL';
  created_at: string;
}

export interface AuditLog {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id: string;
  actor_name: string;
  previous_state?: string | null;
  new_state?: string | null;
  change_reason?: string | null;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  environment: string;
  database: string;
  system_capabilities?: Record<string, string>;
}

export interface ConditionIntakeItem {
  condition_name: string;
  onset_date?: string;
  clinical_status?: string;
}

export interface AllergyIntakeItem {
  allergen: string;
  reaction?: string;
  severity?: 'MILD' | 'MODERATE' | 'SEVERE';
}

export interface MedicationIntakeItem {
  medication_name: string;
  dosage?: string;
  frequency?: string;
  route?: string;
}

export interface PatientIntakeSubmission {
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  blood_type?: string;
  mrn?: string;
  symptoms?: string;
  existing_conditions?: ConditionIntakeItem[];
  allergies?: AllergyIntakeItem[];
  current_medications?: MedicationIntakeItem[];
  additional_notes?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  preferred_language?: string;
}

export interface PatientIntakeResponse {
  patient_id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  blood_type?: string | null;
  symptoms?: string | null;
  additional_notes?: string | null;
  provenance_source: string;
  conditions_count: number;
  allergies_count: number;
  medications_count: number;
  created_at: string;
  updated_at: string;
  audit_id: string;
}

export interface ClinicalProvenanceDetail {
  entity_type: string;
  entity_id: string;
  item_name: string;
  item_value?: string | null;
  raw_value?: string | null;
  source_type: ProvenanceSource;
  method: string;
  document_id?: string | null;
  filename?: string | null;
  page_number?: number | null;
  extraction_timestamp?: string | null;
  confidence?: number | null;
  verification_status: VerificationStatus;
  verified_by?: string | null;
  verified_at?: string | null;
  source_snippet?: string | null;
  document_stream_url?: string | null;
}

export interface VerificationQueueItem {
  id: string;
  entity_type: 'lab' | 'medication' | 'condition' | 'allergy' | 'observation' | string;
  patient_id: string;
  patient_name: string;
  item_name: string;
  extracted_value: string;
  original_value?: string | null;
  editable_value: string;
  corrected_value?: string | null;
  source_document?: string | null;
  page_number?: number | null;
  confidence?: number | null;
  reasons: string[];
  verification_status: string;
  verified_by?: string | null;
  verified_at?: string | null;
  source_snippet?: string | null;
  document_id?: string | null;
  created_at: string;
}

export interface VerificationActionPayload {
  entity_type: string;
  entity_id: string;
  action: 'ACCEPT' | 'EDIT' | 'REJECT';
  corrected_value?: string | null;
  reviewer_name?: string;
  reviewer_role?: string;
  notes?: string;
}

export interface VerificationActionResponse {
  status: string;
  entity_type: string;
  entity_id: string;
  action: string;
  original_value?: string | null;
  corrected_value?: string | null;
  verification_status: string;
  verified_by: string;
  verified_at: string;
  audit_id?: string;
}

export interface ClinicalSummarySections {
  record_overview: string;
  recently_documented: string;
  laboratory_values: string;
  historical_changes: string;
  potential_conflicts: string;
  missing_information: string;
  verification_required: string;
}

export interface SummaryProvenanceSources {
  document_ids: string[];
  lab_ids: string[];
  medication_ids: string[];
  condition_ids: string[];
  allergy_ids: string[];
  observation_ids: string[];
  conflict_ids: string[];
}

export interface ClinicalSummary {
  id: string;
  patient_id: string;
  summary_text: string;
  sections?: ClinicalSummarySections | null;
  structured_provenance_sources?: SummaryProvenanceSources | null;
  key_findings?: string[];
  disclaimer: string;
  model_version: string;
  is_ai_generated: boolean;
  is_verified: boolean;
  created_at: string;
}
