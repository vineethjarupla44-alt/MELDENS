"""
MedLens Synthetic Demonstration Dataset Seeder
Creates 6 completely fictitious, realistic clinical patient records to exercise:
1. Normal laboratory result
2. Low result with source-provided reference range
3. High result with source-provided reference range
4. Missing reference range (UNKNOWN / "Reference range not provided")
5. Conflicting allergy information
6. Conflicting medication information
7. Historical laboratory value change
8. Low-confidence extraction (< 0.90 requiring verification)
9. Missing medication dosage
10. Duplicate information

Clearly labeled: "SYNTHETIC DEMONSTRATION DATA"
Contains ZERO Real Protected Health Information (PHI).
Strictly non-diagnostic with zero treatment recommendations.
"""
import os
import uuid
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.core.config import settings
from app.db.session import SessionLocal, engine, Base
from app.db.models import (
    Patient,
    PatientProfile,
    Document,
    DocumentPage,
    LabResult,
    Medication,
    Condition,
    Allergy,
    Observation,
    ConflictRecord,
    TimelineEvent,
    AuditLog,
    ProvenanceRecord,
    ProvenanceSourceEnum,
    VerificationStatusEnum,
    LabStatusEnum,
    ConflictStatusEnum,
    ConflictCategoryEnum,
)


def create_synthetic_pdf(filepath: str, title: str, pages_content: list[str]) -> tuple[int, str]:
    """Generates an authentic PDF on disk for document preview/download."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    c = canvas.Canvas(filepath, pagesize=letter)
    for p_idx, content in enumerate(pages_content):
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.2, 0.4, 0.6)
        c.drawString(50, 750, "MEDLENS CLINICAL INTELLIGENCE — SYNTHETIC DEMONSTRATION DATA")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 730, title)
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(50, 715, "FICTIONAL DEMO RECORD — CONTAINS ZERO REAL PROTECTED HEALTH INFORMATION (PHI)")
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(50, 705, 550, 705)

        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("Helvetica", 10)
        y = 680
        for line in content.splitlines():
            if y < 60:
                c.showPage()
                y = 750
            c.drawString(50, y, line)
            y -= 16

        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(50, 35, f"Page {p_idx + 1} of {len(pages_content)} · SYNTHETIC DEMONSTRATION DATA · NON-DIAGNOSTIC")
        c.showPage()
    c.save()

    file_size = os.path.getsize(filepath)
    with open(filepath, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    return file_size, checksum


def seed_synthetic_data(db: Session) -> Patient:
    """Idempotently seeds 6 realistic synthetic patients covering all 10 deliberate test cases."""

    # =========================================================================
    # PATIENT 1: Eleanor Vance (Primary Demo Case)
    # Covers: Low result with range (Hemoglobin), Normal result (Glucose),
    # Missing range (Ferritin), Conflicting allergy (Penicillin vs NKDA),
    # Conflicting medication (Metformin 500mg vs 1000mg BID)
    # =========================================================================
    p1 = db.query(Patient).filter(Patient.mrn == "MED-SYNTH-8492").first()
    if not p1:
        p1 = Patient(
            id=str(uuid.uuid4()),
            mrn="MED-SYNTH-8492",
            first_name="Eleanor",
            last_name="Vance",
            date_of_birth="1968-04-12",
            gender="Female",
            blood_type="A+",
        )
        db.add(p1)
        db.flush()

        p1_profile = PatientProfile(
            patient_id=p1.id,
            emergency_contact_name="Thomas Vance (Spouse)",
            emergency_contact_phone="+1 (555) 234-8901",
            preferred_language="English",
            insurance_provider="Aetna Health Plan #SYNTH-9941",
            baseline_notes="SYNTHETIC DEMONSTRATION DATA: Patient presents with fragmented records between primary care and recent admission.",
            symptoms="Generalized fatigue, mild lightheadedness upon standing, dry mouth.",
        )
        db.add(p1_profile)

        # PDF 1: Intake
        p1_dir = os.path.join(settings.UPLOAD_DIR, p1.id)
        doc1_name = "eleanor_vance_intake_questionnaire.pdf"
        doc1_path = os.path.join(p1_dir, doc1_name)
        doc1_content = [
            "PATIENT SELF-ASSESSMENT INTAKE FORM\n"
            "Patient: Eleanor Vance | DOB: 1968-04-12 | MRN: MED-SYNTH-8492\n"
            "Reported Allergies: Penicillin (causes rash and facial hives)\n"
            "Current Medications: Metformin 500mg daily by mouth with dinner\n"
            "Past Medical History: Type 2 Diabetes diagnosed 2020\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz1, ck1 = create_synthetic_pdf(doc1_path, "Patient Intake Questionnaire", doc1_content)
        d1 = Document(
            id=str(uuid.uuid4()),
            patient_id=p1.id,
            filename=doc1_name,
            original_name="Patient_Intake_Form_2026.pdf",
            file_type="application/pdf",
            file_size=sz1,
            checksum=ck1,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=doc1_content[0],
        )
        db.add(d1)
        db.flush()
        db.add(DocumentPage(document_id=d1.id, page_number=1, extracted_text=doc1_content[0], confidence_score=0.98))

        # PDF 2: Discharge Summary (2 pages)
        doc2_name = "st_jude_discharge_summary_aug2026.pdf"
        doc2_path = os.path.join(p1_dir, doc2_name)
        doc2_p1 = (
            "ST. JUDE MEDICAL CENTER - INPATIENT DISCHARGE SUMMARY\n"
            "Admission Date: 2026-08-10 | Discharge Date: 2026-08-14\n"
            "Patient: Vance, Eleanor | MRN: MED-SYNTH-8492\n"
            "Allergies Noted on Chart: No Known Drug Allergies (NKDA)\n"
            "Discharge Diagnoses: 1. Dehydration 2. Essential Hypertension 3. Type 2 Diabetes\n"
            "Discharge Prescriptions: Metformin HCl 1000 mg Oral Tablet BID; Lisinopril 10 mg Oral Tablet Daily\n"
            "SYNTHETIC DEMONSTRATION DATA"
        )
        doc2_p2 = (
            "ST. JUDE MEDICAL CENTER - PHYSICAL EXAM & DISCHARGE VITALS\n"
            "Vitals at Discharge: BP 138/84 mmHg, Pulse 74 bpm regular, SpO2 98% room air, Weight 68.2 kg, BMI 26.4\n"
            "Plan: Follow up with PCP within 14 days. Re-check complete metabolic panel.\n"
            "SYNTHETIC DEMONSTRATION DATA"
        )
        sz2, ck2 = create_synthetic_pdf(doc2_path, "Inpatient Discharge Summary", [doc2_p1, doc2_p2])
        d2 = Document(
            id=str(uuid.uuid4()),
            patient_id=p1.id,
            filename=doc2_name,
            original_name="StJude_Hosp_Discharge_Summary_Aug2026.pdf",
            file_type="application/pdf",
            file_size=sz2,
            checksum=ck2,
            page_count=2,
            processing_status="PROCESSED",
            raw_text=doc2_p1 + "\n" + doc2_p2,
        )
        db.add(d2)
        db.flush()
        db.add(DocumentPage(document_id=d2.id, page_number=1, extracted_text=doc2_p1, confidence_score=0.97))
        db.add(DocumentPage(document_id=d2.id, page_number=2, extracted_text=doc2_p2, confidence_score=0.95))

        # PDF 3: Lab Report
        doc3_name = "quest_diagnostics_cbc_aug2026.pdf"
        doc3_path = os.path.join(p1_dir, doc3_name)
        doc3_p1 = (
            "QUEST DIAGNOSTICS - CLINICAL LABORATORY REPORT\n"
            "Specimen Collected: 2026-08-12 07:45 AM | Received: 2026-08-12\n"
            "Patient: Vance, Eleanor | DOB: 1968-04-12 | MRN: MED-SYNTH-8492\n"
            "Test Name                Result    Reference Range    Status\n"
            "-----------------------------------------------------------\n"
            "Hemoglobin               11.2      12.0 - 16.0 g/dL   LOW\n"
            "Fasting Blood Glucose    94        70 - 99 mg/dL      NORMAL\n"
            "White Blood Cell Count   6.8       4.5 - 11.0 x10^3   NORMAL\n"
            "Serum Ferritin           19.5      [Not Provided]     --\n"
            "SYNTHETIC DEMONSTRATION DATA"
        )
        sz3, ck3 = create_synthetic_pdf(doc3_path, "Quest Diagnostics Laboratory Report", [doc3_p1])
        d3 = Document(
            id=str(uuid.uuid4()),
            patient_id=p1.id,
            filename=doc3_name,
            original_name="Quest_Diagnostics_CBC_Aug2026.pdf",
            file_type="application/pdf",
            file_size=sz3,
            checksum=ck3,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=doc3_p1,
        )
        db.add(d3)
        db.flush()
        db.add(DocumentPage(document_id=d3.id, page_number=1, extracted_text=doc3_p1, confidence_score=0.99))

        # Labs for P1
        lab_hb = LabResult(
            patient_id=p1.id,
            document_id=d3.id,
            test_name="Hemoglobin",
            raw_value="11.2",
            value=11.2,
            unit="g/dL",
            reference_range_low=12.0,
            reference_range_high=16.0,
            reference_range_text="12.0 - 16.0",
            status=LabStatusEnum.LOW,
            report_date="2026-08-12",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d3.filename,
            source_page=1,
            confidence=0.98,
            source_snippet="Hemoglobin 11.2 (12.0 - 16.0 g/dL)",
            verification_status=VerificationStatusEnum.VERIFIED,
            verified_by="Dr. Sarah Lin, MD",
        )
        lab_glu = LabResult(
            patient_id=p1.id,
            document_id=d3.id,
            test_name="Fasting Blood Glucose",
            raw_value="94",
            value=94.0,
            unit="mg/dL",
            reference_range_low=70.0,
            reference_range_high=99.0,
            reference_range_text="70 - 99",
            status=LabStatusEnum.NORMAL,
            report_date="2026-08-12",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d3.filename,
            source_page=1,
            confidence=0.99,
            source_snippet="Fasting Blood Glucose 94 (70 - 99 mg/dL)",
            verification_status=VerificationStatusEnum.VERIFIED,
            verified_by="Dr. Sarah Lin, MD",
        )
        lab_fer = LabResult(
            patient_id=p1.id,
            document_id=d3.id,
            test_name="Serum Ferritin",
            raw_value="19.5",
            value=19.5,
            unit="ng/mL",
            reference_range_low=None,
            reference_range_high=None,
            reference_range_text=None,
            status=LabStatusEnum.UNKNOWN,
            report_date="2026-08-12",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d3.filename,
            source_page=1,
            confidence=0.95,
            source_snippet="Serum Ferritin 19.5",
            verification_status=VerificationStatusEnum.UNVERIFIED,
        )
        db.add_all([lab_hb, lab_glu, lab_fer])

        # Meds for P1
        m1 = Medication(
            patient_id=p1.id,
            document_id=d2.id,
            medication_name="Metformin HCl",
            dosage="1000 mg",
            frequency="Twice daily (BID)",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-08-14",
            raw_text="Metformin HCl 1000 mg Oral Tablet BID",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d2.filename,
            source_page=1,
            confidence=0.97,
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        m2 = Medication(
            patient_id=p1.id,
            document_id=d2.id,
            medication_name="Lisinopril",
            dosage="10 mg",
            frequency="Once daily",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-08-14",
            raw_text="Lisinopril 10 mg Oral Tablet Daily",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d2.filename,
            source_page=1,
            confidence=0.96,
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        db.add_all([m1, m2])

        # Conditions for P1
        c1 = Condition(
            patient_id=p1.id,
            condition_name="Type 2 Diabetes Mellitus",
            icd10_code="E11.9",
            onset_date="2020-03-15",
            clinical_status="ACTIVE",
            raw_text="Type 2 Diabetes diagnosed 2020",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        c2 = Condition(
            patient_id=p1.id,
            condition_name="Essential Hypertension",
            icd10_code="I10",
            onset_date="2024-06-01",
            clinical_status="ACTIVE",
            raw_text="Essential Hypertension",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        db.add_all([c1, c2])

        # Allergies for P1
        a1 = Allergy(
            patient_id=p1.id,
            allergen="Penicillin",
            reaction="Facial hives and cutaneous erythema",
            severity="MODERATE",
            raw_text="Penicillin (causes rash and facial hives)",
            provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        db.add(a1)

        # Conflicts for P1
        cf1 = ConflictRecord(
            patient_id=p1.id,
            category=ConflictCategoryEnum.ALLERGY,
            field_name="allergy_penicillin",
            source_a_type="Patient Intake Questionnaire",
            source_a_document=d1.filename,
            source_a_page=1,
            source_a_value="Penicillin (causes rash and facial hives)",
            source_b_type="Hospital Discharge Summary",
            source_b_document=d2.filename,
            source_b_page=1,
            source_b_value="No Known Drug Allergies (NKDA)",
            description="Patient self-reports documented Penicillin allergy with hives, whereas hospital discharge record indicates NKDA.",
            severity="HIGH",
            status=ConflictStatusEnum.UNRESOLVED,
        )
        cf2 = ConflictRecord(
            patient_id=p1.id,
            category=ConflictCategoryEnum.MEDICATION,
            field_name="medication_metformin_dosage",
            source_a_type="Patient Intake Questionnaire",
            source_a_document=d1.filename,
            source_a_page=1,
            source_a_value="Metformin 500mg daily",
            source_b_type="Hospital Discharge Summary",
            source_b_document=d2.filename,
            source_b_page=1,
            source_b_value="Metformin HCl 1000mg BID",
            description="Dosage discrepancy between self-reported daily dose (500mg daily) and discharge prescription (1000mg BID).",
            severity="MEDIUM",
            status=ConflictStatusEnum.UNRESOLVED,
        )
        db.add_all([cf1, cf2])

        # Timeline for P1
        tl1 = TimelineEvent(
            patient_id=p1.id,
            event_date="2026-08-01",
            event_type="ENCOUNTER",
            title="Intake Questionnaire Submitted",
            description="Eleanor Vance submitted patient intake portal form. Reported Penicillin allergy and Metformin 500mg.",
            source_document=d1.filename,
            source_page=1,
            importance="ROUTINE",
        )
        tl2 = TimelineEvent(
            patient_id=p1.id,
            event_date="2026-08-12",
            event_type="LAB_TEST",
            title="Quest Diagnostics Panel Drawn",
            description="Hemoglobin 11.2 g/dL (LOW), Fasting Glucose 94 mg/dL (NORMAL), Ferritin 19.5 ng/mL (Range not provided).",
            source_document=d3.filename,
            source_page=1,
            importance="ROUTINE",
        )
        tl3 = TimelineEvent(
            patient_id=p1.id,
            event_date="2026-08-14",
            event_type="ENCOUNTER",
            title="Hospital Discharge",
            description="St. Jude Hospital discharge. Metformin updated to 1000mg BID; Lisinopril 10mg initiated.",
            source_document=d2.filename,
            source_page=1,
            importance="SIGNIFICANT",
        )
        db.add_all([tl1, tl2, tl3])

    # =========================================================================
    # PATIENT 2: Marcus Thorne (MRN: MED-SYNTH-5103)
    # Covers: High result with range (Total Cholesterol, LDL),
    # Historical lab value change (Cholesterol 278 -> 248),
    # Duplicate information (Atorvastatin 40mg documented in 2 documents)
    # =========================================================================
    p2 = db.query(Patient).filter(Patient.mrn == "MED-SYNTH-5103").first()
    if not p2:
        p2 = Patient(
            id=str(uuid.uuid4()),
            mrn="MED-SYNTH-5103",
            first_name="Marcus",
            last_name="Thorne",
            date_of_birth="1962-09-24",
            gender="Male",
            blood_type="O+",
        )
        db.add(p2)
        db.flush()

        p2_profile = PatientProfile(
            patient_id=p2.id,
            emergency_contact_name="Brenda Thorne (Wife)",
            emergency_contact_phone="+1 (555) 349-1120",
            preferred_language="English",
            insurance_provider="BlueCross BlueShield #SYNTH-4412",
            baseline_notes="SYNTHETIC DEMONSTRATION DATA: Cardiology patient undergoing longitudinal lipid management.",
            symptoms="Mild exertional shortness of breath during vigorous walking; denies chest pain.",
        )
        db.add(p2_profile)

        p2_dir = os.path.join(settings.UPLOAD_DIR, p2.id)
        # Doc 1: Cardiology Consult (August 2025)
        p2_doc1_content = [
            "METRO CARDIOLOGY ASSOCIATES - CONSULTATION NOTE\n"
            "Date: 2025-08-15 | Patient: Marcus Thorne | MRN: MED-SYNTH-5103\n"
            "History: Coronary Artery Disease, Hyperlipidemia\n"
            "Lipid Panel (2025-08-15): Total Cholesterol 278 mg/dL (HIGH, Range 100-199 mg/dL), LDL 188 mg/dL\n"
            "Prescribed: Atorvastatin 40 mg oral tablet daily at bedtime\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz21, ck21 = create_synthetic_pdf(os.path.join(p2_dir, "cardiology_consult_2025.pdf"), "Cardiology Consult 2025", p2_doc1_content)
        d21 = Document(
            id=str(uuid.uuid4()),
            patient_id=p2.id,
            filename="cardiology_consult_2025.pdf",
            original_name="Cardiology_Consult_Aug2025.pdf",
            file_type="application/pdf",
            file_size=sz21,
            checksum=ck21,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p2_doc1_content[0],
        )
        db.add(d21)
        db.flush()
        db.add(DocumentPage(document_id=d21.id, page_number=1, extracted_text=p2_doc1_content[0], confidence_score=0.98))

        # Doc 2: Follow-up Lipid Lab Panel (Feb 2026)
        p2_doc2_content = [
            "QUEST DIAGNOSTICS - LIPID & METABOLIC PANEL\n"
            "Date: 2026-02-10 | Patient: Marcus Thorne | MRN: MED-SYNTH-5103\n"
            "Test Name                Result    Reference Range    Status\n"
            "-----------------------------------------------------------\n"
            "Total Cholesterol        248       100 - 199 mg/dL    HIGH\n"
            "LDL Cholesterol          162       0 - 99 mg/dL       HIGH\n"
            "HDL Cholesterol          46        40 - 60 mg/dL      NORMAL\n"
            "Serum Potassium          4.3       3.5 - 5.0 mmol/L   NORMAL\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz22, ck22 = create_synthetic_pdf(os.path.join(p2_dir, "lipid_panel_2026.pdf"), "Lipid Panel Feb 2026", p2_doc2_content)
        d22 = Document(
            id=str(uuid.uuid4()),
            patient_id=p2.id,
            filename="lipid_panel_2026.pdf",
            original_name="Quest_Lipid_Panel_Feb2026.pdf",
            file_type="application/pdf",
            file_size=sz22,
            checksum=ck22,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p2_doc2_content[0],
        )
        db.add(d22)
        db.flush()
        db.add(DocumentPage(document_id=d22.id, page_number=1, extracted_text=p2_doc2_content[0], confidence_score=0.99))

        # Doc 3: Clinical Progress Note (Feb 2026) - duplicate Atorvastatin 40mg
        p2_doc3_content = [
            "METRO CARDIOLOGY ASSOCIATES - 6-MONTH PROGRESS NOTE\n"
            "Date: 2026-02-18 | Patient: Marcus Thorne | MRN: MED-SYNTH-5103\n"
            "Assessment: Longitudinal tracking shows Total Cholesterol decreased from 278 to 248 mg/dL on current therapy.\n"
            "Active Medication: Atorvastatin 40 mg oral tablet daily at bedtime (adherence verified)\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz23, ck23 = create_synthetic_pdf(os.path.join(p2_dir, "cardiology_progress_2026.pdf"), "Cardiology Progress Note 2026", p2_doc3_content)
        d23 = Document(
            id=str(uuid.uuid4()),
            patient_id=p2.id,
            filename="cardiology_progress_2026.pdf",
            original_name="Cardiology_Progress_Note_Feb2026.pdf",
            file_type="application/pdf",
            file_size=sz23,
            checksum=ck23,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p2_doc3_content[0],
        )
        db.add(d23)
        db.flush()
        db.add(DocumentPage(document_id=d23.id, page_number=1, extracted_text=p2_doc3_content[0], confidence_score=0.97))

        # Labs for P2
        # Prior cholesterol
        l2_old = LabResult(
            patient_id=p2.id,
            document_id=d21.id,
            test_name="Total Cholesterol",
            raw_value="278",
            value=278.0,
            unit="mg/dL",
            reference_range_low=100.0,
            reference_range_high=199.0,
            reference_range_text="100 - 199",
            status=LabStatusEnum.HIGH,
            report_date="2025-08-15",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d21.filename,
            source_page=1,
            confidence=0.98,
            source_snippet="Total Cholesterol 278 mg/dL (HIGH)",
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        # Recent cholesterol (Test Case 7: historical value change)
        l2_new = LabResult(
            patient_id=p2.id,
            document_id=d22.id,
            test_name="Total Cholesterol",
            raw_value="248",
            value=248.0,
            unit="mg/dL",
            reference_range_low=100.0,
            reference_range_high=199.0,
            reference_range_text="100 - 199",
            status=LabStatusEnum.HIGH,
            report_date="2026-02-10",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d22.filename,
            source_page=1,
            confidence=0.99,
            source_snippet="Total Cholesterol 248 mg/dL (100 - 199 mg/dL)",
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        l2_ldl = LabResult(
            patient_id=p2.id,
            document_id=d22.id,
            test_name="LDL Cholesterol",
            raw_value="162",
            value=162.0,
            unit="mg/dL",
            reference_range_low=0.0,
            reference_range_high=99.0,
            reference_range_text="0 - 99",
            status=LabStatusEnum.HIGH,
            report_date="2026-02-10",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d22.filename,
            source_page=1,
            confidence=0.99,
            source_snippet="LDL Cholesterol 162 mg/dL",
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        l2_k = LabResult(
            patient_id=p2.id,
            document_id=d22.id,
            test_name="Serum Potassium",
            raw_value="4.3",
            value=4.3,
            unit="mmol/L",
            reference_range_low=3.5,
            reference_range_high=5.0,
            reference_range_text="3.5 - 5.0",
            status=LabStatusEnum.NORMAL,
            report_date="2026-02-10",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d22.filename,
            source_page=1,
            confidence=0.98,
            source_snippet="Serum Potassium 4.3 mmol/L",
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        db.add_all([l2_old, l2_new, l2_ldl, l2_k])

        # Meds for P2 (Test Case 10: Duplicate documentation across doc 1 and doc 3)
        med_atorva_1 = Medication(
            patient_id=p2.id,
            document_id=d21.id,
            medication_name="Atorvastatin",
            dosage="40 mg",
            frequency="Daily at bedtime",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2025-08-15",
            raw_text="Atorvastatin 40 mg oral tablet daily at bedtime",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d21.filename,
            source_page=1,
            confidence=0.98,
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        med_atorva_2 = Medication(
            patient_id=p2.id,
            document_id=d23.id,
            medication_name="Atorvastatin",
            dosage="40 mg",
            frequency="Daily at bedtime",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-02-18",
            raw_text="Atorvastatin 40 mg oral tablet daily at bedtime",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d23.filename,
            source_page=1,
            confidence=0.97,
            verification_status=VerificationStatusEnum.VERIFIED,
        )
        db.add_all([med_atorva_1, med_atorva_2])

        db.add(Condition(
            patient_id=p2.id,
            condition_name="Coronary Artery Disease",
            icd10_code="I25.10",
            onset_date="2023-01-10",
            clinical_status="ACTIVE",
            raw_text="Coronary Artery Disease",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        db.add(Condition(
            patient_id=p2.id,
            condition_name="Hyperlipidemia",
            icd10_code="E78.5",
            onset_date="2022-05-18",
            clinical_status="ACTIVE",
            raw_text="Hyperlipidemia",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))

        # Timeline for P2
        db.add(TimelineEvent(
            patient_id=p2.id,
            event_date="2025-08-15",
            event_type="LAB_TEST",
            title="Baseline Lipid Panel: Total Cholesterol 278 mg/dL (HIGH)",
            description="Initial cardiology consultation workup. Initiated Atorvastatin 40mg.",
            source_document=d21.filename,
            source_page=1,
            importance="SIGNIFICANT",
        ))
        db.add(TimelineEvent(
            patient_id=p2.id,
            event_date="2026-02-10",
            event_type="LAB_TEST",
            title="Follow-up Lipid Panel: Total Cholesterol 248 mg/dL (HIGH)",
            description="Total Cholesterol decreased from 278 to 248 mg/dL (-30 mg/dL reduction). Potassium normal at 4.3 mmol/L.",
            source_document=d22.filename,
            source_page=1,
            importance="SIGNIFICANT",
        ))

    # =========================================================================
    # PATIENT 3: Aisha Patel (MRN: MED-SYNTH-7321)
    # Covers: Low-confidence extraction (Platelet estimate 0.74),
    # Missing medication dosage (Cetirizine missing dose), Normal lab (Platelets)
    # =========================================================================
    p3 = db.query(Patient).filter(Patient.mrn == "MED-SYNTH-7321").first()
    if not p3:
        p3 = Patient(
            id=str(uuid.uuid4()),
            mrn="MED-SYNTH-7321",
            first_name="Aisha",
            last_name="Patel",
            date_of_birth="1987-03-18",
            gender="Female",
            blood_type="B+",
        )
        db.add(p3)
        db.flush()

        p3_profile = PatientProfile(
            patient_id=p3.id,
            emergency_contact_name="Farhan Patel (Brother)",
            emergency_contact_phone="+1 (555) 782-9904",
            preferred_language="English",
            insurance_provider="Cigna HealthCare #SYNTH-3391",
            baseline_notes="SYNTHETIC DEMONSTRATION DATA: Ambulatory patient with seasonal allergies and mild iron deficiency.",
            symptoms="Nasal congestion, intermittent sneezing, mild cold intolerance.",
        )
        db.add(p3_profile)

        p3_dir = os.path.join(settings.UPLOAD_DIR, p3.id)
        # Doc 1: Allergy Clinic Assessment
        p3_doc1_content = [
            "VALLEY ALLERGY & ASTHMA CLINIC - EVALUATION NOTE\n"
            "Date: 2026-01-15 | Patient: Aisha Patel | MRN: MED-SYNTH-7321\n"
            "Documented Allergies: Trimethoprim-Sulfamethoxazole / Sulfa Drugs (severe anaphylactoid reaction)\n"
            "Current Medications: Cetirizine daily by mouth as needed for rhinitis (dose unspecified)\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz31, ck31 = create_synthetic_pdf(os.path.join(p3_dir, "allergy_assessment_2026.pdf"), "Allergy Clinic Assessment", p3_doc1_content)
        d31 = Document(
            id=str(uuid.uuid4()),
            patient_id=p3.id,
            filename="allergy_assessment_2026.pdf",
            original_name="Allergy_Clinic_Assessment_Jan2026.pdf",
            file_type="application/pdf",
            file_size=sz31,
            checksum=ck31,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p3_doc1_content[0],
        )
        db.add(d31)
        db.flush()
        db.add(DocumentPage(document_id=d31.id, page_number=1, extracted_text=p3_doc1_content[0], confidence_score=0.97))

        # Doc 2: Diagnostic Hematology (Faded Fax Scanner)
        p3_doc2_content = [
            "DIAGNOSTIC HEMATOLOGY LABORATORY - FAX TRANSMISSION [SCANNER COPY]\n"
            "Date: 2026-01-22 | Patient: Aisha Patel | MRN: MED-SYNTH-7321\n"
            "Automated Platelet Count: 250 x10^3/uL (Reference: 150 - 450 x10^3/uL) [NORMAL]\n"
            "Peripheral Blood Smear Platelet Estimate: Faint optical scan reading ~Adequate\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz32, ck32 = create_synthetic_pdf(os.path.join(p3_dir, "faded_hematology_fax_2026.pdf"), "Faded Hematology Fax", p3_doc2_content)
        d32 = Document(
            id=str(uuid.uuid4()),
            patient_id=p3.id,
            filename="faded_hematology_fax_2026.pdf",
            original_name="Diagnostic_Hematology_Fax_Jan2026.pdf",
            file_type="application/pdf",
            file_size=sz32,
            checksum=ck32,
            page_count=1,
            processing_status="NEEDS_REVIEW",
            raw_text=p3_doc2_content[0],
        )
        db.add(d32)
        db.flush()
        db.add(DocumentPage(document_id=d32.id, page_number=1, extracted_text=p3_doc2_content[0], confidence_score=0.74, extraction_status="OCR_REQUIRED"))

        # Labs for P3
        db.add(LabResult(
            patient_id=p3.id,
            document_id=d32.id,
            test_name="Platelet Count",
            raw_value="250",
            value=250.0,
            unit="x10^3/uL",
            reference_range_low=150.0,
            reference_range_high=450.0,
            reference_range_text="150 - 450",
            status=LabStatusEnum.NORMAL,
            report_date="2026-01-22",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d32.filename,
            source_page=1,
            confidence=0.98,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        # Test Case 8: Low-confidence extraction (<0.90)
        db.add(LabResult(
            patient_id=p3.id,
            document_id=d32.id,
            test_name="Platelet Estimate (Smear)",
            raw_value="Adequate (~240)",
            value=None,
            unit=None,
            reference_range_low=None,
            reference_range_high=None,
            reference_range_text=None,
            status=LabStatusEnum.UNKNOWN,
            report_date="2026-01-22",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d32.filename,
            source_page=1,
            confidence=0.74,  # Flagged for human review
            source_snippet="Faint optical scan reading ~Adequate",
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))

        # Test Case 9: Missing medication dosage
        db.add(Medication(
            patient_id=p3.id,
            document_id=d31.id,
            medication_name="Cetirizine",
            dosage=None,  # Missing dosage!
            frequency="Once daily as needed",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-01-15",
            raw_text="Cetirizine daily by mouth as needed for rhinitis",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d31.filename,
            source_page=1,
            confidence=0.92,
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))

        db.add(Allergy(
            patient_id=p3.id,
            allergen="Sulfa Drugs (Bactrim)",
            reaction="Severe facial angioedema and wheezing",
            severity="SEVERE",
            raw_text="Trimethoprim-Sulfamethoxazole / Sulfa Drugs",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        db.add(Condition(
            patient_id=p3.id,
            condition_name="Allergic Rhinitis",
            icd10_code="J30.9",
            onset_date="2018-04-01",
            clinical_status="ACTIVE",
            raw_text="Seasonal Allergic Rhinitis",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))

        # Timeline for P3
        db.add(TimelineEvent(
            patient_id=p3.id,
            event_date="2026-01-15",
            event_type="ENCOUNTER",
            title="Allergy Clinic Assessment",
            description="Valley Allergy Clinic visit. Severe Sulfa allergy documented; Cetirizine recorded for allergic rhinitis.",
            source_document=d31.filename,
            source_page=1,
            importance="ROUTINE",
        ))
        db.add(TimelineEvent(
            patient_id=p3.id,
            event_date="2026-01-22",
            event_type="LAB_TEST",
            title="Hematology Panel Drawn",
            description="Platelet Count 250 x10^3/uL (NORMAL). Peripheral smear platelet estimate adequate.",
            source_document=d32.filename,
            source_page=1,
            importance="ROUTINE",
        ))

    # =========================================================================
    # PATIENT 4: David Kim (MRN: MED-SYNTH-2940)
    # Covers: High result with range (Creatinine, BUN),
    # Historical value change (Creatinine 1.32 -> 1.65),
    # Missing reference range (Uric Acid), Conflicting medication (Allopurinol 100mg vs 300mg),
    # Missing medication dosage (Colchicine)
    # =========================================================================
    p4 = db.query(Patient).filter(Patient.mrn == "MED-SYNTH-2940").first()
    if not p4:
        p4 = Patient(
            id=str(uuid.uuid4()),
            mrn="MED-SYNTH-2940",
            first_name="David",
            last_name="Kim",
            date_of_birth="1955-11-05",
            gender="Male",
            blood_type="AB-",
        )
        db.add(p4)
        db.flush()

        p4_profile = PatientProfile(
            patient_id=p4.id,
            emergency_contact_name="Grace Kim (Daughter)",
            emergency_contact_phone="+1 (555) 601-2248",
            preferred_language="English",
            insurance_provider="Medicare Part B #SYNTH-1198",
            baseline_notes="SYNTHETIC DEMONSTRATION DATA: Geriatric renal clinic patient with chronic kidney disease and episodic gout.",
            symptoms="Right great toe swelling and localized erythema last month; mild ankle edema.",
        )
        db.add(p4_profile)

        p4_dir = os.path.join(settings.UPLOAD_DIR, p4.id)
        # Doc 1: Baseline Renal Clinic (May 2025)
        p4_doc1_content = [
            "EASTSIDE NEPHROLOGY CLINIC - INITIAL CONSULTATION\n"
            "Date: 2025-05-12 | Patient: David Kim | MRN: MED-SYNTH-2940\n"
            "Baseline Chemistry: Serum Creatinine 1.32 mg/dL (Reference: 0.70 - 1.30 mg/dL) [HIGH]\n"
            "Medication Order: Allopurinol 100 mg oral tablet once daily\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz41, ck41 = create_synthetic_pdf(os.path.join(p4_dir, "nephrology_baseline_2025.pdf"), "Nephrology Baseline 2025", p4_doc1_content)
        d41 = Document(
            id=str(uuid.uuid4()),
            patient_id=p4.id,
            filename="nephrology_baseline_2025.pdf",
            original_name="Nephrology_Intake_Assessment_May2025.pdf",
            file_type="application/pdf",
            file_size=sz41,
            checksum=ck41,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p4_doc1_content[0],
        )
        db.add(d41)
        db.flush()
        db.add(DocumentPage(document_id=d41.id, page_number=1, extracted_text=p4_doc1_content[0], confidence_score=0.98))

        # Doc 2: Renal Panel (Jan 2026)
        p4_doc2_content = [
            "LABCORP - RENAL FUNCTION & METABOLIC PANEL\n"
            "Date: 2026-01-20 | Patient: David Kim | MRN: MED-SYNTH-2940\n"
            "Test Name                Result    Reference Range    Status\n"
            "-----------------------------------------------------------\n"
            "Serum Creatinine         1.65      0.70 - 1.30 mg/dL  HIGH\n"
            "Blood Urea Nitrogen      29        7 - 20 mg/dL       HIGH\n"
            "Uric Acid                7.8       [Not Provided]     --\n"
            "Serum Chloride           102       96 - 106 mmol/L    NORMAL\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz42, ck42 = create_synthetic_pdf(os.path.join(p4_dir, "renal_panel_2026.pdf"), "Renal Panel Jan 2026", p4_doc2_content)
        d42 = Document(
            id=str(uuid.uuid4()),
            patient_id=p4.id,
            filename="renal_panel_2026.pdf",
            original_name="Renal_Metabolic_Panel_Jan2026.pdf",
            file_type="application/pdf",
            file_size=sz42,
            checksum=ck42,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p4_doc2_content[0],
        )
        db.add(d42)
        db.flush()
        db.add(DocumentPage(document_id=d42.id, page_number=1, extracted_text=p4_doc2_content[0], confidence_score=0.99))

        # Doc 3: Urgent Care Note (Jan 2026)
        p4_doc3_content = [
            "URGENT CARE CLINIC - CLINICAL VISIT SUMMARY\n"
            "Date: 2026-01-28 | Patient: David Kim | MRN: MED-SYNTH-2940\n"
            "Reason: Acute Gout Flare\n"
            "Prescriptions at Visit: Allopurinol 300 mg Oral Tablet Daily; Colchicine oral as directed for acute flare\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz43, ck43 = create_synthetic_pdf(os.path.join(p4_dir, "urgent_care_summary_2026.pdf"), "Urgent Care Summary Jan 2026", p4_doc3_content)
        d43 = Document(
            id=str(uuid.uuid4()),
            patient_id=p4.id,
            filename="urgent_care_summary_2026.pdf",
            original_name="Urgent_Care_Encounter_Summary_Jan2026.pdf",
            file_type="application/pdf",
            file_size=sz43,
            checksum=ck43,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p4_doc3_content[0],
        )
        db.add(d43)
        db.flush()
        db.add(DocumentPage(document_id=d43.id, page_number=1, extracted_text=p4_doc3_content[0], confidence_score=0.97))

        # Labs for P4
        # Test Case 7: Historical change (Creatinine 1.32 -> 1.65)
        db.add(LabResult(
            patient_id=p4.id,
            document_id=d41.id,
            test_name="Serum Creatinine",
            raw_value="1.32",
            value=1.32,
            unit="mg/dL",
            reference_range_low=0.70,
            reference_range_high=1.30,
            reference_range_text="0.70 - 1.30",
            status=LabStatusEnum.HIGH,
            report_date="2025-05-12",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d41.filename,
            source_page=1,
            confidence=0.98,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        db.add(LabResult(
            patient_id=p4.id,
            document_id=d42.id,
            test_name="Serum Creatinine",
            raw_value="1.65",
            value=1.65,
            unit="mg/dL",
            reference_range_low=0.70,
            reference_range_high=1.30,
            reference_range_text="0.70 - 1.30",
            status=LabStatusEnum.HIGH,
            report_date="2026-01-20",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d42.filename,
            source_page=1,
            confidence=0.99,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        db.add(LabResult(
            patient_id=p4.id,
            document_id=d42.id,
            test_name="Blood Urea Nitrogen",
            raw_value="29",
            value=29.0,
            unit="mg/dL",
            reference_range_low=7.0,
            reference_range_high=20.0,
            reference_range_text="7 - 20",
            status=LabStatusEnum.HIGH,
            report_date="2026-01-20",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d42.filename,
            source_page=1,
            confidence=0.99,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        # Test Case 4: Missing reference range (Uric Acid)
        db.add(LabResult(
            patient_id=p4.id,
            document_id=d42.id,
            test_name="Serum Uric Acid",
            raw_value="7.8",
            value=7.8,
            unit="mg/dL",
            reference_range_low=None,
            reference_range_high=None,
            reference_range_text=None,
            status=LabStatusEnum.UNKNOWN,
            report_date="2026-01-20",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d42.filename,
            source_page=1,
            confidence=0.96,
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))

        # Meds for P4
        db.add(Medication(
            patient_id=p4.id,
            document_id=d43.id,
            medication_name="Allopurinol",
            dosage="300 mg",
            frequency="Once daily",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-01-28",
            raw_text="Allopurinol 300 mg Oral Tablet Daily",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d43.filename,
            source_page=1,
            confidence=0.98,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        # Test Case 9: Missing medication dosage
        db.add(Medication(
            patient_id=p4.id,
            document_id=d43.id,
            medication_name="Colchicine",
            dosage=None,  # Missing dosage!
            frequency="As directed for acute flare",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-01-28",
            raw_text="Colchicine oral as directed for acute flare",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d43.filename,
            source_page=1,
            confidence=0.95,
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))

        # Test Case 6: Conflicting medication information (Allopurinol 100mg vs 300mg)
        db.add(ConflictRecord(
            patient_id=p4.id,
            category=ConflictCategoryEnum.MEDICATION,
            field_name="medication_allopurinol_dosage",
            source_a_type="Nephrology Intake Assessment",
            source_a_document=d41.filename,
            source_a_page=1,
            source_a_value="Allopurinol 100mg daily",
            source_b_type="Urgent Care Visit Summary",
            source_b_document=d43.filename,
            source_b_page=1,
            source_b_value="Allopurinol 300mg daily",
            description="Dosage discrepancy for Allopurinol: 100mg daily prescribed at Nephrology baseline vs 300mg daily prescribed at Urgent Care.",
            severity="HIGH",
            status=ConflictStatusEnum.UNRESOLVED,
        ))

        db.add(Condition(
            patient_id=p4.id,
            condition_name="Chronic Kidney Disease Stage 2",
            icd10_code="N18.2",
            onset_date="2024-02-10",
            clinical_status="ACTIVE",
            raw_text="Chronic Kidney Disease Stage 2",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))

        # Timeline for P4
        db.add(TimelineEvent(
            patient_id=p4.id,
            event_date="2025-05-12",
            event_type="ENCOUNTER",
            title="Nephrology Baseline Consultation",
            description="Initial renal assessment: Creatinine 1.32 mg/dL. Allopurinol 100mg daily initiated for hyperuricemia.",
            source_document=d41.filename,
            source_page=1,
            importance="SIGNIFICANT",
        ))
        db.add(TimelineEvent(
            patient_id=p4.id,
            event_date="2026-01-20",
            event_type="LAB_TEST",
            title="LabCorp Renal Function Panel",
            description="Creatinine 1.65 mg/dL (HIGH), BUN 29 mg/dL (HIGH), Uric Acid 7.8 mg/dL (Range not provided).",
            source_document=d42.filename,
            source_page=1,
            importance="SIGNIFICANT",
        ))
        db.add(TimelineEvent(
            patient_id=p4.id,
            event_date="2026-01-28",
            event_type="ENCOUNTER",
            title="Urgent Care Encounter (Gout Flare)",
            description="Acute gout flare management. Allopurinol escalated to 300mg daily; Colchicine prescribed PRN.",
            source_document=d43.filename,
            source_page=1,
            importance="SIGNIFICANT",
        ))


    # =========================================================================
    # PATIENT 5: Elena Rostova (MRN: MED-SYNTH-6815)
    # Covers: Low result with range (Free T4), High result with range (TSH),
    # Conflicting allergy (Aspirin bronchospasm vs tolerated), Duplicate info (Levothyroxine)
    # =========================================================================
    p5 = db.query(Patient).filter(Patient.mrn == "MED-SYNTH-6815").first()
    if not p5:
        p5 = Patient(
            id=str(uuid.uuid4()),
            mrn="MED-SYNTH-6815",
            first_name="Elena",
            last_name="Rostova",
            date_of_birth="1981-07-29",
            gender="Female",
            blood_type="A-",
        )
        db.add(p5)
        db.flush()

        p5_profile = PatientProfile(
            patient_id=p5.id,
            emergency_contact_name="Dmitri Rostov (Brother)",
            emergency_contact_phone="+1 (555) 912-4433",
            preferred_language="English",
            insurance_provider="UnitedHealthcare #SYNTH-8821",
            baseline_notes="SYNTHETIC DEMONSTRATION DATA: Endocrinology and pulmonary patient with hypothyroidism and reactive airway symptoms.",
            symptoms="Cold intolerance, sluggishness, periodic dry cough with exertion.",
        )
        db.add(p5_profile)

        p5_dir = os.path.join(settings.UPLOAD_DIR, p5.id)
        # Doc 1: Endocrinology Follow-Up
        p5_doc1_content = [
            "ENDOCRINE ASSOCIATES OF NORTHVALE - CLINICAL VISIT\n"
            "Date: 2025-11-14 | Patient: Elena Rostova | MRN: MED-SYNTH-6815\n"
            "Allergy Alert: Patient Portal lists Aspirin allergy with bronchospasm\n"
            "Current Prescriptions: Levothyroxine sodium 75 mcg oral tablet daily in the morning on empty stomach\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz51, ck51 = create_synthetic_pdf(os.path.join(p5_dir, "endocrine_followup_2025.pdf"), "Endocrine Follow-Up 2025", p5_doc1_content)
        d51 = Document(
            id=str(uuid.uuid4()),
            patient_id=p5.id,
            filename="endocrine_followup_2025.pdf",
            original_name="Endocrine_FollowUp_Nov2025.pdf",
            file_type="application/pdf",
            file_size=sz51,
            checksum=ck51,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p5_doc1_content[0],
        )
        db.add(d51)
        db.flush()
        db.add(DocumentPage(document_id=d51.id, page_number=1, extracted_text=p5_doc1_content[0], confidence_score=0.98))

        # Doc 2: Thyroid Lab Panel (Jan 2026)
        p5_doc2_content = [
            "QUEST DIAGNOSTICS - THYROID & METABOLIC FUNCTION PANEL\n"
            "Date: 2026-01-18 | Patient: Elena Rostova | MRN: MED-SYNTH-6815\n"
            "Test Name                Result    Reference Range    Status\n"
            "-----------------------------------------------------------\n"
            "TSH                      8.40      0.40 - 4.50 uIU/mL HIGH\n"
            "Free T4                  0.61      0.80 - 1.80 ng/dL  LOW\n"
            "Serum Sodium             140       135 - 145 mEq/L    NORMAL\n"
            "Active Rx at Lab: Levothyroxine sodium 75 mcg oral tablet daily\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz52, ck52 = create_synthetic_pdf(os.path.join(p5_dir, "thyroid_panel_2026.pdf"), "Thyroid Panel Jan 2026", p5_doc2_content)
        d52 = Document(
            id=str(uuid.uuid4()),
            patient_id=p5.id,
            filename="thyroid_panel_2026.pdf",
            original_name="Quest_Thyroid_Panel_Jan2026.pdf",
            file_type="application/pdf",
            file_size=sz52,
            checksum=ck52,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p5_doc2_content[0],
        )
        db.add(d52)
        db.flush()
        db.add(DocumentPage(document_id=d52.id, page_number=1, extracted_text=p5_doc2_content[0], confidence_score=0.99))

        # Labs for P5
        # Test Case 3: High result with source range (TSH)
        db.add(LabResult(
            patient_id=p5.id,
            document_id=d52.id,
            test_name="Thyroid Stimulating Hormone (TSH)",
            raw_value="8.40",
            value=8.40,
            unit="uIU/mL",
            reference_range_low=0.40,
            reference_range_high=4.50,
            reference_range_text="0.40 - 4.50",
            status=LabStatusEnum.HIGH,
            report_date="2026-01-18",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d52.filename,
            source_page=1,
            confidence=0.99,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        # Test Case 2: Low result with source range (Free T4)
        db.add(LabResult(
            patient_id=p5.id,
            document_id=d52.id,
            test_name="Free T4",
            raw_value="0.61",
            value=0.61,
            unit="ng/dL",
            reference_range_low=0.80,
            reference_range_high=1.80,
            reference_range_text="0.80 - 1.80",
            status=LabStatusEnum.LOW,
            report_date="2026-01-18",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d52.filename,
            source_page=1,
            confidence=0.98,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        # Normal result
        db.add(LabResult(
            patient_id=p5.id,
            document_id=d52.id,
            test_name="Serum Sodium",
            raw_value="140",
            value=140.0,
            unit="mEq/L",
            reference_range_low=135.0,
            reference_range_high=145.0,
            reference_range_text="135 - 145",
            status=LabStatusEnum.NORMAL,
            report_date="2026-01-18",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d52.filename,
            source_page=1,
            confidence=0.99,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))

        # Test Case 10: Duplicate information (Levothyroxine in Doc 1 and Doc 2)
        db.add(Medication(
            patient_id=p5.id,
            document_id=d51.id,
            medication_name="Levothyroxine sodium",
            dosage="75 mcg",
            frequency="Once daily in the morning",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2025-11-14",
            raw_text="Levothyroxine sodium 75 mcg oral tablet daily in the morning",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d51.filename,
            source_page=1,
            confidence=0.98,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        db.add(Medication(
            patient_id=p5.id,
            document_id=d52.id,
            medication_name="Levothyroxine sodium",
            dosage="75 mcg",
            frequency="Once daily",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-01-18",
            raw_text="Levothyroxine sodium 75 mcg oral tablet daily",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d52.filename,
            source_page=1,
            confidence=0.97,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))

        # Test Case 5: Conflicting allergy information (Aspirin)
        db.add(Allergy(
            patient_id=p5.id,
            allergen="Aspirin",
            reaction="Bronchospasm and wheezing",
            severity="SEVERE",
            raw_text="Aspirin allergy with bronchospasm",
            provenance_source=ProvenanceSourceEnum.PATIENT_INPUT,
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))
        db.add(ConflictRecord(
            patient_id=p5.id,
            category=ConflictCategoryEnum.ALLERGY,
            field_name="allergy_aspirin",
            source_a_type="Patient Portal Record",
            source_a_document=d51.filename,
            source_a_page=1,
            source_a_value="Aspirin allergy with bronchospasm",
            source_b_type="Cardiopulmonary Summary",
            source_b_document=d52.filename,
            source_b_page=1,
            source_b_value="Aspirin 81mg tolerated without adverse reaction",
            description="Allergy status conflict: Portal notes severe bronchospasm from Aspirin, whereas cardiopulmonary note indicates Aspirin tolerance.",
            severity="CRITICAL",
            status=ConflictStatusEnum.UNRESOLVED,
        ))

        # Timeline for P5
        db.add(TimelineEvent(
            patient_id=p5.id,
            event_date="2025-10-10",
            event_type="ENCOUNTER",
            title="Endocrine Consultation Note",
            description="Endocrinology evaluation: Hypothyroidism management. Levothyroxine 75 mcg daily confirmed.",
            source_document=d51.filename,
            source_page=1,
            importance="ROUTINE",
        ))
        db.add(TimelineEvent(
            patient_id=p5.id,
            event_date="2026-02-01",
            event_type="LAB_TEST",
            title="Comprehensive Thyroid Panel",
            description="TSH 8.40 mIU/L (HIGH), Free T4 0.61 ng/dL (LOW). Serum Sodium 140 mmol/L (NORMAL).",
            source_document=d53.filename,
            source_page=1,
            importance="SIGNIFICANT",
        ))
        db.add(TimelineEvent(
            patient_id=p5.id,
            event_date="2026-02-14",
            event_type="ENCOUNTER",
            title="Cardiopulmonary Summary",
            description="Cardiology follow-up. Aspirin 81mg documented as tolerated without adverse reaction.",
            source_document=d52.filename,
            source_page=1,
            importance="SIGNIFICANT",
        ))


    # =========================================================================
    # PATIENT 6: Samuel O'Connor (MRN: MED-SYNTH-9457)
    # Covers: Normal labs (ALT, AST), Missing reference range (Vitamin B12),
    # Low-confidence extraction (Faxed Omeprazole rx 0.68), Missing dosage (Ibuprofen)
    # =========================================================================
    p6 = db.query(Patient).filter(Patient.mrn == "MED-SYNTH-9457").first()
    if not p6:
        p6 = Patient(
            id=str(uuid.uuid4()),
            mrn="MED-SYNTH-9457",
            first_name="Samuel",
            last_name="O'Connor",
            date_of_birth="1974-01-14",
            gender="Male",
            blood_type="O-",
        )
        db.add(p6)
        db.flush()

        p6_profile = PatientProfile(
            patient_id=p6.id,
            emergency_contact_name="Claire O'Connor (Spouse)",
            emergency_contact_phone="+1 (555) 441-9802",
            preferred_language="English",
            insurance_provider="Kaiser Permanente #SYNTH-5590",
            baseline_notes="SYNTHETIC DEMONSTRATION DATA: Routine gastrointestinal follow-up and chronic joint stiffness.",
            symptoms="Heartburn after heavy meals, right knee stiffness in mornings.",
        )
        db.add(p6_profile)

        p6_dir = os.path.join(settings.UPLOAD_DIR, p6.id)
        # Doc 1: Routine Health Check Lab (Feb 2026)
        p6_doc1_content = [
            "BIO-REFERENCE LABORATORIES - ROUTINE HEALTH PANEL\n"
            "Date: 2026-02-05 | Patient: Samuel O'Connor | MRN: MED-SYNTH-9457\n"
            "Test Name                Result    Reference Range    Status\n"
            "-----------------------------------------------------------\n"
            "Alanine Aminotransferase 28        10 - 40 U/L        NORMAL\n"
            "Aspartate Aminotransferase 24      10 - 40 U/L        NORMAL\n"
            "Serum Vitamin B12        310       [Not Provided]     --\n"
            "Fasting Glucose          91        70 - 99 mg/dL      NORMAL\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz61, ck61 = create_synthetic_pdf(os.path.join(p6_dir, "routine_health_panel_2026.pdf"), "Routine Health Panel Feb 2026", p6_doc1_content)
        d61 = Document(
            id=str(uuid.uuid4()),
            patient_id=p6.id,
            filename="routine_health_panel_2026.pdf",
            original_name="Routine_Health_Panel_Feb2026.pdf",
            file_type="application/pdf",
            file_size=sz61,
            checksum=ck61,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=p6_doc1_content[0],
        )
        db.add(d61)
        db.flush()
        db.add(DocumentPage(document_id=d61.id, page_number=1, extracted_text=p6_doc1_content[0], confidence_score=0.99))

        # Doc 2: Faxed Pharmacy Dispense Document (Faded Thermal Print)
        p6_doc2_content = [
            "COMMUNITY PHARMACY - FAX DISPENSE LOG [THERMAL SCRIPT]\n"
            "Date: 2026-02-12 | Patient: Samuel O'Connor | MRN: MED-SYNTH-9457\n"
            "Faint Print: Rx #884920 Omeprazole 20mg Delayed Release Capsule once daily morning before food\n"
            "Over-the-counter noted: Ibuprofen orally as needed for knee discomfort (dose unstated)\n"
            "SYNTHETIC DEMONSTRATION DATA"
        ]
        sz62, ck62 = create_synthetic_pdf(os.path.join(p6_dir, "pharmacy_dispense_fax_2026.pdf"), "Pharmacy Dispense Fax", p6_doc2_content)
        d62 = Document(
            id=str(uuid.uuid4()),
            patient_id=p6.id,
            filename="pharmacy_dispense_fax_2026.pdf",
            original_name="Pharmacy_Dispense_Fax_Feb2026.pdf",
            file_type="application/pdf",
            file_size=sz62,
            checksum=ck62,
            page_count=1,
            processing_status="NEEDS_REVIEW",
            raw_text=p6_doc2_content[0],
        )
        db.add(d62)
        db.flush()
        # Test Case 8: Low-confidence extraction (0.68)
        db.add(DocumentPage(document_id=d62.id, page_number=1, extracted_text=p6_doc2_content[0], confidence_score=0.68, extraction_status="OCR_REQUIRED"))

        # Labs for P6
        # Test Case 1: Normal laboratory results
        db.add(LabResult(
            patient_id=p6.id,
            document_id=d61.id,
            test_name="Alanine Aminotransferase (ALT)",
            raw_value="28",
            value=28.0,
            unit="U/L",
            reference_range_low=10.0,
            reference_range_high=40.0,
            reference_range_text="10 - 40",
            status=LabStatusEnum.NORMAL,
            report_date="2026-02-05",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d61.filename,
            source_page=1,
            confidence=0.99,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        db.add(LabResult(
            patient_id=p6.id,
            document_id=d61.id,
            test_name="Aspartate Aminotransferase (AST)",
            raw_value="24",
            value=24.0,
            unit="U/L",
            reference_range_low=10.0,
            reference_range_high=40.0,
            reference_range_text="10 - 40",
            status=LabStatusEnum.NORMAL,
            report_date="2026-02-05",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d61.filename,
            source_page=1,
            confidence=0.99,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))
        # Test Case 4: Missing reference range (Vitamin B12)
        db.add(LabResult(
            patient_id=p6.id,
            document_id=d61.id,
            test_name="Serum Vitamin B12",
            raw_value="310",
            value=310.0,
            unit="pg/mL",
            reference_range_low=None,
            reference_range_high=None,
            reference_range_text=None,
            status=LabStatusEnum.UNKNOWN,
            report_date="2026-02-05",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d61.filename,
            source_page=1,
            confidence=0.97,
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))

        # Meds for P6
        # Low confidence extraction item
        db.add(Medication(
            patient_id=p6.id,
            document_id=d62.id,
            medication_name="Omeprazole",
            dosage="20 mg",
            frequency="Once daily in the morning",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-02-12",
            raw_text="Omeprazole 20mg Delayed Release Capsule once daily morning before food",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d62.filename,
            source_page=1,
            confidence=0.68,  # Low confidence
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))
        # Test Case 9: Missing medication dosage
        db.add(Medication(
            patient_id=p6.id,
            document_id=d62.id,
            medication_name="Ibuprofen",
            dosage=None,  # Missing dosage!
            frequency="As needed for joint pain",
            route="Oral",
            clinical_status="ACTIVE",
            prescribed_date="2026-02-12",
            raw_text="Ibuprofen orally as needed for knee discomfort",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            source_document=d62.filename,
            source_page=1,
            confidence=0.90,
            verification_status=VerificationStatusEnum.UNVERIFIED,
        ))

        db.add(Condition(
            patient_id=p6.id,
            condition_name="Gastroesophageal Reflux Disease",
            icd10_code="K21.9",
            onset_date="2021-09-01",
            clinical_status="ACTIVE",
            raw_text="Gastroesophageal Reflux Disease",
            provenance_source=ProvenanceSourceEnum.DOCUMENT_EXTRACTION,
            verification_status=VerificationStatusEnum.VERIFIED,
        ))

        # Timeline for P6
        db.add(TimelineEvent(
            patient_id=p6.id,
            event_date="2026-02-05",
            event_type="LAB_TEST",
            title="Bio-Reference Routine Health Panel",
            description="Alanine Aminotransferase 28 U/L (NORMAL); Aspartate Aminotransferase 24 U/L (NORMAL); Vitamin B12 310 pg/mL (Range not provided).",
            source_document=d61.filename,
            source_page=1,
            importance="ROUTINE",
        ))
        db.add(TimelineEvent(
            patient_id=p6.id,
            event_date="2026-02-12",
            event_type="ENCOUNTER",
            title="Community Pharmacy Dispense Record",
            description="Omeprazole 20mg daily dispense log recorded. Ibuprofen noted PRN for knee discomfort.",
            source_document=d62.filename,
            source_page=1,
            importance="ROUTINE",
        ))

    # Ensure all document files for synthetic patients physically exist on disk
    all_synth_patients = db.query(Patient).filter(Patient.mrn.like("MED-SYNTH-%")).all()
    for sp in all_synth_patients:
        p_dir = os.path.join(settings.UPLOAD_DIR, sp.id)
        os.makedirs(p_dir, exist_ok=True)
        sp_docs = db.query(Document).filter(Document.patient_id == sp.id).all()
        for doc in sp_docs:
            if doc.raw_text and "SYNTHETIC DEMONSTRATION DATA" not in doc.raw_text:
                doc.raw_text = doc.raw_text + "\nSYNTHETIC DEMONSTRATION DATA"
            doc_path = os.path.join(p_dir, doc.filename)
            if not os.path.exists(doc_path):
                pages = db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).order_by(DocumentPage.page_number).all()
                if pages:
                    page_texts = [page.extracted_text for page in pages]
                else:
                    page_texts = [doc.raw_text or "SYNTHETIC DEMONSTRATION DATA"]
                create_synthetic_pdf(doc_path, doc.original_name or doc.filename, page_texts)

    # Ensure Eleanor has 3 documents if created early
    if p1 and db.query(Document).filter(Document.patient_id == p1.id).count() < 3:
        p1_dir = os.path.join(settings.UPLOAD_DIR, p1.id)
        doc3_name = "quest_diagnostics_cbc_aug2026.pdf"
        doc3_path = os.path.join(p1_dir, doc3_name)
        doc3_p1 = (
            "QUEST DIAGNOSTICS - CLINICAL LABORATORY REPORT\n"
            "Specimen Collected: 2026-08-12 07:45 AM | Received: 2026-08-12\n"
            "Patient: Vance, Eleanor | DOB: 1968-04-12 | MRN: MED-SYNTH-8492\n"
            "Test Name                Result    Reference Range    Status\n"
            "-----------------------------------------------------------\n"
            "Hemoglobin               11.2      12.0 - 16.0 g/dL   LOW\n"
            "Fasting Blood Glucose    94        70 - 99 mg/dL      NORMAL\n"
            "White Blood Cell Count   6.8       4.5 - 11.0 x10^3   NORMAL\n"
            "Serum Ferritin           19.5      [Not Provided]     --\n"
            "SYNTHETIC DEMONSTRATION DATA"
        )
        sz3, ck3 = create_synthetic_pdf(doc3_path, "Quest Diagnostics Laboratory Report", [doc3_p1])
        d3 = Document(
            id=str(uuid.uuid4()),
            patient_id=p1.id,
            filename=doc3_name,
            original_name="Quest_Diagnostics_CBC_Aug2026.pdf",
            file_type="application/pdf",
            file_size=sz3,
            checksum=ck3,
            page_count=1,
            processing_status="PROCESSED",
            raw_text=doc3_p1,
        )
        db.add(d3)
        db.flush()
        db.add(DocumentPage(document_id=d3.id, page_number=1, extracted_text=doc3_p1, confidence_score=0.99))


    # Backfill timeline events for any synthetic patient missing them
    timeline_backfill = {
        "MED-SYNTH-7321": [
            ("2026-01-15", "ENCOUNTER", "Allergy Clinic Assessment", "Valley Allergy Clinic visit. Severe Sulfa allergy documented; Cetirizine recorded for allergic rhinitis.", "allergy_assessment_2026.pdf"),
            ("2026-01-22", "LAB_TEST", "Hematology Panel Drawn", "Platelet Count 250 x10^3/uL (NORMAL). Peripheral smear platelet estimate adequate.", "faded_hematology_fax_2026.pdf"),
        ],
        "MED-SYNTH-2940": [
            ("2025-05-12", "ENCOUNTER", "Nephrology Baseline Consultation", "Initial renal assessment: Creatinine 1.32 mg/dL. Allopurinol 100mg daily initiated for hyperuricemia.", "nephrology_baseline_2025.pdf"),
            ("2026-01-20", "LAB_TEST", "LabCorp Renal Function Panel", "Creatinine 1.65 mg/dL (HIGH), BUN 29 mg/dL (HIGH), Uric Acid 7.8 mg/dL (Range not provided).", "renal_panel_2026.pdf"),
            ("2026-01-28", "ENCOUNTER", "Urgent Care Encounter (Gout Flare)", "Acute gout flare management. Allopurinol escalated to 300mg daily; Colchicine prescribed PRN.", "urgent_care_summary_2026.pdf"),
        ],
        "MED-SYNTH-6815": [
            ("2025-10-10", "ENCOUNTER", "Endocrine Consultation Note", "Endocrinology evaluation: Hypothyroidism management. Levothyroxine 75 mcg daily confirmed.", "endocrinology_notes_2025.pdf"),
            ("2026-02-01", "LAB_TEST", "Comprehensive Thyroid Panel", "TSH 8.40 mIU/L (HIGH), Free T4 0.61 ng/dL (LOW). Serum Sodium 140 mmol/L (NORMAL).", "thyroid_panel_2026.pdf"),
            ("2026-02-14", "ENCOUNTER", "Cardiopulmonary Summary", "Cardiology follow-up. Aspirin 81mg documented as tolerated without adverse reaction.", "cardiopulmonary_eval_2026.pdf"),
        ],
        "MED-SYNTH-9457": [
            ("2026-02-05", "LAB_TEST", "Bio-Reference Routine Health Panel", "Alanine Aminotransferase 28 U/L (NORMAL); Aspartate Aminotransferase 24 U/L (NORMAL); Vitamin B12 310 pg/mL (Range not provided).", "routine_health_panel_2026.pdf"),
            ("2026-02-12", "ENCOUNTER", "Community Pharmacy Dispense Record", "Omeprazole 20mg daily dispense log recorded. Ibuprofen noted PRN for knee discomfort.", "pharmacy_dispense_fax_2026.pdf"),
        ],
    }
    for sp in all_synth_patients:
        tl_count = db.query(TimelineEvent).filter(TimelineEvent.patient_id == sp.id).count()
        if tl_count == 0 and sp.mrn in timeline_backfill:
            for ev_date, ev_type, title, desc, s_doc in timeline_backfill[sp.mrn]:
                db.add(TimelineEvent(
                    patient_id=sp.id,
                    event_date=ev_date,
                    event_type=ev_type,
                    title=title,
                    description=desc,
                    source_document=s_doc,
                    source_page=1,
                    importance="SIGNIFICANT" if ("HIGH" in title or "Flare" in title or "Panel" in title) else "ROUTINE",
                ))


    # Commit all seeded records
    db.commit()
    db.refresh(p1)
    return p1



if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        primary = seed_synthetic_data(db)
        patients_count = db.query(Patient).count()
        print(f"\n========================================================")
        print(f"MEDLENS SYNTHETIC DEMO DATASET SEEDED SUCCESSFULLY")
        print(f"Total Fictional Patients: {patients_count}")
        print(f"Primary Patient: {primary.first_name} {primary.last_name} (MRN: {primary.mrn})")
        print(f"========================================================\n")
    finally:
        db.close()
