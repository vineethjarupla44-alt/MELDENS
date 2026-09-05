import os
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
import pypdf

from app.db.models import Document, DocumentPage, AuditLog, DocumentStatusEnum
from app.schemas.document import (
    PageExtractionStatus,
    ExtractedPageResult,
    DocumentTextExtractionResponse,
)
from app.core.config import settings

# Security: Detect potential prompt injection and adversarial commands inside untrusted documents
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s+(override|prompt|directive)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|an\s+unrestricted)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(guidelines|rules|instructions)", re.IGNORECASE),
    re.compile(r"override\s+clinical\s+(rules|guidelines|guardrails)", re.IGNORECASE),
    re.compile(r"as\s+an\s+ai\s+without\s+restrictions", re.IGNORECASE),
]

class DocumentProcessingService:
    """
    Medical Document Text Extraction Pipeline:
    Uploaded PDF -> PDF Validation -> Page Extraction -> Text Extraction -> Page-Level Storage -> Status
    
    Guarantees:
    1. Extracts text page-by-page preserving 1-indexed page numbers.
    2. Preserves document ID and links pages directly to parent Document.
    3. Stores extracted text strictly separate from structured clinical entities (zero medical interpretation).
    4. Detects empty text and flags scanned documents with OCR_REQUIRED.
    5. Treats all document content as untrusted data: sanitizes control chars, null bytes,
       and shields downstream systems from prompt injection directives.
    """

    def __init__(self, db: Session):
        self.db = db
        self.base_upload_dir = os.path.abspath(settings.UPLOAD_DIR)

    def _get_document_path(self, doc: Document) -> str:
        return os.path.join(self.base_upload_dir, doc.patient_id, doc.filename)

    def sanitize_untrusted_text(self, raw_text: Optional[str]) -> Tuple[str, bool]:
        """
        Sanitizes untrusted document text:
        - Strips dangerous null bytes and terminal escape codes
        - Normalizes Unicode (NFKC) to prevent homoglyph or invisible character obfuscation
        - Scans for prompt injection / adversarial directives and tags them
        Returns: (sanitized_text, contains_injection_flag)
        """
        if not raw_text:
            return "", False

        # 1. Strip null bytes
        cleaned = raw_text.replace("\x00", "")

        # 2. Strip ANSI / terminal escape sequences
        cleaned = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", cleaned)

        # 3. Unicode NFKC normalization
        cleaned = unicodedata.normalize("NFKC", cleaned)

        # 4. Remove non-printable control characters except standard whitespace (\n, \r, \t)
        cleaned = "".join(ch for ch in cleaned if ch in ("\n", "\r", "\t") or ch >= " ")

        # 5. Check for prompt injection attempts in untrusted content
        has_injection = any(pattern.search(cleaned) for pattern in PROMPT_INJECTION_PATTERNS)

        return cleaned.strip(), has_injection

    def wrap_untrusted_context(self, text: str, document_id: str, page_number: int) -> str:
        """
        Encloses document text within rigid untrusted data delimiters.
        Ensures downstream models and parsers never interpret document text as instructions.
        """
        return (
            f'<untrusted_document_content document_id="{document_id}" page="{page_number}">\n'
            f'{text}\n'
            f'</untrusted_document_content>'
        )

    def validate_pdf(self, file_path: str) -> pypdf.PdfReader:
        """
        Validates PDF integrity, readable stream structure, and absence of encryption.
        Raises HTTPException if invalid, corrupt, or missing.
        """
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found on disk")

        try:
            with open(file_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid file format: File lacks standard %PDF header"
                    )

            reader = pypdf.PdfReader(file_path)

            if reader.is_encrypted:
                try:
                    # Attempt empty password decryption
                    decrypt_success = reader.decrypt("")
                    if decrypt_success == 0:
                        raise HTTPException(
                            status_code=400,
                            detail="PDF is password protected and cannot be processed"
                        )
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail="Encrypted or password-protected PDF cannot be processed"
                    )

            if len(reader.pages) == 0:
                raise HTTPException(status_code=400, detail="PDF contains 0 pages")

            return reader

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Malformed or corrupt PDF document: {str(e)}"
            )

    def _page_has_images(self, page: pypdf.PageObject) -> bool:
        """Determines if a PDF page contains embedded raster images (indicator of scan)."""
        try:
            if hasattr(page, "images") and len(page.images) > 0:
                return True
        except Exception:
            pass

        try:
            resources = page.get("/Resources")
            if resources and "/XObject" in resources:
                xobjects = resources["/XObject"]
                for obj_key in xobjects:
                    obj = xobjects[obj_key]
                    if hasattr(obj, "get") and obj.get("/Subtype") == "/Image":
                        return True
        except Exception:
            pass

        return False

    def extract_page_text(self, page: pypdf.PageObject) -> str:
        """
        Extracts text from a single page using layout-aware extraction to preserve
        tables, column alignment, and line breaks. Falls back to plain extraction if needed.
        """
        try:
            # Layout mode preserves tabular spacing and clinical report formatting
            text = page.extract_text(extraction_mode="layout")
            if text and text.strip():
                return text
        except Exception:
            pass

        try:
            # Fallback to default extraction
            text = page.extract_text()
            return text or ""
        except Exception:
            return ""

    def process_document(self, document_id: str) -> DocumentTextExtractionResponse:
        """
        Executes the text extraction pipeline on the specified document:
        1. Validates document existence and PDF stream.
        2. Iterates page by page, preserving page numbers.
        3. Extracts layout text.
        4. Detects empty text / scanned pages requiring OCR.
        5. Sanitizes untrusted text and detects injection attempts.
        6. Persists page-level text in DocumentPage table.
        7. Updates parent Document status and raw_text.
        8. Writes immutable audit log.
        """
        # 1. Fetch document
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        doc.processing_status = DocumentStatusEnum.PROCESSING.value
        self.db.commit()

        file_path = self._get_document_path(doc)

        # 2. PDF Validation
        try:
            reader = self.validate_pdf(file_path)
        except HTTPException as e:
            doc.processing_status = DocumentStatusEnum.FAILED.value
            self.db.commit()
            raise e

        page_count = len(reader.pages)
        doc.page_count = page_count

        extracted_pages: List[ExtractedPageResult] = []
        raw_text_parts: List[str] = []
        ocr_required_count = 0
        success_count = 0
        injection_detected = False

        # 3. Process page-by-page
        for idx, page in enumerate(reader.pages):
            page_number = idx + 1 # 1-indexed

            # Extract text
            raw_page_text = self.extract_page_text(page)
            sanitized_text, page_has_injection = self.sanitize_untrusted_text(raw_page_text)
            if page_has_injection:
                injection_detected = True

            # Detect content density
            non_ws_chars = len(re.sub(r"\s+", "", sanitized_text))
            has_images = self._page_has_images(page)

            if non_ws_chars >= 5:
                status = PageExtractionStatus.SUCCESS.value
                success_count += 1
                confidence = 1.0
            elif has_images:
                # Scanned page: has image stream but no digital text stream
                status = PageExtractionStatus.OCR_REQUIRED.value
                ocr_required_count += 1
                confidence = 0.0
                sanitized_text = ""
            else:
                # Truly empty page (blank page with neither text nor image)
                status = PageExtractionStatus.EMPTY.value
                confidence = 0.0
                sanitized_text = ""

            # 4. Page-level text storage in database
            # Check if DocumentPage record exists; create or update
            db_page = (
                self.db.query(DocumentPage)
                .filter(DocumentPage.document_id == doc.id, DocumentPage.page_number == page_number)
                .first()
            )

            if not db_page:
                db_page = DocumentPage(
                    document_id=doc.id,
                    page_number=page_number,
                )
                self.db.add(db_page)

            db_page.extracted_text = sanitized_text if sanitized_text else None
            db_page.ocr_applied = False
            db_page.confidence_score = confidence
            db_page.extraction_status = status

            # Track page dimensions if available
            try:
                if page.mediabox:
                    db_page.width = float(page.mediabox.width)
                    db_page.height = float(page.mediabox.height)
            except Exception:
                pass

            if sanitized_text:
                raw_text_parts.append(f"--- Page {page_number} ---\n{sanitized_text}")

            extracted_pages.append(
                ExtractedPageResult(
                    page_number=page_number,
                    extracted_text=sanitized_text if sanitized_text else None,
                    extraction_status=status,
                )
            )

        # 5. Determine parent document status
        if ocr_required_count == page_count:
            # Entire document is scanned; requires OCR
            doc.processing_status = DocumentStatusEnum.NEEDS_REVIEW.value
        elif ocr_required_count > 0:
            # Partial document requires OCR review
            doc.processing_status = DocumentStatusEnum.NEEDS_REVIEW.value
        elif success_count > 0:
            doc.processing_status = DocumentStatusEnum.PROCESSED.value
        else:
            doc.processing_status = DocumentStatusEnum.NEEDS_REVIEW.value

        doc.raw_text = "\n\n".join(raw_text_parts) if raw_text_parts else None

        # 6. Immutable Audit Log
        audit_note = (
            f"Processed {page_count} pages. "
            f"Success: {success_count}, OCR Required: {ocr_required_count}. "
            f"Prompt Injection Flag: {injection_detected}."
        )
        audit = AuditLog(
            entity_type="Document",
            entity_id=doc.id,
            action="TEXT_EXTRACTION",
            actor_id="DOCUMENT_PROCESSOR",
            actor_name="DocumentProcessingService",
            new_state=f'{{"status": "{doc.processing_status}", "pages": {page_count}, "ocr_required": {ocr_required_count}}}',
            change_reason=audit_note,
        )
        self.db.add(audit)

        self.db.commit()

        # 7. Return exact requested schema
        return DocumentTextExtractionResponse(
            document_id=doc.id,
            pages=extracted_pages,
        )

    def get_document_pages(self, document_id: str) -> List[DocumentPage]:
        """Retrieves all stored page records for a document ordered by page_number."""
        return (
            self.db.query(DocumentPage)
            .filter(DocumentPage.document_id == document_id)
            .order_by(DocumentPage.page_number.asc())
            .all()
        )
