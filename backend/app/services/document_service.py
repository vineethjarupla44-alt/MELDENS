import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentPage, TimelineEvent, AuditLog, Patient, DocumentStatusEnum
from app.core.config import settings
import pypdf

# Supported MIME types & extensions
ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.base_upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        os.makedirs(self.base_upload_dir, exist_ok=True)

    def _get_patient_upload_dir(self, patient_id: str) -> str:
        """Isolated storage per patient; prevents public folder traversal."""
        patient_dir = os.path.join(self.base_upload_dir, patient_id)
        os.makedirs(patient_dir, exist_ok=True)
        return patient_dir

    def _sanitize_filename(self, filename: str) -> str:
        """Strips path traversal artifacts and insecure characters."""
        basename = os.path.basename(filename)
        clean_name = "".join(c for c in basename if c.isalnum() or c in (".", "_", "-", " ")).strip()
        return clean_name or f"document_{uuid.uuid4().hex[:8]}"

    async def upload_document(
        self, 
        patient_id: str, 
        file: UploadFile,
        actor_name: str = "System Uploader"
    ) -> Document:
        """
        Securely uploads and registers a medical document.
        Validates file type and size.
        Computes SHA-256 checksum.
        Preserves original filename, upload timestamp, and patient ownership.
        """
        # 1. Verify Patient exists
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

        # 2. File type validation
        original_name = self._sanitize_filename(file.filename or "unknown_file")
        _, ext = os.path.splitext(original_name)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, PNG, JPG/JPEG."
            )

        content_type = file.content_type or ""
        if content_type not in ALLOWED_MIME_TYPES and ext != ".pdf":
            # Some browsers pass generic octet-stream for PDFs or images
            if ext == ".pdf":
                content_type = "application/pdf"
            elif ext == ".png":
                content_type = "image/png"
            elif ext in (".jpg", ".jpeg"):
                content_type = "image/jpeg"
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid MIME type '{content_type}' for extension '{ext}'."
                )

        # 3. Secure disk storage with random unique prefix
        patient_dir = self._get_patient_upload_dir(patient_id)
        file_uuid = str(uuid.uuid4())
        stored_filename = f"{file_uuid}_{original_name}"
        dest_path = os.path.join(patient_dir, stored_filename)

        # Ensure no path traversal escaped the patient directory
        if not os.path.abspath(dest_path).startswith(patient_dir):
            raise HTTPException(status_code=400, detail="Invalid destination file path")

        # 4. Stream file to disk and calculate SHA-256 checksum & file size
        hasher = hashlib.sha256()
        total_size = 0

        try:
            with open(dest_path, "wb") as f_out:
                while chunk := await file.read(1024 * 1024): # 1 MB chunks
                    total_size += len(chunk)
                    if total_size > MAX_FILE_SIZE_BYTES:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
                        )
                    hasher.update(chunk)
                    f_out.write(chunk)
        except Exception as e:
            if os.path.exists(dest_path):
                os.remove(dest_path)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        checksum = hasher.hexdigest()

        # 5. Page count extraction (pypdf for PDF, 1 for image)
        page_count = 1
        processing_status = DocumentStatusEnum.UPLOADED

        if ext == ".pdf":
            try:
                reader = pypdf.PdfReader(dest_path)
                page_count = len(reader.pages)
            except Exception as pdf_err:
                # PDF might be password-protected or malformed
                processing_status = DocumentStatusEnum.NEEDS_REVIEW

        # 6. Database record creation
        doc = Document(
            id=file_uuid,
            patient_id=patient_id,
            filename=stored_filename,
            original_name=original_name,
            file_type=content_type,
            file_size=total_size,
            upload_date=datetime.utcnow(),
            processing_status=processing_status.value,
            page_count=page_count,
            checksum=checksum,
        )
        self.db.add(doc)
        self.db.flush()

        # 7. Pre-create DocumentPage placeholders
        for p_num in range(1, page_count + 1):
            page_record = DocumentPage(
                document_id=doc.id,
                page_number=p_num,
                ocr_applied=False,
            )
            self.db.add(page_record)

        # 8. Timeline Event
        timeline_ev = TimelineEvent(
            patient_id=patient_id,
            event_date=datetime.utcnow().strftime("%Y-%m-%d"),
            event_type="DOCUMENT_UPLOAD",
            title=f"Medical Document Uploaded: {original_name}",
            description=f"Uploaded {ext.upper()} document ({page_count} pages, {total_size // 1024} KB). Checksum: {checksum[:8]}...",
            source_document=original_name,
            source_page=1,
            importance="ROUTINE",
        )
        self.db.add(timeline_ev)

        # 9. Audit Log
        audit = AuditLog(
            entity_type="Document",
            entity_id=doc.id,
            action="CREATE",
            actor_id="UPLOAD_HANDLER",
            actor_name=actor_name,
            new_state=f'{{"filename": "{original_name}", "size": {total_size}, "pages": {page_count}, "checksum": "{checksum}"}}',
            change_reason="Secure medical document upload",
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(doc)
        return doc

    def list_documents(self, patient_id: str) -> List[Document]:
        return (
            self.db.query(Document)
            .filter(Document.patient_id == patient_id)
            .order_by(Document.upload_date.desc())
            .all()
        )

    def get_document(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_document_file(self, document_id: str) -> Tuple[str, str, str]:
        """
        Retrieves file details for secure backend-controlled streaming.
        Returns: (absolute_file_path, original_filename, mime_type)
        """
        doc = self.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        file_path = os.path.join(self._get_patient_upload_dir(doc.patient_id), doc.filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Stored file missing from disk")

        return file_path, doc.original_name, doc.file_type

    def delete_document(self, document_id: str, actor_name: str = "User") -> bool:
        doc = self.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete physical file from disk
        file_path = os.path.join(self._get_patient_upload_dir(doc.patient_id), doc.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Failed to remove physical file {file_path}: {e}")

        # Audit Log for Deletion
        audit = AuditLog(
            entity_type="Document",
            entity_id=doc.id,
            action="DELETE",
            actor_id="DOCUMENT_HANDLER",
            actor_name=actor_name,
            previous_state=f'{{"filename": "{doc.original_name}", "patient_id": "{doc.patient_id}"}}',
            change_reason="User requested document deletion",
        )
        self.db.add(audit)

        self.db.delete(doc)
        self.db.commit()
        return True
