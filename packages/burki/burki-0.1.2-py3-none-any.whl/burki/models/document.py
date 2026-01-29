"""
Document models for the Burki SDK (RAG).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Document(BaseModel):
    """Represents a document in the knowledge base."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    assistant_id: int
    organization_id: int
    
    filename: str
    original_filename: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    
    status: str = "pending"  # pending, processing, completed, failed
    processing_progress: float = 0.0
    error_message: Optional[str] = None
    
    # Processing metadata
    chunk_count: Optional[int] = None
    total_tokens: Optional[int] = None
    
    # Storage
    storage_key: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentUpload(BaseModel):
    """Request model for uploading a document."""
    
    assistant_id: int
    auto_process: bool = True


class DocumentStatus(BaseModel):
    """Status of document processing."""
    
    id: int
    status: str
    processing_progress: float = 0.0
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None
    total_tokens: Optional[int] = None


class DocumentList(BaseModel):
    """Response model for listing documents."""
    
    items: List[Document]
    total: int


class DocumentChunk(BaseModel):
    """A chunk of a processed document."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    content: str
    chunk_index: int
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(BaseModel):
    """Model for creating/uploading a document."""
    
    assistant_id: int
    auto_process: bool = True


class DocumentUpdate(BaseModel):
    """Model for updating a document."""
    
    filename: Optional[str] = None
    status: Optional[str] = None


# Re-export all models
__all__ = [
    "Document",
    "DocumentUpload",
    "DocumentStatus",
    "DocumentList",
    "DocumentChunk",
    "DocumentCreate",
    "DocumentUpdate",
]
