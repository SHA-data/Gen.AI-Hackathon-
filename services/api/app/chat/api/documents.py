"""Documents and Upload API endpoint (Part B2.8, Part B2.13).
Upload CSVs (routed to finance import) or documents (PDF/Text/Docx to RAG ingestion).
"""
import hashlib
from typing import Dict, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel

from services.api.app.core.audit import audit_logger
from services.api.app.core.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentUploadResponse(BaseModel):
    document_id: UUID
    filename: str
    file_size_bytes: int
    content_hash: str
    target_pipeline: str  # 'finance_import' | 'rag_ingestion'
    status: str
    quality_report: Optional[Dict[str, str]] = None

_documents_db: Dict[UUID, DocumentUploadResponse] = {}
_hash_index: Dict[tuple[UUID, str], UUID] = {}

ALLOWED_MIME_TYPES = {
    "text/csv": "finance_import",
    "application/vnd.ms-excel": "finance_import",
    "application/pdf": "rag_ingestion",
    "text/plain": "rag_ingestion",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "rag_ingestion",
}

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    auth: AuthContext = Depends(get_auth_context),
):
    contents = await file.read()
    file_size = len(contents)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE} bytes",
        )

    # Calculate SHA-256 content hash
    content_hash = hashlib.sha256(contents).hexdigest()
    hash_key = (auth.org_id, content_hash)

    # Duplicate check per Part B2.8: UNIQUE(org_id, content_hash)
    if hash_key in _hash_index:
        existing_id = _hash_index[hash_key]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate file detected (hash: {content_hash[:8]}). Please specify if this is new data or a replacement.",
        )

    # Determine pipeline
    mime = file.content_type or "application/octet-stream"
    if file.filename.endswith(".csv"):
        mime = "text/csv"

    pipeline = ALLOWED_MIME_TYPES.get(mime)
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File format '{mime}' is not supported. Upload CSV for finance or PDF/Text for documents.",
        )

    doc_id = uuid4()
    quality_report = None
    if pipeline == "finance_import":
        # Simulate forward to Finance import contract
        quality_report = {
            "rows_parsed": "142",
            "date_range": "2026-04-01 to 2026-09-30",
            "duplicate_rows": "0",
            "inferred_schema": "date, description, amount, category",
            "status": "ready_for_cfo_engine",
        }

    doc_resp = DocumentUploadResponse(
        document_id=doc_id,
        filename=file.filename or "uploaded_file",
        file_size_bytes=file_size,
        content_hash=content_hash,
        target_pipeline=pipeline,
        status="completed" if pipeline == "finance_import" else "processing",
        quality_report=quality_report,
    )

    _documents_db[doc_id] = doc_resp
    _hash_index[hash_key] = doc_id

    # Append-only audit log
    await audit_logger.log(
        org_id=auth.org_id,
        actor_user_id=auth.user_id,
        action=f"upload:{pipeline}",
        entity_type="document",
        entity_id=doc_id,
        decision="stored",
        metadata={"filename": file.filename, "size": file_size},
    )

    return doc_resp

@router.get("/{id}/status")
async def get_document_status(
    id: UUID,
    auth: AuthContext = Depends(get_auth_context),
):
    doc = _documents_db.get(id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return {
        "document_id": str(doc.document_id),
        "status": doc.status,
        "filename": doc.filename,
        "quality_report": doc.quality_report,
    }
