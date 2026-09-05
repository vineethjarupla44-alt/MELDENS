from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.db.models import Document, DocumentPage
from app.schemas.document import DocumentCreate, DocumentPageCreate

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_document(self, doc_in: DocumentCreate) -> Document:
        db_doc = Document(
            patient_id=doc_in.patient_id,
            filename=doc_in.filename,
            original_name=doc_in.original_name,
            file_type=doc_in.file_type,
            file_size=doc_in.file_size,
            processing_status=doc_in.processing_status,
            raw_text=doc_in.raw_text,
            page_count=doc_in.page_count,
            checksum=doc_in.checksum,
        )
        self.db.add(db_doc)
        self.db.commit()
        self.db.refresh(db_doc)
        return db_doc

    def add_page(self, page_in: DocumentPageCreate) -> DocumentPage:
        db_page = DocumentPage(
            document_id=page_in.document_id,
            page_number=page_in.page_number,
            extracted_text=page_in.extracted_text,
            ocr_applied=page_in.ocr_applied,
            confidence_score=page_in.confidence_score,
            width=page_in.width,
            height=page_in.height,
            image_path=page_in.image_path,
        )
        self.db.add(db_page)
        self.db.commit()
        self.db.refresh(db_page)
        return db_page

    def get_document(self, doc_id: str) -> Optional[Document]:
        return (
            self.db.query(Document)
            .options(joinedload(Document.pages))
            .filter(Document.id == doc_id)
            .first()
        )

    def list_by_patient(self, patient_id: str) -> List[Document]:
        return (
            self.db.query(Document)
            .options(joinedload(Document.pages))
            .filter(Document.patient_id == patient_id)
            .order_by(Document.upload_date.desc())
            .all()
        )
