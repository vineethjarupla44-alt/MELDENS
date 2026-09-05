from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import enum

class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class PageExtractionStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    OCR_REQUIRED = "OCR_REQUIRED"
    EMPTY = "EMPTY"
    FAILED = "FAILED"

class DocumentPageBase(BaseModel):
    page_number: int = Field(..., description="1-indexed page number within the document")
    extracted_text: Optional[str] = Field(None, description="Raw text extracted from this page")
    ocr_applied: bool = Field(default=False, description="Whether OCR was performed on this page")
    confidence_score: Optional[float] = Field(None, description="OCR/extraction confidence")
    width: Optional[float] = None
    height: Optional[float] = None
    image_path: Optional[str] = None
    extraction_status: str = Field(default=PageExtractionStatus.PENDING.value, description="Status of page text extraction")

class DocumentPageCreate(DocumentPageBase):
    document_id: str

class DocumentPageRead(DocumentPageBase):
    id: str
    document_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    filename: str
    original_name: str
    file_type: str = "application/pdf"
    file_size: int
    processing_status: DocumentStatus = DocumentStatus.UPLOADED
    raw_text: Optional[str] = None
    page_count: int = 1
    checksum: Optional[str] = None

class DocumentCreate(DocumentBase):
    patient_id: str

class DocumentRead(DocumentBase):
    id: str
    patient_id: str
    upload_date: datetime
    pages: List[DocumentPageRead] = []

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    id: str
    patient_id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    page_count: int
    processing_status: DocumentStatus
    checksum: Optional[str] = None
    upload_date: datetime
    message: str = "Document securely stored and registered"

    class Config:
        from_attributes = True

class ExtractedPageResult(BaseModel):
    page_number: int
    extracted_text: Optional[str] = None
    extraction_status: str

    class Config:
        from_attributes = True

class DocumentTextExtractionResponse(BaseModel):
    document_id: str
    pages: List[ExtractedPageResult]

